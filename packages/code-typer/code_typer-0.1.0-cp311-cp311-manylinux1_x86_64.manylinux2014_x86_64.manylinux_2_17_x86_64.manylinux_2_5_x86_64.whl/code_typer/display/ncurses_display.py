"""ncurses-based terminal display for code-typer.

This module provides a line-based text buffer with support for:
- Sequential typing (append mode)
- Mid-document editing (insert mode)
- Cursor movement
- Line insertion/deletion
"""

import curses
import time
from datetime import datetime
from typing import Optional

from code_typer.syntax.highlighter import TokenType


class NcursesDisplay:
    """Terminal display using ncurses for rendering typed code.

    The display maintains a line-based buffer (_line_contents) that is the
    source of truth for all content. All operations update this buffer and
    then redraw as needed.
    """

    # Color pair IDs
    COLOR_DEFAULT = 0
    COLOR_KEYWORD = 1
    COLOR_STRING = 2
    COLOR_COMMENT = 3
    COLOR_NUMBER = 4
    COLOR_FUNCTION = 5
    COLOR_CLASS = 6
    COLOR_OPERATOR = 7
    COLOR_DECORATOR = 8
    COLOR_ERROR = 9
    COLOR_HEADER = 10
    COLOR_LINE_NUMBER = 11
    COLOR_BUILTIN = 12
    COLOR_STATUSLINE = 13
    COLOR_MODE = 14

    def __init__(self):
        """Initialize the display (but don't start curses yet)."""
        self._stdscr = None
        self._pad = None
        self._current_row = 0
        self._current_col = 0
        self._line_number_width = 4
        self._content_start_col = 6  # Line number + separator
        self._scroll_offset = 0
        self._max_content_rows = 10000  # Pad height for scrolling
        self._colors_initialized = False
        self._show_line_numbers = True
        self._current_line_number = 1
        self._header_rows = 2  # Rows reserved for header

        # Line content buffer - source of truth
        self._line_contents: list[str] = [""]
        # Color attributes per line (list of (char, attr) tuples for each line)
        self._line_colors: list[list[int]] = [[]]
        self._line_start_row = 0  # First row after header

        # Vim-like status line
        self._statusline_enabled = True
        self._statusline_rows = 2
        self._vim_mode = "INSERT"
        self._filename = ""
        self._total_chars = 0
        self._chars_typed = 0
        self._last_clock_update = 0.0  # Track last clock update time
        self._last_clock_second = -1  # Track last displayed second

        # Dedicated window for clock updates
        self._clock_win = None

        # Insert mode flag - when True, newlines insert new lines
        self._insert_mode = False

        # Free scroll mode - when True, scroll is independent of cursor position
        # Used during review mode and manual scrolling
        self._free_scroll_mode = False

    def __enter__(self):
        """Start curses mode."""
        self._stdscr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        curses.curs_set(1)
        self._stdscr.keypad(True)

        if curses.has_colors():
            curses.start_color()
            curses.use_default_colors()
            self._init_colors()
            self._colors_initialized = True

        self._max_y, self._max_x = self._stdscr.getmaxyx()
        self._pad = curses.newpad(self._max_content_rows, max(self._max_x, 500))

        self._stdscr.clear()
        self._stdscr.refresh()

        if self._show_line_numbers:
            self._draw_line_number()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Restore terminal state."""
        if self._stdscr:
            self._stdscr.keypad(False)
            curses.nocbreak()
            curses.echo()
            curses.endwin()
        return False

    def _init_colors(self):
        """Initialize color pairs for syntax highlighting."""
        try:
            curses.init_pair(self.COLOR_KEYWORD, curses.COLOR_BLUE, -1)
            curses.init_pair(self.COLOR_STRING, curses.COLOR_GREEN, -1)
            curses.init_pair(self.COLOR_COMMENT, curses.COLOR_CYAN, -1)
            curses.init_pair(self.COLOR_NUMBER, curses.COLOR_MAGENTA, -1)
            curses.init_pair(self.COLOR_FUNCTION, curses.COLOR_YELLOW, -1)
            curses.init_pair(self.COLOR_CLASS, curses.COLOR_YELLOW, -1)
            curses.init_pair(self.COLOR_OPERATOR, curses.COLOR_WHITE, -1)
            curses.init_pair(self.COLOR_DECORATOR, curses.COLOR_CYAN, -1)
            curses.init_pair(self.COLOR_ERROR, curses.COLOR_RED, -1)
            curses.init_pair(self.COLOR_HEADER, curses.COLOR_WHITE, curses.COLOR_BLUE)
            curses.init_pair(self.COLOR_LINE_NUMBER, curses.COLOR_YELLOW, -1)
            curses.init_pair(self.COLOR_BUILTIN, curses.COLOR_CYAN, -1)
            curses.init_pair(
                self.COLOR_STATUSLINE, curses.COLOR_WHITE, curses.COLOR_BLACK
            )
            curses.init_pair(self.COLOR_MODE, curses.COLOR_BLACK, curses.COLOR_WHITE)
        except curses.error:
            self._colors_initialized = False

    def _update_clock_display(self, force_refresh: bool = False) -> None:
        """Update just the clock text - called frequently, must be fast and safe.

        Args:
            force_refresh: If True, refresh screen immediately (use during sleeps)
        """
        if not self._stdscr:
            return
        try:
            now = datetime.now()
            current_second = now.second

            # Only update if second changed
            if current_second == self._last_clock_second:
                return

            self._last_clock_second = current_second
            current_time = now.strftime("%H:%M:%S")

            # Write clock directly to stdscr at the right position
            status_row = self._max_y - 2
            clock_part = f"{current_time} "
            clock_pos = self._max_x - len(clock_part) - 1

            if clock_pos > 0 and status_row > 0:
                clock_attr = (
                    curses.color_pair(self.COLOR_STATUSLINE)
                    | curses.A_REVERSE
                    | curses.A_BOLD
                )
                # Save cursor, write clock, restore cursor
                saved_y, saved_x = self._stdscr.getyx()
                self._stdscr.addstr(status_row, clock_pos, clock_part, clock_attr)
                self._stdscr.move(saved_y, saved_x)

                if force_refresh:
                    # Mark both pad and stdscr for update
                    visible_rows = self._get_visible_rows()
                    self._pad.noutrefresh(
                        self._scroll_offset, 0, 0, 0, visible_rows, self._max_x - 1
                    )
                    self._stdscr.noutrefresh()
                    curses.doupdate()
        except curses.error:
            pass

    def _handle_resize(self) -> None:
        """Handle terminal resize event."""
        try:
            # Get new dimensions
            new_max_y, new_max_x = self._stdscr.getmaxyx()

            # Only act if dimensions actually changed
            if new_max_y == self._max_y and new_max_x == self._max_x:
                return

            self._max_y = new_max_y
            self._max_x = new_max_x

            # Recreate pad with new width if needed
            if new_max_x > self._pad.getmaxyx()[1]:
                self._pad = curses.newpad(self._max_content_rows, max(new_max_x, 500))

            # Clear and redraw everything
            self._stdscr.clear()
            self._stdscr.refresh()
            self._redraw_all_content()
            self._refresh_display()
            self._update_cursor()
        except curses.error:
            pass

    def _get_color_attr(
        self, token_type: Optional[TokenType], error: bool = False
    ) -> int:
        """Get curses attribute for a token type."""
        if not self._colors_initialized:
            return curses.A_NORMAL

        if error:
            return curses.color_pair(self.COLOR_ERROR) | curses.A_BOLD

        if token_type is None:
            return curses.A_NORMAL

        color_map = {
            TokenType.KEYWORD: self.COLOR_KEYWORD,
            TokenType.STRING: self.COLOR_STRING,
            TokenType.COMMENT: self.COLOR_COMMENT,
            TokenType.NUMBER: self.COLOR_NUMBER,
            TokenType.FUNCTION: self.COLOR_FUNCTION,
            TokenType.CLASS: self.COLOR_CLASS,
            TokenType.OPERATOR: self.COLOR_OPERATOR,
            TokenType.DECORATOR: self.COLOR_DECORATOR,
            TokenType.BUILTIN: self.COLOR_BUILTIN,
        }

        color_id = color_map.get(token_type, self.COLOR_DEFAULT)
        attr = curses.color_pair(color_id)

        if token_type in (TokenType.KEYWORD, TokenType.CLASS):
            attr |= curses.A_BOLD

        return attr

    def _get_current_line_idx(self) -> int:
        """Get the index into _line_contents for current cursor position."""
        return self._current_row - self._line_start_row

    def _draw_line_number(self, line_idx: Optional[int] = None):
        """Draw a line number."""
        if not self._show_line_numbers:
            return

        if line_idx is None:
            line_idx = self._get_current_line_idx()

        row = self._line_start_row + line_idx
        line_num = line_idx + 1
        line_str = f"{line_num:>{self._line_number_width}} "

        try:
            attr = (
                curses.color_pair(self.COLOR_LINE_NUMBER)
                if self._colors_initialized
                else curses.A_DIM
            )
            self._pad.addstr(row, 0, line_str, attr)
        except curses.error:
            pass

    def _draw_statusline(self):
        """Draw vim-like status line at the bottom of the screen."""
        if not self._statusline_enabled:
            return

        try:
            status_row = self._max_y - 2
            cmd_row = self._max_y - 1

            # Clear status rows
            self._stdscr.move(status_row, 0)
            self._stdscr.clrtoeol()
            self._stdscr.move(cmd_row, 0)
            self._stdscr.clrtoeol()

            status_attr = curses.color_pair(self.COLOR_STATUSLINE) | curses.A_REVERSE
            mode_attr = curses.color_pair(self.COLOR_MODE) | curses.A_BOLD

            filename = self._filename if self._filename else "[No Name]"
            if len(filename) > 40:
                filename = "..." + filename[-37:]

            total_lines = len(self._line_contents)
            if total_lines > 0:
                percent = int((self._current_line_number / total_lines) * 100)
                if self._current_line_number == 1:
                    pos_str = "Top"
                elif self._current_line_number >= total_lines:
                    pos_str = "Bot"
                else:
                    pos_str = f"{percent}%"
            else:
                pos_str = "Top"

            line_col = f"{self._current_line_number},{self._current_col + 1}"
            char_count = (
                f"{self._chars_typed}/{self._total_chars}"
                if self._total_chars > 0
                else ""
            )
            current_time = datetime.now().strftime("%H:%M:%S")

            # Build status line with clock at the far right
            clock_part = f"{current_time} "
            right_info = f" {char_count}  {line_col:>10}  {pos_str:>4}  "
            left_part = f" {filename} "

            middle_width = (
                self._max_x - len(left_part) - len(right_info) - len(clock_part)
            )
            if middle_width < 0:
                middle_width = 0
            middle = " " * middle_width

            # Draw status line
            status_line = left_part + middle + right_info
            status_line = status_line[: self._max_x - len(clock_part) - 1]

            self._stdscr.addstr(status_row, 0, status_line, status_attr)

            # Draw clock at far right with bold
            clock_attr = status_attr | curses.A_BOLD
            clock_pos = self._max_x - len(clock_part) - 1
            if clock_pos > 0:
                self._stdscr.addstr(status_row, clock_pos, clock_part, clock_attr)

            mode_text = f"-- {self._vim_mode} --"
            self._stdscr.addstr(cmd_row, 0, mode_text, mode_attr)

            self._stdscr.noutrefresh()
        except curses.error:
            pass

    def update_clock(self) -> None:
        """Update the clock display if the second has changed."""
        self._update_clock_display()

    def sleep_with_clock(self, duration: float) -> None:
        """Sleep for duration while keeping clock updated."""
        remaining = duration
        while remaining > 0:
            chunk = min(remaining, 0.1)  # 100ms chunks
            time.sleep(chunk)
            remaining -= chunk
            self._update_clock_display(force_refresh=True)

    def _get_visible_rows(self) -> int:
        """Get the number of visible content rows (excluding status line)."""
        status_reserved = self._statusline_rows if self._statusline_enabled else 0
        return max(1, self._max_y - 1 - status_reserved)

    def _refresh_display(self):
        """Refresh the pad display with proper scrolling."""
        # Check if terminal was resized
        try:
            new_max_y, new_max_x = self._stdscr.getmaxyx()
            if new_max_y != self._max_y or new_max_x != self._max_x:
                self._handle_resize()
                return
        except curses.error:
            pass

        visible_rows = self._get_visible_rows()

        # Calculate max scroll based on actual content
        total_content_rows = self._line_start_row + len(self._line_contents)
        max_scroll = max(0, total_content_rows - visible_rows)

        # Only auto-adjust scroll to keep cursor visible when NOT in free scroll mode
        # Free scroll mode allows user to scroll anywhere, independent of cursor
        if not self._free_scroll_mode:
            if self._current_row >= self._scroll_offset + visible_rows:
                self._scroll_offset = self._current_row - visible_rows + 1

            if self._current_row < self._scroll_offset:
                self._scroll_offset = self._current_row

        # Clamp scroll offset to valid range
        self._scroll_offset = max(0, min(self._scroll_offset, max_scroll))

        try:
            self._pad.noutrefresh(
                self._scroll_offset, 0, 0, 0, visible_rows, self._max_x - 1
            )
        except curses.error:
            pass

        self._draw_statusline()
        curses.doupdate()

    def _update_cursor(self):
        """Update physical cursor position."""
        col = (
            self._content_start_col + self._current_col
            if self._show_line_numbers
            else self._current_col
        )
        cursor_row = self._current_row - self._scroll_offset
        visible_rows = self._get_visible_rows()

        try:
            if 0 <= cursor_row <= visible_rows:
                self._stdscr.move(cursor_row, min(col, self._max_x - 1))
                self._stdscr.refresh()
        except curses.error:
            pass

    def _redraw_all_content(self):
        """Redraw all content from _line_contents with stored colors."""
        try:
            # Clear content area
            for row in range(self._line_start_row, self._max_content_rows):
                self._pad.move(row, 0)
                self._pad.clrtoeol()

            # Redraw each line
            for i, content in enumerate(self._line_contents):
                row = self._line_start_row + i

                # Draw line number
                if self._show_line_numbers:
                    line_num = i + 1
                    line_str = f"{line_num:>{self._line_number_width}} "
                    attr = (
                        curses.color_pair(self.COLOR_LINE_NUMBER)
                        if self._colors_initialized
                        else curses.A_DIM
                    )
                    self._pad.addstr(row, 0, line_str, attr)

                # Get colors for this line (or empty list if none)
                colors = self._line_colors[i] if i < len(self._line_colors) else []

                # Draw content with stored colors
                col = self._content_start_col if self._show_line_numbers else 0
                char_idx = 0
                for char in content:
                    if char == "\t":
                        tab_width = 4 - ((col - self._content_start_col) % 4)
                        # Use stored attr if available
                        char_attr = (
                            colors[char_idx]
                            if char_idx < len(colors)
                            else curses.A_NORMAL
                        )
                        for _ in range(tab_width):
                            self._pad.addch(row, col, " ", char_attr)
                            col += 1
                        char_idx += 1
                    else:
                        # Use stored attr if available
                        char_attr = (
                            colors[char_idx]
                            if char_idx < len(colors)
                            else curses.A_NORMAL
                        )
                        self._pad.addch(row, col, char, char_attr)
                        col += 1
                        char_idx += 1

        except curses.error:
            pass

    # =========================================================================
    # PUBLIC API - Content Operations
    # =========================================================================

    def type_char(
        self, char: str, token_type: Optional[TokenType] = None, error: bool = False
    ) -> None:
        """Type a single character at current cursor position."""
        if char == "\n":
            self.newline()
            return

        if char == "\t":
            self.type_tab(token_type=token_type)
            return

        attr = self._get_color_attr(token_type, error)
        col = (
            self._content_start_col + self._current_col
            if self._show_line_numbers
            else self._current_col
        )

        try:
            self._pad.addch(self._current_row, col, char, attr)
            self._current_col += 1
            self._chars_typed += 1

            # Update line contents and colors
            line_idx = self._get_current_line_idx()
            while len(self._line_contents) <= line_idx:
                self._line_contents.append("")
                self._line_colors.append([])
            self._line_contents[line_idx] += char
            self._line_colors[line_idx].append(attr)

            self._refresh_display()
            self._update_cursor()
        except curses.error:
            pass

    def type_tab(self, token_type: Optional[TokenType] = None) -> None:
        """Type a tab character."""
        tab_width = 4 - (self._current_col % 4)
        col = (
            self._content_start_col + self._current_col
            if self._show_line_numbers
            else self._current_col
        )
        attr = self._get_color_attr(token_type, False)

        try:
            for _ in range(tab_width):
                self._pad.addch(self._current_row, col, " ", attr)
                col += 1
            self._current_col += tab_width
            self._chars_typed += 1

            line_idx = self._get_current_line_idx()
            while len(self._line_contents) <= line_idx:
                self._line_contents.append("")
                self._line_colors.append([])
            self._line_contents[line_idx] += "\t"
            self._line_colors[line_idx].append(attr)  # Store tab's color

            self._refresh_display()
            self._update_cursor()
        except curses.error:
            pass

    def backspace(self) -> None:
        """Delete the character before cursor."""
        if self._current_col > 0:
            self._current_col -= 1
            col = (
                self._content_start_col + self._current_col
                if self._show_line_numbers
                else self._current_col
            )

            try:
                self._pad.addch(self._current_row, col, " ")

                line_idx = self._get_current_line_idx()
                if (
                    line_idx < len(self._line_contents)
                    and self._line_contents[line_idx]
                ):
                    self._line_contents[line_idx] = self._line_contents[line_idx][:-1]
                    # Also remove color
                    if (
                        line_idx < len(self._line_colors)
                        and self._line_colors[line_idx]
                    ):
                        self._line_colors[line_idx].pop()

                self._refresh_display()
                self._update_cursor()
            except curses.error:
                pass

    def newline(self) -> None:
        """Move to next line. In insert mode, inserts a new line first."""
        self._chars_typed += 1
        line_idx = self._get_current_line_idx()

        # In insert mode with content below, INSERT a new line
        if self._insert_mode and line_idx + 1 < len(self._line_contents):
            self._line_contents.insert(line_idx + 1, "")
            self._line_colors.insert(line_idx + 1, [])
            self._redraw_all_content()

        self._current_row += 1
        self._current_col = 0
        self._current_line_number += 1

        # Ensure line exists in buffer
        new_line_idx = self._get_current_line_idx()
        while len(self._line_contents) <= new_line_idx:
            self._line_contents.append("")
            self._line_colors.append([])

        if self._show_line_numbers:
            self._draw_line_number(new_line_idx)

        self._refresh_display()
        self._update_cursor()

    def delete_word(self) -> None:
        """Delete the last word (like Ctrl+Backspace)."""
        line_idx = self._get_current_line_idx()
        if line_idx >= len(self._line_contents):
            return

        content = self._line_contents[line_idx]
        if not content:
            return

        end = len(content)
        while end > 0 and content[end - 1] == " ":
            end -= 1

        start = end
        while start > 0 and content[start - 1] not in " \t":
            start -= 1

        chars_to_delete = len(content) - start
        for _ in range(chars_to_delete):
            self.backspace()

    def delete_line(self) -> None:
        """Clear the current line content (not remove the line)."""
        line_idx = self._get_current_line_idx()
        if line_idx >= len(self._line_contents):
            return

        col_start = self._content_start_col if self._show_line_numbers else 0
        try:
            for col in range(col_start, col_start + self._current_col + 1):
                self._pad.addch(self._current_row, col, " ")
        except curses.error:
            pass

        self._current_col = 0
        self._line_contents[line_idx] = ""

        self._refresh_display()
        self._update_cursor()

    # =========================================================================
    # PUBLIC API - Cursor Movement
    # =========================================================================

    def move_up(self) -> None:
        """Move cursor up one line."""
        if self._current_row > self._line_start_row:
            self._current_row -= 1
            self._current_line_number -= 1

            line_idx = self._get_current_line_idx()
            if line_idx < len(self._line_contents):
                max_col = len(self._line_contents[line_idx])
                self._current_col = min(self._current_col, max_col)

            self._refresh_display()
            self._update_cursor()

    def move_down(self) -> None:
        """Move cursor down one line."""
        line_idx = self._get_current_line_idx()
        if line_idx < len(self._line_contents) - 1:
            self._current_row += 1
            self._current_line_number += 1

            new_line_idx = self._get_current_line_idx()
            if new_line_idx < len(self._line_contents):
                max_col = len(self._line_contents[new_line_idx])
                self._current_col = min(self._current_col, max_col)

            self._refresh_display()
            self._update_cursor()

    def move_home(self) -> None:
        """Move cursor to start of line."""
        self._current_col = 0
        self._update_cursor()

    def move_end(self) -> None:
        """Move cursor to end of line."""
        line_idx = self._get_current_line_idx()
        if line_idx < len(self._line_contents):
            self._current_col = len(self._line_contents[line_idx])
        self._update_cursor()

    def goto_line(self, line_num: int, col: int = 0) -> None:
        """Move cursor to a specific line (1-indexed)."""
        # Clamp to valid range
        max_line = len(self._line_contents)
        line_num = max(1, min(line_num, max_line))

        target_row = self._line_start_row + line_num - 1
        self._current_row = target_row
        self._current_line_number = line_num

        line_idx = line_num - 1
        if 0 <= line_idx < len(self._line_contents):
            max_col = len(self._line_contents[line_idx])
            self._current_col = min(col, max_col)
        else:
            self._current_col = 0

        self._refresh_display()
        self._update_cursor()

    # =========================================================================
    # PUBLIC API - Structural Line Operations
    # =========================================================================

    def insert_line_at(self, line_num: int, content: str = "") -> None:
        """Insert a new line at position, shifting content down.

        Args:
            line_num: Line number to insert at (1-indexed)
            content: Initial content for the line
        """
        line_idx = line_num - 1
        line_idx = max(0, min(line_idx, len(self._line_contents)))

        self._line_contents.insert(line_idx, content)
        self._line_colors.insert(line_idx, [])  # Empty colors for new line
        self._redraw_all_content()

        # Adjust cursor if it was at or below insertion point
        cursor_line_idx = self._get_current_line_idx()
        if cursor_line_idx >= line_idx:
            self._current_row += 1
            self._current_line_number += 1

        self._refresh_display()
        self._update_cursor()

    def delete_line_at(self, line_num: int) -> None:
        """Delete a line at position, shifting content up.

        Args:
            line_num: Line number to delete (1-indexed)
        """
        line_idx = line_num - 1

        if line_idx < 0 or line_idx >= len(self._line_contents):
            return

        # Don't delete if it's the only line
        if len(self._line_contents) <= 1:
            self._line_contents[0] = ""
            if self._line_colors:
                self._line_colors[0] = []
            self._redraw_all_content()
            self._refresh_display()
            return

        self._line_contents.pop(line_idx)
        if line_idx < len(self._line_colors):
            self._line_colors.pop(line_idx)
        self._redraw_all_content()

        # Adjust cursor if it was below deletion point
        cursor_line_idx = self._get_current_line_idx()
        if cursor_line_idx > line_idx:
            self._current_row -= 1
            self._current_line_number -= 1
        elif cursor_line_idx == line_idx and cursor_line_idx >= len(
            self._line_contents
        ):
            # Cursor was on deleted line and it was the last line
            self._current_row = self._line_start_row + len(self._line_contents) - 1
            self._current_line_number = len(self._line_contents)

        self._refresh_display()
        self._update_cursor()

    def clear_current_line(self) -> None:
        """Clear content of current line (keeps the line, clears content)."""
        line_idx = self._get_current_line_idx()

        if 0 <= line_idx < len(self._line_contents):
            self._line_contents[line_idx] = ""
            if line_idx < len(self._line_colors):
                self._line_colors[line_idx] = []

            # Clear visual
            row = self._current_row
            col_start = self._content_start_col if self._show_line_numbers else 0
            try:
                self._pad.move(row, col_start)
                self._pad.clrtoeol()
            except curses.error:
                pass

            self._current_col = 0
            self._refresh_display()
            self._update_cursor()

    def open_line_above(self) -> None:
        """Insert a blank line above current and move cursor there (like vim O)."""
        line_idx = self._get_current_line_idx()
        self._line_contents.insert(line_idx, "")
        self._line_colors.insert(line_idx, [])
        self._redraw_all_content()
        # Cursor stays at same row, which now has the blank line
        self._current_col = 0
        self._refresh_display()
        self._update_cursor()

    # =========================================================================
    # PUBLIC API - Mode and State
    # =========================================================================

    def set_vim_mode(self, mode: str) -> None:
        """Set the vim mode indicator (just for display)."""
        self._vim_mode = mode
        self._draw_statusline()

    def set_insert_mode(self, enabled: bool) -> None:
        """Enable/disable insert mode (affects newline behavior)."""
        self._insert_mode = enabled

    def set_statusline_enabled(self, enabled: bool) -> None:
        """Enable or disable the status line."""
        self._statusline_enabled = enabled
        if enabled:
            self._refresh_display()

    def get_current_line(self) -> int:
        """Get current line number (1-indexed)."""
        return self._current_line_number

    def get_total_lines(self) -> int:
        """Get total number of lines."""
        return len(self._line_contents)

    def reset_scroll(self) -> None:
        """Reset scroll position to the top."""
        self._scroll_offset = 0
        self._refresh_display()

    def get_max_scroll(self) -> int:
        """Get the maximum valid scroll offset."""
        visible_rows = self._get_visible_rows()
        total_content_rows = self._line_start_row + len(self._line_contents)
        return max(0, total_content_rows - visible_rows)

    def get_content(self) -> str:
        """Get the current document content as a string."""
        return "\n".join(self._line_contents)

    def get_normalized_content(self) -> str:
        """Get normalized content for comparison.

        Normalization:
        - Strip trailing whitespace from each line
        - Remove trailing blank lines
        - Join with single newlines
        """
        lines = [line.rstrip() for line in self._line_contents]
        # Remove trailing empty lines
        while lines and not lines[-1]:
            lines.pop()
        return "\n".join(lines)

    def get_content_lines(self) -> list[str]:
        """Get a copy of the current line contents.

        Returns a copy to prevent external mutation of internal state.
        """
        return list(self._line_contents)

    def set_content_lines(self, lines: list[str]) -> None:
        """Set the document content from a list of lines.

        This replaces the entire content and triggers a redraw.
        """
        self._line_contents = list(lines)  # Make a copy
        # Ensure colors array matches
        self._line_colors = [[] for _ in self._line_contents]
        # Redraw
        self._redraw_all_content()
        self._refresh_display()

    def set_line_colors(self, colors: list[list[int]]) -> None:
        """Set the color attributes for all lines.

        Args:
            colors: List of color attribute lists, one per line.
                    Each inner list contains color attributes for each character.
        """
        self._line_colors = [list(line_colors) for line_colors in colors]
        # Redraw with new colors
        self._redraw_all_content()
        self._refresh_display()

    # =========================================================================
    # PUBLIC API - File Display
    # =========================================================================

    def show_file_header(self, path, total_chars: int = 0) -> None:
        """Display file header at the top."""
        header = f" File: {path} "

        self._pad.clear()
        self._current_row = 0
        self._current_col = 0
        self._scroll_offset = 0
        self._current_line_number = 1
        self._line_contents = [""]
        self._line_colors = [[]]  # Reset colors
        self._insert_mode = False

        self._filename = str(path)
        self._total_chars = total_chars
        self._chars_typed = 0

        try:
            attr = (
                curses.color_pair(self.COLOR_HEADER)
                if self._colors_initialized
                else curses.A_REVERSE
            )
            centered = header.center(self._max_x)
            self._pad.addstr(0, 0, centered[: self._max_x - 1], attr)
            self._current_row = self._header_rows
            self._line_start_row = self._header_rows
            self._draw_line_number()
            self._refresh_display()
        except curses.error:
            pass

    def show_file_transition(self, pause_duration: float = 1.0) -> None:
        """Show transition between files."""
        time.sleep(pause_duration)
        self._pad.clear()
        self._stdscr.clear()
        self._stdscr.refresh()

    def clear(self) -> None:
        """Clear the display."""
        if self._pad:
            self._pad.clear()
        if self._stdscr:
            self._stdscr.clear()
            self._stdscr.refresh()

        self._current_row = 0
        self._current_col = 0
        self._scroll_offset = 0
        self._current_line_number = 1
        self._line_contents = [""]
        self._line_colors = [[]]  # Reset colors
        self._insert_mode = False

    def check_scroll_input(self) -> bool:
        """Check for scroll input without blocking.

        Called during typing to allow user to scroll while content is being typed.
        Returns True if 'q' was pressed (to abort), False otherwise.
        """
        if not self._stdscr:
            return False

        # Update clock
        self._update_clock_display()

        # Set non-blocking mode
        self._stdscr.nodelay(True)

        # Enable free scroll so user can scroll anywhere
        old_free_scroll = self._free_scroll_mode
        self._free_scroll_mode = True

        try:
            key = self._stdscr.getch()

            if key == -1:  # No input
                self._free_scroll_mode = old_free_scroll
                return False

            if key == curses.KEY_RESIZE:
                self._handle_resize()

            elif key in (ord("q"), ord("Q"), 27):  # q, Q, or Escape - abort
                self._free_scroll_mode = old_free_scroll
                return True

            elif key == curses.KEY_UP or key == ord("k"):
                if self._scroll_offset > 0:
                    self._scroll_offset -= 1
                    self._refresh_display()

            elif key == curses.KEY_DOWN or key == ord("j"):
                max_scroll = self.get_max_scroll()
                if self._scroll_offset < max_scroll:
                    self._scroll_offset += 1
                    self._refresh_display()

            elif key == curses.KEY_PPAGE or key == ord("b"):
                visible = self._get_visible_rows()
                self._scroll_offset = max(0, self._scroll_offset - visible)
                self._refresh_display()

            elif key == curses.KEY_NPAGE or key == ord(" ") or key == ord("f"):
                visible = self._get_visible_rows()
                max_scroll = self.get_max_scroll()
                self._scroll_offset = min(max_scroll, self._scroll_offset + visible)
                self._refresh_display()

            elif key == curses.KEY_HOME or key == ord("g"):
                self._scroll_offset = 0
                self._refresh_display()

            elif key == curses.KEY_END or key == ord("G"):
                self._scroll_offset = self.get_max_scroll()
                self._refresh_display()

        except curses.error:
            pass
        finally:
            # Restore blocking mode and scroll mode
            self._stdscr.nodelay(False)
            self._free_scroll_mode = old_free_scroll

        return False

    def wait_for_exit(self) -> None:
        """Wait for user to press 'q' to exit, allowing scrolling in the meantime.

        This keeps the display open so users can review the typed code.
        Arrow keys, Page Up/Down, Home/End allow scrolling through the content.
        Press 'q' or Escape to exit.
        """
        if not self._stdscr:
            return

        # Update status line to show we're in review mode
        self._vim_mode = "REVIEW"
        self._draw_statusline()

        # Enable free scroll mode for review - user can scroll anywhere
        self._free_scroll_mode = True

        # Start at the top of the file for review
        self._scroll_offset = 0
        self._refresh_display()

        # Enable keypad for special keys
        self._stdscr.keypad(True)
        # Use timeout mode so we can update clock
        self._stdscr.timeout(100)  # 100ms timeout

        # Hide cursor during review
        try:
            curses.curs_set(0)
        except curses.error:
            pass

        while True:
            try:
                # Update clock (force refresh since no typing is happening)
                self._update_clock_display(force_refresh=True)

                key = self._stdscr.getch()

                if key == -1:  # Timeout, no key pressed
                    continue

                if key == curses.KEY_RESIZE:
                    self._handle_resize()
                    continue

                if key in (ord("q"), ord("Q"), 27):  # q, Q, or Escape
                    break

                elif key == curses.KEY_UP or key == ord("k"):
                    # Scroll up
                    if self._scroll_offset > 0:
                        self._scroll_offset -= 1
                        self._refresh_display()

                elif key == curses.KEY_DOWN or key == ord("j"):
                    # Scroll down
                    max_scroll = self.get_max_scroll()
                    if self._scroll_offset < max_scroll:
                        self._scroll_offset += 1
                        self._refresh_display()

                elif key == curses.KEY_PPAGE or key == ord("b"):  # Page Up or 'b'
                    # Scroll up by page
                    visible = self._get_visible_rows()
                    self._scroll_offset = max(0, self._scroll_offset - visible)
                    self._refresh_display()

                elif (
                    key == curses.KEY_NPAGE or key == ord(" ") or key == ord("f")
                ):  # Page Down, space, or 'f'
                    # Scroll down by page
                    visible = self._get_visible_rows()
                    max_scroll = self.get_max_scroll()
                    self._scroll_offset = min(max_scroll, self._scroll_offset + visible)
                    self._refresh_display()

                elif key == curses.KEY_HOME or key == ord("g"):
                    # Go to top
                    self._scroll_offset = 0
                    self._refresh_display()

                elif key == curses.KEY_END or key == ord("G"):
                    # Go to bottom
                    self._scroll_offset = self.get_max_scroll()
                    self._refresh_display()

            except curses.error:
                pass

        # Restore cursor and scroll mode
        self._free_scroll_mode = False
        try:
            curses.curs_set(1)
        except curses.error:
            pass
