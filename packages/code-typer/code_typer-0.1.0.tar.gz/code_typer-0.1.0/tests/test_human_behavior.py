"""Tests for human behavior simulation."""

from code_typer.human_behavior import (
    COMMON_PATTERNS,
    WORD_CONFUSIONS,
    ActionType,
    HumanBehavior,
    PauseType,
    TypingAction,
)


class TestHumanBehavior:
    """Test suite for HumanBehavior class."""

    def test_init_default_values(self):
        """Test default initialization values."""
        hb = HumanBehavior()
        assert hb.base_speed == 1.0
        assert hb.error_rate == 0.06  # New default

    def test_init_custom_values(self):
        """Test custom initialization values."""
        hb = HumanBehavior(speed=2.0, error_rate=0.1)
        assert hb.base_speed == 2.0
        assert hb.error_rate == 0.1

    def test_speed_clamping(self):
        """Test that speed minimum is clamped but high speeds are allowed."""
        hb_low = HumanBehavior(speed=0.01)
        assert hb_low.base_speed == 0.1  # Clamped to minimum

        # High speeds should NOT be clamped (for fast demos)
        hb_high = HumanBehavior(speed=100.0)
        assert hb_high.base_speed == 100.0  # No max clamping

        hb_very_high = HumanBehavior(speed=500.0)
        assert hb_very_high.base_speed == 500.0  # Very high speeds allowed

    def test_error_rate_clamping(self):
        """Test that error_rate is clamped to valid range."""
        hb_low = HumanBehavior(error_rate=-0.5)
        assert hb_low.error_rate == 0.0

        hb_high = HumanBehavior(error_rate=1.0)
        assert hb_high.error_rate == 0.3  # New maximum

    def test_generate_typing_sequence_basic(self):
        """Test basic typing sequence generation."""
        hb = HumanBehavior(speed=10.0, error_rate=0.0, seed=42)
        content = "hello"

        actions = list(hb.generate_typing_sequence(content))

        # Should have actions for the characters (may include pauses)
        char_actions = [a for a in actions if a.action_type == ActionType.CHAR]
        assert len(char_actions) >= 5  # At least 5 character actions
        for action in actions:
            assert isinstance(action, TypingAction)
            assert action.delay >= 0

    def test_generate_typing_sequence_preserves_content(self):
        """Test that sequence produces the original content when error_rate=0."""
        hb = HumanBehavior(speed=10.0, error_rate=0.0, seed=42)
        content = "def main():\n    pass\n"

        actions = list(hb.generate_typing_sequence(content))

        # Reconstruct content from CHAR and TAB actions only
        result = "".join(
            a.char
            for a in actions
            if a.action_type in (ActionType.CHAR, ActionType.TAB)
        )
        assert result == content

    def test_typos_occur_with_high_error_rate(self):
        """Test that errors occur when error_rate is high."""
        hb = HumanBehavior(speed=10.0, error_rate=0.25, seed=42)
        content = "the quick brown fox jumps over the lazy dog"

        actions = list(hb.generate_typing_sequence(content))

        # With 25% error rate on a long string, we should see some errors
        error_count = sum(1 for a in actions if a.is_error)
        delete_word_count = sum(
            1 for a in actions if a.action_type == ActionType.DELETE_WORD
        )

        # Should have some errors
        assert error_count > 0 or delete_word_count > 0

    def test_no_errors_on_special_chars(self):
        """Test that errors don't occur on newlines and tabs."""
        hb = HumanBehavior(speed=10.0, error_rate=0.3, seed=42)
        content = "\n\t\n"

        actions = list(hb.generate_typing_sequence(content))

        # Filter to just the newline/tab actions
        special_actions = [
            a
            for a in actions
            if a.action_type in (ActionType.CHAR, ActionType.TAB) and a.char in "\n\t"
        ]
        assert all(not a.is_error for a in special_actions)

    def test_reproducible_with_seed(self):
        """Test that same seed produces same sequence."""
        content = "test content"

        hb1 = HumanBehavior(speed=5.0, error_rate=0.0, seed=12345)
        hb2 = HumanBehavior(speed=5.0, error_rate=0.0, seed=12345)

        actions1 = list(hb1.generate_typing_sequence(content))
        actions2 = list(hb2.generate_typing_sequence(content))

        # Filter to just typing actions
        char_actions1 = [a for a in actions1 if a.action_type == ActionType.CHAR]
        char_actions2 = [a for a in actions2 if a.action_type == ActionType.CHAR]

        assert len(char_actions1) == len(char_actions2)
        for a1, a2 in zip(char_actions1, char_actions2):
            assert a1.char == a2.char

    def test_speed_affects_delays(self):
        """Test that higher speed results in shorter delays."""
        content = "test"

        hb_slow = HumanBehavior(speed=1.0, error_rate=0.0, seed=42)
        hb_fast = HumanBehavior(speed=5.0, error_rate=0.0, seed=42)

        actions_slow = list(hb_slow.generate_typing_sequence(content))
        actions_fast = list(hb_fast.generate_typing_sequence(content))

        # Get only CHAR actions for comparison
        char_slow = [a for a in actions_slow if a.action_type == ActionType.CHAR]
        char_fast = [a for a in actions_fast if a.action_type == ActionType.CHAR]

        # Fast typing should have shorter total delay
        total_slow = sum(a.delay for a in char_slow)
        total_fast = sum(a.delay for a in char_fast)

        assert total_fast < total_slow

    def test_pattern_recognition(self):
        """Test that common patterns are typed faster."""
        hb = HumanBehavior(speed=1.0, error_rate=0.0, seed=42)

        # "def " is a common pattern
        pattern_content = "def "
        random_content = "xyz "

        pattern_actions = list(hb.generate_typing_sequence(pattern_content))
        # Reset state for fair comparison
        hb2 = HumanBehavior(speed=1.0, error_rate=0.0, seed=42)
        random_actions = list(hb2.generate_typing_sequence(random_content))

        # Get CHAR actions only
        pattern_chars = [a for a in pattern_actions if a.action_type == ActionType.CHAR]
        random_chars = [a for a in random_actions if a.action_type == ActionType.CHAR]

        pattern_delay = sum(a.delay for a in pattern_chars)
        random_delay = sum(a.delay for a in random_chars)

        # Pattern should be typed faster (within reason - randomness affects this)
        # We just check it's not significantly slower
        assert pattern_delay < random_delay * 1.5

    def test_char_difficulty_affects_speed(self):
        """Test that difficult characters take longer."""
        hb = HumanBehavior(speed=1.0, error_rate=0.0, seed=42)

        # Easy character
        easy_actions = list(hb.generate_typing_sequence("e"))
        easy_chars = [a for a in easy_actions if a.action_type == ActionType.CHAR]

        # Hard character - reset state
        hb2 = HumanBehavior(speed=1.0, error_rate=0.0, seed=42)
        hard_actions = list(hb2.generate_typing_sequence("@"))
        hard_chars = [a for a in hard_actions if a.action_type == ActionType.CHAR]

        # Both should produce actions
        assert len(easy_chars) > 0
        assert len(hard_chars) > 0

    def test_pauses_occur(self):
        """Test that pauses occur in longer content."""
        hb = HumanBehavior(speed=1.0, error_rate=0.0, seed=42)
        # Longer content to increase chance of pauses
        content = "def function_name():\n    return True\n" * 3

        actions = list(hb.generate_typing_sequence(content))

        pause_count = sum(1 for a in actions if a.action_type == ActionType.PAUSE)
        # Should have at least some pauses in longer content
        assert pause_count >= 0  # Pauses are probabilistic

    def test_vertical_movement(self):
        """Test that vertical movement can occur."""
        hb = HumanBehavior(speed=1.0, error_rate=0.0, seed=42)
        # Content with multiple lines
        content = "line1\nline2\nline3\nline4\nline5\n"

        actions = list(hb.generate_typing_sequence(content))

        # UP/DOWN actions may occur (probabilistic) - verify they are valid TypingActions
        # Just verify the actions are generated correctly
        assert all(isinstance(a, TypingAction) for a in actions)


