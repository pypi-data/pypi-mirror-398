"""Deep Python code analysis with dependency detection.

This module provides sophisticated AST analysis to:
1. Extract code structure (imports, classes, functions)
2. Build call graphs to understand dependencies
3. Determine optimal typing order based on dependencies
4. Track exact source locations for every element

The key insight is that when typing code realistically, we should:
- Type function A's signature before function B's if B calls A
- Type bodies in the same dependency order
- Handle circular dependencies gracefully
"""

import ast
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class ElementType(Enum):
    """Type of code element."""

    MODULE_DOCSTRING = "module_docstring"
    IMPORT = "import"
    CLASS = "class"
    METHOD = "method"
    FUNCTION = "function"
    CLASS_ATTRIBUTE = "class_attribute"


@dataclass
class SourceLocation:
    """Exact source location of a code element."""

    start_line: int  # 1-indexed
    end_line: int  # 1-indexed, inclusive
    start_col: int  # 0-indexed
    end_col: int  # 0-indexed

    @classmethod
    def from_node(cls, node: Any) -> "SourceLocation":
        """Create from AST node."""
        return cls(
            start_line=node.lineno,
            end_line=node.end_lineno or node.lineno,
            start_col=node.col_offset,
            end_col=node.end_col_offset or node.col_offset,
        )


@dataclass
class ImportInfo:
    """Information about an import statement."""

    source: str  # The full import text
    names: list[str]  # Imported names
    module: Optional[str]  # Module for 'from X import Y'
    location: SourceLocation
    is_from_import: bool


@dataclass
class FunctionInfo:
    """Detailed information about a function or method."""

    name: str
    qualified_name: str  # e.g., "MyClass.my_method" or "my_function"
    signature: str  # Full signature text
    signature_first_line: str  # Just the first line (for searching)
    body: str  # Body text (without docstring)
    docstring: Optional[str]
    decorators: list[str]
    location: SourceLocation
    signature_location: SourceLocation
    body_location: Optional[SourceLocation]
    indent: int
    is_method: bool
    is_async: bool
    parent_class: Optional[str] = None
    # Dependencies detected from AST
    calls: set[str] = field(default_factory=set)  # Functions/methods this calls
    references: set[str] = field(default_factory=set)  # Names referenced


@dataclass
class ClassInfo:
    """Detailed information about a class."""

    name: str
    signature: str
    docstring: Optional[str]
    methods: list[FunctionInfo]
    attributes: list[str]  # Class-level attributes
    decorators: list[str]
    base_classes: list[str]  # Names of base classes
    location: SourceLocation
    indent: int


@dataclass
class CodeStructure:
    """Complete analyzed structure of Python code."""

    source: str
    lines: list[str]
    module_docstring: Optional[str]
    module_docstring_location: Optional[SourceLocation]
    imports: list[ImportInfo]
    classes: list[ClassInfo]
    functions: list[FunctionInfo]
    # Dependency information
    call_graph: dict[str, set[str]]  # element -> elements it calls
    reverse_graph: dict[str, set[str]]  # element -> elements that call it
    # Computed order
    dependency_order: list[str]  # Topologically sorted element names


