"""Core component classes for regex pattern building."""

import re
from abc import ABC, abstractmethod
# from typing import Any, Iterable, List, Match, Optional, Pattern, Union
import typing


class Component(ABC):
    """Abstract base class for all regex pattern components."""

    @abstractmethod
    def build(self) -> str:
        """Build and return the regex pattern string."""
        pass

    def __str__(self) -> str:
        """Return the regex pattern string."""
        return self.build()

    def __repr__(self) -> str:
        """Return a string representation for debugging."""
        return f"{self.__class__.__name__}({self.build()!r})"

    def __add__(self, other: "Component") -> "Sequence":
        """Concatenate with another component using +."""
        if isinstance(other, Sequence):
            return Sequence(self, *other.components)
        return Sequence(self, other)

    def __radd__(self, other: "Component") -> "Sequence":
        """Right-hand concatenation."""
        if isinstance(other, Sequence):
            return Sequence(*other.components, self)
        return Sequence(other, self)

    def __or__(self, other: "Component") -> "Either":
        """Create alternation using |."""
        if isinstance(self, Either):
            return Either(*self.components, other)
        if isinstance(other, Either):
            return Either(self, *other.components)
        return Either(self, other)

    def __ror__(self, other: "Component") -> "Either":
        """Right-hand alternation."""
        if isinstance(other, Either):
            return Either(*other.components, self)
        if isinstance(self, Either):
            return Either(other, *self.components)
        return Either(other, self)

    def repeat(self, min: int = 0, max: typing.Optional[int] = None) -> "Repeat":
        """Return a Repeat wrapper with min/max bounds."""
        return Repeat(self, min=min, max=max)

    def zero_or_more(self) -> "ZeroOrMore":
        """Return a ZeroOrMore wrapper (same as *)."""
        return ZeroOrMore(self)

    def one_or_more(self) -> "OneOrMore":
        """Return a OneOrMore wrapper (same as +)."""
        return OneOrMore(self)

    def optional(self) -> "Optional":
        """Return an Optional wrapper (same as ?)."""
        return Optional(self)


class Str(Component):
    """Literal string component that escapes special regex characters."""

    def __init__(self, text: str) -> None:
        self.text = text

    def build(self) -> str:
        """Escape and return the literal string."""
        if set(self.text) == {" "}:
            return " "
        return re.escape(self.text)


class Raw(Component):
    """Raw regex pattern component (no escaping)."""

    def __init__(self, pattern: str) -> None:
        self.pattern = pattern

    def build(self) -> str:
        """Return the raw pattern without escaping."""
        return self.pattern


class CharSet(Component):
    """Character set component [abc]."""

    def __init__(self, chars: str) -> None:
        self.chars = chars

    def build(self) -> str:
        """Build the character set."""
        # Escape special chars that matter inside character classes
        escaped = self.chars.replace("\\", "\\\\").replace("]", r"\]").replace("^", r"\^").replace("-", r"\-")
        return f"[{escaped}]"


class Range(Component):
    """Character range component [a-z]."""

    def __init__(self, start: str, end: str) -> None:
        if len(start) != 1 or len(end) != 1:
            raise ValueError("Range start and end must be single characters")
        self.start = start
        self.end = end

    def build(self) -> str:
        """Build the character range."""
        return f"[{re.escape(self.start)}-{re.escape(self.end)}]"


class Digit(Component):
    """Single digit character class \\d."""

    def build(self) -> str:
        return r"\d"


class Digits(Component):
    """One or more digits \\d+."""

    def build(self) -> str:
        return r"\d+"


class WordChar(Component):
    """Word character class \\w."""

    def build(self) -> str:
        return r"\w"


class Whitespace(Component):
    """Whitespace character class \\s."""

    def build(self) -> str:
        return r"\s"


class AllChars(Component):
    """Any character (dot) .."""

    def build(self) -> str:
        return "."


class StartOfLine(Component):
    """Start of line anchor ^."""

    def build(self) -> str:
        return "^"


class EndOfLine(Component):
    """End of line anchor $."""

    def build(self) -> str:
        return "$"


