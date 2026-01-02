"""Core typing engine that orchestrates the typing simulation."""

import time
from typing import Any, Optional

from code_typer.human_behavior import ActionType, HumanBehavior
from code_typer.realistic_python_typer import RealisticPythonTyper


class TyperEngine:
    """Main engine that orchestrates typing simulation.

    Coordinates between human behavior simulation, syntax highlighting,
    and display rendering.
    """

    def __init__(
        self,
        display,
        speed: float = 1.0,
        error_rate: float = 0.06,
        enable_highlight: bool = True,
        seed: Optional[int] = None,
    ):
        """Initialize the typing engine.

        Args:
            display: Display instance for rendering (NcursesDisplay)
            speed: Typing speed multiplier
            error_rate: Probability of making errors (default 0.06 = 6%)
            enable_highlight: Whether to enable syntax highlighting
            seed: Random seed for reproducibility
        """
        self.display = display
        self.enable_highlight = enable_highlight
        self.human = HumanBehavior(speed=speed, error_rate=error_rate, seed=seed)
        self._highlighter = None
        self._current_line = 0
        self._current_col = 0
        self._verification_error: Optional[str] = (
            None  # Stores SHA256 verification errors
        )

    def reset(self) -> None:
        """Reset state for a new file.

        Call this between files when processing a directory to prevent
        state accumulation (fatigue, momentum, etc.) from affecting
        subsequent files.
        """
        self.human.reset()
        self._current_line = 0
        self._current_col = 0
        self._verification_error = None

    def _get_highlighter(self, language: str):
        """Get or create a highlighter for the given language."""
        if not self.enable_highlight:
            return None

        from code_typer.syntax import Highlighter, PythonHighlighter, SQLHighlighter

        highlighter_map = {
            "python": PythonHighlighter,
            "sql": SQLHighlighter,
        }

        highlighter_class = highlighter_map.get(language)
        if highlighter_class:
            return highlighter_class()

        return Highlighter()

    def type_content(self, content: str, language: str = "text") -> None:
        """Type out the content with human-like behavior.

        Args:
            content: The text content to type
            language: Programming language for syntax highlighting
        """
        self._highlighter = self._get_highlighter(language)

        # Pre-tokenize content for syntax highlighting
        tokens = None
        if self._highlighter:
            tokens = list(self._highlighter.tokenize(content))

        # Build a map of position -> token type for coloring
        token_map: dict[int, Any] = {}
        if tokens:
            pos = 0
            for token in tokens:
                for i, _char in enumerate(token.text):
                    token_map[pos + i] = token.token_type
                pos += len(token.text)

        # Process typing actions
        for action in self.human.generate_typing_sequence(content):
            # Apply delay (in small chunks to allow scroll input)
            delay_remaining = action.delay
            while delay_remaining > 0:
                chunk = min(delay_remaining, 0.05)  # Check input every 50ms
                time.sleep(chunk)
                delay_remaining -= chunk

                # Check for scroll input during typing
                if hasattr(self.display, "check_scroll_input"):
                    if self.display.check_scroll_input():
                        return  # User pressed 'q' to abort

            # Use content_pos from action for syntax highlighting
            pos = action.content_pos if action.content_pos >= 0 else -1

            # Handle different action types
            if action.action_type == ActionType.CHAR:
                token_type = token_map.get(pos) if pos >= 0 else None

                if action.char == "\n":
                    self.display.newline()
                    self._current_line += 1
                    self._current_col = 0
                else:
                    # Errors look like normal text - no special highlighting
                    self.display.type_char(action.char, token_type=token_type)
                    self._current_col += 1

            elif action.action_type == ActionType.TAB:
                token_type = token_map.get(pos) if pos >= 0 else None
                self.display.type_tab(token_type=token_type)
                self._current_col += 4  # Tab width

            elif action.action_type == ActionType.BACKSPACE:
                self.display.backspace()
                if self._current_col > 0:
                    self._current_col -= 1

            elif action.action_type == ActionType.DELETE_WORD:
                self.display.delete_word()

            elif action.action_type == ActionType.DELETE_LINE:
                self.display.delete_line()
                self._current_col = 0

            elif action.action_type == ActionType.UP:
                self.display.move_up()
                if self._current_line > 0:
                    self._current_line -= 1

            elif action.action_type == ActionType.DOWN:
                self.display.move_down()
                self._current_line += 1

            elif action.action_type == ActionType.HOME:
                self.display.move_home()
                self._current_col = 0

            elif action.action_type == ActionType.END:
                self.display.move_end()

            elif action.action_type == ActionType.PAUSE:
                # Pause is already handled by the delay
                pass

    def type_file(self, file_info) -> None:
        """Type out a file's content.

        Args:
            file_info: FileInfo object with path, content, and language
        """
        self.type_content(file_info.content, file_info.language)

    def type_python_smart(self, content: str, skeleton_first: bool = True) -> bool:
        """Type Python code using realistic simulation with cursor movement.

        This simulates how humans actually write code:
        1. Write function/class skeletons with 'pass' placeholder
        2. Go BACK UP to add imports at the top
        3. Go to each function and replace 'pass' with actual body
        4. Go back and add docstrings

        The cursor actually moves to the correct positions, just like in vim.

        Args:
            content: Python source code to type
            skeleton_first: If True, use realistic mode with cursor movement

        Returns:
            True if content was verified successfully, False otherwise
        """
        self._highlighter = self._get_highlighter("python")

        if not skeleton_first:
            # Fall back to linear typing
            self.type_content(content, "python")
            return True  # Linear mode doesn't have verification

        try:
            # Create realistic typer with cursor movements
            realistic_typer = RealisticPythonTyper(content)

            # Let the typer handle all the cursor movement and typing
            realistic_typer.type_with_movements(self, self.human)

            # Verify content integrity with SHA256
            success, message = realistic_typer.verify_content(self.display)
            if not success:
                # Store verification failure for later display
                self._verification_error = message
                return False
            return True
        except SyntaxError:
            # If code has syntax errors, fall back to linear typing
            self.type_content(content, "python")
            return True  # Linear mode doesn't have verification
