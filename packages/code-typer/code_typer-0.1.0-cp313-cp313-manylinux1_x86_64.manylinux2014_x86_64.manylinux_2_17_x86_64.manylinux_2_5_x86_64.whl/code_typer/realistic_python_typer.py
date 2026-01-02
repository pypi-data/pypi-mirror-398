"""Realistic Python typing that simulates how programmers actually write code.

The realistic typing order is:
1. Type class/function SIGNATURES in dependency order (dependencies first)
2. Go back to top and add imports
3. Fill in function BODIES in same dependency order
4. Add docstrings (module docstring at top)

Key features:
- Uses CodeAnalyzer for deep AST analysis and dependency detection
- Cursor ACTUALLY moves when going back to insert content
- Human behavior simulation (mistakes, pauses, variable speed) on all typing
- SHA256 verification to ensure content integrity
"""

import hashlib
from typing import Any

from code_typer.code_analyzer import ClassInfo, CodeAnalyzer


def normalize_content(content: str) -> str:
    """Normalize content for comparison.

    - Strip trailing whitespace from each line
    - Remove trailing blank lines
    - Normalize line endings to \\n
    """
    lines = content.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    lines = [line.rstrip() for line in lines]
    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines)


def content_hash(content: str) -> str:
    """Calculate SHA256 hash of normalized content."""
    normalized = normalize_content(content)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


