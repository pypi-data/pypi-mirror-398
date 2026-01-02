"""Tests for realistic Python typing with cursor movement."""

from code_typer.realistic_python_typer import RealisticPythonTyper


class TestRealisticPythonTyper:
    """Test suite for RealisticPythonTyper."""

    def test_analyze_simple_function(self):
        """Test analyzing a simple function."""
        code = """def hello():
    return "world"
"""
        typer = RealisticPythonTyper(code)
        assert len(typer.structure.functions) == 1
        assert typer.structure.functions[0].name == "hello"
        assert "return" in typer.structure.functions[0].body

    def test_analyze_class_with_methods(self):
        """Test analyzing a class with methods."""
        code = """class MyClass:
    def __init__(self):
        self.value = 0

    def get_value(self):
        return self.value
"""
        typer = RealisticPythonTyper(code)
        assert len(typer.structure.classes) == 1
        assert typer.structure.classes[0].name == "MyClass"
        assert len(typer.structure.classes[0].methods) == 2

    def test_analyze_imports(self):
        """Test analyzing imports."""
        code = """import os
from typing import Optional
from dataclasses import dataclass

def foo():
    pass
"""
        typer = RealisticPythonTyper(code)
        assert len(typer.structure.imports) == 3
        assert "import os" in typer.structure.imports[0].source
        assert "Optional" in typer.structure.imports[1].source
        assert "dataclass" in typer.structure.imports[2].source

    def test_analyze_module_docstring(self):
        """Test analyzing module docstring."""
        code = '''"""This is a module docstring."""

def foo():
    pass
'''
        typer = RealisticPythonTyper(code)
        assert typer.structure.module_docstring is not None
        assert "module docstring" in typer.structure.module_docstring

    def test_function_with_docstring(self):
        """Test function docstring is extracted separately from body."""
        code = '''def greet(name):
    """Greet someone by name."""
    return f"Hello, {name}!"
'''
        typer = RealisticPythonTyper(code)
        assert len(typer.structure.functions) == 1
        assert typer.structure.functions[0].docstring is not None
        assert "Greet someone" in typer.structure.functions[0].docstring
        assert "return" in typer.structure.functions[0].body
        assert "Greet someone" not in typer.structure.functions[0].body

    def test_class_with_decorators(self):
        """Test class decorators are extracted."""
        code = """@dataclass
@frozen
class Point:
    x: int
    y: int
"""
        typer = RealisticPythonTyper(code)
        assert len(typer.structure.classes) == 1
        assert len(typer.structure.classes[0].decorators) == 2
        assert "@dataclass" in typer.structure.classes[0].decorators[0]
        assert "@frozen" in typer.structure.classes[0].decorators[1]

    def test_multiline_signature(self):
        """Test function with multiline signature."""
        code = """def complex_function(
    arg1: str,
    arg2: int,
    arg3: Optional[float] = None
) -> Dict[str, Any]:
    return {"arg1": arg1}
"""
        typer = RealisticPythonTyper(code)
        assert len(typer.structure.functions) == 1
        # Signature should include all lines up to the colon
        assert "arg1" in typer.structure.functions[0].signature
        assert "arg2" in typer.structure.functions[0].signature
        assert "arg3" in typer.structure.functions[0].signature

    def test_empty_function_body(self):
        """Test function with only pass."""
        code = """def empty():
    pass
"""
        typer = RealisticPythonTyper(code)
        assert len(typer.structure.functions) == 1
        assert typer.structure.functions[0].body.strip() == "pass"

    def test_function_indent_detection(self):
        """Test that function indentation is correctly detected."""
        code = """class Outer:
    def method(self):
        return 1
"""
        typer = RealisticPythonTyper(code)
        assert len(typer.structure.classes) == 1
        assert len(typer.structure.classes[0].methods) == 1
        # Method should have indent of 4 (inside class)
        assert typer.structure.classes[0].methods[0].indent == 4


class TestFunctionInfo:
    """Test FunctionInfo dataclass."""

    def test_create_function_info(self):
        """Test creating a FunctionInfo from code analysis."""
        code = """def test():
    return 1
"""
        typer = RealisticPythonTyper(code)
        info = typer.structure.functions[0]
        assert info.name == "test"
        assert "def test():" in info.signature
        assert "return 1" in info.body
        assert info.docstring is None
        assert info.indent == 0

    def test_function_info_with_docstring(self):
        """Test FunctionInfo with docstring."""
        code = '''def greet(name):
    """Say hello."""
    return name
'''
        typer = RealisticPythonTyper(code)
        info = typer.structure.functions[0]
        assert info.docstring is not None
        assert "Say hello" in info.docstring


class TestClassInfo:
    """Test ClassInfo dataclass."""

    def test_create_class_info(self):
        """Test creating a ClassInfo from code analysis."""
        code = """class MyClass:
    def method(self):
        pass
"""
        typer = RealisticPythonTyper(code)
        info = typer.structure.classes[0]
        assert info.name == "MyClass"
        assert len(info.methods) == 1
        assert info.methods[0].name == "method"

    def test_class_info_with_decorators(self):
        """Test ClassInfo with decorators."""
        code = '''@dataclass
class DataClass:
    """A data class."""
    pass
'''
        typer = RealisticPythonTyper(code)
        info = typer.structure.classes[0]
        assert len(info.decorators) == 1
        assert "@dataclass" in info.decorators[0]


class TestDependencyOrder:
    """Test dependency-aware typing order."""

    def test_dependency_order_simple(self):
        """Test that dependencies come before dependents."""
        code = """def helper():
    return 1

def main():
    return helper()
"""
        typer = RealisticPythonTyper(code)
        order = typer.analyzer.get_typing_order()

        # Extract just the function names from signatures
        sig_order = [name for name, phase, _ in order if phase == "signature"]

        # helper should come before main (main depends on helper)
        assert sig_order.index("helper") < sig_order.index("main")

    def test_dependency_order_methods(self):
        """Test method dependency order within a class."""
        code = """class Calculator:
    def add(self, a, b):
        return a + b

    def add_three(self, a, b, c):
        return self.add(self.add(a, b), c)
"""
        typer = RealisticPythonTyper(code)
        order = typer.analyzer.get_typing_order()

        # Extract method names from signatures
        sig_order = [name for name, phase, _ in order if phase == "signature"]

        # add should come before add_three
        assert sig_order.index("Calculator.add") < sig_order.index(
            "Calculator.add_three"
        )