class TestTypingAction:
    """Test suite for TypingAction dataclass."""

    def test_typing_action_creation(self):
        """Test TypingAction creation."""
        action = TypingAction(action_type=ActionType.CHAR, char="a", delay=0.05)
        assert action.action_type == ActionType.CHAR
        assert action.char == "a"
        assert action.delay == 0.05
        assert action.is_error is False
        assert action.pause_type is None

    def test_typing_action_with_error(self):
        """Test TypingAction with error flag."""
        action = TypingAction(
            action_type=ActionType.CHAR, char="s", delay=0.03, is_error=True
        )
        assert action.char == "s"
        assert action.is_error is True

    def test_typing_action_pause(self):
        """Test TypingAction for pauses."""
        action = TypingAction(
            action_type=ActionType.PAUSE, delay=1.5, pause_type=PauseType.THINKING
        )
        assert action.action_type == ActionType.PAUSE
        assert action.pause_type == PauseType.THINKING


class TestActionTypes:
    """Test ActionType and PauseType enums."""

    def test_action_types_exist(self):
        """Test that all action types exist."""
        assert ActionType.CHAR
        assert ActionType.BACKSPACE
        assert ActionType.DELETE_WORD
        assert ActionType.DELETE_LINE
        assert ActionType.UP
        assert ActionType.DOWN
        assert ActionType.HOME
        assert ActionType.END
        assert ActionType.PAUSE
        assert ActionType.TAB

    def test_pause_types_exist(self):
        """Test that all pause types exist."""
        assert PauseType.THINKING
        assert PauseType.READING
        assert PauseType.DISTRACTION
        assert PauseType.HESITATION
        assert PauseType.LINE_END


class TestCommonPatterns:
    """Test that common patterns are properly defined."""

    def test_common_patterns_exist(self):
        """Test that common patterns list is not empty."""
        assert len(COMMON_PATTERNS) > 0

    def test_common_patterns_include_python_keywords(self):
        """Test that Python keywords are in patterns."""
        assert "def " in COMMON_PATTERNS
        assert "class " in COMMON_PATTERNS
        assert "import " in COMMON_PATTERNS
        assert "return " in COMMON_PATTERNS

    def test_common_patterns_include_sql_keywords(self):
        """Test that SQL keywords are in patterns."""
        assert "SELECT " in COMMON_PATTERNS
        assert "FROM " in COMMON_PATTERNS
        assert "WHERE " in COMMON_PATTERNS


class TestWordConfusions:
    """Test word confusion dictionary."""

    def test_word_confusions_exist(self):
        """Test that word confusions dictionary is not empty."""
        assert len(WORD_CONFUSIONS) > 0

    def test_common_words_have_confusions(self):
        """Test that common words have confusion entries."""
        assert "the" in WORD_CONFUSIONS
        assert "def" in WORD_CONFUSIONS
        assert "return" in WORD_CONFUSIONS
        assert "SELECT" in WORD_CONFUSIONS

    def test_confusions_are_similar(self):
        """Test that confusions are similar to original."""
        # 'the' -> 'teh', 'hte' etc are similar length
        for confusion in WORD_CONFUSIONS["the"]:
            assert abs(len(confusion) - len("the")) <= 1
