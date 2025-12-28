"""
Example usage patterns for the regex_recipes library.

This file demonstrates various ways to use regex_recipes for building regex patterns.
"""

# ============================================================================
# BASIC EXAMPLES
# ============================================================================

from regex_recipes import Regex, Str, Digit, Range, AllChars, ZeroOrMore, Optional, OneOrMore, WordChar, R


# Example 1: Simple literal pattern
def example_simple_literal() -> None:
    """Match a simple literal string."""
    pattern = Regex(Str("hello"))
    assert pattern.match("hello") is not None
    assert pattern.match("goodbye") is None


# Example 2: Concatenation with +
def example_concatenation() -> None:
    """Concatenate components."""
    pattern = Regex(Str("aaa"), ZeroOrMore(AllChars()), Str("bbb"))
    assert pattern.search("aaa anything here bbb") is not None


# Example 3: Using operator overloads
def example_operator_overloads() -> None:
    """Use + and | operators for composition."""
    # Concatenation
    pattern1 = Str("hello") + Str(" ") + WordChar().one_or_more()

    # Alternation
    pattern2 = Str("cat") | Str("dog") | Str("bird")
    print(f"Pattern1: {pattern1}")
    print(f"Pattern2: {pattern2}")    
    assert str(pattern1) == r"hello \w+"
    assert str(pattern2) == r"(?:cat|dog|bird)"


# ============================================================================
# CHARACTER CLASSES & QUANTIFIERS
# ============================================================================

def example_character_classes() -> None:
    """Work with character classes and quantifiers."""
    from regex_recipes import CharSet, Whitespace
    
    # Character set
    vowels = CharSet("aeiou")
    consonants = Range("b", "z")
    
    # Digit patterns
    single_digit = Digit()
    multiple_digits = Digit().one_or_more()  # \d+
    optional_digit = Digit().optional()       # \d?
    exact_three = Digit().repeat(3)           # \d{3}
    range_repeat = Digit().repeat(2, 5)       # \d{2,5}
    
    # Whitespace
    space = Whitespace()


# ============================================================================
# REAL-WORLD PATTERNS
# ============================================================================

def example_email_pattern() -> None:
    """Match email addresses."""
    email = Regex(
        WordChar().one_or_more(),          # username
        Str("@"),
        WordChar().one_or_more(),          # domain name
        Str("."),
        Range("a", "z").one_or_more()      # TLD
    ).ignore_case()  # Case-insensitive
    
    assert email.match("user@example.com") is not None
    assert email.match("invalid@.com") is None
    print(f"Email pattern: {email.pattern}")


def example_phone_number() -> None:
    """Match formatted phone numbers."""
    phone = Regex(
        Str("("),
        Digit().repeat(3),
        Str(")"),
        Digit().repeat(3),
        Str("-"),
        Digit().repeat(4)
    )
    
    assert phone.fullmatch("(555)123-4567") is not None
    assert phone.fullmatch("555-123-4567") is None
    print(f"Phone pattern: {phone.pattern}")


def example_url_pattern() -> None:
    """Match HTTP(S) URLs."""
    from regex_recipes import StartOfLine, EndOfLine
    
    url = Regex(
        StartOfLine(),
        Str("http"),
        Optional(Str("s")),
        Str("://"),
        WordChar().one_or_more(),
        Optional(Str(".") + WordChar().one_or_more()),
        EndOfLine()
    )
    
    assert url.match("https://example.com") is not None
    assert url.match("http://test") is not None
    assert url.match("ftp://fail.com") is None
    print(f"URL pattern: {url.pattern}")


def example_ipv4_address() -> None:
    """Match IPv4 addresses."""
    from regex_recipes import Either
    
    # 0-255
    octet = Either(
        Regex(Str("25"), Range("0", "5")),              # 250-255
        Regex(Str("2"), Range("0", "4"), Digit()),      # 200-249
        Regex(Str("1"), Digit(), Digit()),              # 100-199
        Regex(Range("1", "9"), Digit()),                # 10-99
        Digit()                                          # 0-9
    )
    
    ipv4 = Regex(
        octet, Str("."),
        octet, Str("."),
        octet, Str("."),
        octet
    )
    
    assert ipv4.fullmatch("192.168.1.1") is not None
    assert ipv4.fullmatch("256.1.1.1") is None


