"""Utility functions for file validation and error handling."""

from pathlib import Path
from typing import List, Optional

from rich.console import Console
from rich.text import Text

console = Console()


def validate_input_file(file_path: Path, extensions: Optional[List[str]] = None) -> None:
    """
    Validate that an input file exists and has the correct extension.
    
    Args:
        file_path: Path to the file to validate
        extensions: Optional list of allowed extensions (e.g., ['.pdf', '.jpg'])
    
    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the file extension is not allowed
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")
    
    if not file_path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")
    
    if extensions is not None:
        if file_path.suffix.lower() not in [ext.lower() for ext in extensions]:
            raise ValueError(
                f"Invalid file extension. Expected one of {extensions}, got {file_path.suffix}"
            )


def validate_output_file(file_path: Path, overwrite: bool = False) -> None:
    """
    Validate that an output file path is valid and handle existing files.
    
    Args:
        file_path: Path to the output file
        overwrite: Whether to allow overwriting existing files
    
    Raises:
        ValueError: If the file exists and overwrite is False, or if parent directory doesn't exist
    """
    if file_path.exists() and not overwrite:
        raise ValueError(
            f"Output file already exists: {file_path}. Use --overwrite to replace it."
        )
    
    parent_dir = file_path.parent
    if not parent_dir.exists():
        parent_dir.mkdir(parents=True, exist_ok=True)
    elif not parent_dir.is_dir():
        raise ValueError(f"Parent path is not a directory: {parent_dir}")


def print_success(message: str) -> None:
    """Print a success message with green styling."""
    console.print(Text(message, style="green bold"))


def print_error(message: str) -> None:
    """Print an error message with red styling."""
    console.print(Text(f"Error: {message}", style="red bold"))


def print_info(message: str) -> None:
    """Print an info message with blue styling."""
    console.print(Text(message, style="blue"))


def ensure_pdf_extension(file_path: Path) -> Path:
    """
    Ensure a file path has a .pdf extension.
    
    Args:
        file_path: Path to ensure has .pdf extension
    
    Returns:
        Path with .pdf extension
    """
    if file_path.suffix.lower() != ".pdf":
        return file_path.with_suffix(".pdf")
    return file_path

