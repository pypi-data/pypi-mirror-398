"""Tests for file handler."""

from pathlib import Path

import pytest

from code_typer.file_handler import EXTENSION_LANGUAGE_MAP, FileHandler, FileInfo


class TestFileHandler:
    """Test suite for FileHandler class."""

    def test_single_python_file(self, tmp_path):
        """Test loading a single Python file."""
        py_file = tmp_path / "test.py"
        py_file.write_text("def hello():\n    print('Hello')\n")

        handler = FileHandler(py_file)

        assert handler.total_files == 1
        files = list(handler.iterate_files())
        assert len(files) == 1
        assert files[0].language == "python"
        assert "def hello" in files[0].content

    def test_single_sql_file(self, tmp_path):
        """Test loading a single SQL file."""
        sql_file = tmp_path / "query.sql"
        sql_file.write_text("SELECT * FROM users WHERE active = 1;")

        handler = FileHandler(sql_file)

        assert handler.total_files == 1
        files = list(handler.iterate_files())
        assert files[0].language == "sql"
        assert "SELECT" in files[0].content

    def test_directory_recursive(self, tmp_path):
        """Test loading files from a directory recursively."""
        # Create directory structure
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("# main\n")
        (tmp_path / "src" / "utils.py").write_text("# utils\n")
        (tmp_path / "tests").mkdir()
        (tmp_path / "tests" / "test_main.py").write_text("# test\n")

        handler = FileHandler(tmp_path)

        assert handler.total_files == 3

    def test_skip_hidden_directories(self, tmp_path):
        """Test that hidden directories are skipped."""
        (tmp_path / ".git").mkdir()
        (tmp_path / ".git" / "config.py").write_text("# git config\n")
        (tmp_path / "main.py").write_text("# main\n")

        handler = FileHandler(tmp_path)

        assert handler.total_files == 1

    def test_skip_pycache(self, tmp_path):
        """Test that __pycache__ is skipped."""
        (tmp_path / "__pycache__").mkdir()
        (tmp_path / "__pycache__" / "module.cpython-39.pyc").write_bytes(b"bytecode")
        (tmp_path / "module.py").write_text("# module\n")

        handler = FileHandler(tmp_path)

        assert handler.total_files == 1

    def test_skip_node_modules(self, tmp_path):
        """Test that node_modules is skipped."""
        (tmp_path / "node_modules").mkdir()
        (tmp_path / "node_modules" / "package").mkdir()
        (tmp_path / "node_modules" / "package" / "index.js").write_text("// js\n")
        (tmp_path / "app.py").write_text("# app\n")

        handler = FileHandler(tmp_path)

        assert handler.total_files == 1

    def test_has_more_files(self, tmp_path):
        """Test has_more_files method."""
        (tmp_path / "a.py").write_text("# a\n")
        (tmp_path / "b.py").write_text("# b\n")

        handler = FileHandler(tmp_path)

        files_iter = handler.iterate_files()
        _ = next(files_iter)
        assert handler.has_more_files() is True

        _ = next(files_iter)
        assert handler.has_more_files() is False

    def test_current_file_number(self, tmp_path):
        """Test current_file_number property."""
        (tmp_path / "a.py").write_text("# a\n")
        (tmp_path / "b.py").write_text("# b\n")

        handler = FileHandler(tmp_path)

        for i, _ in enumerate(handler.iterate_files(), 1):
            assert handler.current_file_number == i

    def test_encoding_handling(self, tmp_path):
        """Test handling of different file encodings."""
        # UTF-8 with special characters
        utf8_file = tmp_path / "utf8.py"
        utf8_file.write_text("# café résumé\n", encoding="utf-8")

        handler = FileHandler(utf8_file)
        files = list(handler.iterate_files())

        assert "café" in files[0].content

    def test_nonexistent_path_raises(self, tmp_path):
        """Test that nonexistent path raises ValueError."""
        with pytest.raises(ValueError, match="does not exist"):
            FileHandler(tmp_path / "nonexistent.py")

    def test_empty_directory(self, tmp_path):
        """Test handling of empty directory."""
        handler = FileHandler(tmp_path)
        assert handler.total_files == 0

    def test_only_unsupported_files(self, tmp_path):
        """Test directory with only unsupported file types."""
        (tmp_path / "readme.txt").write_text("readme")
        (tmp_path / "image.png").write_bytes(b"PNG data")

        handler = FileHandler(tmp_path)
        assert handler.total_files == 0


class TestFileInfo:
    """Test suite for FileInfo dataclass."""

    def test_file_info_creation(self):
        """Test FileInfo creation."""
        info = FileInfo(
            path=Path("/test/file.py"), content="# test\n", language="python"
        )

        assert info.path == Path("/test/file.py")
        assert info.content == "# test\n"
        assert info.language == "python"

    def test_relative_path_property(self):
        """Test relative_path property."""
        info = FileInfo(
            path=Path("/home/user/project/main.py"), content="", language="python"
        )

        assert info.relative_path == "/home/user/project/main.py"


class TestExtensionMapping:
    """Test language detection from file extensions."""

    def test_python_extensions(self):
        """Test Python file extension mapping."""
        assert EXTENSION_LANGUAGE_MAP[".py"] == "python"
        assert EXTENSION_LANGUAGE_MAP[".pyx"] == "python"
        assert EXTENSION_LANGUAGE_MAP[".pxd"] == "python"

    def test_sql_extension(self):
        """Test SQL file extension mapping."""
        assert EXTENSION_LANGUAGE_MAP[".sql"] == "sql"

    def test_common_extensions(self):
        """Test common file extension mappings."""
        assert EXTENSION_LANGUAGE_MAP[".js"] == "javascript"
        assert EXTENSION_LANGUAGE_MAP[".ts"] == "typescript"
        assert EXTENSION_LANGUAGE_MAP[".go"] == "go"
        assert EXTENSION_LANGUAGE_MAP[".rs"] == "rust"
