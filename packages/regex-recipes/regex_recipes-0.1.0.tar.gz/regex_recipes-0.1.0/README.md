# regex-recipes

A fluent, composable API for building regular expressions in Python. Say goodbye to cryptic regex strings and hello to readable, maintainable pattern building.

## Overview

`regex-recipes` provides a Pythonic, object-oriented approach to constructing regular expressions. Instead of writing complex regex strings, you can use an intuitive builder API that makes your patterns clear and self-documenting.

```python
from regex_recipes import Regex, Str, Digit, WordChar, Range

# Build an email pattern with readable, composable components
email = Regex(
    WordChar().one_or_more(),          # username
    Str("@"),
    WordChar().one_or_more(),          # domain
    Str("."),
    Range("a", "z").one_or_more()      # TLD
).ignore_case()

# Use it like a standard regex
email.match("user@example.com")  # ✓ Matches
```

## Features

- **Fluent API**: Chain methods for readable pattern construction
- **Composable Components**: Combine primitives into complex patterns
- **Type-Safe**: Full type hints for IDE support and runtime checking
- **Intuitive Syntax**: Use `+` for concatenation, `|` for alternation
- **Operator Overloading**: Natural Python expressions for regex composition
- **Pattern Reusability**: Build components once, use them anywhere
- **No Dependencies**: Pure Python implementation
- **Comprehensive Coverage**: Support for character classes, quantifiers, anchors, groups, and lookarounds

## Installation

Install from PyPI:

```bash
pip install regex-recipes
```

Or install with development dependencies:

```bash
pip install regex-recipes[dev]
```

## Quick Start

### Basic Literals

```python
from regex_recipes import Regex, Str

pattern = Regex(Str("hello"))
pattern.match("hello")      # Match object
pattern.match("goodbye")    # None
```

### Concatenation

```python
from regex_recipes import Regex, Str, Digit, WordChar

# Using direct composition
pattern = Regex(Str("User"), Digit().one_or_more())
# Equivalent to: r"User\d+"

# Or use the + operator
pattern = Str("hello") + Str(" ") + WordChar().one_or_more()
# Equivalent to: r"hello \w+"
```

### Alternation

```python
from regex_recipes import Str

# Using the | operator
pattern = Str("cat") | Str("dog") | Str("bird")
# Equivalent to: r"(?:cat|dog|bird)"
```

## Core Components

### Character Classes

```python
from regex_recipes import (
    Digit,              # \d
    WordChar,           # \w (letters, digits, underscore)
    Whitespace,         # \s
    AllChars,           # .
    CharSet,            # [abc]
    Range,              # [a-z]
)

# Single digit
pattern = Digit()

# Any word character
pattern = WordChar()

# Custom character set
pattern = CharSet("aeiou")  # Vowels

# Character range
pattern = Range("a", "z")   # Lowercase letters
pattern = Range("A", "Z")   # Uppercase letters
pattern = Range("0", "9")   # Digits (same as Digit())
```

### Quantifiers

```python
from regex_recipes import Digit

digit = Digit()

# Exactly one (default)
digit.repeat(1)

# Zero or more: *
digit.zero_or_more()

# One or more: +
digit.one_or_more()

# Optional (zero or one): ?
digit.optional()

# Exact count: {n}
digit.repeat(3)  # \d{3}

# Range: {n,m}
digit.repeat(2, 5)  # \d{2,5}

# At least n: {n,}
digit.repeat(3, None)  # \d{3,}
```

### Groups & Captures

```python
from regex_recipes import Group, NonCapturingGroup, NamedGroup, Digit

# Capturing group
group = Group(Digit().repeat(3))
# Equivalent to: (\d{3})

# Non-capturing group
group = NonCapturingGroup(Digit().repeat(3))
# Equivalent to: (?:\d{3})

# Named capturing group
group = NamedGroup("areacode", Digit().repeat(3))
# Equivalent to: (?P<areacode>\d{3})
```

### Anchors

```python
from regex_recipes import StartOfLine, EndOfLine, WordBoundary, Str

# Start of line: ^
pattern = StartOfLine() + Str("hello")

# End of line: $
pattern = Str("world") + EndOfLine()

# Word boundary: \b
pattern = WordBoundary() + Str("word") + WordBoundary()
```

### Lookarounds

```python
from regex_recipes import Lookahead, NegativeLookahead, Lookbehind, NegativeLookbehind

# Positive lookahead: (?=...)
pattern = Lookahead(Str("success"))

# Negative lookahead: (?!...)
pattern = NegativeLookahead(Str("failure"))

# Positive lookbehind: (?<=...)
pattern = Lookbehind(Str("after"))

# Negative lookbehind: (?<!...)
pattern = NegativeLookbehind(Str("before"))
```

## Regex API

The `Regex` class wraps your components and provides standard regex methods:

```python
from regex_recipes import Regex, Digit

pattern = Regex(Digit().repeat(3), "-", Digit().repeat(4))

# Match from the beginning
pattern.match("123-4567")

# Search anywhere in the string
pattern.search("Call me at 123-4567 today")

# Match the entire string
pattern.fullmatch("123-4567")

# Find all matches
pattern.findall("123-4567 and 987-6543")

# Replace matches
pattern.sub("XXX-XXXX", "Call 123-4567 now")

# Get the compiled pattern string
pattern.pattern  # r"\d{3}-\d{4}"

# Flags
pattern.ignore_case()
pattern.multiline()
pattern.dotall()
```

## Real-World Examples

### Email Validation

```python
from regex_recipes import Regex, WordChar, Str, Range

email = Regex(
    WordChar().one_or_more(),          # Local part
    Str("@"),
    WordChar().one_or_more(),          # Domain
    Str("."),
    Range("a", "z").one_or_more()      # TLD
).ignore_case()

assert email.match("user@example.com")
```

### Phone Number Formatting

```python
from regex_recipes import Regex, Digit, Str, Group, NamedGroup

phone = Regex(
    Str("("),
    NamedGroup("area", Digit().repeat(3)),
    Str(")"),
    NamedGroup("exchange", Digit().repeat(3)),
    Str("-"),
    NamedGroup("line", Digit().repeat(4))
)

assert phone.fullmatch("(555)123-4567")
```

### URL Pattern

```python
from regex_recipes import Regex, Str, Range, WordChar, AllChars

url = Regex(
    Str("http") + (Str("s")).optional(),  # https or http
    Str("://"),
    WordChar().one_or_more(),             # Domain
    Str("."),
    Range("a", "z").one_or_more(),        # TLD
    (Str("/") + AllChars().zero_or_more()).optional()  # Optional path
).ignore_case()

assert url.match("https://example.com/path")
```

### Hex Color Code

```python
from regex_recipes import Regex, Str, Range, CharSet

hex_color = Regex(
    Str("#"),
    CharSet("0123456789ABCDEFabcdef").repeat(6)
)

assert hex_color.fullmatch("#FF5733")
```

## Builder API

For more complex patterns, use the fluent `Builder` class:

```python
from regex_recipes import Builder

password = (Builder()
    .digit().one_or_more()              # At least one digit
    .raw(r"[A-Z]").one_or_more()        # At least one uppercase
    .raw(r"[a-z]").one_or_more()        # At least one lowercase
    .raw(r"[!@#$%^&*]").one_or_more()   # At least one special char
    .build())
```

## API Reference

### Component Base Methods

All components inherit from `Component` and support:

- `build()` → `str`: Generate the regex pattern string
- `__str__()` → `str`: Same as `build()`
- `__add__(other)` → `Sequence`: Concatenate components
- `__or__(other)` → `Either`: Create alternation
- `zero_or_more()` → `ZeroOrMore`: Match 0+ times (*)
- `one_or_more()` → `OneOrMore`: Match 1+ times (+)
- `optional()` → `Optional`: Match 0-1 times (?)
- `repeat(n, m=None)` → `Repeat`: Match n to m times

### Regex Methods

- `match(string)` → `Match | None`: Match at start of string
- `search(string)` → `Match | None`: Search anywhere
- `fullmatch(string)` → `Match | None`: Match entire string
- `findall(string)` → `list[Any]`: Find all matches
- `sub(repl, string)` → `str`: Replace all matches
- `split(string)` → `list[str]`: Split by pattern
- `ignore_case()` → `Regex`: Case-insensitive flag
- `multiline()` → `Regex`: Multiline mode
- `dotall()` → `Regex`: Dot matches newlines
- `pattern` → `str`: Get the regex pattern string

## Testing

Run the test suite:

```bash
pytest tests/
```

With coverage:

```bash
pytest --cov=regex_recipes tests/
```

## Development

### Setup

```bash
git clone https://github.com/adityavkulkarni/regex-recipes.git
cd regex-recipes
pip install -e ".[dev]"
```

### Code Quality

```bash
# Format code
black .

# Lint
ruff check .

# Type checking
mypy regex_recipes/
```

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

### v0.1.0 (Initial Release)

- Initial release with core components
- Fluent builder API
- Support for character classes, quantifiers, groups, and lookarounds
- Type hints and comprehensive documentation

## Inspiration

This library is inspired by similar fluent regex builders in other languages:
- JavaScript: [XRegExp](http://xregexp.com/)
- Java: [RegexBuilder](https://github.com/Kag0/RegexBuilder)
- Rust: [regex](https://docs.rs/regex/latest/regex/)

## Support

For questions, issues, or suggestions, please visit the [GitHub Issues](https://github.com/adityavkulkarni/regex-recipes/issues) page.