def example_credit_card() -> None:
    """Match credit card numbers (16 digits with optional dashes)."""
    card = Regex(
        Digit().repeat(4),
        Optional(Str("-")),
        Digit().repeat(4),
        Optional(Str("-")),
        Digit().repeat(4),
        Optional(Str("-")),
        Digit().repeat(4)
    )
    
    assert card.fullmatch("1234-5678-9012-3456") is not None
    assert card.fullmatch("1234567890123456") is not None
    assert card.fullmatch("1234-56789-0123-456") is None


# ============================================================================
# GROUPS & CAPTURE
# ============================================================================

def example_groups() -> None:
    """Use capturing and non-capturing groups."""
    from regex_recipes import Group, NonCapturingGroup, NamedGroup
    
    # Capturing group
    capturing = Regex(
        Str("name:"),
        Group(WordChar().one_or_more())
    )
    
    match = capturing.search("name:Alice")
    if match:
        print(f"Name captured: {match.group(1)}")
    
    # Non-capturing group (just for grouping, doesn't capture)
    non_capturing = Regex(
        Str("http"),
        NonCapturingGroup(Optional(Str("s"))),  # (?: optional without capture
        Str("://")
    )
    
    # Named group
    named = Regex(
        Str("user:"),
        NamedGroup("username", WordChar().one_or_more())
    )
    
    match = named.search("user:bob")
    if match:
        print(f"Username: {match.group('username')}")


# ============================================================================
# LOOKAROUNDS
# ============================================================================

def example_lookarounds() -> None:
    """Use lookahead and lookbehind assertions."""
    from regex_recipes import Lookahead, NegativeLookahead, Lookbehind, NegativeLookbehind
    
    # Positive lookahead: match digit followed by letter (but don't capture letter)
    digit_before_letter = Regex(
        Digit(),
        Lookahead(Range("a", "z"))
    )
    
    # Negative lookahead: match digit NOT followed by letter
    digit_not_letter = Regex(
        Digit(),
        NegativeLookahead(Range("a", "z"))
    )
    
    # Positive lookbehind: match letter preceded by digit
    letter_after_digit = Regex(
        Lookbehind(Digit()),
        Range("a", "z")
    )


# ============================================================================
# FLAGS & MODES
# ============================================================================

def example_flags() -> None:
    """Use regex flags for different matching modes."""
    import re
    
    pattern = Regex(Str("hello"))
    
    # Method 1: Set flag during building
    case_insensitive = pattern.ignore_case()
    assert case_insensitive.search("HELLO") is not None
    
    # Method 2: Pass flags at match time
    assert pattern.search("HELLO", flags=re.IGNORECASE) is not None
    
    # Chaining multiple flags
    multiline_verbose = pattern.multiline().dotall().verbose()


# ============================================================================
# BUILDER API (FLUENT STYLE)
# ============================================================================

def example_builder_api() -> None:
    """Use the fluent Builder API."""
    
    # Build step by step
    pattern = (R()
        .str("user")
        .str(":")
        .digit().repeat(1, 3)
        .str("@")
        .word_char().one_or_more()
        .build()
    )
    
    assert pattern.match("user:42@domain") is not None
    print(f"Pattern: {pattern.pattern}")


def example_builder_email() -> None:
    """Build email pattern with Builder."""
    pattern = (R()
        .word_char().one_or_more()
        .str("@")
        .word_char().one_or_more()
        .str(".")
        .range("a", "z").one_or_more()
        .build()
    ).ignore_case()
    
    assert pattern.match("test@example.com") is not None


# ============================================================================
# ALTERNATION
# ============================================================================

def example_alternation() -> None:
    """Use alternation (OR logic)."""
    from regex_recipes import Either
    
    # Option 1: Either class
    greeting = Either(Str("hello"), Str("hi"), Str("hey"))
    
    # Option 2: | operator
    color = Str("red") | Str("green") | Str("blue")
    
    assert Regex(greeting).match("hello") is not None
    assert Regex(color).match("blue") is not None


