"""SQL syntax highlighting."""

from collections.abc import Generator

from code_typer.syntax.highlighter import Highlighter, Token, TokenType


class SQLHighlighter(Highlighter):
    """Syntax highlighter for SQL code."""

    # SQL keywords (common across dialects)
    KEYWORDS = {
        # Data Query Language (DQL)
        "SELECT",
        "FROM",
        "WHERE",
        "AND",
        "OR",
        "NOT",
        "IN",
        "LIKE",
        "BETWEEN",
        "IS",
        "NULL",
        "TRUE",
        "FALSE",
        "DISTINCT",
        "ALL",
        "AS",
        "ON",
        "USING",
        "ORDER",
        "BY",
        "ASC",
        "DESC",
        "NULLS",
        "FIRST",
        "LAST",
        "GROUP",
        "HAVING",
        "LIMIT",
        "OFFSET",
        "FETCH",
        "NEXT",
        "ROWS",
        "ONLY",
        "UNION",
        "INTERSECT",
        "EXCEPT",
        "MINUS",
        # Joins
        "JOIN",
        "INNER",
        "LEFT",
        "RIGHT",
        "FULL",
        "OUTER",
        "CROSS",
        "NATURAL",
        # Data Manipulation Language (DML)
        "INSERT",
        "INTO",
        "VALUES",
        "UPDATE",
        "SET",
        "DELETE",
        "MERGE",
        "UPSERT",
        "REPLACE",
        # Data Definition Language (DDL)
        "CREATE",
        "ALTER",
        "DROP",
        "TRUNCATE",
        "RENAME",
        "COMMENT",
        "TABLE",
        "VIEW",
        "INDEX",
        "SEQUENCE",
        "DATABASE",
        "SCHEMA",
        "COLUMN",
        "CONSTRAINT",
        "PRIMARY",
        "KEY",
        "FOREIGN",
        "REFERENCES",
        "UNIQUE",
        "CHECK",
        "DEFAULT",
        "AUTO_INCREMENT",
        "SERIAL",
        "IF",
        "EXISTS",
        "CASCADE",
        "RESTRICT",
        # Data Control Language (DCL)
        "GRANT",
        "REVOKE",
        "PRIVILEGES",
        "TO",
        "WITH",
        "OPTION",
        # Transaction Control
        "BEGIN",
        "COMMIT",
        "ROLLBACK",
        "SAVEPOINT",
        "TRANSACTION",
        # Common clauses
        "CASE",
        "WHEN",
        "THEN",
        "ELSE",
        "END",
        "OVER",
        "PARTITION",
        "WINDOW",
        "RANGE",
        "PRECEDING",
        "FOLLOWING",
        "UNBOUNDED",
        "CURRENT",
        "ROW",
        # Subqueries
        "ANY",
        "SOME",
        # Common table expressions
        "RECURSIVE",
    }

    # SQL functions
    FUNCTIONS = {
        # Aggregate functions
        "COUNT",
        "SUM",
        "AVG",
        "MIN",
        "MAX",
        "ARRAY_AGG",
        "STRING_AGG",
        "LISTAGG",
        "GROUP_CONCAT",
        # String functions
        "CONCAT",
        "SUBSTRING",
        "SUBSTR",
        "TRIM",
        "LTRIM",
        "RTRIM",
        "UPPER",
        "LOWER",
        "LENGTH",
        "LEN",
        "REPLACE",
        "REVERSE",
        "LPAD",
        "RPAD",
        "LEFT",
        "RIGHT",
        "POSITION",
        "CHARINDEX",
        "SPLIT_PART",
        # Numeric functions
        "ABS",
        "CEIL",
        "CEILING",
        "FLOOR",
        "ROUND",
        "TRUNC",
        "MOD",
        "POWER",
        "SQRT",
        "EXP",
        "LOG",
        "LN",
        "SIGN",
        "RANDOM",
        "RAND",
        # Date/Time functions
        "NOW",
        "CURRENT_DATE",
        "CURRENT_TIME",
        "CURRENT_TIMESTAMP",
        "DATE",
        "TIME",
        "TIMESTAMP",
        "EXTRACT",
        "DATE_PART",
        "DATE_TRUNC",
        "DATEADD",
        "DATEDIFF",
        "DATE_ADD",
        "DATE_SUB",
        "INTERVAL",
        "YEAR",
        "MONTH",
        "DAY",
        "HOUR",
        "MINUTE",
        "SECOND",
        # Conversion functions
        "CAST",
        "CONVERT",
        "COALESCE",
        "NULLIF",
        "NVL",
        "IFNULL",
        "IIF",
        # Window functions
        "ROW_NUMBER",
        "RANK",
        "DENSE_RANK",
        "NTILE",
        "LAG",
        "LEAD",
        "FIRST_VALUE",
        "LAST_VALUE",
        "NTH_VALUE",
    }

    # SQL data types
    TYPES = {
        "INT",
        "INTEGER",
        "SMALLINT",
        "BIGINT",
        "TINYINT",
        "DECIMAL",
        "NUMERIC",
        "FLOAT",
        "REAL",
        "DOUBLE",
        "PRECISION",
        "CHAR",
        "VARCHAR",
        "TEXT",
        "NCHAR",
        "NVARCHAR",
        "NTEXT",
        "DATE",
        "TIME",
        "DATETIME",
        "TIMESTAMP",
        "TIMESTAMPTZ",
        "BOOLEAN",
        "BOOL",
        "BIT",
        "BLOB",
        "CLOB",
        "BINARY",
        "VARBINARY",
        "BYTEA",
        "JSON",
        "JSONB",
        "XML",
        "UUID",
        "ARRAY",
    }

    def _setup_patterns(self) -> None:
        """Set up SQL-specific patterns."""
        self._token_patterns = [
            # Multi-line comments
            (r"/\*[\s\S]*?\*/", TokenType.COMMENT),
            # Single-line comments (-- and #)
            (r"--[^\n]*", TokenType.COMMENT),
            (r"#[^\n]*", TokenType.COMMENT),
            # Strings (single quotes, with escape handling)
            (r"'(?:[^'\\]|\\.|'')*'", TokenType.STRING),
            # Dollar-quoted strings (PostgreSQL)
            (r"\$\$[\s\S]*?\$\$", TokenType.STRING),
            (
                r"\$[a-zA-Z_][a-zA-Z0-9_]*\$[\s\S]*?\$[a-zA-Z_][a-zA-Z0-9_]*\$",
                TokenType.STRING,
            ),
            # Identifiers in double quotes or backticks
            (r'"[^"]*"', TokenType.TEXT),
            (r"`[^`]*`", TokenType.TEXT),
            # Whitespace
            (r"[ \t]+", TokenType.WHITESPACE),
            (r"\n", TokenType.WHITESPACE),
            # Numbers
            (r"\b\d+\.?\d*(?:[eE][+-]?\d+)?\b", TokenType.NUMBER),
            # Placeholders
            (r"\$\d+", TokenType.VARIABLE),  # PostgreSQL positional
            (r":\w+", TokenType.VARIABLE),  # Named parameters
            (r"\?", TokenType.VARIABLE),  # JDBC-style
            (r"@\w+", TokenType.VARIABLE),  # SQL Server variables
            # Identifiers - classified in tokenize()
            (r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", TokenType.TEXT),
            # Operators
            (r"<>|!=|<=|>=|::|\|\||&&|[+\-*/%=<>!&|^~]", TokenType.OPERATOR),
            # Punctuation
            (r"[(){}\[\],;:.]+", TokenType.PUNCTUATION),
            # Anything else
            (r".", TokenType.TEXT),
        ]

    def tokenize(self, content: str) -> Generator[Token, None, None]:
        """Tokenize SQL code with keyword/function classification."""
        pattern = self._compile_patterns()

        for match in pattern.finditer(content):
            base_type = self._get_token_type(match)
            text = match.group()

            # Classify identifiers (SQL is case-insensitive for keywords)
            if base_type == TokenType.TEXT:
                upper_text = text.upper()
                if upper_text in self.KEYWORDS:
                    token_type = TokenType.KEYWORD
                elif upper_text in self.FUNCTIONS:
                    token_type = TokenType.FUNCTION
                elif upper_text in self.TYPES:
                    token_type = TokenType.BUILTIN
                else:
                    token_type = TokenType.TEXT
            else:
                token_type = base_type

            yield Token(
                token_type=token_type, text=text, start=match.start(), end=match.end()
            )
