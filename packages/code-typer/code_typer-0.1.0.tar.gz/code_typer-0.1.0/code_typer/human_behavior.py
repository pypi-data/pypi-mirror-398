"""Human-like typing behavior simulation.

This module implements truly realistic typing patterns including:
- Variable typing speed with momentum (bursts and slowdowns)
- Thinking pauses, reading pauses, and distraction pauses
- Wrong word generation (not just single character typos)
- Line and word deletions
- Vertical cursor movement (going back to fix things)
- Real tab characters
- Fatigue simulation over time
"""

import random
import time
from collections.abc import Generator, Mapping
from dataclasses import dataclass
from enum import Enum, auto
from types import MappingProxyType
from typing import Optional

# Try to import fast Cython implementations
try:
    from code_typer._fast_human import (
        calculate_delay_fast,
        check_pattern_match_fast,
        extract_current_word_fast,
        update_momentum_fast,
    )

    _USE_CYTHON = True
except ImportError:
    _USE_CYTHON = False


class ActionType(Enum):
    """Types of typing actions."""

    CHAR = auto()  # Type a single character
    BACKSPACE = auto()  # Delete one character
    DELETE_WORD = auto()  # Delete entire word (Ctrl+Backspace)
    DELETE_LINE = auto()  # Delete entire line (Ctrl+U or select+delete)
    UP = auto()  # Move cursor up
    DOWN = auto()  # Move cursor down
    HOME = auto()  # Move to start of line
    END = auto()  # Move to end of line
    PAUSE = auto()  # Pause (thinking, reading, distraction)
    TAB = auto()  # Tab character


class PauseType(Enum):
    """Types of pauses."""

    THINKING = auto()  # Thinking about what to type next
    READING = auto()  # Reading/reviewing code
    DISTRACTION = auto()  # Brief distraction (checking phone, etc)
    HESITATION = auto()  # Brief hesitation mid-word
    LINE_END = auto()  # Natural pause at end of line


@dataclass
class TypingAction:
    """Represents a single typing action."""

    action_type: ActionType
    char: str = ""
    delay: float = 0.0  # Delay before this action in seconds
    is_error: bool = False  # Whether this is an erroneous action
    pause_type: Optional[PauseType] = None
    repeat: int = 1  # For repeated actions (e.g., multiple backspaces)
    content_pos: int = -1  # Position in original content (-1 = not applicable)


# Common word confusions/typos (word -> common mistakes)
# Immutable to prevent accidental modification of shared state
WORD_CONFUSIONS: Mapping[str, tuple[str, ...]] = MappingProxyType(
    {
        "the": ("teh", "hte", "th", "thew"),
        "and": ("adn", "nad", "annd"),
        "for": ("fro", "fo", "forr"),
        "def": ("dfe", "de", "deaf"),
        "self": ("slef", "sefl", "sel"),
        "return": ("retrun", "reutrn", "retrn", "retunr"),
        "import": ("improt", "imoprt", "imprt"),
        "from": ("form", "fomr", "frmo"),
        "class": ("calss", "clss", "classs"),
        "function": ("fucntion", "funciton", "funtion"),
        "print": ("pirnt", "pritn", "prnit"),
        "while": ("whiel", "wihle", "whle"),
        "True": ("Ture", "Treu"),
        "False": ("Flase", "Fasle"),
        "None": ("Nonn", "Non"),
        "if": ("fi", "iff"),
        "else": ("esle", "els", "elese"),
        "elif": ("elfi", "leif"),
        "with": ("wiht", "wtih"),
        "as": ("sa", "ass"),
        "in": ("ni", "inn"),
        "is": ("si", "iss"),
        "not": ("nto", "no"),
        "or": ("ro", "orr"),
        "try": ("tyr", "trry"),
        "except": ("exept", "excpet", "ecxept"),
        "finally": ("finaly", "fianlly"),
        "raise": ("rasie", "riase"),
        "assert": ("assret", "asert"),
        "yield": ("yeild", "yiled"),
        "lambda": ("lamda", "lamba"),
        "global": ("gloabl", "glboal"),
        "pass": ("pss", "passs"),
        "break": ("braek", "brek"),
        "continue": ("contniue", "coninue", "contineu"),
        "SELECT": ("SELCT", "SLECT", "SEELCT"),
        "FROM": ("FORM", "FOMR"),
        "WHERE": ("WEHRE", "WHEER", "WHER"),
        "INSERT": ("INSRET", "INSER"),
        "UPDATE": ("UDPATE", "UPDTE"),
        "DELETE": ("DELTE", "DELET"),
        "CREATE": ("CRAETE", "CREAT"),
        "TABLE": ("TABEL", "TALBE"),
        "INDEX": ("INDX", "IDNEX"),
        "JOIN": ("JION", "JOING"),
        "LEFT": ("LFET", "LEDT"),
        "RIGHT": ("RIHGT", "RIGTH"),
        "INNER": ("INNRE", "INER"),
        "OUTER": ("OUETR", "OUTRE"),
        "GROUP": ("GROPU", "GOUP"),
        "ORDER": ("ORDEER", "ORDR"),
        "HAVING": ("HAVIGN", "HAIVNG"),
        "LIMIT": ("LIMT", "LIMI"),
        "OFFSET": ("OFFSTE", "OFFET"),
    }
)