# ============================================================================
# MATCHING & SEARCHING
# ============================================================================

def example_matching() -> None:
    """Demonstrate different matching methods."""
    pattern = Regex(Digit().repeat(3))
    
    # match() - from start of string
    assert pattern.match("123abc") is not None
    assert pattern.match("abc123") is None
    
    # fullmatch() - entire string
    assert pattern.fullmatch("123") is not None
    assert pattern.fullmatch("123abc") is None
    
    # search() - anywhere in string
    assert pattern.search("abc123def") is not None
    
    # findall() - all matches
    digits_pattern = Regex(Digit().one_or_more())
    matches = digits_pattern.findall("I have 10 apples and 25 oranges")
    assert matches == ["10", "25"]
    
    # finditer() - iterator
    for match in digits_pattern.finditer("1 2 3"):
        print(f"Found: {match.group()}")
    
    # sub() - substitute
    result = digits_pattern.sub("X", "10 apples, 5 oranges")
    assert result == "X apples, X oranges"
    
    # subn() - substitute with count
    result, count = digits_pattern.subn("X", "1 2 3")
    assert result == "X X X"
    assert count == 3


# ============================================================================
# VALIDATION
# ============================================================================

def example_validation() -> None:
    """Validate patterns before use."""
    valid_pattern = Regex(Digit().one_or_more())
    
    # This should not raise
    valid_pattern.validate()
    print("Pattern is valid!")


# ============================================================================
# REUSABLE COMPONENTS
# ============================================================================

def example_reusable_components() -> None:
    """Build reusable components."""
    # Define once, reuse many times
    digits = Digit().one_or_more()
    dash = Str("-")
    
    # Phone number: 3-3-4
    phone = Regex(
        digits.repeat(3),
        dash,
        digits.repeat(3),
        dash,
        digits.repeat(4)
    )
    
    # Date: YYYY-MM-DD
    date = Regex(
        digits.repeat(4),
        dash,
        digits.repeat(2),
        dash,
        digits.repeat(2)
    )
    
    assert phone.fullmatch("555-123-4567") is not None
    assert date.fullmatch("2025-12-25") is not None


# ============================================================================
# RUNNING EXAMPLES
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("regex_recipes Library - Usage Examples")
    print("=" * 70)
    
    print("\n1. Simple Literal")
    example_simple_literal()
    print("   ✓ Passed")
    
    print("\n2. Concatenation")
    example_concatenation()
    print("   ✓ Passed")
    
    print("\n3. Operator Overloads")
    example_operator_overloads()
    print("   ✓ Passed")
    
    print("\n4. Character Classes")
    example_character_classes()
    print("   ✓ Passed")
    
    print("\n5. Email Pattern")
    example_email_pattern()
    print("   ✓ Passed")
    
    print("\n6. Phone Number")
    example_phone_number()
    print("   ✓ Passed")
    
    print("\n7. URL Pattern")
    example_url_pattern()
    print("   ✓ Passed")
    
    print("\n8. IPv4 Address")
    example_ipv4_address()
    print("   ✓ Passed")
    
    print("\n9. Credit Card")
    example_credit_card()
    print("   ✓ Passed")
    
    print("\n10. Groups & Capture")
    example_groups()
    print("    ✓ Passed")
    
    print("\n11. Lookarounds")
    example_lookarounds()
    print("    ✓ Passed")
    
    print("\n12. Flags")
    example_flags()
    print("    ✓ Passed")
    
    print("\n13. Builder API")
    example_builder_api()
    print("    ✓ Passed")
    
    print("\n14. Builder Email")
    example_builder_email()
    print("    ✓ Passed")
    
    print("\n15. Alternation")
    example_alternation()
    print("    ✓ Passed")
    
    print("\n16. Matching & Searching")
    example_matching()
    print("    ✓ Passed")
    
    print("\n17. Validation")
    example_validation()
    print("    ✓ Passed")
    
    print("\n18. Reusable Components")
    example_reusable_components()
    print("    ✓ Passed")
    
    print("\n" + "=" * 70)
    print("All examples passed! ✨")
    print("=" * 70)
