"""File and directory handling for code-typer."""

import os
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

# Mapping of file extensions to language names
EXTENSION_LANGUAGE_MAP = {
    ".py": "python",
    ".pyx": "python",
    ".pxd": "python",
    ".sql": "sql",
    ".js": "javascript",
    ".ts": "typescript",
    ".jsx": "javascript",
    ".tsx": "typescript",
    ".rs": "rust",
    ".go": "go",
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".hpp": "cpp",
    ".java": "java",
    ".rb": "ruby",
    ".sh": "shell",
    ".bash": "shell",
    ".zsh": "shell",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".json": "json",
    ".toml": "toml",
    ".md": "markdown",
    ".html": "html",
    ".css": "css",
}

# Files/directories to skip
SKIP_PATTERNS = {
    "__pycache__",
    ".git",
    ".svn",
    ".hg",
    "node_modules",
    ".venv",
    "venv",
    ".env",
    ".tox",
    ".pytest_cache",
    ".mypy_cache",
    "*.pyc",
    "*.pyo",
    "*.so",
    "*.egg-info",
    "dist",
    "build",
}


@dataclass
class FileInfo:
    """Information about a file to be typed."""

    path: Path
    content: str
    language: str

    @property
    def relative_path(self) -> str:
        """Get the path as a string for display."""
        return str(self.path)


class FileHandler:
    """Handles file and directory traversal for showcasing code."""

    def __init__(self, path: Path, encoding: str = "utf-8"):
        """Initialize the file handler.

        Args:
            path: Path to a file or directory
            encoding: File encoding to use when reading
        """
        self.path = path.resolve()
        self.encoding = encoding
        self._files: list[FileInfo] = []
        self._current_index = 0
        self._load_files()

    def _should_skip(self, path: Path) -> bool:
        """Check if a path should be skipped."""
        name = path.name

        # Check exact matches
        if name in SKIP_PATTERNS:
            return True

        # Check if it's a hidden file/dir (starts with .)
        if name.startswith(".") and name not in {"."}:
            return True

        # Check pattern matches for files
        if path.is_file():
            for pattern in SKIP_PATTERNS:
                if pattern.startswith("*") and name.endswith(pattern[1:]):
                    return True

        return False

    def _detect_language(self, path: Path) -> str:
        """Detect the programming language from file extension."""
        suffix = path.suffix.lower()
        return EXTENSION_LANGUAGE_MAP.get(suffix, "text")

    def _load_files(self) -> None:
        """Load all files to be showcased."""
        if self.path.is_file():
            self._load_single_file(self.path)
        elif self.path.is_dir():
            self._load_directory(self.path)
        else:
            raise ValueError(f"Path does not exist: {self.path}")

    def _load_single_file(self, path: Path) -> None:
        """Load a single file."""
        try:
            content = path.read_text(encoding=self.encoding)
            language = self._detect_language(path)
            self._files.append(FileInfo(path=path, content=content, language=language))
        except UnicodeDecodeError:
            # Try with latin-1 as fallback
            content = path.read_text(encoding="latin-1")
            language = self._detect_language(path)
            self._files.append(FileInfo(path=path, content=content, language=language))

    def _load_directory(self, directory: Path) -> None:
        """Recursively load all code files from a directory."""
        for root, dirs, files in os.walk(directory):
            root_path = Path(root)

            # Filter out directories to skip
            dirs[:] = [d for d in dirs if not self._should_skip(root_path / d)]
            dirs.sort()  # Ensure consistent ordering

            # Process files
            for filename in sorted(files):
                file_path = root_path / filename
                if not self._should_skip(file_path):
                    suffix = file_path.suffix.lower()
                    if suffix in EXTENSION_LANGUAGE_MAP:
                        self._load_single_file(file_path)

    def iterate_files(self) -> Iterator[FileInfo]:
        """Iterate over all files to be showcased."""
        for i, file_info in enumerate(self._files):
            self._current_index = i
            yield file_info

    def has_more_files(self) -> bool:
        """Check if there are more files after the current one."""
        return self._current_index < len(self._files) - 1

    @property
    def total_files(self) -> int:
        """Get the total number of files."""
        return len(self._files)

    @property
    def current_file_number(self) -> int:
        """Get the current file number (1-indexed)."""
        return self._current_index + 1
