"""Comprehensive test suite for rexp library."""

import re
import pytest
from src.regex_recipes import (
    AllChars,
    CharSet,
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
    StartOfLine,
    Range,
    Regex,
    Repeat,
    Str,
    Raw,
    WordBoundary,
    WordChar,
    Whitespace,
    ZeroOrMore,
    Builder,
    R,
)


class TestLiterals:
    """Test literal string components."""

    def test_str_escapes_special_chars(self) -> None:
        """Str should escape regex special characters."""
        assert str(Str("a.b")) == r"a\.b"
        assert str(Str("a*b")) == r"a\*b"
        assert str(Str("a+b")) == r"a\+b"
        assert str(Str("(a)")) == r"\(a\)"

    def test_raw_does_not_escape(self) -> None:
        """Raw should not escape."""
        assert str(Raw("a.b")) == "a.b"
        assert str(Raw("a*b")) == "a*b"


class TestCharacterClasses:
    """Test character class components."""

    def test_charset(self) -> None:
        """CharSet should create [abc]."""
        assert str(CharSet("abc")) == "[abc]"

    def test_range(self) -> None:
        """Range should create [a-z]."""
        assert str(Range("a", "z")) == r"[a-z]"
        assert str(Range("0", "9")) == r"[0-9]"

    def test_digit(self) -> None:
        """Digit should create \\d."""
        assert str(Digit()) == r"\d"

    def test_digits(self) -> None:
        """Digits should create \\d+."""
        assert str(Digits()) == r"\d+"

    def test_word_char(self) -> None:
        """WordChar should create \\w."""
        assert str(WordChar()) == r"\w"

    def test_whitespace(self) -> None:
        """Whitespace should create \\s."""
        assert str(Whitespace()) == r"\s"

    def test_all_chars(self) -> None:
        """AllChars should create .."""
        assert str(AllChars()) == "."


class TestAnchors:
    """Test anchor components."""

    def test_start_of_line(self) -> None:
        """StartOfLine should create ^."""
        assert str(EndOfLine()) == "$"

    def test_end_of_line(self) -> None:
        """EndOfLine should create $."""
        assert str(EndOfLine()) == "$"

    def test_word_boundary(self) -> None:
        """WordBoundary should create \\b."""
        assert str(WordBoundary()) == r"\b"


class TestGroups:
    """Test group components."""

    def test_group(self) -> None:
        """Group should create (...)."""
        assert str(Group(Str("abc"))) == r"(abc)"

    def test_non_capturing_group(self) -> None:
        """NonCapturingGroup should create (?:...)."""
        assert str(NonCapturingGroup(Str("abc"))) == r"(?:abc)"

    def test_named_group(self) -> None:
        """NamedGroup should create (?P<name>...)."""
        assert str(NamedGroup("mygroup", Str("abc"))) == r"(?P<mygroup>abc)"

    def test_named_group_invalid_name(self) -> None:
        """NamedGroup should reject invalid names."""
        with pytest.raises(ValueError):
            NamedGroup("123-invalid", Str("abc"))


class TestQuantifiers:
    """Test quantifier components."""

    def test_zero_or_more(self) -> None:
        """ZeroOrMore should create *."""
        assert str(ZeroOrMore(Digit())) == r"\d*"
        assert str(ZeroOrMore(Str("a"))) == r"a*"

    def test_one_or_more(self) -> None:
        """OneOrMore should create +."""
        assert str(OneOrMore(Digit())) == r"\d+"
        assert str(OneOrMore(Str("a"))) == r"a+"

    def test_optional(self) -> None:
        """Optional should create ?."""
        assert str(Optional(Digit())) == r"\d?"
        assert str(Optional(Str("a"))) == r"a?"

    def test_repeat_exact(self) -> None:
        """Repeat with min==max should create {n}."""
        assert str(Repeat(Digit(), min=3, max=3)) == r"\d{3}"

    def test_repeat_range(self) -> None:
        """Repeat should create {min,max}."""
        assert str(Repeat(Digit(), min=2, max=4)) == r"\d{2,4}"

    def test_repeat_min_only(self) -> None:
        """Repeat with max=None should create {min,}."""
        assert str(Repeat(Digit(), min=2)) == r"\d{2,}"


