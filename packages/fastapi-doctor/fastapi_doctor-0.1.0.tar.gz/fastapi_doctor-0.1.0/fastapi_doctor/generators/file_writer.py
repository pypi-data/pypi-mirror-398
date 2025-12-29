"""
File writing utilities for project generation.
"""

import os
from pathlib import Path


class FileWriter:
    """Utility class for writing files and creating directories."""

    def __init__(self, base_path: Path) -> None:
        """
        Initialize the FileWriter with a base path.

        Args:
            base_path: The root directory for all file operations.
        """
        self.base_path = base_path

    def write(self, relative_path: str, content: str) -> None:
        """
        Write content to a file at the specified relative path.

        Args:
            relative_path: Path relative to base_path.
            content: Content to write to the file.
        """
        file_path = self.base_path / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")

    def create_directories(self, directories: list[str]) -> None:
        """
        Create multiple directories relative to the base path.

        Args:
            directories: List of directory paths to create.
        """
        for directory in directories:
            (self.base_path / directory).mkdir(parents=True, exist_ok=True)

    def delete(self, relative_path: str) -> None:
        """
        Delete a file at the specified relative path.

        Args:
            relative_path: Path relative to base_path.
        """
        file_path = self.base_path / relative_path
        if file_path.exists():
            os.unlink(file_path)

