"""Smart Python typing simulator that mimics real human coding behavior.

This module provides a sophisticated simulation of how humans actually write Python code:

1. SKELETON FIRST: Write class/function signatures with 'pass', then fill in bodies
2. IMPORTS ON DEMAND: Add imports when you first need them, not all upfront
3. DOCSTRINGS AFTER SIGNATURE: Write the docstring right after def/class line
4. LOGICAL GROUPING: Write related code together
5. INCREMENTAL: Build up code piece by piece

Example human coding flow:
1. "I need a class for handling users..."
2. Writes: class UserHandler:
3.             pass
4. "It needs an __init__ method..."
5. Goes into class, writes: def __init__(self):
6.                              pass
7. "And a method to process..."
8. Writes: def process(self, data):
9.             pass
10. Now goes back to fill in __init__...
11. "Oh, I need to import dataclass..."
12. Goes to top, adds: from dataclasses import dataclass
"""

import ast
from collections.abc import Generator
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional


class WritePhase(Enum):
    """Phases of code writing."""

    SETUP = auto()  # Module docstring, initial comments
    SKELETON = auto()  # Function/class signatures with pass
    FILL_BODY = auto()  # Filling in function bodies
    ADD_IMPORT = auto()  # Going back to add an import
    REFINEMENT = auto()  # Adding docstrings, type hints, etc.


@dataclass
class CodeChunk:
    """A chunk of code to be typed."""

    content: str
    phase: WritePhase
    description: str
    line_hint: int = 0  # Approximate line number for context
    insert_at_top: bool = False  # For imports
    replace_pass: bool = False  # For filling in bodies
    target_function: Optional[str] = None  # Which function to fill


@dataclass
class FunctionInfo:
    """Information about a function/method."""

    name: str
    signature: str  # Just the def line(s)
    docstring: Optional[str]
    body: str  # The actual body (without signature and docstring)
    full_content: str  # Complete function
    start_line: int
    end_line: int
    indent: int
    decorators: list[str]
    is_method: bool
    parent_class: Optional[str]
    dependencies: set[str]  # Names used that might need imports


@dataclass
class ClassInfo:
    """Information about a class."""

    name: str
    signature: str  # Just the class line
    docstring: Optional[str]
    methods: list[FunctionInfo]
    full_content: str
    start_line: int
    end_line: int
    indent: int
    decorators: list[str]
    bases: list[str]  # Base classes
    dependencies: set[str]


@dataclass
class ImportInfo:
    """Information about an import."""

    content: str
    names: list[str]  # Names being imported
    module: Optional[str]  # For 'from X import Y'
    start_line: int


