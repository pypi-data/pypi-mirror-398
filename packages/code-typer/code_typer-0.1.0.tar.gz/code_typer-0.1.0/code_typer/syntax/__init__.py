"""Syntax highlighting module."""

from code_typer.syntax.highlighter import Highlighter, TokenType
from code_typer.syntax.python import PythonHighlighter
from code_typer.syntax.sql import SQLHighlighter

__all__ = ["Highlighter", "TokenType", "PythonHighlighter", "SQLHighlighter"]
