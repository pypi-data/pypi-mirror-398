"""Integration tests for smart Python mode with realistic typing."""

from unittest.mock import patch

from code_typer.code_analyzer import CodeAnalyzer
from code_typer.realistic_python_typer import RealisticPythonTyper


class MockDisplay:
    """Mock display for testing without ncurses."""

    def __init__(self):
        self._line_contents = [""]
        self._line_colors = [[]]
        self._current_row = 0
        self._current_col = 0
        self._insert_mode = False
        self._vim_mode = "INSERT"
        self._line_start_row = 0

    def set_vim_mode(self, mode):
        self._vim_mode = mode

    def set_insert_mode(self, enabled):
        self._insert_mode = enabled

    def sleep_with_clock(self, duration):
        """Mock sleep - does nothing in tests."""
        pass

    def get_content(self) -> str:
        """Get the current document content."""
        return "\n".join(self._line_contents)

    def get_normalized_content(self) -> str:
        """Get normalized content for comparison."""
        lines = [line.rstrip() for line in self._line_contents]
        while lines and not lines[-1]:
            lines.pop()
        return "\n".join(lines)

    def get_content_lines(self) -> list:
        """Get a copy of the current line contents."""
        return list(self._line_contents)

    def set_content_lines(self, lines: list) -> None:
        """Set the document content from a list of lines."""
        self._line_contents = list(lines)
        self._line_colors = [[] for _ in self._line_contents]

    def set_line_colors(self, colors: list) -> None:
        """Set the color attributes for all lines."""
        self._line_colors = [list(c) for c in colors]

    def goto_line(self, line_num, col=0):
        self._current_row = line_num - 1
        self._current_col = col

    def open_line_above(self):
        line_idx = self._current_row
        self._line_contents.insert(line_idx, "")
        self._line_colors.insert(line_idx, [])

    def insert_line_at(self, line_num, content=""):
        line_idx = line_num - 1
        line_idx = max(0, min(line_idx, len(self._line_contents)))
        self._line_contents.insert(line_idx, content)
        self._line_colors.insert(line_idx, [])

    def delete_line_at(self, line_num):
        line_idx = line_num - 1
        if 0 <= line_idx < len(self._line_contents):
            self._line_contents.pop(line_idx)
            if line_idx < len(self._line_colors):
                self._line_colors.pop(line_idx)

    def newline(self):
        line_idx = self._current_row
        if self._insert_mode and line_idx + 1 < len(self._line_contents):
            self._line_contents.insert(line_idx + 1, "")
            self._line_colors.insert(line_idx + 1, [])
        self._current_row += 1
        self._current_col = 0
        while len(self._line_contents) <= self._current_row:
            self._line_contents.append("")
            self._line_colors.append([])

    def type_char(self, char, token_type=None, error=False):
        if char == "\n":
            self.newline()
            return
        if char == "\t":
            self.type_tab(token_type=token_type)
            return
        line_idx = self._current_row
        while len(self._line_contents) <= line_idx:
            self._line_contents.append("")
            self._line_colors.append([])
        self._line_contents[line_idx] += char
        self._current_col += 1

    def type_tab(self, token_type=None):
        tab_width = 4 - (self._current_col % 4)
        line_idx = self._current_row
        while len(self._line_contents) <= line_idx:
            self._line_contents.append("")
            self._line_colors.append([])
        self._line_contents[line_idx] += "\t"
        self._current_col += tab_width


class MockEngine:
    """Mock engine for testing."""

    def __init__(self, display):
        self.display = display

    def type_content(self, content, language="text"):
        for char in content:
            self.display.type_char(char)


class MockHuman:
    """Mock human behavior for testing."""

    def _scaled_uniform(self, low, high):
        return 0.0  # No delays in tests