class SmartPythonAnalyzer:
    """Analyzes Python code for smart typing simulation."""

    def __init__(self, source: str):
        self.source = source
        self.lines = source.split("\n")
        self.tree = ast.parse(source)

        # Extracted info
        self.module_docstring: Optional[str] = None
        self.imports: list[ImportInfo] = []
        self.classes: list[ClassInfo] = []
        self.functions: list[FunctionInfo] = []  # Top-level functions only
        self.other_code: list[tuple[int, int, str]] = []  # (start, end, content)

        self._analyze()

    def _get_source_lines(self, start: int, end: int) -> str:
        """Get source lines (1-indexed to 0-indexed conversion)."""
        return "\n".join(self.lines[start - 1 : end])

    def _get_indent(self, line_no: int) -> int:
        """Get indentation of a line (1-indexed)."""
        if 1 <= line_no <= len(self.lines):
            line = self.lines[line_no - 1]
            return len(line) - len(line.lstrip())
        return 0

    def _extract_decorators(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef
    ) -> list[str]:
        """Extract decorator lines."""
        decorators = []
        for dec in node.decorator_list:
            decorators.append(
                self._get_source_lines(dec.lineno, dec.end_lineno or dec.lineno)
            )
        return decorators

    def _extract_function_signature(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> str:
        """Extract just the function signature (def line, potentially multi-line)."""
        lines = []
        paren_depth = 0

        for i in range(node.lineno - 1, min(node.lineno + 20, len(self.lines))):
            line = self.lines[i]
            lines.append(line)
            paren_depth += line.count("(") - line.count(")")
            if ":" in line and paren_depth <= 0:
                break

        return "\n".join(lines)

    def _extract_docstring_node(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef
    ) -> Optional[ast.Expr]:
        """Get the docstring AST node if present."""
        if (
            node.body
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant)
            and isinstance(node.body[0].value.value, str)
        ):
            return node.body[0]
        return None

    def _extract_docstring(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef
    ) -> Optional[str]:
        """Extract docstring content."""
        doc_node = self._extract_docstring_node(node)
        if doc_node:
            return self._get_source_lines(
                doc_node.lineno, doc_node.end_lineno or doc_node.lineno
            )
        return None

    def _extract_body_without_docstring(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> str:
        """Extract function body, skipping docstring."""
        doc_node = self._extract_docstring_node(node)
        start_idx = 1 if doc_node else 0

        body_nodes = node.body[start_idx:]
        if not body_nodes:
            return ""

        first_line = body_nodes[0].lineno
        last_line = body_nodes[-1].end_lineno or body_nodes[-1].lineno

        return self._get_source_lines(first_line, last_line)

    def _find_dependencies(self, node: ast.AST) -> set[str]:
        """Find external names used in a node."""
        deps = set()
        for child in ast.walk(node):
            if isinstance(child, ast.Name):
                # Skip common builtins
                if child.id not in {
                    "True",
                    "False",
                    "None",
                    "print",
                    "len",
                    "str",
                    "int",
                    "float",
                    "list",
                    "dict",
                    "set",
                    "tuple",
                    "range",
                    "enumerate",
                    "zip",
                    "map",
                    "filter",
                    "isinstance",
                    "issubclass",
                    "type",
                    "super",
                    "open",
                    "input",
                    "Exception",
                    "ValueError",
                    "TypeError",
                    "KeyError",
                    "IndexError",
                    "self",
                }:
                    deps.add(child.id)
            elif isinstance(child, ast.Attribute):
                # Get root name
                current: ast.expr = child
                while isinstance(current, ast.Attribute):
                    current = current.value
                if isinstance(current, ast.Name) and current.id != "self":
                    deps.add(current.id)
        return deps

    def _analyze_function(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        parent_class: Optional[str] = None,
    ) -> FunctionInfo:
        """Analyze a function/method."""
        decorators = self._extract_decorators(node)
        signature = self._extract_function_signature(node)
        docstring = self._extract_docstring(node)
        body = self._extract_body_without_docstring(node)
        full_content = self._get_source_lines(
            node.decorator_list[0].lineno if node.decorator_list else node.lineno,
            node.end_lineno or node.lineno,
        )

        return FunctionInfo(
            name=node.name,
            signature=signature,
            docstring=docstring,
            body=body,
            full_content=full_content,
            start_line=node.lineno,
            end_line=node.end_lineno or node.lineno,
            indent=self._get_indent(node.lineno),
            decorators=decorators,
            is_method=parent_class is not None,
            parent_class=parent_class,
            dependencies=self._find_dependencies(node),
        )

    def _analyze_class(self, node: ast.ClassDef) -> ClassInfo:
        """Analyze a class."""
        decorators = self._extract_decorators(node)

        # Class signature (just the class line)
        signature = self.lines[node.lineno - 1]

        docstring = self._extract_docstring(node)

        # Extract methods
        methods = []
        for child in node.body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                methods.append(self._analyze_function(child, parent_class=node.name))

        # Base classes
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                bases.append(ast.unparse(base))

        full_content = self._get_source_lines(
            node.decorator_list[0].lineno if node.decorator_list else node.lineno,
            node.end_lineno or node.lineno,
        )

        return ClassInfo(
            name=node.name,
            signature=signature,
            docstring=docstring,
            methods=methods,
            full_content=full_content,
            start_line=node.lineno,
            end_line=node.end_lineno or node.lineno,
            indent=self._get_indent(node.lineno),
            decorators=decorators,
            bases=bases,
            dependencies=self._find_dependencies(node),
        )

    def _analyze(self):
        """Perform the analysis."""
        # Check for module docstring
        if (
            self.tree.body
            and isinstance(self.tree.body[0], ast.Expr)
            and isinstance(self.tree.body[0].value, ast.Constant)
            and isinstance(self.tree.body[0].value.value, str)
        ):
            doc_node = self.tree.body[0]
            self.module_docstring = self._get_source_lines(
                doc_node.lineno, doc_node.end_lineno or doc_node.lineno
            )

        # Analyze top-level nodes
        for node in self.tree.body:
            if isinstance(node, ast.Import):
                names = [alias.asname or alias.name for alias in node.names]
                self.imports.append(
                    ImportInfo(
                        content=self._get_source_lines(
                            node.lineno, node.end_lineno or node.lineno
                        ),
                        names=names,
                        module=None,
                        start_line=node.lineno,
                    )
                )

            elif isinstance(node, ast.ImportFrom):
                names = [alias.asname or alias.name for alias in node.names]
                self.imports.append(
                    ImportInfo(
                        content=self._get_source_lines(
                            node.lineno, node.end_lineno or node.lineno
                        ),
                        names=names,
                        module=node.module,
                        start_line=node.lineno,
                    )
                )

            elif isinstance(node, ast.ClassDef):
                self.classes.append(self._analyze_class(node))

            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self.functions.append(self._analyze_function(node))


class SmartPythonTyper:
    """Generates realistic typing sequence for Python code.

    Simulates human coding behavior:
    1. Write structure first (signatures with pass)
    2. Fill in bodies
    3. Add imports as needed
    """

    def __init__(self, source: str, skeleton_first: bool = True):
        """Initialize the smart typer.

        Args:
            source: Python source code
            skeleton_first: If True, write signatures first then fill bodies.
                          If False, write code more linearly.
        """
        self.source = source
        self.skeleton_first = skeleton_first
        self.analyzer = SmartPythonAnalyzer(source)

        # Track state
        self.written_imports: set[str] = set()
        self.pending_imports: list[ImportInfo] = []

    def _make_skeleton(self, func: FunctionInfo) -> str:
        """Create a skeleton version of a function (signature + docstring + pass)."""
        parts = []

        # Decorators
        for dec in func.decorators:
            parts.append(dec)

        # Signature
        parts.append(func.signature)

        # Docstring (if present, write it in skeleton)
        if func.docstring:
            parts.append(func.docstring)
        else:
            # Just pass
            indent = " " * (func.indent + 4)
            parts.append(f"{indent}pass")

        return "\n".join(parts)

    def _make_skeleton_no_docstring(self, func: FunctionInfo) -> str:
        """Create a skeleton version of a function WITHOUT docstring."""
        parts = []

        # Decorators
        for dec in func.decorators:
            parts.append(dec)

        # Signature
        parts.append(func.signature)

        # Just pass (no docstring yet - added later)
        indent = " " * (func.indent + 4)
        parts.append(f"{indent}pass")

        return "\n".join(parts)

    def _make_class_skeleton(self, cls: ClassInfo) -> str:
        """Create a skeleton version of a class (with docstrings)."""
        parts = []

        # Decorators
        for dec in cls.decorators:
            parts.append(dec)

        # Signature
        parts.append(cls.signature)

        # Docstring
        if cls.docstring:
            parts.append("    " + cls.docstring.strip())

        # Method skeletons
        if cls.methods:
            for method in cls.methods:
                parts.append("")  # Blank line
                skeleton = self._make_skeleton(method)
                parts.append(skeleton)
        else:
            parts.append("    pass")

        return "\n".join(parts)

    def _make_class_skeleton_no_docstring(self, cls: ClassInfo) -> str:
        """Create a skeleton version of a class WITHOUT docstrings."""
        parts = []

        # Decorators
        for dec in cls.decorators:
            parts.append(dec)

        # Signature
        parts.append(cls.signature)

        # Method skeletons (without their docstrings)
        if cls.methods:
            for method in cls.methods:
                parts.append("")  # Blank line
                skeleton = self._make_skeleton_no_docstring(method)
                parts.append(skeleton)
        else:
            parts.append("    pass")

        return "\n".join(parts)

    def _check_import_needed(self, deps: set[str]) -> list[ImportInfo]:
        """Check if any imports are needed for dependencies."""
        needed = []
        for dep in deps:
            for imp in self.analyzer.imports:
                if dep in imp.names and dep not in self.written_imports:
                    needed.append(imp)
                    self.written_imports.update(imp.names)
        return needed

    def generate_chunks(self) -> Generator[CodeChunk, None, None]:
        """Generate code chunks in realistic human coding order.

        Order: structure -> imports -> bodies -> docstrings
        """
        if self.skeleton_first:
            yield from self._generate_skeleton_first()
        else:
            yield from self._generate_linear()

    def _generate_skeleton_first(self) -> Generator[CodeChunk, None, None]:
        """Generate chunks using skeleton-first approach.

        Realistic human coding order:
        1. Write class/function skeletons first (structure)
        2. Add imports as needed when implementing
        3. Fill in bodies
        4. Add docstrings last (polish/documentation)
        """
        imports_written = set()

        # Phase 1: Write class skeletons (without docstrings)
        for cls in self.analyzer.classes:
            # Check if we need imports for base classes
            for base in cls.bases:
                for imp in self.analyzer.imports:
                    if base in imp.names and base not in imports_written:
                        yield CodeChunk(
                            content=imp.content + "\n",
                            phase=WritePhase.ADD_IMPORT,
                            description=f"Adding import for base class {base}",
                            insert_at_top=True,
                        )
                        imports_written.update(imp.names)

            # Write class skeleton (without docstring)
            skeleton = self._make_class_skeleton_no_docstring(cls)
            yield CodeChunk(
                content=skeleton + "\n\n",
                phase=WritePhase.SKELETON,
                description=f"Writing class {cls.name} structure",
                line_hint=cls.start_line,
            )

        # Phase 2: Write function skeletons (without docstrings)
        for func in self.analyzer.functions:
            skeleton = self._make_skeleton_no_docstring(func)
            yield CodeChunk(
                content=skeleton + "\n\n",
                phase=WritePhase.SKELETON,
                description=f"Writing function {func.name} structure",
                line_hint=func.start_line,
            )

        # Phase 3: Fill in class method bodies (add imports as needed)
        for cls in self.analyzer.classes:
            for method in cls.methods:
                if (
                    method.body
                    and method.body.strip()
                    and method.body.strip() != "pass"
                ):
                    # Check if we need imports for this method
                    for dep in method.dependencies:
                        for imp in self.analyzer.imports:
                            if dep in imp.names and dep not in imports_written:
                                yield CodeChunk(
                                    content=imp.content + "\n",
                                    phase=WritePhase.ADD_IMPORT,
                                    description=f"Need to import {dep}",
                                    insert_at_top=True,
                                )
                                imports_written.update(imp.names)

                    yield CodeChunk(
                        content=method.body + "\n",
                        phase=WritePhase.FILL_BODY,
                        description=f"Implementing {cls.name}.{method.name}",
                        replace_pass=True,
                        target_function=f"{cls.name}.{method.name}",
                    )

        # Phase 4: Fill in function bodies (add imports as needed)
        for func in self.analyzer.functions:
            if func.body and func.body.strip() and func.body.strip() != "pass":
                # Check imports needed
                for dep in func.dependencies:
                    for imp in self.analyzer.imports:
                        if dep in imp.names and dep not in imports_written:
                            yield CodeChunk(
                                content=imp.content + "\n",
                                phase=WritePhase.ADD_IMPORT,
                                description=f"Need to import {dep}",
                                insert_at_top=True,
                            )
                            imports_written.update(imp.names)

                yield CodeChunk(
                    content=func.body + "\n",
                    phase=WritePhase.FILL_BODY,
                    description=f"Implementing {func.name}",
                    replace_pass=True,
                    target_function=func.name,
                )

        # Phase 5: Add any remaining imports not yet written
        for imp in self.analyzer.imports:
            if not any(name in imports_written for name in imp.names):
                yield CodeChunk(
                    content=imp.content + "\n",
                    phase=WritePhase.ADD_IMPORT,
                    description="Adding import",
                    insert_at_top=True,
                )
                imports_written.update(imp.names)

        # Phase 6: Add docstrings last (documentation/polish)
        if self.analyzer.module_docstring:
            yield CodeChunk(
                content=self.analyzer.module_docstring + "\n\n",
                phase=WritePhase.REFINEMENT,
                description="Adding module docstring",
                insert_at_top=True,
            )

        for cls in self.analyzer.classes:
            if cls.docstring:
                yield CodeChunk(
                    content="    " + cls.docstring.strip() + "\n",
                    phase=WritePhase.REFINEMENT,
                    description=f"Adding docstring for {cls.name}",
                )

            for method in cls.methods:
                if method.docstring:
                    indent = " " * (method.indent + 4)
                    yield CodeChunk(
                        content=indent + method.docstring.strip() + "\n",
                        phase=WritePhase.REFINEMENT,
                        description=f"Adding docstring for {cls.name}.{method.name}",
                    )

        for func in self.analyzer.functions:
            if func.docstring:
                indent = " " * (func.indent + 4)
                yield CodeChunk(
                    content=indent + func.docstring.strip() + "\n",
                    phase=WritePhase.REFINEMENT,
                    description=f"Adding docstring for {func.name}",
                )

    def _generate_linear(self) -> Generator[CodeChunk, None, None]:
        """Generate chunks in linear order (but still with some realism)."""

        # Write imports
        if self.analyzer.imports:
            import_content = "\n".join(imp.content for imp in self.analyzer.imports)
            yield CodeChunk(
                content=import_content + "\n\n",
                phase=WritePhase.SETUP,
                description="Writing imports",
            )

        # Write classes
        for cls in self.analyzer.classes:
            yield CodeChunk(
                content=cls.full_content + "\n\n",
                phase=WritePhase.SKELETON,
                description=f"Writing class {cls.name}",
            )

        # Write functions
        for func in self.analyzer.functions:
            yield CodeChunk(
                content=func.full_content + "\n\n",
                phase=WritePhase.SKELETON,
                description=f"Writing function {func.name}",
            )

    def get_typing_content(self) -> str:
        """Get the complete content in typing order.

        Note: This returns the content that would be typed, but for skeleton-first
        mode, the final result differs from source (has intermediate pass statements).
        Use get_final_content() to get the actual final code.
        """
        chunks = list(self.generate_chunks())
        return "".join(chunk.content for chunk in chunks)

    def get_final_content(self) -> str:
        """Get the final source code (original)."""
        return self.source


def create_smart_python_sequence(
    source: str, skeleton_first: bool = True
) -> Generator[tuple[str, str, WritePhase], None, None]:
    """Create a smart typing sequence for Python code.

    Args:
        source: Python source code
        skeleton_first: Whether to use skeleton-first approach

    Yields:
        (content, description, phase) tuples
    """
    typer = SmartPythonTyper(source, skeleton_first=skeleton_first)
    for chunk in typer.generate_chunks():
        yield (chunk.content, chunk.description, chunk.phase)