# Common programming patterns (typed faster as muscle memory)
# Immutable tuple to prevent accidental modification
COMMON_PATTERNS: tuple[str, ...] = (
    "def ",
    "return ",
    "import ",
    "from ",
    "class ",
    "if ",
    "else:",
    "elif ",
    "for ",
    "while ",
    "self.",
    "self,",
    "__init__",
    "__name__",
    "print(",
    "len(",
    "range(",
    "str(",
    "int(",
    "True",
    "False",
    "None",
    "SELECT ",
    "FROM ",
    "WHERE ",
    "INSERT ",
    "UPDATE ",
    "CREATE ",
    "DROP ",
    "ALTER ",
    "JOIN ",
    "AND ",
    "OR ",
    "function ",
    "const ",
    "let ",
    "var ",
    "async ",
    "await ",
    "    ",
    "\t",
    "): ",
    "-> ",
    "=> ",
    "== ",
    "!= ",
    "<= ",
    ">= ",
    "**",
    "++",
    "--",
    "&&",
    "||",
)

# Nearby keys for single character typos
# Immutable to prevent accidental modification of shared state
NEARBY_KEYS: Mapping[str, str] = MappingProxyType(
    {
        "a": "sqwz",
        "b": "vghn",
        "c": "xdfv",
        "d": "erfcxs",
        "e": "wrsdf",
        "f": "rtgvcd",
        "g": "tyhbvf",
        "h": "yujnbg",
        "i": "uojkl",
        "j": "uikmnh",
        "k": "ioljm",
        "l": "opk",
        "m": "njk",
        "n": "bhjm",
        "o": "ipkl",
        "p": "ol",
        "q": "wa",
        "r": "edft",
        "s": "awedxz",
        "t": "rfgy",
        "u": "yihj",
        "v": "cfgb",
        "w": "qase",
        "x": "zsdc",
        "y": "tghu",
        "z": "asx",
        "1": "2q",
        "2": "13qw",
        "3": "24we",
        "4": "35er",
        "5": "46rt",
        "6": "57ty",
        "7": "68yu",
        "8": "79ui",
        "9": "80io",
        "0": "9op",
    }
)


