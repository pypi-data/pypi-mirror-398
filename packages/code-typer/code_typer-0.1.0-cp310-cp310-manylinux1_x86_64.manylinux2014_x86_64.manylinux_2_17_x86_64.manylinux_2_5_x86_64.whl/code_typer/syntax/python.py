"""Python syntax highlighting."""

from collections.abc import Generator

from code_typer.syntax.highlighter import Highlighter, Token, TokenType


class PythonHighlighter(Highlighter):
    """Syntax highlighter for Python code."""

    # Python keywords (immutable to prevent accidental modification)
    KEYWORDS: frozenset[str] = frozenset(
        {
            "False",
            "None",
            "True",
            "and",
            "as",
            "assert",
            "async",
            "await",
            "break",
            "class",
            "continue",
            "def",
            "del",
            "elif",
            "else",
            "except",
            "finally",
            "for",
            "from",
            "global",
            "if",
            "import",
            "in",
            "is",
            "lambda",
            "nonlocal",
            "not",
            "or",
            "pass",
            "raise",
            "return",
            "try",
            "while",
            "with",
            "yield",
            "match",
            "case",
            "type",
        }
    )

    # Python built-in functions (immutable to prevent accidental modification)
    BUILTINS: frozenset[str] = frozenset(
        {
            "abs",
            "all",
            "any",
            "ascii",
            "bin",
            "bool",
            "breakpoint",
            "bytearray",
            "bytes",
            "callable",
            "chr",
            "classmethod",
            "compile",
            "complex",
            "delattr",
            "dict",
            "dir",
            "divmod",
            "enumerate",
            "eval",
            "exec",
            "filter",
            "float",
            "format",
            "frozenset",
            "getattr",
            "globals",
            "hasattr",
            "hash",
            "help",
            "hex",
            "id",
            "input",
            "int",
            "isinstance",
            "issubclass",
            "iter",
            "len",
            "list",
            "locals",
            "map",
            "max",
            "memoryview",
            "min",
            "next",
            "object",
            "oct",
            "open",
            "ord",
            "pow",
            "print",
            "property",
            "range",
            "repr",
            "reversed",
            "round",
            "set",
            "setattr",
            "slice",
            "sorted",
            "staticmethod",
            "str",
            "sum",
            "super",
            "tuple",
            "type",
            "vars",
            "zip",
            "__import__",
            # Common exception types
            "Exception",
            "BaseException",
            "ValueError",
            "TypeError",
            "KeyError",
            "IndexError",
            "AttributeError",
            "ImportError",
            "RuntimeError",
            "StopIteration",
            "FileNotFoundError",
            "OSError",
            "IOError",
        }
    )

    def _setup_patterns(self) -> None:
        """Set up Python-specific patterns."""
        # Order matters - more specific patterns first
        self._token_patterns = [
            # Triple-quoted strings (must come before single-quoted)
            (r'"""[\s\S]*?"""', TokenType.STRING),
            (r"'''[\s\S]*?'''", TokenType.STRING),
            # F-strings (simplified - doesn't handle nested braces perfectly)
            (r'f"(?:[^"\\]|\\.)*"', TokenType.STRING),
            (r"f'(?:[^'\\]|\\.)*'", TokenType.STRING),
            # Raw strings
            (r'r"(?:[^"\\]|\\.)*"', TokenType.STRING),
            (r"r'(?:[^'\\]|\\.)*'", TokenType.STRING),
            # Regular strings
            (r'"(?:[^"\\]|\\.)*"', TokenType.STRING),
            (r"'(?:[^'\\]|\\.)*'", TokenType.STRING),
            # Comments
            (r"#[^\n]*", TokenType.COMMENT),
            # Decorators
            (r"@[a-zA-Z_][a-zA-Z0-9_.]*", TokenType.DECORATOR),
            # Whitespace
            (r"[ \t]+", TokenType.WHITESPACE),
            (r"\n", TokenType.WHITESPACE),
            # Numbers (including floats, hex, octal, binary, complex)
            (r"\b0[xX][0-9a-fA-F_]+\b", TokenType.NUMBER),
            (r"\b0[oO][0-7_]+\b", TokenType.NUMBER),
            (r"\b0[bB][01_]+\b", TokenType.NUMBER),
            (r"\b\d+\.?\d*(?:[eE][+-]?\d+)?[jJ]?\b", TokenType.NUMBER),
            (r"\b\.\d+(?:[eE][+-]?\d+)?[jJ]?\b", TokenType.NUMBER),
            # Identifiers - classified in tokenize()
            (r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", TokenType.TEXT),
            # Operators
            (r"->|:=|==|!=|<=|>=|<<|>>|\*\*|//|[+\-*/%=<>!&|^~@]", TokenType.OPERATOR),
            # Punctuation
            (r"[(){}\[\],;:.]+", TokenType.PUNCTUATION),
            # Anything else
            (r".", TokenType.TEXT),
        ]

    def tokenize(self, content: str) -> Generator[Token, None, None]:
        """Tokenize Python code with keyword/builtin classification."""
        pattern = self._compile_patterns()

        # Track if we're after 'def' or 'class' for function/class name detection
        prev_token_text = None

        for match in pattern.finditer(content):
            base_type = self._get_token_type(match)
            text = match.group()

            # Classify identifiers
            if base_type == TokenType.TEXT and text.isidentifier():
                if text in self.KEYWORDS:
                    token_type = TokenType.KEYWORD
                elif text in self.BUILTINS:
                    token_type = TokenType.BUILTIN
                elif prev_token_text == "def":
                    token_type = TokenType.FUNCTION
                elif prev_token_text == "class":
                    token_type = TokenType.CLASS
                else:
                    token_type = TokenType.TEXT
            else:
                token_type = base_type

            yield Token(
                token_type=token_type, text=text, start=match.start(), end=match.end()
            )

            # Track previous non-whitespace token
            if base_type != TokenType.WHITESPACE:
                prev_token_text = text
