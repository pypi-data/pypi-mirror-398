"""Module for unlocking PDF files."""

from pathlib import Path
from typing import Optional

import pikepdf

from offlinepdf.utils import (
    ensure_pdf_extension,
    print_error,
    print_success,
    validate_input_file,
)


def unlock_pdf(
    input_path: Path,
    password: str,
    output_path: Optional[Path] = None,
) -> None:
    """
    Remove password protection from a PDF file.
    
    Creates a new file with "_unlocked" appended to the filename if output_path is not provided.
    For example: "document.pdf" -> "document_unlocked.pdf"
    
    Args:
        input_path: Path to the PDF file
        password: Password required to decrypt the password-protected PDF
        output_path: Optional path for the output file. If not provided, uses default naming.
    
    Raises:
        FileNotFoundError: If input file doesn't exist
        pikepdf.PasswordError: If PDF is password-protected and password is incorrect
        pikepdf.PdfError: If PDF processing fails
    """
    validate_input_file(input_path, [".pdf"])
    
    # Generate output path if not provided
    if output_path is None:
        input_path_obj = Path(input_path)
        output_path = input_path_obj.parent / f"{input_path_obj.stem}_unlocked{input_path_obj.suffix}"
    else:
        output_path = ensure_pdf_extension(Path(output_path))
    
    try:
        # Open PDF with password to decrypt it
        pdf = pikepdf.open(input_path, password=password, allow_overwriting_input=True)
        # Save without password protection (saving automatically removes encryption)
        pdf.save(output_path)
        print_success(f"✓ Successfully unlocked PDF: {output_path}")
    
    except pikepdf.PasswordError:
        print_error("Incorrect password provided")
        raise
    except pikepdf.PdfError as e:
        print_error(f"Failed to process PDF: {str(e)}")
        raise
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        raise