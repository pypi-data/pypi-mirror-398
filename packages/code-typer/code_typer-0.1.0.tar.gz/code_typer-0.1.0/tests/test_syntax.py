"""Tests for syntax highlighting."""

from code_typer.syntax import Highlighter, PythonHighlighter, SQLHighlighter, TokenType
from code_typer.syntax.highlighter import Token


class TestHighlighter:
    """Test suite for base Highlighter class."""

    def test_tokenize_basic(self):
        """Test basic tokenization."""
        h = Highlighter()
        tokens = list(h.tokenize("hello 123"))

        assert len(tokens) > 0
        assert any(t.token_type == TokenType.TEXT for t in tokens)
        assert any(t.token_type == TokenType.NUMBER for t in tokens)

    def test_tokenize_preserves_content(self):
        """Test that tokenization preserves original content."""
        h = Highlighter()
        content = "function test() { return 42; }"
        tokens = list(h.tokenize(content))

        reconstructed = "".join(t.text for t in tokens)
        assert reconstructed == content

    def test_token_positions(self):
        """Test that token positions are correct."""
        h = Highlighter()
        content = "ab cd"
        tokens = list(h.tokenize(content))

        for token in tokens:
            assert content[token.start : token.end] == token.text

    def test_get_token_at(self):
        """Test getting token at specific position."""
        h = Highlighter()
        content = "hello world"

        token = h.get_token_at(content, 0)
        assert token is not None
        assert "hello" in token.text

        token = h.get_token_at(content, 6)
        assert token is not None
        assert "world" in token.text


class TestPythonHighlighter:
    """Test suite for Python syntax highlighter."""

    def test_keywords(self):
        """Test Python keyword highlighting."""
        h = PythonHighlighter()
        code = "def foo(): return True"
        tokens = list(h.tokenize(code))

        keywords = [t for t in tokens if t.token_type == TokenType.KEYWORD]
        keyword_texts = {t.text for t in keywords}

        assert "def" in keyword_texts
        assert "return" in keyword_texts
        assert "True" in keyword_texts

    def test_function_name(self):
        """Test function name highlighting."""
        h = PythonHighlighter()
        code = "def my_function():"
        tokens = list(h.tokenize(code))

        functions = [t for t in tokens if t.token_type == TokenType.FUNCTION]
        assert len(functions) == 1
        assert functions[0].text == "my_function"

    def test_class_name(self):
        """Test class name highlighting."""
        h = PythonHighlighter()
        code = "class MyClass:"
        tokens = list(h.tokenize(code))

        classes = [t for t in tokens if t.token_type == TokenType.CLASS]
        assert len(classes) == 1
        assert classes[0].text == "MyClass"

    def test_strings(self):
        """Test string highlighting."""
        h = PythonHighlighter()
        code = "\"hello\" 'world'"
        tokens = list(h.tokenize(code))

        strings = [t for t in tokens if t.token_type == TokenType.STRING]
        assert len(strings) == 2

    def test_triple_quoted_strings(self):
        """Test triple-quoted string highlighting."""
        h = PythonHighlighter()
        code = '"""docstring"""'
        tokens = list(h.tokenize(code))

        strings = [t for t in tokens if t.token_type == TokenType.STRING]
        assert len(strings) == 1
        assert '"""' in strings[0].text

    def test_comments(self):
        """Test comment highlighting."""
        h = PythonHighlighter()
        code = "x = 1  # this is a comment"
        tokens = list(h.tokenize(code))

        comments = [t for t in tokens if t.token_type == TokenType.COMMENT]
        assert len(comments) == 1
        assert "this is a comment" in comments[0].text

    def test_decorators(self):
        """Test decorator highlighting."""
        h = PythonHighlighter()
        code = "@property\ndef foo(): pass"
        tokens = list(h.tokenize(code))

        decorators = [t for t in tokens if t.token_type == TokenType.DECORATOR]
        assert len(decorators) == 1
        assert decorators[0].text == "@property"

    def test_numbers(self):
        """Test number highlighting."""
        h = PythonHighlighter()
        code = "x = 42 + 3.14 + 0xFF + 0b1010"
        tokens = list(h.tokenize(code))

        numbers = [t for t in tokens if t.token_type == TokenType.NUMBER]
        assert len(numbers) >= 3

    def test_builtins(self):
        """Test builtin function highlighting."""
        h = PythonHighlighter()
        code = "print(len(range(10)))"
        tokens = list(h.tokenize(code))

        builtins = [t for t in tokens if t.token_type == TokenType.BUILTIN]
        builtin_texts = {t.text for t in builtins}

        assert "print" in builtin_texts
        assert "len" in builtin_texts
        assert "range" in builtin_texts

    def test_fstrings(self):
        """Test f-string highlighting."""
        h = PythonHighlighter()
        code = 'f"Hello {name}"'
        tokens = list(h.tokenize(code))

        strings = [t for t in tokens if t.token_type == TokenType.STRING]
        assert len(strings) >= 1


