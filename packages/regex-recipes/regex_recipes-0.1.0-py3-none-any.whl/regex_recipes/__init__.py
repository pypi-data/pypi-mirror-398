"""rexp: A fluent, composable API for building regular expressions."""

__version__ = "0.1.0"
__author__ = "RExp Contributors"
__all__ = [
    # Core
    "Component",
    "Regex",
    # Literals
    "Str",
    "Raw",
    # Character classes
    "CharSet",
    "Range",
    "Digit",
    "Digits",
    "WordChar",
    "Whitespace",
    "AllChars",
    # Groups
    "Group",
    "NonCapturingGroup",
    "NamedGroup",
    # Quantifiers
    "ZeroOrMore",
    "OneOrMore",
    "Optional",
    "Repeat",
    # Anchors
    "StartOfLine",
    "EndOfLine",
    "WordBoundary",
    # Logical
    "Either",
    "Sequence",
    # Lookarounds
    "Lookahead",
    "NegativeLookahead",
    "Lookbehind",
    "NegativeLookbehind",
    # Convenience
    "Builder",
]

from regex_recipes.components import (
    AllChars,
    CharSet,
    Component,
    Digit,
    Digits,
    Either,
    EndOfLine,
    Group,
    Lookahead,
    Lookbehind,
    NamedGroup,
    NegativeLookahead,
    NegativeLookbehind,
    NonCapturingGroup,
    OneOrMore,
    Optional,
    Range,
    Regex,
    Repeat,
    Sequence,
    StartOfLine,
    Str,
    Raw,
    WordBoundary,
    WordChar,
    Whitespace,
    ZeroOrMore,
)
from regex_recipes.builder import Builder

def R() -> Builder:
    """Create a new regex builder instance."""
    return Builder()
