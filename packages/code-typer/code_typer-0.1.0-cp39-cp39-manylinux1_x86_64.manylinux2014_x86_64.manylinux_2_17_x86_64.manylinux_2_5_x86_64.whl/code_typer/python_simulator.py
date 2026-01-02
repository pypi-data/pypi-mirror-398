"""AST-based Python code simulation for realistic human-like coding.

This module analyzes Python code structure and generates typing sequences
that simulate how humans actually write code:
- Write function/class signatures first, then fill in bodies
- Add imports as they become needed (not all at once at the top)
- Write docstrings after the signature
- Jump around to add helper functions
- Incremental refinement
"""

import ast
from collections.abc import Generator
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional


class CodeBlockType(Enum):
    """Types of code blocks."""

    IMPORT = auto()
    FROM_IMPORT = auto()
    CLASS_DEF = auto()
    FUNCTION_DEF = auto()
    METHOD_DEF = auto()
    DECORATOR = auto()
    DOCSTRING = auto()
    ASSIGNMENT = auto()
    EXPRESSION = auto()
    COMMENT = auto()
    BLANK = auto()
    BODY = auto()  # Function/method body content


@dataclass
class CodeBlock:
    """Represents a block of code with metadata."""

    block_type: CodeBlockType
    content: str
    start_line: int
    end_line: int
    indent: int = 0
    name: Optional[str] = None  # For functions/classes
    parent: Optional[str] = None  # Parent class/function name
    dependencies: set[str] = field(default_factory=set)  # Required imports/names
    is_skeleton: bool = False  # True if this is just the signature


@dataclass
class CodingAction:
    """Represents a single coding action in the simulation."""

    action: str  # 'write', 'insert', 'go_back', 'fill_body'
    content: str
    line: int
    description: str  # Human-readable description for debugging


class PythonCodeAnalyzer:
    """Analyzes Python code structure using AST."""

    def __init__(self, source: str):
        self.source = source
        self.lines = source.split("\n")
        self.tree = ast.parse(source)
        self.blocks: list[CodeBlock] = []
        self.imports: dict[str, CodeBlock] = {}  # name -> import block
        self.functions: dict[str, CodeBlock] = {}
        self.classes: dict[str, CodeBlock] = {}
        self._analyze()

    def _get_source_segment(self, node: ast.AST) -> str:
        """Get the source code for an AST node."""
        return ast.get_source_segment(self.source, node) or ""

    def _get_indent(self, line_no: int) -> int:
        """Get indentation level of a line (0-indexed)."""
        if 0 <= line_no < len(self.lines):
            line = self.lines[line_no]
            return len(line) - len(line.lstrip())
        return 0

    def _extract_signature(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
        """Extract just the function signature (def line + pass)."""
        lines = []

        # Include decorators
        for decorator in node.decorator_list:
            dec_line = self.lines[decorator.lineno - 1]
            lines.append(dec_line)

        # Get the def line(s) - might span multiple lines
        def_lines = []
        paren_count = 0
        for i in range(node.lineno - 1, min(node.lineno + 10, len(self.lines))):
            line = self.lines[i]
            def_lines.append(line)
            paren_count += line.count("(") - line.count(")")
            if paren_count <= 0 and ":" in line:
                break

        lines.extend(def_lines)
        indent = self._get_indent(node.lineno - 1)
        lines.append(" " * (indent + 4) + "pass")

        return "\n".join(lines)

    def _extract_class_signature(self, node: ast.ClassDef) -> str:
        """Extract just the class signature."""
        lines = []

        # Include decorators
        for decorator in node.decorator_list:
            dec_line = self.lines[decorator.lineno - 1]
            lines.append(dec_line)

        # Get the class line
        class_line = self.lines[node.lineno - 1]
        lines.append(class_line)

        # Add pass
        indent = self._get_indent(node.lineno - 1)
        lines.append(" " * (indent + 4) + "pass")

        return "\n".join(lines)

    def _extract_docstring(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef
    ) -> Optional[str]:
        """Extract docstring if present."""
        if (
            node.body
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant)
            and isinstance(node.body[0].value.value, str)
        ):
            return self._get_source_segment(node.body[0])
        return None

    def _extract_body(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef, skip_docstring: bool = True
    ) -> str:
        """Extract the function body (without signature and optionally docstring)."""
        start_idx = 0
        if skip_docstring and self._extract_docstring(node):
            start_idx = 1

        body_nodes = node.body[start_idx:]
        if not body_nodes:
            return ""

        # Get line range
        first_line = body_nodes[0].lineno - 1
        last_line = body_nodes[-1].end_lineno

        return "\n".join(self.lines[first_line:last_line])

    def _find_dependencies(self, node: ast.AST) -> set[str]:
        """Find names used in a node that might need imports."""
        deps = set()
        for child in ast.walk(node):
            if isinstance(child, ast.Name):
                deps.add(child.id)
            elif isinstance(child, ast.Attribute):
                # Get the root name (e.g., 'os' from 'os.path.join')
                current: ast.expr = child
                while isinstance(current, ast.Attribute):
                    current = current.value
                if isinstance(current, ast.Name):
                    deps.add(current.id)
        return deps

    def _analyze(self):
        """Analyze the source code structure."""
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname or alias.name
                    block = CodeBlock(
                        block_type=CodeBlockType.IMPORT,
                        content=self._get_source_segment(node),
                        start_line=node.lineno,
                        end_line=node.end_lineno or node.lineno,
                        name=name,
                    )
                    self.blocks.append(block)
                    self.imports[name] = block

            elif isinstance(node, ast.ImportFrom):
                content = self._get_source_segment(node)
                for alias in node.names:
                    name = alias.asname or alias.name
                    block = CodeBlock(
                        block_type=CodeBlockType.FROM_IMPORT,
                        content=content,
                        start_line=node.lineno,
                        end_line=node.end_lineno or node.lineno,
                        name=name,
                        dependencies={node.module} if node.module else set(),
                    )
                    self.imports[name] = block
                self.blocks.append(
                    CodeBlock(
                        block_type=CodeBlockType.FROM_IMPORT,
                        content=content,
                        start_line=node.lineno,
                        end_line=node.end_lineno or node.lineno,
                    )
                )

            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Check if it's a method (inside a class)
                parent = None
                for potential_parent in ast.walk(self.tree):
                    if isinstance(potential_parent, ast.ClassDef):
                        for child in potential_parent.body:
                            if child is node:
                                parent = potential_parent.name
                                break

                block_type = (
                    CodeBlockType.METHOD_DEF if parent else CodeBlockType.FUNCTION_DEF
                )
                deps = self._find_dependencies(node)

                block = CodeBlock(
                    block_type=block_type,
                    content=self._get_source_segment(node),
                    start_line=node.lineno,
                    end_line=node.end_lineno or node.lineno,
                    indent=self._get_indent(node.lineno - 1),
                    name=node.name,
                    parent=parent,
                    dependencies=deps,
                )
                self.blocks.append(block)
                self.functions[node.name] = block

            elif isinstance(node, ast.ClassDef):
                deps = self._find_dependencies(node)
                block = CodeBlock(
                    block_type=CodeBlockType.CLASS_DEF,
                    content=self._get_source_segment(node),
                    start_line=node.lineno,
                    end_line=node.end_lineno or node.lineno,
                    indent=self._get_indent(node.lineno - 1),
                    name=node.name,
                    dependencies=deps,
                )
                self.blocks.append(block)
                self.classes[node.name] = block

    def get_imports_for_name(self, name: str) -> Optional[CodeBlock]:
        """Get the import block needed for a name."""
        return self.imports.get(name)

    def get_structure_summary(self) -> dict:
        """Get a summary of the code structure."""
        return {
            "imports": list(self.imports.keys()),
            "classes": list(self.classes.keys()),
            "functions": [
                f
                for f in self.functions.keys()
                if self.functions[f].block_type == CodeBlockType.FUNCTION_DEF
            ],
            "methods": {
                cls: [f for f, b in self.functions.items() if b.parent == cls]
                for cls in self.classes.keys()
            },
        }


