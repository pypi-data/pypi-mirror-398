"""Fluent builder API for regex construction."""

from typing import Optional, Union

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
    Optional as OptionalComp,
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


class Builder:
    """Fluent builder for constructing regex patterns."""

    def __init__(self) -> None:
        self._components: list[Component] = []

    def str(self, text: str) -> "Builder":
        """Add a literal string (auto-escaped)."""
        self._components.append(Str(text))
        return self

    def raw(self, pattern: str) -> "Builder":
        """Add a raw regex pattern (no escaping)."""
        self._components.append(Raw(pattern))
        return self

    def char_set(self, chars: str) -> "Builder":
        """Add a character set [abc]."""
        self._components.append(CharSet(chars))
        return self

    def range(self, start: str, end: str) -> "Builder":
        """Add a character range [a-z]."""
        self._components.append(Range(start, end))
        return self

    def digit(self) -> "Builder":
        """Add a single digit \\d."""
        self._components.append(Digit())
        return self

    def digits(self) -> "Builder":
        """Add one or more digits \\d+."""
        self._components.append(Digits())
        return self

    def word_char(self) -> "Builder":
        """Add a word character \\w."""
        self._components.append(WordChar())
        return self

    def whitespace(self) -> "Builder":
        """Add a whitespace character \\s."""
        self._components.append(Whitespace())
        return self

    def any(self) -> "Builder":
        """Add any character (dot)."""
        self._components.append(AllChars())
        return self

    def start_of_line(self) -> "Builder":
        """Add start of line anchor ^."""
        self._components.append(StartOfLine())
        return self

    def end_of_line(self) -> "Builder":
        """Add end of line anchor $."""
        self._components.append(EndOfLine())
        return self

    def word_boundary(self) -> "Builder":
        """Add word boundary anchor \\b."""
        self._components.append(WordBoundary())
        return self

    def group(self, component: Component) -> "Builder":
        """Add a capturing group."""
        self._components.append(Group(component))
        return self

    def non_capturing_group(self, component: Component) -> "Builder":
        """Add a non-capturing group."""
        self._components.append(NonCapturingGroup(component))
        return self

    def named_group(self, name: str, component: Component) -> "Builder":
        """Add a named capturing group."""
        self._components.append(NamedGroup(name, component))
        return self

    def zero_or_more(self) -> "Builder":
        """Apply zero-or-more quantifier * to last component."""
        if not self._components:
            raise ValueError("No component to quantify")
        last = self._components.pop()
        self._components.append(ZeroOrMore(last))
        return self

    def one_or_more(self) -> "Builder":
        """Apply one-or-more quantifier + to last component."""
        if not self._components:
            raise ValueError("No component to quantify")
        last = self._components.pop()
        self._components.append(OneOrMore(last))
        return self

    def optional(self) -> "Builder":
        """Apply optional quantifier ? to last component."""
        if not self._components:
            raise ValueError("No component to quantify")
        last = self._components.pop()
        self._components.append(OptionalComp(last))
        return self

    def repeat(self, min: int = 0, max: Optional[int] = None) -> "Builder":
        """Apply repeat {min,max} quantifier to last component."""
        if not self._components:
            raise ValueError("No component to quantify")
        last = self._components.pop()
        self._components.append(Repeat(last, min=min, max=max))
        return self

    def either(self, *components: Component) -> "Builder":
        """Add alternation (a|b|c)."""
        if len(components) < 2:
            raise ValueError("Either requires at least 2 components")
        self._components.append(Either(*components))
        return self

    def lookahead(self, component: Component) -> "Builder":
        """Add positive lookahead (?= ... )."""
        self._components.append(Lookahead(component))
        return self

    def negative_lookahead(self, component: Component) -> "Builder":
        """Add negative lookahead (?! ... )."""
        self._components.append(NegativeLookahead(component))
        return self

    def lookbehind(self, component: Component) -> "Builder":
        """Add positive lookbehind (?<= ... )."""
        self._components.append(Lookbehind(component))
        return self

    def negative_lookbehind(self, component: Component) -> "Builder":
        """Add negative lookbehind (?<! ... )."""
        self._components.append(NegativeLookbehind(component))
        return self

    def build(self) -> Regex:
        """Build and return a Regex instance."""
        return Regex(*self._components)

    def __str__(self) -> str:
        """Return the pattern string."""
        return self.build().build()