class TestSQLHighlighter:
    """Test suite for SQL syntax highlighter."""

    def test_keywords(self):
        """Test SQL keyword highlighting."""
        h = SQLHighlighter()
        code = "SELECT * FROM users WHERE id = 1"
        tokens = list(h.tokenize(code))

        keywords = [t for t in tokens if t.token_type == TokenType.KEYWORD]
        keyword_texts = {t.text.upper() for t in keywords}

        assert "SELECT" in keyword_texts
        assert "FROM" in keyword_texts
        assert "WHERE" in keyword_texts

    def test_keywords_case_insensitive(self):
        """Test that SQL keywords are case-insensitive."""
        h = SQLHighlighter()
        code = "select * from users"
        tokens = list(h.tokenize(code))

        keywords = [t for t in tokens if t.token_type == TokenType.KEYWORD]
        assert len(keywords) == 2  # select, from

    def test_functions(self):
        """Test SQL function highlighting."""
        h = SQLHighlighter()
        code = "SELECT COUNT(*), MAX(id) FROM users"
        tokens = list(h.tokenize(code))

        functions = [t for t in tokens if t.token_type == TokenType.FUNCTION]
        func_texts = {t.text.upper() for t in functions}

        assert "COUNT" in func_texts
        assert "MAX" in func_texts

    def test_strings(self):
        """Test SQL string highlighting."""
        h = SQLHighlighter()
        code = "WHERE name = 'John''s'"
        tokens = list(h.tokenize(code))

        strings = [t for t in tokens if t.token_type == TokenType.STRING]
        assert len(strings) == 1

    def test_comments_single_line(self):
        """Test single-line comment highlighting."""
        h = SQLHighlighter()
        code = "SELECT * -- get all\nFROM users"
        tokens = list(h.tokenize(code))

        comments = [t for t in tokens if t.token_type == TokenType.COMMENT]
        assert len(comments) == 1

    def test_comments_multi_line(self):
        """Test multi-line comment highlighting."""
        h = SQLHighlighter()
        code = "/* multi\nline */ SELECT"
        tokens = list(h.tokenize(code))

        comments = [t for t in tokens if t.token_type == TokenType.COMMENT]
        assert len(comments) == 1
        assert "multi" in comments[0].text

    def test_numbers(self):
        """Test number highlighting."""
        h = SQLHighlighter()
        code = "WHERE id = 42 AND price > 19.99"
        tokens = list(h.tokenize(code))

        numbers = [t for t in tokens if t.token_type == TokenType.NUMBER]
        assert len(numbers) == 2

    def test_data_types(self):
        """Test SQL data type highlighting."""
        h = SQLHighlighter()
        code = "CREATE TABLE t (id INT, name VARCHAR(100))"
        tokens = list(h.tokenize(code))

        types = [t for t in tokens if t.token_type == TokenType.BUILTIN]
        type_texts = {t.text.upper() for t in types}

        assert "INT" in type_texts
        assert "VARCHAR" in type_texts

    def test_placeholders(self):
        """Test placeholder highlighting."""
        h = SQLHighlighter()
        code = "SELECT * FROM users WHERE id = $1 AND name = :name"
        tokens = list(h.tokenize(code))

        variables = [t for t in tokens if t.token_type == TokenType.VARIABLE]
        assert len(variables) == 2


class TestTokenType:
    """Test TokenType enum."""

    def test_all_token_types_exist(self):
        """Test that expected token types exist."""
        assert TokenType.TEXT
        assert TokenType.KEYWORD
        assert TokenType.STRING
        assert TokenType.COMMENT
        assert TokenType.NUMBER
        assert TokenType.FUNCTION
        assert TokenType.CLASS
        assert TokenType.OPERATOR
        assert TokenType.DECORATOR
        assert TokenType.BUILTIN


class TestToken:
    """Test Token dataclass."""

    def test_token_creation(self):
        """Test Token creation."""
        token = Token(token_type=TokenType.KEYWORD, text="def", start=0, end=3)

        assert token.token_type == TokenType.KEYWORD
        assert token.text == "def"
        assert token.start == 0
        assert token.end == 3
