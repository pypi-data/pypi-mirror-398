"""Nim handler for mkdocstrings."""

from importlib.metadata import PackageNotFoundError, version

from mkdocstrings_handlers.nim.collector import NimCollector, NimEntry, NimModule, NimParam
from mkdocstrings_handlers.nim.docstring import (
    DocstringStyle,
    ParamDoc,
    ParsedDocstring,
    RaisesDoc,
    ReturnsDoc,
    parse_docstring,
)
from mkdocstrings_handlers.nim.handler import NimHandler, get_handler

try:
    __version__ = version("mkdocstrings-nim")
except PackageNotFoundError:
    # Package not installed (development mode without pip install -e)
    __version__ = "0.0.0.dev"

__all__ = [
    "__version__",
    "NimHandler",
    "get_handler",
    "NimCollector",
    "NimModule",
    "NimEntry",
    "NimParam",
    "parse_docstring",
    "DocstringStyle",
    "ParsedDocstring",
    "ParamDoc",
    "ReturnsDoc",
    "RaisesDoc",
]
