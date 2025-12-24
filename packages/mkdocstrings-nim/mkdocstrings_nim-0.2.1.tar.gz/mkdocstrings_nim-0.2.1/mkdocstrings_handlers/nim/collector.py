"""Collector for Nim documentation."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from collections import OrderedDict
from dataclasses import dataclass, field
from importlib.resources import as_file, files
from pathlib import Path
from typing import Any

from mkdocstrings import CollectionError

# Cache directory for compiled nimdocinfo binary
_CACHE_DIR = Path(tempfile.gettempdir()) / "mkdocstrings-nim-cache"

# Maximum number of modules to cache per collector instance
_MAX_CACHE_SIZE = 128

# Sentinel markers for JSON extraction (must match nimdocinfo.nim)
_JSON_START_MARKER = "<<MKDOCSTRINGS_JSON_START>>"
_JSON_END_MARKER = "<<MKDOCSTRINGS_JSON_END>>"


@dataclass
class NimParam:
    """A Nim parameter."""

    name: str
    type: str
    description: str = ""


@dataclass
class NimField:
    """A Nim type field or enum value."""

    name: str
    type: str
    doc: str = ""
    exported: bool = True
    branch: str = ""  # For case object branches: "when kind = x"


@dataclass
class NimEntry:
    """A documented Nim entry (proc, type, const, etc.)."""

    name: str
    kind: str
    line: int
    signature: str
    doc: str = ""
    params: list[NimParam] = field(default_factory=list)
    returns: str = ""
    returns_doc: str = ""
    pragmas: list[str] = field(default_factory=list)
    raises: list[str] = field(default_factory=list)
    exported: bool = True  # True if symbol has * (public API)
    fields: list[NimField] = field(default_factory=list)  # For object/ref object types
    values: list[NimField] = field(default_factory=list)  # For enum types


@dataclass
class NimModule:
    """A documented Nim module."""

    module: str
    file: str
    doc: str = ""
    entries: list[NimEntry] = field(default_factory=list)


class NimCollector:
    """Collects documentation from Nim source files."""

    def __init__(self, paths: list[str], base_dir: Path):
        """Initialize the collector.

        Args:
            paths: Search paths for Nim source files.
            base_dir: Base directory of the project.
        """
        self.paths = paths
        self.base_dir = base_dir
        self._cache: OrderedDict[str, tuple[float, NimModule]] = OrderedDict()
        # Use importlib.resources for reliable path resolution
        extractor_files = files("mkdocstrings_handlers.nim").joinpath("extractor")
        self._nimdocinfo_source = extractor_files.joinpath("nimdocinfo.nim")

    def _resolve_identifier(self, identifier: str) -> Path:
        """Resolve a module identifier to a file path.

        Args:
            identifier: Module identifier like 'lockfreequeues.ops'

        Returns:
            Path to the Nim source file.

        Raises:
            CollectionError: If the file cannot be found.
        """
        # Convert dots to path separators
        rel_path = identifier.replace(".", "/") + ".nim"

        for search_path in self.paths:
            full_path = self.base_dir / search_path / rel_path
            if full_path.exists():
                return full_path

        # Try without nested path (just filename)
        filename = identifier.split(".")[-1] + ".nim"
        for search_path in self.paths:
            full_path = self.base_dir / search_path / filename
            if full_path.exists():
                return full_path

        raise CollectionError(f"Could not find Nim file for identifier: {identifier}")

    def _ensure_nimdocinfo_compiled(self) -> Path:
        """Ensure nimdocinfo is compiled and return path to binary.

        Copies Nim source files to a cache directory and compiles them there.
        This avoids writing to the installed package directory.

        Thread-safe: Uses atomic rename pattern to handle concurrent compilation.

        Returns:
            Path to the compiled nimdocinfo binary.

        Raises:
            CollectionError: If compilation fails.
        """
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache_binary = _CACHE_DIR / "nimdocinfo"

        # Get the extractor package files
        extractor_pkg = files("mkdocstrings_handlers.nim").joinpath("extractor")

        with (
            as_file(extractor_pkg.joinpath("nimdocinfo.nim")) as src_main,
            as_file(extractor_pkg.joinpath("extractor.nim")) as src_extractor,
        ):
            # Fast path: binary exists and is up-to-date
            if cache_binary.exists():
                binary_mtime = cache_binary.stat().st_mtime
                if (
                    src_main.stat().st_mtime <= binary_mtime
                    and src_extractor.stat().st_mtime <= binary_mtime
                ):
                    return cache_binary

            # Need to compile - use atomic rename pattern for thread safety
            # Compile in a temp directory, then atomically rename
            with tempfile.TemporaryDirectory(dir=_CACHE_DIR) as tmp_dir:
                tmp_path = Path(tmp_dir)
                tmp_main = tmp_path / "nimdocinfo.nim"
                tmp_extractor = tmp_path / "extractor.nim"
                tmp_binary = tmp_path / "nimdocinfo"

                # Copy source files to temp directory
                shutil.copy2(src_main, tmp_main)
                shutil.copy2(src_extractor, tmp_extractor)

                # Compile in temp directory
                result = subprocess.run(
                    ["nim", "c", f"--outdir:{tmp_path}", str(tmp_main)],
                    capture_output=True,
                    text=True,
                    timeout=120,  # First compile can be slow
                )

                if result.returncode != 0:
                    raise CollectionError(f"Failed to compile nimdocinfo:\n{result.stderr}")

                # Atomic rename - if another process won the race, that's fine
                try:
                    os.replace(tmp_binary, cache_binary)
                except OSError:
                    # Another process may have beat us - check if binary exists
                    if not cache_binary.exists():
                        raise

            return cache_binary

    def _extract_json(self, stdout: str, filepath: Path) -> dict[str, Any]:
        """Extract JSON from stdout using sentinel markers.

        Args:
            stdout: Raw stdout from nimdocinfo.
            filepath: Path to the source file (for error messages).

        Returns:
            Parsed JSON data.

        Raises:
            CollectionError: If markers not found or JSON invalid.
        """
        start_idx = stdout.find(_JSON_START_MARKER)
        end_idx = stdout.find(_JSON_END_MARKER)

        if start_idx == -1 or end_idx == -1:
            # Truncate output for error message
            preview = stdout[:500] + ("..." if len(stdout) > 500 else "")
            raise CollectionError(
                f"Could not find JSON markers in nimdocinfo output for {filepath}.\n"
                f"This may indicate the nimdocinfo binary is outdated. "
                f"Try deleting the cache: rm -rf {_CACHE_DIR}\n"
                f"Output was:\n{preview}"
            )

        json_str = stdout[start_idx + len(_JSON_START_MARKER) : end_idx].strip()

        try:
            result: dict[str, Any] = json.loads(json_str)
            return result
        except json.JSONDecodeError as e:
            raise CollectionError(f"Invalid JSON from nimdocinfo: {e}") from e

    def _run_nimdocinfo(self, filepath: Path) -> dict[str, Any]:
        """Run nimdocinfo on a Nim file.

        Args:
            filepath: Path to the Nim source file.

        Returns:
            Parsed JSON output from nimdocinfo.

        Raises:
            CollectionError: If nimdocinfo fails.
        """
        try:
            binary_path = self._ensure_nimdocinfo_compiled()

            result = subprocess.run(
                [str(binary_path), str(filepath)],
                capture_output=True,
                text=True,
                cwd=str(self.base_dir),
                timeout=60,
            )

            if result.returncode != 0:
                raise CollectionError(
                    f"nimdocinfo failed:\n{result.stderr}\n\n"
                    f"To debug, run manually:\n"
                    f"  {binary_path} {filepath}"
                )

            # Extract JSON using sentinel markers
            return self._extract_json(result.stdout, filepath)

        except FileNotFoundError as e:
            raise CollectionError(
                "Nim compiler not found. Install from https://nim-lang.org/install.html\n"
                "Then verify installation: nim --version"
            ) from e
        except subprocess.TimeoutExpired as e:
            raise CollectionError(
                f"nimdocinfo timed out processing {filepath}. "
                "The file may be too complex or have circular imports."
            ) from e

    def _parse_module(self, data: dict[str, Any]) -> NimModule:
        """Parse JSON data into NimModule.

        Args:
            data: JSON data from nimdocinfo.

        Returns:
            Parsed NimModule.

        Raises:
            CollectionError: If required fields are missing.
        """
        # Validate required module-level fields
        required_fields = {"module", "file", "entries"}
        missing = required_fields - data.keys()
        if missing:
            raise CollectionError(
                f"Invalid nimdocinfo output: missing required fields {missing}. "
                f"Got keys: {list(data.keys())}"
            )

        entries = []
        for i, entry_data in enumerate(data.get("entries", [])):
            # Validate required entry-level fields
            entry_required = {"name", "kind", "line", "signature"}
            entry_missing = entry_required - entry_data.keys()
            if entry_missing:
                raise CollectionError(
                    f"Entry {i} missing required fields {entry_missing}. "
                    f"Got keys: {list(entry_data.keys())}"
                )

            params = [
                NimParam(name=p["name"], type=p["type"]) for p in entry_data.get("params", [])
            ]

            fields = [
                NimField(
                    name=f["name"],
                    type=f["type"],
                    doc=f.get("doc", ""),
                    exported=f.get("exported", True),
                    branch=f.get("branch", ""),
                )
                for f in entry_data.get("fields", [])
            ]

            values = [
                NimField(
                    name=v["name"],
                    type=v["type"],
                    doc=v.get("doc", ""),
                    exported=v.get("exported", True),
                    branch=v.get("branch", ""),
                )
                for v in entry_data.get("values", [])
            ]

            entries.append(
                NimEntry(
                    name=entry_data["name"],
                    kind=entry_data["kind"],
                    line=entry_data["line"],
                    signature=entry_data["signature"],
                    doc=entry_data.get("doc", ""),
                    params=params,
                    returns=entry_data.get("returns", ""),
                    pragmas=entry_data.get("pragmas", []),
                    raises=entry_data.get("raises", []),
                    exported=entry_data.get("exported", True),
                    fields=fields,
                    values=values,
                )
            )

        # Make file path relative to base_dir for source links
        file_path = Path(data["file"])
        try:
            relative_file = file_path.relative_to(self.base_dir)
        except ValueError:
            # If path is not relative to base_dir, use as-is
            relative_file = file_path

        return NimModule(
            module=data["module"],
            file=str(relative_file),
            doc=data.get("doc", ""),
            entries=entries,
        )

    def collect(self, identifier: str) -> NimModule:
        """Collect documentation for a module identifier.

        Uses LRU cache to avoid re-parsing modules. Cache is bounded
        to _MAX_CACHE_SIZE entries. Cache entries are invalidated when
        the source file is modified.

        Args:
            identifier: Module identifier like 'lockfreequeues.ops'

        Returns:
            NimModule with documentation.
        """
        filepath = self._resolve_identifier(identifier)
        current_mtime = filepath.stat().st_mtime

        if identifier in self._cache:
            cached_mtime, cached_module = self._cache[identifier]
            if cached_mtime == current_mtime:
                # Move to end for LRU behavior
                self._cache.move_to_end(identifier)
                return cached_module
            # File changed, remove stale entry
            del self._cache[identifier]

        data = self._run_nimdocinfo(filepath)
        module = self._parse_module(data)

        # Evict oldest entries if cache is full
        while len(self._cache) >= _MAX_CACHE_SIZE:
            self._cache.popitem(last=False)

        self._cache[identifier] = (current_mtime, module)
        return module