class WordBoundary(Component):
    """Word boundary anchor \\b."""

    def build(self) -> str:
        return r"\b"


class Group(Component):
    """Capturing group ( ... )."""

    def __init__(self, component: Component) -> None:
        self.component = component

    def build(self) -> str:
        """Build a capturing group."""
        return f"({self.component.build()})"


class NonCapturingGroup(Component):
    """Non-capturing group (?: ... )."""

    def __init__(self, component: Component) -> None:
        self.component = component

    def build(self) -> str:
        """Build a non-capturing group."""
        return f"(?:{self.component.build()})"


class NamedGroup(Component):
    """Named capturing group (?P<name> ... )."""

    def __init__(self, name: str, component: Component) -> None:
        if not name.isidentifier():
            raise ValueError(f"Invalid group name: {name}")
        self.name = name
        self.component = component

    def build(self) -> str:
        """Build a named capturing group."""
        return f"(?P<{self.name}>{self.component.build()})"


class ZeroOrMore(Component):
    """Quantifier * (zero or more)."""

    def __init__(self, component: Component) -> None:
        self.component = component

    def build(self) -> str:
        """Build the zero-or-more quantifier."""
        inner = self._wrap_if_needed(self.component)
        return f"{inner}*"

    @staticmethod
    def _wrap_if_needed(component: Component) -> str:
        """Wrap component in non-capturing group if it's a complex component."""
        if isinstance(component, (Group, NonCapturingGroup, NamedGroup)):
            return component.build()
        if isinstance(component, (Str, Raw, Digit, WordChar, Whitespace, AllChars, CharSet, Range)):
            return component.build()
        return f"(?:{component.build()})"


class OneOrMore(Component):
    """Quantifier + (one or more)."""

    def __init__(self, component: Component) -> None:
        self.component = component

    def build(self) -> str:
        """Build the one-or-more quantifier."""
        inner = ZeroOrMore._wrap_if_needed(self.component)
        return f"{inner}+"


class Optional(Component):
    """Quantifier ? (zero or one)."""

    def __init__(self, component: Component) -> None:
        self.component = component

    def build(self) -> str:
        """Build the optional quantifier."""
        inner = ZeroOrMore._wrap_if_needed(self.component)
        return f"{inner}?"


class Repeat(Component):
    """Bounded repetition {min,max}."""

    def __init__(self, component: Component, min: int = 0, max: typing.Optional[int] = None) -> None:
        if min < 0:
            raise ValueError("min must be >= 0")
        if max is not None and max < min:
            raise ValueError("max must be >= min")
        self.component = component
        self.min = min
        self.max = max

    def build(self) -> str:
        """Build the repeat quantifier."""
        inner = ZeroOrMore._wrap_if_needed(self.component)
        if self.max is None:
            return f"{inner}{{{self.min},}}"
        if self.min == self.max:
            return f"{inner}{{{self.min}}}"
        return f"{inner}{{{self.min},{self.max}}}"


class Sequence(Component):
    """Sequence of components."""

    def __init__(self, *components: Component) -> None:
        self.components: typing.List[Component] = []
        for component in components:
            if isinstance(component, Sequence):
                self.components.extend(component.components)
            else:
                self.components.append(component)

    def build(self) -> str:
        """Build the sequence."""
        return "".join(c.build() for c in self.components)


class Either(Component):
    """Alternation (a|b|c) wrapped in non-capturing group."""

    def __init__(self, *components: Component) -> None:
        if len(components) < 2:
            raise ValueError("Either requires at least 2 components")
        self.components: typing.List[Component] = []
        for component in components:
            if isinstance(component, Either):
                self.components.extend(component.components)
            else:
                self.components.append(component)

    def build(self) -> str:
        """Build the alternation."""
        parts = "|".join(c.build() for c in self.components)
        return f"(?:{parts})"


class Lookahead(Component):
    """Positive lookahead (?= ... )."""

    def __init__(self, component: Component) -> None:
        self.component = component

    def build(self) -> str:
        """Build the positive lookahead."""
        return f"(?={self.component.build()})"