class CodingPlanGenerator:
    """Generates a realistic coding plan based on code analysis."""

    def __init__(self, analyzer: PythonCodeAnalyzer):
        self.analyzer = analyzer
        self.written_imports: set[str] = set()
        self.written_names: set[str] = set()

    def _needs_import(self, deps: set[str]) -> list[CodeBlock]:
        """Check which imports are needed for dependencies."""
        needed = []
        for dep in deps:
            if dep not in self.written_imports and dep in self.analyzer.imports:
                needed.append(self.analyzer.imports[dep])
                self.written_imports.add(dep)
        return needed

    def generate_plan(self) -> list[CodingAction]:
        """Generate a realistic coding plan.

        Human coding patterns:
        1. Start with main structure (class/function signatures)
        2. Add imports as needed (when first using something)
        3. Fill in bodies after signatures
        4. Add docstrings
        """
        actions = []
        source_lines = self.analyzer.lines

        # Strategy: Write code in a more human way
        # 1. First, identify the overall structure
        # 2. Write imports that are used at module level first
        # 3. Write class/function skeletons
        # 4. Fill in the bodies

        # Group blocks by type and sort by line number
        imports = sorted(
            [
                b
                for b in self.analyzer.blocks
                if b.block_type in (CodeBlockType.IMPORT, CodeBlockType.FROM_IMPORT)
            ],
            key=lambda b: b.start_line,
        )

        classes = sorted(
            [
                b
                for b in self.analyzer.blocks
                if b.block_type == CodeBlockType.CLASS_DEF
            ],
            key=lambda b: b.start_line,
        )

        functions = sorted(
            [
                b
                for b in self.analyzer.blocks
                if b.block_type == CodeBlockType.FUNCTION_DEF
            ],
            key=lambda b: b.start_line,
        )

        # For now, use a simpler but still more realistic approach:
        # Write the file in logical chunks, simulating human behavior

        written_lines = set()

        # Phase 1: Module-level structure (imports, then definitions)
        # But write imports only when we're about to use them

        # First pass: write any module docstring or comments at the top
        for i, line in enumerate(source_lines):
            stripped = line.strip()
            if (
                stripped.startswith('"""')
                or stripped.startswith("'''")
                or stripped.startswith("#")
            ):
                if i not in written_lines:
                    actions.append(
                        CodingAction(
                            action="write",
                            content=line + "\n",
                            line=i,
                            description="Write module docstring/comment",
                        )
                    )
                    written_lines.add(i)
            elif stripped and not stripped.startswith(("import", "from")):
                break

        # Find where the first non-import code starts
        first_code_line = 0
        for i, line in enumerate(source_lines):
            stripped = line.strip()
            if stripped and not stripped.startswith(
                ("#", "import", "from", '"""', "'''")
            ):
                if not (stripped.startswith('"""') or stripped.startswith("'''")):
                    first_code_line = i
                    break

        # Write imports that are needed before the first class/function
        for imp in imports:
            if imp.start_line - 1 < first_code_line:
                for line_no in range(imp.start_line - 1, imp.end_line):
                    if line_no not in written_lines:
                        actions.append(
                            CodingAction(
                                action="write",
                                content=source_lines[line_no] + "\n",
                                line=line_no,
                                description="Write import",
                            )
                        )
                        written_lines.add(line_no)

        # Phase 2: Write class and function structures
        for cls in classes:
            # Check if we need any imports for this class
            needed_imports = self._needs_import(cls.dependencies)
            for imp in needed_imports:
                for line_no in range(imp.start_line - 1, imp.end_line):
                    if line_no not in written_lines:
                        actions.append(
                            CodingAction(
                                action="insert_import",
                                content=source_lines[line_no] + "\n",
                                line=line_no,
                                description=f"Add import needed for {cls.name}",
                            )
                        )
                        written_lines.add(line_no)

            # Write the class content (all lines)
            for line_no in range(cls.start_line - 1, cls.end_line):
                if line_no not in written_lines:
                    actions.append(
                        CodingAction(
                            action="write",
                            content=source_lines[line_no] + "\n",
                            line=line_no,
                            description=f"Write class {cls.name}",
                        )
                    )
                    written_lines.add(line_no)

        # Phase 3: Write standalone functions
        for func in functions:
            needed_imports = self._needs_import(func.dependencies)
            for imp in needed_imports:
                for line_no in range(imp.start_line - 1, imp.end_line):
                    if line_no not in written_lines:
                        actions.append(
                            CodingAction(
                                action="insert_import",
                                content=source_lines[line_no] + "\n",
                                line=line_no,
                                description=f"Add import needed for {func.name}",
                            )
                        )
                        written_lines.add(line_no)

            for line_no in range(func.start_line - 1, func.end_line):
                if line_no not in written_lines:
                    actions.append(
                        CodingAction(
                            action="write",
                            content=source_lines[line_no] + "\n",
                            line=line_no,
                            description=f"Write function {func.name}",
                        )
                    )
                    written_lines.add(line_no)

        # Phase 4: Write any remaining lines (module-level code)
        for i, line in enumerate(source_lines):
            if i not in written_lines:
                actions.append(
                    CodingAction(
                        action="write",
                        content=line + "\n",
                        line=i,
                        description="Write remaining code",
                    )
                )
                written_lines.add(i)

        return actions