class CodeAnalyzer:
    """Analyzes Python code to extract structure and dependencies.

    This analyzer goes beyond simple parsing to understand:
    - Which functions depend on which others
    - Class inheritance hierarchies
    - Optimal typing order for realistic simulation
    """

    def __init__(self, source: str):
        self.source = source
        self.lines = source.split("\n")
        self.tree = ast.parse(source)

        # Will be populated by analysis
        self._structure: Optional[CodeStructure] = None

    def analyze(self) -> CodeStructure:
        """Perform full analysis and return the code structure."""
        if self._structure is not None:
            return self._structure

        module_docstring = None
        module_docstring_loc = None
        imports: list[ImportInfo] = []
        classes: list[ClassInfo] = []
        functions: list[FunctionInfo] = []

        # Extract module docstring
        if (
            self.tree.body
            and isinstance(self.tree.body[0], ast.Expr)
            and isinstance(self.tree.body[0].value, ast.Constant)
            and isinstance(self.tree.body[0].value.value, str)
        ):
            docstring_node = self.tree.body[0]
            module_docstring = self._get_source_lines(
                docstring_node.lineno,
                docstring_node.end_lineno or docstring_node.lineno,
            )
            module_docstring_loc = SourceLocation.from_node(docstring_node)

        # Extract imports
        for stmt in self.tree.body:
            if isinstance(stmt, ast.Import):
                imports.append(self._analyze_import(stmt))
            elif isinstance(stmt, ast.ImportFrom):
                imports.append(self._analyze_import_from(stmt))

        # Extract classes
        for stmt in self.tree.body:
            if isinstance(stmt, ast.ClassDef):
                classes.append(self._analyze_class(stmt))

        # Extract top-level functions
        for stmt in self.tree.body:
            if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append(self._analyze_function(stmt))

        # Build call graph
        all_elements = self._collect_all_elements(classes, functions)
        call_graph = self._build_call_graph(all_elements)
        reverse_graph = self._build_reverse_graph(call_graph)

        # Compute dependency order
        dependency_order = self._topological_sort(call_graph, all_elements)

        self._structure = CodeStructure(
            source=self.source,
            lines=self.lines,
            module_docstring=module_docstring,
            module_docstring_location=module_docstring_loc,
            imports=imports,
            classes=classes,
            functions=functions,
            call_graph=call_graph,
            reverse_graph=reverse_graph,
            dependency_order=dependency_order,
        )

        return self._structure

    def _get_source_lines(self, start: int, end: int) -> str:
        """Get source lines (1-indexed, inclusive)."""
        return "\n".join(self.lines[start - 1 : end])

    def _get_indent(self, line_num: int) -> int:
        """Get indentation of a line (1-indexed)."""
        if 1 <= line_num <= len(self.lines):
            line = self.lines[line_num - 1]
            return len(line) - len(line.lstrip())
        return 0

    def _analyze_import(self, node: ast.Import) -> ImportInfo:
        """Analyze an import statement."""
        names = [alias.name for alias in node.names]
        source = self._get_source_lines(node.lineno, node.end_lineno or node.lineno)
        return ImportInfo(
            source=source,
            names=names,
            module=None,
            location=SourceLocation.from_node(node),
            is_from_import=False,
        )

    def _analyze_import_from(self, node: ast.ImportFrom) -> ImportInfo:
        """Analyze a from...import statement."""
        names = [alias.asname or alias.name for alias in node.names]
        source = self._get_source_lines(node.lineno, node.end_lineno or node.lineno)
        return ImportInfo(
            source=source,
            names=names,
            module=node.module,
            location=SourceLocation.from_node(node),
            is_from_import=True,
        )

    def _analyze_function(
        self, node: Any, parent_class: Optional[str] = None
    ) -> FunctionInfo:
        """Analyze a function or method."""
        is_async = isinstance(node, ast.AsyncFunctionDef)
        qualified_name = f"{parent_class}.{node.name}" if parent_class else node.name

        # Get signature (may span multiple lines)
        sig_end_line = self._find_signature_end(node)
        signature = self._get_source_lines(node.lineno, sig_end_line)
        signature_first_line = self.lines[node.lineno - 1]

        # Extract docstring
        docstring = None
        body_start_idx = 0
        if (
            node.body
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant)
            and isinstance(node.body[0].value.value, str)
        ):
            doc_node = node.body[0]
            docstring = self._get_source_lines(
                doc_node.lineno, doc_node.end_lineno or doc_node.lineno
            )
            body_start_idx = 1

        # Extract body (excluding docstring)
        body = ""
        body_location = None
        body_nodes = node.body[body_start_idx:]
        if body_nodes:
            body_start_line = body_nodes[0].lineno
            body_end_line = body_nodes[-1].end_lineno or body_nodes[-1].lineno
            body = self._get_source_lines(body_start_line, body_end_line)
            body_location = SourceLocation(
                start_line=body_start_line,
                end_line=body_end_line,
                start_col=0,
                end_col=0,
            )

        # Extract decorators
        decorators = []
        for dec in node.decorator_list:
            dec_text = self._get_source_lines(dec.lineno, dec.end_lineno or dec.lineno)
            decorators.append(dec_text)

        # Analyze calls and references in the body
        calls, references = self._analyze_body_dependencies(node)

        return FunctionInfo(
            name=node.name,
            qualified_name=qualified_name,
            signature=signature,
            signature_first_line=signature_first_line,
            body=body,
            docstring=docstring,
            decorators=decorators,
            location=SourceLocation.from_node(node),
            signature_location=SourceLocation(
                start_line=node.lineno,
                end_line=sig_end_line,
                start_col=node.col_offset,
                end_col=0,
            ),
            body_location=body_location,
            indent=self._get_indent(node.lineno),
            is_method=parent_class is not None,
            is_async=is_async,
            parent_class=parent_class,
            calls=calls,
            references=references,
        )

    def _analyze_class(self, node: ast.ClassDef) -> ClassInfo:
        """Analyze a class definition."""
        signature = self.lines[node.lineno - 1]

        # Extract docstring
        docstring = None
        if (
            node.body
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant)
            and isinstance(node.body[0].value.value, str)
        ):
            doc_node = node.body[0]
            docstring = self._get_source_lines(
                doc_node.lineno, doc_node.end_lineno or doc_node.lineno
            )

        # Extract methods
        methods = []
        for child in node.body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                methods.append(self._analyze_function(child, parent_class=node.name))

        # Extract class attributes (simple assignments)
        attributes = []
        for child in node.body:
            if isinstance(child, ast.AnnAssign) and isinstance(child.target, ast.Name):
                attributes.append(child.target.id)
            elif isinstance(child, ast.Assign):
                for target in child.targets:
                    if isinstance(target, ast.Name):
                        attributes.append(target.id)

        # Extract decorators
        decorators = []
        for dec in node.decorator_list:
            dec_text = self._get_source_lines(dec.lineno, dec.end_lineno or dec.lineno)
            decorators.append(dec_text)

        # Extract base classes
        base_classes = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                base_classes.append(base.id)
            elif isinstance(base, ast.Attribute):
                # Handle module.Class
                parts: list[str] = []
                attr_node: ast.expr = base
                while isinstance(attr_node, ast.Attribute):
                    parts.append(attr_node.attr)
                    attr_node = attr_node.value
                if isinstance(attr_node, ast.Name):
                    parts.append(attr_node.id)
                base_classes.append(".".join(reversed(parts)))

        return ClassInfo(
            name=node.name,
            signature=signature,
            docstring=docstring,
            methods=methods,
            attributes=attributes,
            decorators=decorators,
            base_classes=base_classes,
            location=SourceLocation.from_node(node),
            indent=self._get_indent(node.lineno),
        )

    def _find_signature_end(self, node) -> int:
        """Find the line where a function signature ends (the line with ':')."""
        end_line = node.lineno
        paren_depth = 0
        for i in range(node.lineno - 1, min(node.lineno + 20, len(self.lines))):
            line = self.lines[i]
            paren_depth += line.count("(") - line.count(")")
            if ":" in line and paren_depth <= 0:
                end_line = i + 1
                break
        return end_line

    def _analyze_body_dependencies(self, node) -> tuple[set[str], set[str]]:
        """Analyze a function body to find calls and references.

        Returns:
            (calls, references) - Sets of names called and referenced
        """
        calls = set()
        references = set()

        for child in ast.walk(node):
            # Function/method calls
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    calls.add(child.func.id)
                elif isinstance(child.func, ast.Attribute):
                    # self.method() -> just method name
                    # other.method() -> other.method
                    if isinstance(child.func.value, ast.Name):
                        if child.func.value.id == "self":
                            calls.add(child.func.attr)
                        else:
                            calls.add(f"{child.func.value.id}.{child.func.attr}")
                    else:
                        calls.add(child.func.attr)

            # Name references (for variable dependencies)
            elif isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load):
                references.add(child.id)

        return calls, references

    def _collect_all_elements(
        self, classes: list[ClassInfo], functions: list[FunctionInfo]
    ) -> dict[str, FunctionInfo]:
        """Collect all functions and methods into a single dict."""
        elements = {}

        for func in functions:
            elements[func.qualified_name] = func

        for cls in classes:
            for method in cls.methods:
                elements[method.qualified_name] = method

        return elements

    def _build_call_graph(
        self, elements: dict[str, FunctionInfo]
    ) -> dict[str, set[str]]:
        """Build a call graph from function dependencies.

        Returns:
            Dict mapping function name -> set of functions it calls
        """
        graph = {}
        element_names = set(elements.keys())

        # Also include simple function names (without class prefix)
        simple_names = {}
        for name in element_names:
            if "." in name:
                simple = name.split(".")[-1]
                simple_names[simple] = name
            else:
                simple_names[name] = name

        for name, func in elements.items():
            dependencies = set()
            for call in func.calls:
                # Check if this call refers to a known element
                if call in element_names:
                    dependencies.add(call)
                elif call in simple_names:
                    dependencies.add(simple_names[call])
                # Handle method calls within same class
                elif (
                    func.parent_class and f"{func.parent_class}.{call}" in element_names
                ):
                    dependencies.add(f"{func.parent_class}.{call}")

            graph[name] = dependencies

        return graph

    def _build_reverse_graph(
        self, call_graph: dict[str, set[str]]
    ) -> dict[str, set[str]]:
        """Build reverse call graph (who calls this function)."""
        reverse: dict[str, set[str]] = {name: set() for name in call_graph}

        for caller, callees in call_graph.items():
            for callee in callees:
                if callee in reverse:
                    reverse[callee].add(caller)

        return reverse

    def _topological_sort(
        self, graph: dict[str, set[str]], elements: dict[str, FunctionInfo]
    ) -> list[str]:
        """Topologically sort elements by dependencies.

        Uses Kahn's algorithm. Handles cycles by breaking them.

        The graph has edges: caller -> callees (what each function calls).
        We want dependencies (callees) to come BEFORE callers.

        Returns:
            List of element names in dependency order (dependencies first)
        """
        # For correct ordering, we need to count how many things CALL each function
        # (not how many things it calls). Use the reverse graph for this.
        # A function with 0 incoming calls and no dependencies should come first.

        # Calculate out-degrees (number of dependencies each function has)
        out_degree = {name: len(deps) for name, deps in graph.items()}

        # Start with elements that have no dependencies (out_degree == 0)
        queue = [name for name, degree in out_degree.items() if degree == 0]
        result = []
        processed = set()

        while queue:
            # Sort queue for deterministic order (alphabetical as tiebreaker)
            queue.sort()
            current = queue.pop(0)

            if current in processed:
                continue

            result.append(current)
            processed.add(current)

            # Find elements that depend on current and reduce their out_degree
            for name, deps in graph.items():
                if current in deps and name not in processed:
                    out_degree[name] -= 1
                    if out_degree[name] == 0:
                        queue.append(name)

        # Handle cycles: add remaining elements
        remaining = [name for name in graph if name not in processed]
        if remaining:
            # Sort by out_degree (lowest first) then alphabetically
            remaining.sort(key=lambda n: (out_degree[n], n))
            result.extend(remaining)

        return result

    def get_typing_order(self) -> list[tuple[str, str, Any]]:
        """Get the optimal order for typing elements.

        Returns:
            List of (element_name, phase, element_info) tuples where phase is:
            - 'signature': Type the signature/declaration
            - 'body': Fill in the body/implementation
        """
        structure = self.analyze()
        order = []

        # Group elements by class for better organization
        class_methods: dict[str, list[FunctionInfo]] = {}
        standalone_funcs: list[FunctionInfo] = []

        for name in structure.dependency_order:
            if "." in name:
                cls_name, method_name = name.split(".", 1)
                if cls_name not in class_methods:
                    class_methods[cls_name] = []
                # Find the method info
                for cls in structure.classes:
                    if cls.name == cls_name:
                        for method in cls.methods:
                            if method.name == method_name:
                                class_methods[cls_name].append(method)
                                break
            else:
                # Standalone function
                for func in structure.functions:
                    if func.name == name:
                        standalone_funcs.append(func)
                        break

        # Build typing order:
        # 1. Classes and functions interleaved by source line order
        # 2. All method bodies (in dependency order)
        # 3. All function bodies (in dependency order)

        # Phase 1: Classes and functions in source order (interleaved)
        # Create a combined list sorted by start line
        toplevel_items: list[tuple[str, int, Any]] = []
        for cls in structure.classes:
            toplevel_items.append(("class", cls.location.start_line, cls))
        for func in standalone_funcs:
            toplevel_items.append(("func", func.location.start_line, func))
        toplevel_items.sort(key=lambda x: x[1])

        for item_type, _, item in toplevel_items:
            if item_type == "class":
                cls = item
                order.append((cls.name, "class_start", cls))
                # Methods in dependency order
                if cls.name in class_methods:
                    for method in class_methods[cls.name]:
                        order.append((method.qualified_name, "signature", method))
                order.append((cls.name, "class_end", cls))
            else:
                func = item
                order.append((func.qualified_name, "signature", func))

        # Phase 3: Method bodies (in dependency order)
        for _cls_name, methods in class_methods.items():
            for method in methods:
                if method.body and method.body.strip() != "pass":
                    order.append((method.qualified_name, "body", method))

        # Phase 4: Function bodies (in dependency order)
        for func in standalone_funcs:
            if func.body and func.body.strip() != "pass":
                order.append((func.qualified_name, "body", func))

        return order

    def get_structure(self) -> CodeStructure:
        """Get the analyzed code structure."""
        return self.analyze()

    def print_dependency_analysis(self):
        """Print a human-readable dependency analysis."""
        structure = self.analyze()

        print("=" * 60)
        print("DEPENDENCY ANALYSIS")
        print("=" * 60)

        print("\n--- Call Graph ---")
        for name, deps in sorted(structure.call_graph.items()):
            if deps:
                print(f"  {name} -> {', '.join(sorted(deps))}")
            else:
                print(f"  {name} -> (no dependencies)")

        print("\n--- Dependency Order ---")
        for i, name in enumerate(structure.dependency_order, 1):
            print(f"  {i}. {name}")

        print("\n--- Typing Order ---")
        for name, phase, _ in self.get_typing_order():
            print(f"  [{phase:12}] {name}")