class NegativeLookahead(Component):
    """Negative lookahead (?! ... )."""

    def __init__(self, component: Component) -> None:
        self.component = component

    def build(self) -> str:
        """Build the negative lookahead."""
        return f"(?!{self.component.build()})"


class Lookbehind(Component):
    """Positive lookbehind (?<= ... )."""

    def __init__(self, component: Component) -> None:
        self.component = component

    def build(self) -> str:
        """Build the positive lookbehind."""
        return f"(?<={self.component.build()})"


class NegativeLookbehind(Component):
    """Negative lookbehind (?<! ... )."""

    def __init__(self, component: Component) -> None:
        self.component = component

    def build(self) -> str:
        """Build the negative lookbehind."""
        return f"(?<!{self.component.build()})"


class Regex:
    """Root regex builder and pattern container."""

    def __init__(self, *components: Component) -> None:
        self.components: typing.List[Component] = []
        for component in components:
            if isinstance(component, Sequence):
                self.components.extend(component.components)
            else:
                self.components.append(component)
        self._flags: int = 0

    def build(self) -> str:
        """Build the complete pattern string."""
        return "".join(c.build() for c in self.components)

    def __str__(self) -> str:
        """Return the regex pattern string."""
        return self.build()

    def __repr__(self) -> str:
        """Return a string representation for debugging."""
        return f"Regex({self.build()!r})"

    @property
    def pattern(self) -> str:
        """Get the regex pattern string."""
        return self.build()

    def validate(self) -> None:
        """Validate the pattern by attempting to compile it."""
        try:
            re.compile(self.build(), self._flags)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {e}") from e

    def compile(self, flags: int = 0) -> typing.Pattern[str]:
        """Compile the pattern to a re.Pattern object."""
        combined_flags = self._flags | flags
        return re.compile(self.build(), combined_flags)

    def with_flags(self, flags: int) -> "Regex":
        """Return a new Regex with additional flags."""
        new_regex = Regex(*self.components)
        new_regex._flags = self._flags | flags
        return new_regex

    def ignore_case(self) -> "Regex":
        """Return a new Regex with IGNORECASE flag."""
        return self.with_flags(re.IGNORECASE)

    def multiline(self) -> "Regex":
        """Return a new Regex with MULTILINE flag."""
        return self.with_flags(re.MULTILINE)

    def dotall(self) -> "Regex":
        """Return a new Regex with DOTALL flag."""
        return self.with_flags(re.DOTALL)

    def verbose(self) -> "Regex":
        """Return a new Regex with VERBOSE flag."""
        return self.with_flags(re.VERBOSE)

    def match(self, string: str, flags: int = 0) -> typing.Optional[typing.Match[str]]:
        """Match pattern at the beginning of the string."""
        return self.compile(flags).match(string)

    def fullmatch(self, string: str, flags: int = 0) -> typing.Optional[typing.Match[str]]:
        """Match the entire string."""
        return self.compile(flags).fullmatch(string)

    def search(self, string: str, flags: int = 0) -> typing.Optional[typing.Match[str]]:
        """Search for the pattern in the string."""
        return self.compile(flags).search(string)

    def findall(self, string: str, flags: int = 0) -> typing.List[typing.Any]:
        """Find all non-overlapping matches."""
        return self.compile(flags).findall(string)

    def finditer(self, string: str, flags: int = 0) -> typing.Iterable[typing.Match[str]]:
        """Find all non-overlapping matches as an iterator."""
        return self.compile(flags).finditer(string)

    def sub(self, repl: typing.Union[str, typing.Any], string: str, count: int = 0, flags: int = 0) -> str:
        """Substitute first count occurrences."""
        return self.compile(flags).sub(repl, string, count)

    def subn(self, repl: typing.Union[str, typing.Any], string: str, count: int = 0, flags: int = 0) -> typing.Tuple[str, int]:
        """Substitute and return (new_string, number_of_subs_made)."""
        return self.compile(flags).subn(repl, string, count)
