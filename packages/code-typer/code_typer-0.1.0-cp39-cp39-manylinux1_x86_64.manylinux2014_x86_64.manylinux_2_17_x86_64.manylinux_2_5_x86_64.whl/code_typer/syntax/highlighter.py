"""Base syntax highlighter with token classification."""

import re
from collections.abc import Generator
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional


class TokenType(Enum):
    """Types of tokens for syntax highlighting."""

    TEXT = auto()  # Plain text
    KEYWORD = auto()  # Language keywords
    STRING = auto()  # String literals
    COMMENT = auto()  # Comments
    NUMBER = auto()  # Numeric literals
    FUNCTION = auto()  # Function names
    CLASS = auto()  # Class names
    OPERATOR = auto()  # Operators
    DECORATOR = auto()  # Decorators (Python @...)
    BUILTIN = auto()  # Built-in functions/types
    VARIABLE = auto()  # Variables
    PUNCTUATION = auto()  # Brackets, commas, etc.
    WHITESPACE = auto()  # Spaces, tabs, newlines


@dataclass
class Token:
    """A single token with its type and text."""

    token_type: TokenType
    text: str
    start: int  # Start position in original text
    end: int  # End position in original text


class Highlighter:
    """Base syntax highlighter.

    Provides basic tokenization. Subclasses implement language-specific rules.
    """

    def __init__(self):
        """Initialize the highlighter."""
        self._token_patterns: list[tuple[str, TokenType]] = []
        self._compiled_pattern: Optional[re.Pattern] = None
        self._setup_patterns()
        # Cache the compiled pattern after setup
        self._compiled_pattern = self._compile_patterns()

    def _setup_patterns(self) -> None:
        """Set up regex patterns for tokenization. Override in subclasses."""
        # Base patterns that work for most languages
        self._token_patterns = [
            # Whitespace
            (r"[ \t]+", TokenType.WHITESPACE),
            (r"\n", TokenType.WHITESPACE),
            # Numbers
            (r"\b\d+\.?\d*\b", TokenType.NUMBER),
            # Identifiers (default to TEXT)
            (r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", TokenType.TEXT),
            # Operators
            (r"[+\-*/%=<>!&|^~]+", TokenType.OPERATOR),
            # Punctuation
            (r"[(){}\[\],;:.]+", TokenType.PUNCTUATION),
            # Anything else
            (r".", TokenType.TEXT),
        ]

    def _compile_patterns(self) -> re.Pattern:
        """Compile all patterns into a single regex.

        This is called once during __init__ and the result is cached.
        """
        pattern_parts = []
        for i, (pattern, _) in enumerate(self._token_patterns):
            pattern_parts.append(f"(?P<t{i}>{pattern})")

        combined = "|".join(pattern_parts)
        return re.compile(combined, re.MULTILINE)

    def _get_token_type(self, match: re.Match) -> TokenType:
        """Get the token type from a match object."""
        for i, (_, token_type) in enumerate(self._token_patterns):
            if match.group(f"t{i}") is not None:
                return token_type
        return TokenType.TEXT

    def tokenize(self, content: str) -> Generator[Token, None, None]:
        """Tokenize content into a sequence of tokens.

        Args:
            content: The source code to tokenize

        Yields:
            Token objects for each recognized token
        """
        # Use cached compiled pattern for performance
        assert self._compiled_pattern is not None

        for match in self._compiled_pattern.finditer(content):
            token_type = self._get_token_type(match)
            text = match.group()
            yield Token(
                token_type=token_type, text=text, start=match.start(), end=match.end()
            )

    def get_token_at(self, content: str, position: int) -> Optional[Token]:
        """Get the token at a specific position.

        Args:
            content: The source code
            position: Character position

        Returns:
            Token at the position, or None
        """
        for token in self.tokenize(content):
            if token.start <= position < token.end:
                return token
        return None