class HumanBehavior:
    """Simulates realistic human-like typing behavior."""

    def __init__(
        self, speed: float = 1.0, error_rate: float = 0.06, seed: Optional[int] = None
    ):
        """Initialize human behavior simulation.

        Args:
            speed: Base typing speed multiplier (1.0 = normal, 2.0 = twice as fast)
            error_rate: Base probability of errors (0.0-1.0, default 0.06 = 6%)
            seed: Random seed for reproducibility
        """
        # Allow very high speeds for fast demos, clamp minimum to prevent division issues
        self.base_speed = max(0.1, speed)
        self.error_rate = max(0.0, min(0.3, error_rate))
        self._rng = random.Random(seed)

        # Dynamic state
        self._momentum = 1.0  # Current speed momentum (0.5-2.0)
        self._fatigue = 0.0  # Accumulated fatigue (0.0-1.0)
        self._chars_typed = 0  # Characters typed in current session
        self._chars_since_error = 0  # Characters since last error
        self._chars_since_pause = 0  # Characters since last pause
        self._current_line = 0  # Track current line for vertical movement
        self._lines_typed: list[str] = []  # Content of typed lines

        # Timing constants (in seconds)
        self.BASE_DELAY = 0.055  # ~180 WPM base
        self.MIN_DELAY = 0.012
        self.MAX_DELAY = 0.20
        self.BACKSPACE_DELAY = (0.04, 0.12)  # Backspace is slower, variable

        # Pause durations
        self.PAUSE_THINKING = (0.8, 3.0)  # Thinking pause range
        self.PAUSE_READING = (0.3, 1.5)  # Reading/reviewing pause
        self.PAUSE_DISTRACTION = (1.0, 4.0)  # Brief distraction
        self.PAUSE_HESITATION = (0.15, 0.4)  # Mid-word hesitation
        self.PAUSE_LINE_END = (0.1, 0.5)  # End of line pause
        self.PAUSE_NOTICE_ERROR = (0.15, 0.5)  # Pause when noticing error

        # Probability thresholds
        self.P_MULTI_CHAR_DELETE = 0.3  # Chance of deleting multiple chars
        self.P_GO_BACK_UP = 0.008  # Chance of going back up to fix something
        self.P_THINKING_PAUSE = 0.03  # Chance of thinking pause
        self.P_DISTRACTION = 0.005  # Chance of distraction pause
        self.P_HESITATION = 0.02  # Chance of mid-word hesitation
        self.P_BURST_START = 0.08  # Chance of starting a burst
        self.P_BURST_END = 0.15  # Chance of ending burst per char
        self.P_SLOWDOWN = 0.05  # Chance of slowing down

        # State flags
        self._in_burst = False
        self._in_slowdown = False

    def reset(self) -> None:
        """Reset dynamic state for a new file/session.

        Call this between files to prevent state accumulation
        (fatigue, momentum, etc.) from affecting subsequent files.
        """
        self._momentum = 1.0
        self._fatigue = 0.0
        self._chars_typed = 0
        self._chars_since_error = 0
        self._chars_since_pause = 0
        self._current_line = 0
        self._lines_typed = []
        self._in_burst = False
        self._in_slowdown = False

    def _update_momentum(self) -> None:
        """Update typing momentum (speed variation)."""
        # Random chance to start/end burst or slowdown
        if not self._in_burst and not self._in_slowdown:
            if self._rng.random() < self.P_BURST_START:
                self._in_burst = True
                self._momentum = self._rng.uniform(1.3, 1.8)
            elif self._rng.random() < self.P_SLOWDOWN:
                self._in_slowdown = True
                self._momentum = self._rng.uniform(0.5, 0.8)
        elif self._in_burst:
            if self._rng.random() < self.P_BURST_END:
                self._in_burst = False
                self._momentum = 1.0
        elif self._in_slowdown:
            if self._rng.random() < self.P_BURST_END * 1.5:  # Slowdowns end faster
                self._in_slowdown = False
                self._momentum = 1.0

        # Add micro-variations using Cython if available
        if _USE_CYTHON:
            self._momentum = update_momentum_fast(
                self._momentum, self._in_burst, self._in_slowdown, self._rng
            )
        else:
            self._momentum *= self._rng.gauss(1.0, 0.08)
            self._momentum = max(0.4, min(2.2, self._momentum))

    def _update_fatigue(self) -> None:
        """Update fatigue based on characters typed."""
        # Fatigue builds up slowly
        self._fatigue = min(0.4, self._chars_typed / 5000)

        # Occasional recovery
        if self._rng.random() < 0.001:
            self._fatigue *= 0.8

    def _get_effective_speed(self) -> float:
        """Get current effective typing speed."""
        speed = self.base_speed * self._momentum
        # Fatigue slows you down
        speed *= 1.0 - self._fatigue * 0.3
        return max(0.3, speed)

    def _calculate_delay(
        self, char: str, prev_char: Optional[str], in_pattern: bool
    ) -> float:
        """Calculate delay before typing a character."""
        self._update_momentum()
        speed = self._get_effective_speed()

        # Use Cython fast path if available
        if _USE_CYTHON:
            return calculate_delay_fast(
                char,
                prev_char if prev_char is not None else "",
                in_pattern,
                self.BASE_DELAY,
                self.MIN_DELAY,
                self.MAX_DELAY,
                speed,
                self._momentum,
                self._rng,
                self.PAUSE_LINE_END,
            )

        # Pure Python fallback
        # Base delay
        delay = self.BASE_DELAY / speed

        # Character difficulty
        if char in "etaoins ":
            delay *= 0.7  # Easy characters
        elif char in "ETAOINS":
            delay *= 0.9  # Shift slows slightly
        elif char in "!@#$%^&*()_+-=[]{}|;:'\",./<>?`~\\":
            delay *= self._rng.uniform(1.2, 1.8)  # Special chars are slow
        elif char == "\n":
            delay *= 0.4  # Enter is quick
        elif char == "\t":
            delay *= 0.3  # Tab is quick

        # Patterns are faster (muscle memory)
        if in_pattern:
            delay *= self._rng.uniform(0.5, 0.7)

        # Add randomness (humans aren't consistent)
        delay *= self._rng.gauss(1.0, 0.25)

        # Context-based pauses
        if prev_char is not None:
            if prev_char == "\n":
                # Pause after newline (looking at next line)
                delay += self._rng.uniform(*self.PAUSE_LINE_END) / speed
            elif prev_char in ".!?":
                # Pause after sentence
                delay += self._rng.uniform(0.1, 0.3) / speed
            elif prev_char in ":{":
                # Pause after block start
                delay += self._rng.uniform(0.05, 0.15) / speed

        return max(self.MIN_DELAY / speed, min(self.MAX_DELAY * 2 / speed, delay))

    def _should_make_error(self, char: str, word_context: str) -> bool:
        """Determine if an error should occur."""
        if char in "\n\t\r":
            return False

        # Minimum spacing between errors
        if self._chars_since_error < 3:
            return False

        # Base probability
        p = self.error_rate

        # Increase probability for difficult characters
        if char in "!@#$%^&*()_+-=[]{}|;:'\",./<>?`~\\":
            p *= 2.0

        # Fatigue increases errors
        p *= 1.0 + self._fatigue

        # Bursts have more errors
        if self._in_burst:
            p *= 1.5

        # Check if word has common confusion
        if word_context.lower() in WORD_CONFUSIONS:
            p *= 1.3

        return self._rng.random() < p

    def _generate_word_error(self, word: str) -> Optional[str]:
        """Generate a wrong word (common confusion)."""
        lower = word.lower()
        if lower in WORD_CONFUSIONS:
            mistakes = WORD_CONFUSIONS[lower]
            wrong = self._rng.choice(mistakes)
            # Preserve case
            if word[0].isupper():
                wrong = wrong[0].upper() + wrong[1:]
            if word.isupper():
                wrong = wrong.upper()
            return wrong
        return None

    def _generate_char_typo(self, char: str) -> str:
        """Generate a single character typo."""
        lower = char.lower()
        if lower in NEARBY_KEYS:
            nearby = NEARBY_KEYS[lower]
            typo = self._rng.choice(nearby)
            if char.isupper():
                typo = typo.upper()
            return typo
        return char

    def _should_pause(self) -> Optional[PauseType]:
        """Check if a pause should occur."""
        self._chars_since_pause += 1

        # Minimum spacing between pauses
        if self._chars_since_pause < 20:
            return None

        # Random pauses
        r = self._rng.random()
        if r < self.P_DISTRACTION:
            return PauseType.DISTRACTION
        elif r < self.P_DISTRACTION + self.P_THINKING_PAUSE:
            return PauseType.THINKING
        elif r < self.P_DISTRACTION + self.P_THINKING_PAUSE + self.P_HESITATION:
            return PauseType.HESITATION

        return None

    def _scaled_uniform(self, min_val: float, max_val: float) -> float:
        """Get a random uniform value scaled by speed."""
        return self._rng.uniform(min_val, max_val) / self.base_speed

    def _scaled_delay(self, delay_range: tuple) -> float:
        """Get a random delay from a range, scaled by speed."""
        return self._rng.uniform(*delay_range) / self.base_speed

    def _get_pause_duration(self, pause_type: PauseType) -> float:
        """Get duration for a pause type."""
        ranges = {
            PauseType.THINKING: self.PAUSE_THINKING,
            PauseType.READING: self.PAUSE_READING,
            PauseType.DISTRACTION: self.PAUSE_DISTRACTION,
            PauseType.HESITATION: self.PAUSE_HESITATION,
            PauseType.LINE_END: self.PAUSE_LINE_END,
        }
        min_d, max_d = ranges.get(pause_type, (0.1, 0.5))
        return self._rng.uniform(min_d, max_d) / self.base_speed

    def _extract_current_word(self, content: str, position: int) -> str:
        """Extract the word at/around current position."""
        if _USE_CYTHON:
            return extract_current_word_fast(content, position)

        # Find word boundaries
        start = position
        while start > 0 and content[start - 1].isalnum():
            start -= 1

        end = position
        while end < len(content) and content[end].isalnum():
            end += 1

        return content[start:end]

    def _check_pattern_match(self, content: str, position: int) -> Optional[str]:
        """Check if current position starts a common pattern."""
        if _USE_CYTHON:
            return check_pattern_match_fast(content, position)

        remaining = content[position:]
        for pattern in COMMON_PATTERNS:
            if remaining.startswith(pattern):
                return pattern
        return None

    def generate_typing_sequence(
        self, content: str
    ) -> Generator[TypingAction, None, None]:
        """Generate a sequence of typing actions for content.

        This is the main method that produces realistic typing behavior.
        """
        i = 0
        pattern_remaining = 0
        prev_char: Optional[str] = None
        current_word = ""

        while i < len(content):
            char = content[i]

            # Track words
            if char.isalnum() or char == "_":
                current_word += char
            else:
                current_word = ""

            # Check for pattern match
            if pattern_remaining <= 0:
                pattern = self._check_pattern_match(content, i)
                if pattern:
                    pattern_remaining = len(pattern)

            in_pattern = pattern_remaining > 0
            if pattern_remaining > 0:
                pattern_remaining -= 1

            # Check for random pause
            pause_type = self._should_pause()
            if pause_type and pause_type != PauseType.HESITATION:
                duration = self._get_pause_duration(pause_type)
                yield TypingAction(
                    action_type=ActionType.PAUSE, delay=duration, pause_type=pause_type
                )
                self._chars_since_pause = 0

            # Calculate base delay
            delay = self._calculate_delay(char, prev_char, in_pattern)

            # Check for error
            upcoming_word = self._extract_current_word(content, i)
            if self._should_make_error(char, upcoming_word):
                # Determine how many wrong characters to type before noticing
                # Most of the time 1, sometimes 2-5
                if self._rng.random() < self.P_MULTI_CHAR_DELETE:
                    # Type multiple wrong chars before noticing
                    max_extra = min(5, len(content) - i)
                    num_wrong_chars = self._rng.randint(2, max(2, max_extra))
                else:
                    num_wrong_chars = 1

                # Generate and type wrong characters
                wrong_chars = []
                for j in range(num_wrong_chars):
                    if i + j >= len(content):
                        break
                    original = content[i + j]
                    if original in "\n\t\r":
                        break  # Don't cross newlines with errors
                    typo = self._generate_char_typo(original)
                    wrong_chars.append((original, typo))

                if wrong_chars and wrong_chars[0][0] != wrong_chars[0][1]:
                    # Type all wrong characters
                    for j, (original, typo) in enumerate(wrong_chars):
                        char_delay = self._calculate_delay(
                            original, prev_char, in_pattern
                        )
                        yield TypingAction(
                            action_type=ActionType.CHAR,
                            char=typo,
                            delay=char_delay,
                            is_error=True,
                            content_pos=i + j,
                        )
                        self._chars_typed += 1
                        prev_char = typo

                    # Pause to notice the mistake (looking at screen)
                    notice_delay = self._scaled_delay(self.PAUSE_NOTICE_ERROR)
                    yield TypingAction(
                        action_type=ActionType.PAUSE,
                        delay=notice_delay,
                        pause_type=PauseType.HESITATION,
                    )

                    # Delete each character with visible backspace movement
                    for _ in range(len(wrong_chars)):
                        backspace_delay = self._scaled_delay(self.BACKSPACE_DELAY)
                        yield TypingAction(
                            action_type=ActionType.BACKSPACE,
                            delay=backspace_delay,
                        )

                    # Now type the correct characters
                    for j, (original, _) in enumerate(wrong_chars):
                        retype_delay = self._scaled_delay(self.BACKSPACE_DELAY)
                        if original == "\t":
                            yield TypingAction(
                                action_type=ActionType.TAB,
                                char="\t",
                                delay=retype_delay,
                                content_pos=i + j,
                            )
                        else:
                            yield TypingAction(
                                action_type=ActionType.CHAR,
                                char=original,
                                delay=retype_delay,
                                content_pos=i + j,
                            )
                        self._chars_typed += 1

                    self._chars_since_error = 0
                    prev_char = wrong_chars[-1][0]  # Last correct char
                    i += len(wrong_chars)
                    continue

            # Check for mid-word hesitation
            if (
                current_word
                and len(current_word) > 2
                and self._rng.random() < self.P_HESITATION
            ):
                yield TypingAction(
                    action_type=ActionType.PAUSE,
                    delay=self._scaled_delay(self.PAUSE_HESITATION),
                    pause_type=PauseType.HESITATION,
                )

            # Normal character
            if char == "\t":
                yield TypingAction(
                    action_type=ActionType.TAB, char="\t", delay=delay, content_pos=i
                )
            else:
                yield TypingAction(
                    action_type=ActionType.CHAR, char=char, delay=delay, content_pos=i
                )

            # Update state
            if char == "\n":
                self._current_line += 1
                # Sometimes longer pause at end of line
                if self._rng.random() < 0.3:
                    yield TypingAction(
                        action_type=ActionType.PAUSE,
                        delay=self._scaled_uniform(0.1, 0.4),
                        pause_type=PauseType.LINE_END,
                    )

            prev_char = char
            self._chars_typed += 1
            self._chars_since_error += 1
            self._update_fatigue()
            i += 1

        # Check for going back up (happens at end of blocks)
        if (
            self._current_line > 3
            and self._rng.random() < self.P_GO_BACK_UP * self._current_line
        ):
            lines_up = self._rng.randint(1, min(3, self._current_line))

            # Pause to "review"
            yield TypingAction(
                action_type=ActionType.PAUSE,
                delay=self._scaled_uniform(0.5, 1.5),
                pause_type=PauseType.READING,
            )

            # Go up
            for _ in range(lines_up):
                yield TypingAction(
                    action_type=ActionType.UP, delay=self._scaled_uniform(0.05, 0.15)
                )

            # Pause to look
            yield TypingAction(
                action_type=ActionType.PAUSE,
                delay=self._scaled_uniform(0.3, 0.8),
                pause_type=PauseType.READING,
            )

            # Go back down
            for _ in range(lines_up):
                yield TypingAction(
                    action_type=ActionType.DOWN, delay=self._scaled_uniform(0.05, 0.15)
                )

    def type_with_timing(
        self, content: str
    ) -> Generator[tuple[str, ActionType], None, None]:
        """Type content with realistic timing.

        Yields (char, action_type) tuples, handling timing internally.
        """
        for action in self.generate_typing_sequence(content):
            time.sleep(action.delay)
            yield (action.char, action.action_type)
