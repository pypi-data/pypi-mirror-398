"""Tests for smart Python typing simulation."""

from code_typer.smart_python_typer import (
    CodeChunk,
    SmartPythonAnalyzer,
    SmartPythonTyper,
    WritePhase,
)


class TestSmartPythonAnalyzer:
    """Test suite for SmartPythonAnalyzer."""

    def test_analyze_simple_function(self):
        """Test analyzing a simple function."""
        code = """def hello():
    return "world"
"""
        analyzer = SmartPythonAnalyzer(code)
        assert len(analyzer.functions) == 1
        assert analyzer.functions[0].name == "hello"

    def test_analyze_class_with_methods(self):
        """Test analyzing a class with methods."""
        code = """class MyClass:
    def __init__(self):
        self.value = 0

    def get_value(self):
        return self.value
"""
        analyzer = SmartPythonAnalyzer(code)
        assert len(analyzer.classes) == 1
        assert analyzer.classes[0].name == "MyClass"
        assert len(analyzer.classes[0].methods) == 2

    def test_analyze_imports(self):
        """Test analyzing imports."""
        code = """import os
from typing import Optional
from dataclasses import dataclass

def foo():
    pass
"""
        analyzer = SmartPythonAnalyzer(code)
        assert len(analyzer.imports) == 3
        names = [name for imp in analyzer.imports for name in imp.names]
        assert "os" in names
        assert "Optional" in names
        assert "dataclass" in names

    def test_analyze_module_docstring(self):
        """Test analyzing module docstring."""
        code = '''"""This is a module docstring."""

def foo():
    pass
'''
        analyzer = SmartPythonAnalyzer(code)
        assert analyzer.module_docstring is not None
        assert "module docstring" in analyzer.module_docstring

    def test_extract_decorators(self):
        """Test extracting decorators."""
        code = """@decorator
@another_decorator
def foo():
    pass
"""
        analyzer = SmartPythonAnalyzer(code)
        assert len(analyzer.functions) == 1
        assert len(analyzer.functions[0].decorators) == 2


class TestSmartPythonTyper:
    """Test suite for SmartPythonTyper."""

    def test_generate_chunks_basic(self):
        """Test basic chunk generation."""
        code = """def hello():
    return "world"
"""
        typer = SmartPythonTyper(code, skeleton_first=True)
        chunks = list(typer.generate_chunks())
        assert len(chunks) > 0
        assert all(isinstance(c, CodeChunk) for c in chunks)

    def test_skeleton_first_phases(self):
        """Test that skeleton-first mode generates correct phases."""
        code = """import os

def foo():
    x = 1
    return x
"""
        typer = SmartPythonTyper(code, skeleton_first=True)
        chunks = list(typer.generate_chunks())
        phases = [c.phase for c in chunks]

        # New order: SKELETON first, then FILL_BODY, then ADD_IMPORT
        assert WritePhase.SKELETON in phases
        assert WritePhase.FILL_BODY in phases
        assert WritePhase.ADD_IMPORT in phases

    def test_skeleton_before_body(self):
        """Test that skeletons are written before bodies."""
        code = """def foo():
    return 1

def bar():
    return 2
"""
        typer = SmartPythonTyper(code, skeleton_first=True)
        chunks = list(typer.generate_chunks())

        skeleton_indices = [
            i for i, c in enumerate(chunks) if c.phase == WritePhase.SKELETON
        ]
        body_indices = [
            i for i, c in enumerate(chunks) if c.phase == WritePhase.FILL_BODY
        ]

        # All skeletons should come before all bodies
        if skeleton_indices and body_indices:
            assert max(skeleton_indices) < min(body_indices)

    def test_imports_after_skeleton(self):
        """Test that imports are added after skeleton (realistic order)."""
        code = """from typing import List

def process(items: List[int]) -> int:
    return sum(items)
"""
        typer = SmartPythonTyper(code, skeleton_first=True)
        chunks = list(typer.generate_chunks())

        # Imports should come after skeleton (when you realize you need them)
        import_chunks = [c for c in chunks if c.phase == WritePhase.ADD_IMPORT]
        skeleton_chunks = [c for c in chunks if c.phase == WritePhase.SKELETON]

        assert len(import_chunks) > 0
        assert len(skeleton_chunks) > 0

        # Find indices
        first_skeleton = next(
            i for i, c in enumerate(chunks) if c.phase == WritePhase.SKELETON
        )
        first_import = next(
            i for i, c in enumerate(chunks) if c.phase == WritePhase.ADD_IMPORT
        )

        # Skeleton should come before imports
        assert first_skeleton < first_import

    def test_class_with_methods(self):
        """Test class with methods generates correct chunks."""
        code = """class Calculator:
    def add(self, a, b):
        return a + b

    def subtract(self, a, b):
        return a - b
"""
        typer = SmartPythonTyper(code, skeleton_first=True)
        chunks = list(typer.generate_chunks())

        # Should have skeleton chunk for the class
        skeleton_chunks = [c for c in chunks if c.phase == WritePhase.SKELETON]
        assert any("Calculator" in c.description for c in skeleton_chunks)

        # Should have body chunks for methods
        body_chunks = [c for c in chunks if c.phase == WritePhase.FILL_BODY]
        assert len(body_chunks) == 2  # add and subtract

    def test_linear_mode(self):
        """Test linear mode (non-skeleton-first)."""
        code = """def foo():
    return 1
"""
        typer = SmartPythonTyper(code, skeleton_first=False)
        chunks = list(typer.generate_chunks())

        # In linear mode, we just get SKELETON chunks (full code)
        phases = {c.phase for c in chunks}
        assert WritePhase.FILL_BODY not in phases

    def test_get_typing_content(self):
        """Test getting the full typing content."""
        code = """def hello():
    return "world"
"""
        typer = SmartPythonTyper(code, skeleton_first=True)
        content = typer.get_typing_content()
        assert "def hello" in content
        assert "return" in content

    def test_get_final_content(self):
        """Test getting the final content (original source)."""
        code = """def hello():
    return "world"
"""
        typer = SmartPythonTyper(code, skeleton_first=True)
        final = typer.get_final_content()
        assert final == code


class TestWritePhase:
    """Test WritePhase enum."""

    def test_all_phases_exist(self):
        """Test that all phases exist."""
        assert WritePhase.SETUP
        assert WritePhase.SKELETON
        assert WritePhase.FILL_BODY
        assert WritePhase.ADD_IMPORT
        assert WritePhase.REFINEMENT


class TestCodeChunk:
    """Test CodeChunk dataclass."""

    def test_create_code_chunk(self):
        """Test creating a CodeChunk."""
        chunk = CodeChunk(
            content="def foo(): pass",
            phase=WritePhase.SKELETON,
            description="Write function foo",
        )
        assert chunk.content == "def foo(): pass"
        assert chunk.phase == WritePhase.SKELETON
        assert chunk.description == "Write function foo"

    def test_optional_fields(self):
        """Test optional fields have defaults."""
        chunk = CodeChunk(content="pass", phase=WritePhase.SKELETON, description="test")
        assert chunk.line_hint == 0
        assert chunk.insert_at_top is False
        assert chunk.replace_pass is False
        assert chunk.target_function is None