class RealisticPythonSimulator:
    """Generates realistic typing sequences for Python code."""

    def __init__(self, source: str):
        self.source = source
        self.analyzer = PythonCodeAnalyzer(source)
        self.planner = CodingPlanGenerator(self.analyzer)

    def generate_content_sequence(self) -> Generator[tuple[str, str], None, None]:
        """Generate (content, description) tuples in realistic coding order.

        Yields chunks of code with descriptions of what's being written.
        """
        plan = self.planner.generate_plan()

        current_chunk: list[str] = []
        current_desc = ""

        for action in plan:
            if action.description != current_desc and current_chunk:
                # Yield the previous chunk
                yield ("".join(current_chunk), current_desc)
                current_chunk = []

            current_chunk.append(action.content)
            current_desc = action.description

        # Yield final chunk
        if current_chunk:
            yield ("".join(current_chunk), current_desc)

    def get_realistic_content(self) -> str:
        """Get the content in realistic coding order.

        This reorders the code to simulate how a human would write it.
        """
        chunks = list(self.generate_content_sequence())
        return "".join(chunk for chunk, _ in chunks)

    def get_structure_info(self) -> dict:
        """Get information about the code structure."""
        return self.analyzer.get_structure_summary()


def simulate_python_coding(source: str) -> Generator[tuple[str, str], None, None]:
    """Main entry point for Python coding simulation.

    Args:
        source: Python source code to simulate typing

    Yields:
        (content, description) tuples representing coding actions
    """
    simulator = RealisticPythonSimulator(source)
    yield from simulator.generate_content_sequence()