class TestSmartModeIntegration:
    """Test the complete smart mode typing flow."""

    def test_simple_function_no_extra_lines(self):
        """Test that body filling doesn't create extra blank lines."""
        code = """def hello():
    x = 1
    return x
"""
        typer = RealisticPythonTyper(code)
        display = MockDisplay()
        engine = MockEngine(display)
        human = MockHuman()

        # Run the realistic typing
        with patch("time.sleep"):  # Skip delays
            typer.type_with_movements(engine, human)

        # Count non-empty lines
        non_empty = [line for line in display._line_contents if line.strip()]
        empty = [line for line in display._line_contents if not line.strip()]

        # Should have exactly 3 non-empty lines: def, x=1, return
        assert len(non_empty) == 3, (
            f"Expected 3 non-empty lines, got {len(non_empty)}: {non_empty}"
        )

        # Should have at most 1 trailing empty line
        assert len(empty) <= 2, f"Too many empty lines: {len(empty)}"

    def test_class_with_methods_no_extra_lines(self):
        """Test class with multiple methods doesn't create extra lines."""
        code = """class Calculator:
    def add(self, a, b):
        return a + b

    def sub(self, a, b):
        return a - b
"""
        typer = RealisticPythonTyper(code)
        display = MockDisplay()
        engine = MockEngine(display)
        human = MockHuman()

        with patch("time.sleep"):
            typer.type_with_movements(engine, human)

        # Count lines
        all_lines = display._line_contents
        non_empty = [line for line in all_lines if line.strip()]

        # class + 2 methods with 2 lines each = 5 content lines
        assert len(non_empty) >= 5, (
            f"Expected at least 5 non-empty lines, got {len(non_empty)}"
        )

        # Check no duplicate blank lines (more than 1 consecutive)
        consecutive_blanks = 0
        max_consecutive = 0
        for line in all_lines:
            if not line.strip():
                consecutive_blanks += 1
                max_consecutive = max(max_consecutive, consecutive_blanks)
            else:
                consecutive_blanks = 0

        assert max_consecutive <= 2, (
            f"Too many consecutive blank lines: {max_consecutive}"
        )

    def test_dependency_order_preserved(self):
        """Test that functions are typed in dependency order."""
        code = """def helper():
    return 1

def main():
    return helper()
"""
        typer = RealisticPythonTyper(code)

        # Check the analyzer order
        order = typer.analyzer.get_typing_order()
        sig_order = [name for name, phase, _ in order if phase == "signature"]
        body_order = [name for name, phase, _ in order if phase == "body"]

        # helper should come before main in both phases
        assert sig_order.index("helper") < sig_order.index("main")
        assert body_order.index("helper") < body_order.index("main")

    def test_imports_added_at_top(self):
        """Test that imports are added at the top of the file."""
        code = """import os
from typing import Optional

def foo():
    return os.getcwd()
"""
        typer = RealisticPythonTyper(code)
        display = MockDisplay()
        engine = MockEngine(display)
        human = MockHuman()

        with patch("time.sleep"):
            typer.type_with_movements(engine, human)

        # Find import lines
        import_indices = []
        for i, line in enumerate(display._line_contents):
            if "import" in line:
                import_indices.append(i)

        # Imports should be near the top (within first 5 lines)
        if import_indices:
            assert max(import_indices) < 5, f"Imports too far down: {import_indices}"

    def test_module_docstring_at_very_top(self):
        """Test that module docstring ends up at the very top."""
        code = '''"""This is a module docstring."""

def foo():
    pass
'''
        typer = RealisticPythonTyper(code)
        display = MockDisplay()
        engine = MockEngine(display)
        human = MockHuman()

        with patch("time.sleep"):
            typer.type_with_movements(engine, human)

        # First non-empty line should contain the docstring
        first_content_line = None
        for line in display._line_contents:
            if line.strip():
                first_content_line = line
                break

        assert first_content_line is not None
        assert '"""' in first_content_line or "'''" in first_content_line, (
            f"First line should be docstring, got: {first_content_line}"
        )


class TestCodeAnalyzerDependencies:
    """Test the dependency detection in CodeAnalyzer."""

    def test_simple_call_dependency(self):
        """Test detection of simple function calls."""
        code = """def a():
    return 1

def b():
    return a()
"""
        analyzer = CodeAnalyzer(code)
        structure = analyzer.analyze()

        # b should depend on a
        assert "a" in structure.call_graph.get("b", set())

    def test_method_call_dependency(self):
        """Test detection of self.method() calls."""
        code = """class Foo:
    def helper(self):
        return 1

    def main(self):
        return self.helper()
"""
        analyzer = CodeAnalyzer(code)
        structure = analyzer.analyze()

        # Foo.main should depend on Foo.helper
        main_deps = structure.call_graph.get("Foo.main", set())
        assert "helper" in main_deps or "Foo.helper" in main_deps

    def test_circular_dependency_handled(self):
        """Test that circular dependencies don't cause infinite loops."""
        code = """def a():
    return b()

def b():
    return a()
"""
        analyzer = CodeAnalyzer(code)
        # Should not hang
        order = analyzer.get_typing_order()
        # Both functions should be in the order
        names = [name for name, _, _ in order]
        assert "a" in names
        assert "b" in names


