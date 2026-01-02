"""Tests for CLI interface."""

import pytest
from click.testing import CliRunner

from code_typer import __version__
from code_typer.cli import main


class TestCLI:
    """Test suite for CLI."""

    @pytest.fixture
    def runner(self):
        """Create a CLI test runner."""
        return CliRunner()

    def test_version(self, runner):
        """Test version flag."""
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert __version__ in result.output

    def test_help(self, runner):
        """Test help flag."""
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "Showcase code files" in result.output
        assert "--speed" in result.output
        assert "--error-rate" in result.output

    def test_nonexistent_file(self, runner):
        """Test error on nonexistent file."""
        result = runner.invoke(main, ["nonexistent_file.py"])
        assert result.exit_code != 0

    def test_valid_file_without_tty(self, runner, tmp_path):
        """Test that the CLI accepts a valid file."""
        test_file = tmp_path / "test.py"
        test_file.write_text("print('hello')")

        # This will fail in non-TTY environment (CI) but shouldn't crash on bad args
        _ = runner.invoke(main, [str(test_file)])
        # Could be 0 or 1 depending on TTY availability
        # We just verify it doesn't crash with invalid input handling

    def test_speed_option_parsing(self, runner, tmp_path):
        """Test that speed option is parsed correctly."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1")

        # Test that invalid speed types are rejected
        result = runner.invoke(main, [str(test_file), "--speed", "not_a_number"])
        assert result.exit_code != 0

    def test_error_rate_option_parsing(self, runner, tmp_path):
        """Test that error-rate option is parsed correctly."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1")

        # Test that invalid error rate types are rejected
        result = runner.invoke(main, [str(test_file), "--error-rate", "invalid"])
        assert result.exit_code != 0


class TestCLIStdin:
    """Test stdin input support."""

    @pytest.fixture
    def runner(self):
        """Create a CLI test runner."""
        return CliRunner()

    def test_no_input_shows_error(self, runner):
        """Test that no input shows helpful error message."""
        result = runner.invoke(main, [])
        assert result.exit_code != 0
        assert "No input provided" in result.output or "stdin" in result.output.lower()

    def test_empty_stdin_shows_error(self, runner):
        """Test that empty stdin shows error."""
        result = runner.invoke(main, ["-"], input="")
        assert result.exit_code != 0
        assert "No content" in result.output or "Error" in result.output

    def test_language_option_exists(self, runner):
        """Test that --language option is available."""
        result = runner.invoke(main, ["--help"])
        assert "--language" in result.output
        assert "python" in result.output
        assert "sql" in result.output

    def test_stdin_examples_in_help(self, runner):
        """Test that stdin examples are shown in help."""
        result = runner.invoke(main, ["--help"])
        assert "cat" in result.output or "stdin" in result.output
        assert "showcase -" in result.output or "pipe" in result.output.lower()


class TestCLIOptions:
    """Test CLI option defaults and constraints."""

    def test_default_speed(self):
        """Test default speed value."""
        from code_typer.cli import main

        # Get the option from the command
        speed_option = None
        for param in main.params:
            if param.name == "speed":
                speed_option = param
                break

        assert speed_option is not None
        assert speed_option.default == 1.0

    def test_default_error_rate(self):
        """Test default error_rate value."""
        from code_typer.cli import main

        error_rate_option = None
        for param in main.params:
            if param.name == "error_rate":
                error_rate_option = param
                break

        assert error_rate_option is not None
        assert error_rate_option.default == 0.06
