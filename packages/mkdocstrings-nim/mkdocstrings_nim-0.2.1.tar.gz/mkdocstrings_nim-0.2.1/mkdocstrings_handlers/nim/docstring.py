"""Docstring parsing for Nim documentation."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

import docstring_parser
from docstring_parser import DocstringStyle as DPStyle
from docstring_parser import ParseError
from mkdocstrings import get_logger

_logger = get_logger(__name__)


class DocstringStyle(Enum):
    """Supported docstring styles."""

    RST = "rst"
    GOOGLE = "google"
    NUMPY = "numpy"
    EPYDOC = "epydoc"
    AUTO = "auto"


@dataclass
class ParamDoc:
    """Parsed parameter documentation."""

    name: str
    description: str = ""
    type: str = ""


@dataclass
class ReturnsDoc:
    """Parsed return value documentation."""

    description: str = ""
    type: str = ""


@dataclass
class RaisesDoc:
    """Parsed raises documentation."""

    type: str
    description: str = ""


@dataclass
class ParsedDocstring:
    """Parsed docstring with structured sections."""

    description: str = ""
    params: list[ParamDoc] = field(default_factory=list)
    returns: ReturnsDoc | None = None
    raises: list[RaisesDoc] = field(default_factory=list)
    examples: list[str] = field(default_factory=list)


# Map our style enum to docstring_parser's style enum
_STYLE_MAP = {
    DocstringStyle.RST: DPStyle.REST,
    DocstringStyle.GOOGLE: DPStyle.GOOGLE,
    DocstringStyle.NUMPY: DPStyle.NUMPYDOC,
    DocstringStyle.EPYDOC: DPStyle.EPYDOC,
    DocstringStyle.AUTO: DPStyle.AUTO,
}


def parse_docstring(doc: str, style: DocstringStyle = DocstringStyle.RST) -> ParsedDocstring:
    """Parse a docstring according to the specified style.

    Uses the docstring_parser library for robust parsing of RST, Google,
    and NumPy docstring formats.

    Args:
        doc: Raw docstring text.
        style: Docstring style to use for parsing.

    Returns:
        Parsed docstring structure.
    """
    if not doc:
        return ParsedDocstring()

    dp_style = _STYLE_MAP.get(style, DPStyle.REST)

    try:
        parsed = docstring_parser.parse(doc, style=dp_style)
    except (ParseError, ValueError) as e:
        # Fall back to auto-detection if specified style fails
        _logger.debug(f"Failed to parse docstring with {style}: {e}")
        try:
            parsed = docstring_parser.parse(doc)
        except (ParseError, ValueError) as e:
            # If all parsing fails, just return description
            _logger.debug(f"Auto-detection also failed: {e}")
            return ParsedDocstring(description=doc.strip())

    result = ParsedDocstring()

    # Extract description (short + long)
    desc_parts = []
    if parsed.short_description:
        desc_parts.append(parsed.short_description)
    if parsed.long_description:
        desc_parts.append(parsed.long_description)
    result.description = "\n\n".join(desc_parts)

    # Extract parameters
    for param in parsed.params:
        result.params.append(
            ParamDoc(
                name=param.arg_name,
                description=param.description or "",
                type=param.type_name or "",
            )
        )

    # Extract returns
    if parsed.returns:
        result.returns = ReturnsDoc(
            description=parsed.returns.description or "",
            type=parsed.returns.type_name or "",
        )

    # Extract raises
    for raises in parsed.raises:
        result.raises.append(
            RaisesDoc(
                type=raises.type_name or "",
                description=raises.description or "",
            )
        )

    # Extract examples
    for example in parsed.examples:
        if example.description:
            result.examples.append(example.description)

    return result