class RealisticPythonTyper:
    """Types Python code with realistic cursor movements and dependency-aware order.

    Uses CodeAnalyzer to understand which functions depend on which others,
    and types them in the correct order so the code "makes sense" as it's written.
    """

    def __init__(self, source: str):
        self.source = source
        self.source_hash = content_hash(source)
        self.analyzer = CodeAnalyzer(source)
        self.structure = self.analyzer.analyze()

    def verify_content(self, display) -> tuple[bool, str]:
        """Verify the typed content matches the original source.

        Args:
            display: The display containing the typed content

        Returns:
            (success, message) tuple
        """
        typed_content = display.get_normalized_content()
        typed_hash = content_hash(typed_content)

        if typed_hash == self.source_hash:
            return True, f"Content verified: SHA256 {typed_hash[:16]}..."

        # Find differences
        original_lines = normalize_content(self.source).split("\n")
        typed_lines = typed_content.split("\n")

        diff_msg = []
        diff_msg.append("Content mismatch!")
        diff_msg.append(
            f"  Original: {len(original_lines)} lines, hash {self.source_hash[:16]}..."
        )
        diff_msg.append(
            f"  Typed:    {len(typed_lines)} lines, hash {typed_hash[:16]}..."
        )

        # Find first difference
        for i, (orig, typed) in enumerate(zip(original_lines, typed_lines)):
            if orig != typed:
                diff_msg.append(f"  First diff at line {i + 1}:")
                diff_msg.append(f"    Original: {repr(orig[:60])}")
                diff_msg.append(f"    Typed:    {repr(typed[:60])}")
                break

        if len(original_lines) != len(typed_lines):
            diff_msg.append(
                f"  Line count differs: {len(original_lines)} vs {len(typed_lines)}"
            )

        return False, "\n".join(diff_msg)

    def type_with_movements(self, engine, human) -> None:
        """Type the code with realistic cursor movements and dependency-aware order.

        Order (simulating how a real programmer writes code):
        1. Type class/function signatures in dependency order (dependencies first)
        2. Go back to top, add imports
        3. Go back to each 'pass', fill in actual body (in dependency order)
        4. Add module docstring at top

        Args:
            engine: TyperEngine instance
            human: HumanBehavior instance
        """
        display = engine.display

        # If no classes or functions, just type linearly
        if not self.structure.classes and not self.structure.functions:
            engine.type_content(self.source, "python")
            return

        # Get the typing order from CodeAnalyzer
        typing_order = self.analyzer.get_typing_order()

        # Collect body phases for Phase 3 and build class info map
        body_phases = []
        class_infos: dict[str, ClassInfo] = {}

        for name, phase, info in typing_order:
            if phase == "class_start":
                class_infos[name] = info
            elif phase == "body":
                body_phases.append((name, info))

        # =====================================================================
        # PHASE 1: Type all signatures in dependency order (append mode)
        # Process typing_order events in order to maintain source order
        # =====================================================================
        display.set_vim_mode("INSERT")
        display.set_insert_mode(False)  # Append mode for initial typing

        current_class = None
        first_method_in_class = True
        typed_classes = set()  # Track which classes we've started
        first_toplevel_typed = False  # Track if we've typed first class/function
        prev_item_end = 0  # Track end line of previous top-level item

        def _get_item_start(item) -> int:
            """Get the start line of an item (including decorators)."""
            start = item.location.start_line
            if hasattr(item, "decorators") and item.decorators:
                lines = self.source.split("\n")
                for i in range(start - 5, start):
                    if 0 <= i < len(lines) and lines[i].strip().startswith("@"):
                        return i + 1  # 1-indexed
            return start

        for _name, phase, info in typing_order:
            if phase == "class_start":
                # Class without methods - type it completely
                cls = info
                if not cls.methods:
                    # Type inter-item content (blank lines, comments)
                    if first_toplevel_typed:
                        item_start = _get_item_start(cls)
                        gap_lines = self._get_inter_item_lines(
                            prev_item_end, item_start
                        )
                        if gap_lines:
                            # Type as single unit for proper multi-line string highlighting
                            gap_content = "\n".join(gap_lines)
                            engine.type_content(gap_content, "python")
                            engine.display.newline()
                    if current_class:
                        current_class = None
                    first_toplevel_typed = True

                    # Type class decorators
                    for dec in cls.decorators:
                        self._type_line(engine, human, dec)

                    # Type class signature
                    self._type_line(engine, human, cls.signature)

                    # Type class body (attributes, docstring, etc.)
                    # Type as single unit for proper multi-line string highlighting
                    class_body = self._get_class_body(cls)
                    if class_body:
                        engine.type_content(class_body, "python")
                        engine.display.newline()

                    typed_classes.add(cls.name)
                    prev_item_end = cls.location.end_line

            elif phase == "signature":
                if info.is_method:
                    # Handle class wrapper
                    if info.parent_class != current_class:
                        # Get inter-item content before this class
                        if first_toplevel_typed:
                            cls = class_infos.get(info.parent_class)
                            if cls:
                                item_start = _get_item_start(cls)
                                gap_lines = self._get_inter_item_lines(
                                    prev_item_end, item_start
                                )
                                if gap_lines:
                                    # Type as single unit for proper multi-line string highlighting
                                    gap_content = "\n".join(gap_lines)
                                    engine.type_content(gap_content, "python")
                                    engine.display.newline()
                        if current_class:
                            pass  # Just switching classes
                        first_toplevel_typed = True

                        # Start new class (if not already typed)
                        if info.parent_class not in typed_classes:
                            cls = class_infos.get(info.parent_class)
                            if cls:
                                # Type class decorators
                                for dec in cls.decorators:
                                    self._type_line(engine, human, dec)

                                # Type class signature
                                self._type_line(engine, human, cls.signature)

                                # Type class preamble (attributes, class docstring)
                                # Type as single unit for proper multi-line string highlighting
                                preamble = self._get_class_preamble(cls)
                                if preamble:
                                    engine.type_content(preamble, "python")
                                    engine.display.newline()

                                typed_classes.add(info.parent_class)

                        current_class = info.parent_class
                        first_method_in_class = True

                    # Blank line before method (except first method in class)
                    if not first_method_in_class:
                        self._type_line(engine, human, "")
                    first_method_in_class = False

                    # Type decorators
                    for dec in info.decorators:
                        self._type_line(engine, human, dec)

                    # Type signature
                    self._type_line(engine, human, info.signature)

                    # Type the pass placeholder
                    pass_indent = " " * (info.indent + 4)
                    self._type_line(engine, human, pass_indent + "pass")
                else:
                    # Standalone function - type inter-item content first
                    if first_toplevel_typed:
                        item_start = _get_item_start(info)
                        gap_lines = self._get_inter_item_lines(
                            prev_item_end, item_start
                        )
                        if gap_lines:
                            # Type as single unit for proper multi-line string highlighting
                            gap_content = "\n".join(gap_lines)
                            engine.type_content(gap_content, "python")
                            engine.display.newline()
                    if current_class:
                        current_class = None
                    first_toplevel_typed = True

                    # Type decorators
                    for dec in info.decorators:
                        self._type_line(engine, human, dec)

                    # Type signature
                    self._type_line(engine, human, info.signature)

                    # Type the pass placeholder
                    pass_indent = " " * (info.indent + 4)
                    self._type_line(engine, human, pass_indent + "pass")

                    prev_item_end = info.location.end_line

            elif phase == "class_end":
                # Update prev_item_end for classes with methods
                cls = info
                if cls.methods:
                    prev_item_end = cls.location.end_line

        # =====================================================================
        # PHASE 2: Go back and add imports (cursor moves UP!)
        # =====================================================================
        if self.structure.imports:
            # Thinking pause - "Oh, I need to import things..."
            display.sleep_with_clock(human._scaled_uniform(0.5, 1.2))
            display.set_vim_mode("NORMAL")
            display.sleep_with_clock(human._scaled_uniform(0.2, 0.5))

            # GO TO LINE 1 - cursor visibly moves up!
            display.goto_line(1, col=0)
            display.sleep_with_clock(human._scaled_uniform(0.2, 0.4))

            # Insert a blank line above (like pressing O in vim)
            display.open_line_above()

            display.set_vim_mode("INSERT")
            display.set_insert_mode(True)  # Insert mode for mid-document typing

            # Type imports section from source (preserving blank lines between groups)
            import_section = self._get_imports_section()
            import_lines = import_section.split("\n")
            for line in import_lines:
                self._type_line(engine, human, line)

            # Type module-level gap content (between imports and first class/function)
            # This includes things like logger assignments, comment blocks, etc.
            # Type as single unit for proper multi-line string highlighting
            gap_content = self._get_module_gap_content()
            if gap_content:
                engine.type_content(gap_content, "python")
                engine.display.newline()
            display.set_insert_mode(False)

        # =====================================================================
        # PHASE 3: Go back and fill in function bodies (in dependency order!)
        # =====================================================================
        if body_phases:
            # Thinking pause - "Now let me implement these functions..."
            display.sleep_with_clock(human._scaled_uniform(0.8, 1.5))
            display.set_vim_mode("NORMAL")
            display.sleep_with_clock(human._scaled_uniform(0.3, 0.6))

            for _name, info in body_phases:
                # Skip if body is just 'pass' or empty
                if not info.body or info.body.strip() in ("pass", ""):
                    continue

                # Find the pass line (1-indexed)
                pass_line = self._find_pass_in_display(
                    display, info.signature_first_line
                )

                if pass_line < 0:
                    # Couldn't find pass line - skip this method
                    continue

                # GO TO THE PASS LINE - cursor visibly moves!
                display.goto_line(pass_line, col=0)
                display.sleep_with_clock(human._scaled_uniform(0.2, 0.5))

                # Delete the pass line (content shifts up)
                display.delete_line_at(pass_line)

                # Insert ONE blank line where pass was
                # The content that was below is now at pass_line, so insert pushes it down
                display.insert_line_at(pass_line, "")

                # Go to the blank line we just inserted
                display.goto_line(pass_line, col=0)

                display.set_vim_mode("INSERT")
                display.set_insert_mode(True)  # Newlines will insert new lines

                # Type docstring first if it exists
                if info.docstring:
                    self._type_body_content(engine, human, info.docstring)
                    engine.display.newline()  # Newline after docstring

                # Type the body - newlines automatically insert lines as needed
                self._type_body_content(engine, human, info.body)

                display.set_insert_mode(False)
                display.set_vim_mode("NORMAL")
                display.sleep_with_clock(human._scaled_uniform(0.1, 0.3))

        # =====================================================================
        # PHASE 4: Add module docstring at top
        # =====================================================================
        if self.structure.module_docstring:
            display.sleep_with_clock(human._scaled_uniform(0.5, 1.0))
            display.set_vim_mode("NORMAL")
            display.sleep_with_clock(human._scaled_uniform(0.2, 0.4))

            # Go to line 1
            display.goto_line(1, col=0)
            display.sleep_with_clock(human._scaled_uniform(0.2, 0.4))

            display.open_line_above()
            display.set_vim_mode("INSERT")
            display.set_insert_mode(True)

            # Type docstring as a single unit for proper multi-line highlighting
            self._type_multiline(engine, human, self.structure.module_docstring)

            # Note: Don't add explicit blank line after docstring
            # The insert_mode newline already creates proper spacing

            display.set_insert_mode(False)

        # =====================================================================
        # FINAL PASS: Verify and correct any mismatches
        # =====================================================================
        self._final_correction_pass(engine, display)

        # Reset scroll to top so user can see the full file
        display.goto_line(1, col=0)
        display.set_vim_mode("INSERT")

    def _final_correction_pass(self, engine, display) -> None:
        """Final pass to ensure typed content matches original exactly.

        This compares the display content with the original source and
        corrects any mismatches by directly setting line contents.
        Also re-applies syntax highlighting to the entire content to fix
        multi-line constructs (docstrings, etc.) that weren't highlighted
        correctly when typed line-by-line.
        """
        original_lines = normalize_content(self.source).split("\n")
        typed_lines = display.get_content_lines()

        # Normalize typed lines (strip trailing whitespace)
        typed_lines = [line.rstrip() for line in typed_lines]
        # Remove trailing empty lines from typed
        while typed_lines and not typed_lines[-1]:
            typed_lines.pop()

        # Check if we need corrections
        needs_correction = False
        if len(original_lines) != len(typed_lines):
            needs_correction = True
        else:
            for _i, (orig, typed) in enumerate(zip(original_lines, typed_lines)):
                if orig != typed:
                    needs_correction = True
                    break

        if needs_correction:
            # Direct correction: replace display content with original
            # This ensures perfect match regardless of typing phase quirks
            display.set_content_lines(original_lines.copy())
            # Reset cursor position
            if hasattr(display, "goto_line"):
                display.goto_line(1, col=0)

        # Always re-apply syntax highlighting to fix multi-line constructs
        # (docstrings, multi-line strings) that were typed line-by-line
        self._apply_full_syntax_highlighting(engine, display)

    def _apply_full_syntax_highlighting(self, engine, display) -> None:
        """Re-apply syntax highlighting to the entire content.

        This tokenizes the full source as a single unit, which correctly
        identifies multi-line constructs like docstrings and strings.
        Then it rebuilds line colors with the correct color attributes.
        """
        # Get content lines from display using proper API
        content_lines = display.get_content_lines()

        # Get the highlighter from the engine (may be None for mocks)
        highlighter = getattr(engine, "_highlighter", None)
        if not highlighter:
            # No highlighting - just clear colors
            display.set_line_colors([[] for _ in content_lines])
            return

        # Get full content from display
        full_content = "\n".join(content_lines)

        # Tokenize the FULL content - this properly handles multi-line strings
        tokens = list(highlighter.tokenize(full_content))

        # Build position -> token_type map
        token_map: dict[int, Any] = {}
        pos = 0
        for token in tokens:
            for i in range(len(token.text)):
                token_map[pos + i] = token.token_type
            pos += len(token.text)

        # Rebuild line colors based on token map
        # Need _get_color_attr method from display (real display has it, mocks may not)
        get_color_attr = getattr(display, "_get_color_attr", None)
        if not get_color_attr:
            # Mock or display without color support - skip color rebuild
            return

        new_colors = []
        char_pos = 0
        for line in content_lines:
            line_colors = []
            for _char in line:
                token_type = token_map.get(char_pos)
                attr = get_color_attr(token_type, False)
                line_colors.append(attr)
                char_pos += 1
            char_pos += 1  # Account for newline character
            new_colors.append(line_colors)

        display.set_line_colors(new_colors)

        # Redraw the content with correct colors
        if hasattr(display, "_redraw_all_content"):
            display._redraw_all_content()
            # Force a FULL screen refresh - not just noutrefresh
            if hasattr(display, "_pad") and hasattr(display, "_stdscr"):
                try:
                    # Mark everything as needing update
                    display._pad.touchwin()
                    # Get visible area
                    visible_rows = (
                        display._get_visible_rows()
                        if hasattr(display, "_get_visible_rows")
                        else display._max_y - 3
                    )
                    scroll_offset = getattr(display, "_scroll_offset", 0)
                    # Refresh pad to screen
                    display._pad.refresh(
                        scroll_offset, 0, 0, 0, visible_rows, display._max_x - 1
                    )
                    # Also refresh stdscr for status line
                    display._draw_statusline()
                    display._stdscr.refresh()
                except Exception:
                    pass

    def _find_pass_in_display(self, display, signature_search: str) -> int:
        """Find the line number (1-indexed) of a 'pass' after a method signature.

        Searches the display's line contents for the signature and finds
        the pass placeholder after it.

        Args:
            display: The display with _line_contents
            signature_search: Part of the method signature to search for

        Returns:
            1-indexed line number of the pass line, or -1 if not found
        """
        lines = display._line_contents
        sig_stripped = signature_search.strip()

        for i, line in enumerate(lines):
            # Find the signature line
            if sig_stripped in line:
                # Look for pass/placeholder in the next few lines
                for j in range(i + 1, min(i + 10, len(lines))):
                    stripped = lines[j].strip()
                    if stripped in ("pass", "raise NotImplementedError()", "..."):
                        return j + 1  # 1-indexed
                    # Stop if we hit another definition
                    if stripped.startswith(("def ", "class ", "async def ")):
                        break
                    # Stop if we hit a decorator (might be for next method)
                    if stripped.startswith("@"):
                        break
        return -1

    def _get_class_body(self, cls: ClassInfo) -> str:
        """Get the body of a class (for classes without methods).

        This extracts everything between the class signature and the end,
        including docstrings, attributes, etc.
        """
        lines = self.source.split("\n")
        start_line = cls.location.start_line  # 1-indexed
        end_line = cls.location.end_line  # 1-indexed

        # Find where the class signature ends (the line with ':')
        sig_end = start_line
        for i in range(start_line - 1, min(start_line + 5, len(lines))):
            if ":" in lines[i]:
                sig_end = i + 1
                break

        # Get body lines (everything after signature to end)
        if sig_end < end_line:
            body_lines = lines[sig_end:end_line]
            return "\n".join(body_lines)
        return ""

    def _get_leading_blank_lines(self, line_num: int) -> int:
        """Count the number of blank lines immediately before a line.

        This preserves the original file's blank line structure (e.g., PEP 8
        uses 2 blank lines between top-level definitions).
        """
        lines = self.source.split("\n")
        count = 0
        for i in range(line_num - 2, -1, -1):  # line_num is 1-indexed
            if not lines[i].strip():
                count += 1
            else:
                break
        return count

    def _get_inter_item_lines(self, prev_end: int, current_start: int) -> list:
        """Get content lines between the end of one item and the start of another.

        This captures blank lines, comment blocks, and any other content
        between top-level definitions.

        Args:
            prev_end: 1-indexed end line of previous item
            current_start: 1-indexed start line of current item

        Returns:
            List of lines to type (may be empty list)
        """
        if prev_end >= current_start - 1:
            return []

        lines = self.source.split("\n")
        # Get lines from prev_end to current_start - 1 (exclusive)
        return lines[prev_end : current_start - 1]

    def _get_imports_section(self) -> str:
        """Get the full imports section from source, preserving blank lines.

        Instead of typing imports individually, this extracts the entire
        import section (from first to last import) including any blank
        lines between import groups (stdlib, third-party, local).
        """
        if not self.structure.imports:
            return ""

        lines = self.source.split("\n")

        # Find first and last import lines
        first_import = min(imp.location.start_line for imp in self.structure.imports)
        last_import = max(imp.location.end_line for imp in self.structure.imports)

        # Extract the section (convert to 0-indexed)
        import_lines = lines[first_import - 1 : last_import]
        return "\n".join(import_lines)

    def _get_module_gap_content(self) -> str:
        """Get module-level content between imports and first class/function.

        This captures content like:
        - Module-level variable assignments (logger = ...)
        - Comment blocks
        - Blank lines that are part of the module structure
        """
        lines = self.source.split("\n")

        # Find the end of the last import
        last_import_end = 0
        for imp in self.structure.imports:
            last_import_end = max(last_import_end, imp.location.end_line)

        # Find the start of the first class or function
        first_def_start = len(lines) + 1
        for cls in self.structure.classes:
            # Account for decorators
            start = cls.location.start_line
            if cls.decorators:
                # Find decorator line
                for i in range(start - 5, start):
                    if 0 <= i < len(lines) and lines[i].strip().startswith("@"):
                        start = i + 1  # 1-indexed
                        break
            first_def_start = min(first_def_start, start)

        for func in self.structure.functions:
            start = func.location.start_line
            if func.decorators:
                for i in range(start - 5, start):
                    if 0 <= i < len(lines) and lines[i].strip().startswith("@"):
                        start = i + 1
                        break
            first_def_start = min(first_def_start, start)

        # Get the gap content (preserve all content including blank lines)
        if last_import_end < first_def_start - 1:
            gap_lines = lines[last_import_end : first_def_start - 1]
            return "\n".join(gap_lines)
        return ""

    def _get_class_preamble(self, cls: ClassInfo) -> str:
        """Get class content before the first method (attributes, class docstring).

        For classes with methods, this extracts everything between the class
        signature and the first method/decorator. This includes:
        - Class docstring
        - Class-level attributes (like `host: str` in Pydantic models)
        - Class variables
        """
        if not cls.methods:
            return ""

        lines = self.source.split("\n")
        start_line = cls.location.start_line  # 1-indexed

        # Find where the class signature ends (the line with ':')
        sig_end = start_line
        for i in range(start_line - 1, min(start_line + 5, len(lines))):
            if ":" in lines[i]:
                sig_end = i + 1
                break

        # Find where the first method starts (including its decorators)
        first_method = cls.methods[0]
        first_method_line = first_method.location.start_line

        # Check for decorators - they come before the method
        if first_method.decorators:
            # Find the decorator line in the source
            for i in range(sig_end, first_method_line):
                line = lines[i].strip()
                if line.startswith("@"):
                    first_method_line = i + 1  # 1-indexed
                    break

        # Get preamble lines (between signature and first method/decorator)
        if sig_end < first_method_line:
            preamble_lines = lines[sig_end : first_method_line - 1]
            return "\n".join(preamble_lines)
        return ""

    def _type_line(self, engine, human, content: str) -> None:
        """Type a line of content followed by newline."""
        if content:
            engine.type_content(content, "python")
        engine.display.newline()

    def _type_body_content(self, engine, human, content: str) -> None:
        """Type body content with proper handling for mid-document insertion.

        The body is typed character by character. Newlines in the content
        will trigger line insertion (when insert_mode is True), which
        automatically handles multi-line bodies.
        """
        if not content:
            return

        # Type entire content - the engine handles newlines correctly
        # When insert_mode=True, newlines insert new lines in the document
        engine.type_content(content, "python")

    def _type_multiline(self, engine, human, content: str) -> None:
        """Type multi-line content as a single tokenized unit.

        This ensures proper syntax highlighting for multi-line strings,
        docstrings, and other constructs that span multiple lines.
        """
        if not content:
            return

        # Type the entire content as one unit - this allows proper tokenization
        # of multi-line strings. The newlines within content are handled by
        # type_content which calls display.newline() for each '\n'.
        engine.type_content(content, "python")
        # Add final newline to move to next line
        engine.display.newline()