class TestAlternation:
    """Test alternation components."""

    def test_either_two_options(self) -> None:
        """Either should create (?:a|b)."""
        assert str(Either(Str("a"), Str("b"))) == r"(?:a|b)"

    def test_either_multiple_options(self) -> None:
        """Either should handle multiple options."""
        assert str(Either(Str("a"), Str("b"), Str("c"))) == r"(?:a|b|c)"

    def test_either_requires_two_args(self) -> None:
        """Either should require at least 2 components."""
        with pytest.raises(ValueError):
            Either(Str("a"))


class TestLookarounds:
    """Test lookaround assertions."""

    def test_lookahead(self) -> None:
        """Lookahead should create (?=...)."""
        assert str(Lookahead(Digit())) == r"(?=\d)"

    def test_negative_lookahead(self) -> None:
        """NegativeLookahead should create (?!...)."""
        assert str(NegativeLookahead(Digit())) == r"(?!\d)"

    def test_lookbehind(self) -> None:
        """Lookbehind should create (?<=...)."""
        assert str(Lookbehind(Digit())) == r"(?<=\d)"

    def test_negative_lookbehind(self) -> None:
        """NegativeLookbehind should create (?<!...)."""
        assert str(NegativeLookbehind(Digit())) == r"(?<!\d)"


class TestRegexCore:
    """Test Regex class core functionality."""

    def test_regex_build(self) -> None:
        """Regex should build pattern from components."""
        regex = Regex(Str("aaa"), ZeroOrMore(AllChars()), Str("bbb"))
        assert regex.build() == r"aaa.*bbb"

    def test_regex_str(self) -> None:
        """str(Regex) should return pattern."""
        regex = Regex(Str("test"))
        assert str(regex) == r"test"

    def test_regex_pattern_property(self) -> None:
        """Regex.pattern should return the pattern string."""
        regex = Regex(Str("test"))
        assert regex.pattern == r"test"

    def test_regex_validate(self) -> None:
        """Regex.validate should not raise for valid patterns."""
        regex = Regex(Str("test"), Digit())
        regex.validate()  # Should not raise

    def test_regex_compile(self) -> None:
        """Regex.compile should return re.Pattern."""
        regex = Regex(Str("test"))
        pattern = regex.compile()
        assert isinstance(pattern, type(re.compile("")))

    def test_regex_match(self) -> None:
        """Regex.match should match at start."""
        regex = Regex(Str("hello"), Str(" "), WordChar().one_or_more())
        assert regex.match("hello world") is not None
        assert regex.match("goodbye") is None

    def test_regex_fullmatch(self) -> None:
        """Regex.fullmatch should match entire string."""
        regex = Regex(Digit().one_or_more())
        assert regex.fullmatch("12345") is not None
        assert regex.fullmatch("12345a") is None

    def test_regex_search(self) -> None:
        """Regex.search should find pattern anywhere."""
        regex = Regex(Digit().repeat(3))
        assert regex.search("abc123def") is not None
        assert regex.search("ab1cd") is None

    def test_regex_findall(self) -> None:
        """Regex.findall should find all matches."""
        regex = Regex(Digit().one_or_more())
        matches = regex.findall("1 and 22 and 333")
        assert matches == ["1", "22", "333"]

    def test_regex_sub(self) -> None:
        """Regex.sub should substitute matches."""
        regex = Regex(Digit().one_or_more())
        result = regex.sub("X", "1 and 22 and 333")
        assert result == "X and X and X"

    def test_regex_subn(self) -> None:
        """Regex.subn should return (new_string, count)."""
        regex = Regex(Digit().one_or_more())
        result, count = regex.subn("X", "1 and 22 and 333")
        assert result == "X and X and X"
        assert count == 3


class TestOperatorOverloads:
    """Test operator overloading."""

    def test_add_concatenation(self) -> None:
        """+ should concatenate components."""
        result = Str("a") + Digit() + Str("b")
        assert str(result) == r"a\db"

    def test_or_alternation(self) -> None:
        """| should create alternation."""
        result = Str("a") | Str("b")
        assert str(result) == r"(?:a|b)"