class TestContentIntegrity:
    """Test SHA256 verification of typed content."""

    def test_simple_function_integrity(self):
        """Verify simple function content matches original."""
        code = """def hello():
    x = 1
    return x
"""
        typer = RealisticPythonTyper(code)
        display = MockDisplay()
        engine = MockEngine(display)
        human = MockHuman()

        with patch("time.sleep"):
            typer.type_with_movements(engine, human)

        success, msg = typer.verify_content(display)
        assert success, f"Content verification failed: {msg}"

    def test_class_with_methods_integrity(self):
        """Verify class with methods matches original."""
        code = """class Calculator:
    def add(self, a, b):
        return a + b

    def multiply(self, a, b):
        return a * b
"""
        typer = RealisticPythonTyper(code)
        display = MockDisplay()
        engine = MockEngine(display)
        human = MockHuman()

        with patch("time.sleep"):
            typer.type_with_movements(engine, human)

        success, msg = typer.verify_content(display)
        assert success, f"Content verification failed: {msg}"

    def test_imports_preserved(self):
        """Verify imports are correctly placed."""
        code = """import os
from typing import List, Optional

def foo():
    return os.getcwd()
"""
        typer = RealisticPythonTyper(code)
        display = MockDisplay()
        engine = MockEngine(display)
        human = MockHuman()

        with patch("time.sleep"):
            typer.type_with_movements(engine, human)

        success, msg = typer.verify_content(display)
        assert success, f"Content verification failed: {msg}"

    def test_docstring_preserved(self):
        """Verify module docstring is correctly placed."""
        code = '''"""This is the module docstring."""

def foo():
    """Function docstring."""
    return 1
'''
        typer = RealisticPythonTyper(code)
        display = MockDisplay()
        engine = MockEngine(display)
        human = MockHuman()

        with patch("time.sleep"):
            typer.type_with_movements(engine, human)

        success, msg = typer.verify_content(display)
        assert success, f"Content verification failed: {msg}"

    def test_multiline_function_body(self):
        """Verify multi-line function bodies are preserved."""
        code = """def complex_function(x, y, z):
    result = x + y
    result *= z
    if result > 100:
        result = 100
    return result
"""
        typer = RealisticPythonTyper(code)
        display = MockDisplay()
        engine = MockEngine(display)
        human = MockHuman()

        with patch("time.sleep"):
            typer.type_with_movements(engine, human)

        success, msg = typer.verify_content(display)
        assert success, f"Content verification failed: {msg}"

    def test_decorators_preserved(self):
        """Verify decorators are correctly placed."""
        code = """@dataclass
class Point:
    x: int
    y: int

@staticmethod
def helper():
    return 1
"""
        typer = RealisticPythonTyper(code)
        display = MockDisplay()
        engine = MockEngine(display)
        human = MockHuman()

        with patch("time.sleep"):
            typer.type_with_movements(engine, human)

        success, msg = typer.verify_content(display)
        assert success, f"Content verification failed: {msg}"

    def test_empty_lines_in_body_preserved(self):
        """Verify empty lines within function bodies are preserved."""
        code = """def function_with_gaps():
    x = 1

    y = 2

    return x + y
"""
        typer = RealisticPythonTyper(code)
        display = MockDisplay()
        engine = MockEngine(display)
        human = MockHuman()

        with patch("time.sleep"):
            typer.type_with_movements(engine, human)

        success, msg = typer.verify_content(display)
        assert success, f"Content verification failed: {msg}"

    def test_complex_class_structure(self):
        """Verify complex class with multiple methods and dependencies."""
        code = """class DataProcessor:
    def __init__(self, data):
        self.data = data

    def validate(self):
        return len(self.data) > 0

    def transform(self):
        if not self.validate():
            return []
        return [x * 2 for x in self.data]

    def process(self):
        transformed = self.transform()
        return sum(transformed)
"""
        typer = RealisticPythonTyper(code)
        display = MockDisplay()
        engine = MockEngine(display)
        human = MockHuman()

        with patch("time.sleep"):
            typer.type_with_movements(engine, human)

        success, msg = typer.verify_content(display)
        assert success, f"Content verification failed: {msg}"