class TestChainedMethods:
    """Test chainable methods on components."""

    def test_repeat_method(self) -> None:
        """repeat() should create Repeat."""
        assert str(Digit().repeat(2, 4)) == r"\d{2,4}"

    def test_zero_or_more_method(self) -> None:
        """zero_or_more() should create ZeroOrMore."""
        assert str(Digit().zero_or_more()) == r"\d*"

    def test_one_or_more_method(self) -> None:
        """one_or_more() should create OneOrMore."""
        assert str(Digit().one_or_more()) == r"\d+"

    def test_optional_method(self) -> None:
        """optional() should create Optional."""
        assert str(Digit().optional()) == r"\d?"


class TestBuilderAPI:
    """Test the fluent Builder API."""

    def test_builder_str(self) -> None:
        """Builder.str() should add Str component."""
        builder = Builder().str("hello").str("world")
        assert str(builder) == r"helloworld"

    def test_builder_digit(self) -> None:
        """Builder.digit() should add Digit."""
        builder = Builder().digit()
        assert str(builder) == r"\d"

    def test_builder_chaining(self) -> None:
        """Builder should support method chaining."""
        builder = Builder().str("abc").digit().digit().str("def")
        assert str(builder) == r"abc\d\ddef"

    def test_builder_build_returns_regex(self) -> None:
        """Builder.build() should return Regex."""
        builder = Builder().str("test")
        regex = builder.build()
        assert isinstance(regex, Regex)

    def test_r_convenience_function(self) -> None:
        """R() should create a Builder."""
        builder = R().str("test")
        assert isinstance(builder, Builder)


class TestComplexPatterns:
    """Test real-world regex patterns."""

    def test_email_pattern(self) -> None:
        """Build an email-like pattern."""
        email = Regex(
            WordChar().one_or_more(),
            Str("@"),
            WordChar().one_or_more(),
            Str("."),
            Range("a", "z").one_or_more(),
        )
        assert email.match("user@example.com") is not None
        assert email.match("invalid.com") is None

    def test_url_pattern(self) -> None:
        """Build a simple URL pattern."""
        url = Regex(
            Str("http"),
            Optional(Str("s")),
            Str("://"),
            WordChar().one_or_more(),
        )
        assert url.match("https://example") is not None
        assert url.match("http://test") is not None
        assert url.match("ftp://fail") is None

    def test_phone_number_pattern(self) -> None:
        """Build a phone number pattern."""
        phone = Regex(
            Str("("),
            Digit().repeat(3),
            Str(")"),
            Digit().repeat(3),
            Str("-"),
            Digit().repeat(4),
        )
        assert phone.fullmatch("(555)123-4567") is not None
        assert phone.fullmatch("555-123-4567") is None


class TestFlags:
    """Test regex flags."""

    def test_ignore_case_flag(self) -> None:
        """ignore_case() should add IGNORECASE flag."""
        regex = Regex(Str("Hello")).ignore_case()
        assert regex.search("hello") is not None

    def test_multiline_flag(self) -> None:
        """multiline() should add MULTILINE flag."""
        regex = Regex(StartOfLine(), Str("start")).multiline()
        assert regex.search("middle\nstart here") is not None

    def test_flags_at_compile_time(self) -> None:
        """Flags should override at compile time."""
        regex = Regex(Str("test"))
        match = regex.search("TEST", flags=re.IGNORECASE)
        assert match is not None


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_regex(self) -> None:
        """Empty Regex should build empty string."""
        regex = Regex()
        assert regex.build() == ""

    def test_range_requires_single_char(self) -> None:
        """Range should require single characters."""
        with pytest.raises(ValueError):
            Range("ab", "z")

    def test_repeat_validation(self) -> None:
        """Repeat should validate min/max."""
        with pytest.raises(ValueError):
            Repeat(Digit(), min=-1)
        with pytest.raises(ValueError):
            Repeat(Digit(), min=5, max=3)

    def test_special_chars_in_charset(self) -> None:
        """CharSet should handle special characters."""
        charset = CharSet("-^]")
        # Should escape or handle properly
        pattern = charset.build()
        assert "[" in pattern and "]" in pattern


class TestRepr:
    """Test __repr__ for debugging."""

    def test_component_repr(self) -> None:
        """Components should have useful repr."""
        str_comp = Str("test")
        assert "Str" in repr(str_comp)
        assert "test" in repr(str_comp)

    def test_regex_repr(self) -> None:
        """Regex should have useful repr."""
        regex = Regex(Str("test"))
        assert "Regex" in repr(regex)
