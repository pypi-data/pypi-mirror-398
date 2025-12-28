"""Module for locking PDF files with password protection."""

from pathlib import Path
from typing import Optional

import pikepdf

from offlinepdf.utils import (
    ensure_pdf_extension,
    print_error,
    print_success,
    validate_input_file,
)


def lock_pdf(
    input_path: Path,
    password: str,
    output_path: Optional[Path] = None,
) -> None:
    """
    Lock a PDF file with password protection.
    
    Creates a new file with "_locked" appended to the filename if output_path is not provided.
    For example: "document.pdf" -> "document_locked.pdf"
    
    Args:
        input_path: Path to the PDF file
        password: Password to lock the PDF with
        output_path: Optional path for the output file. If not provided, uses default naming.
    
    Raises:
        FileNotFoundError: If input file doesn't exist
        pikepdf.PdfError: If PDF processing fails
    """
    validate_input_file(input_path, [".pdf"])
    
    if not password:
        raise ValueError("Password cannot be empty")
    
    # Generate output path if not provided
    if output_path is None:
        input_path_obj = Path(input_path)
        output_path = input_path_obj.parent / f"{input_path_obj.stem}_locked{input_path_obj.suffix}"
    else:
        output_path = ensure_pdf_extension(Path(output_path))
    
    try:
        # Open the PDF (may need password if already protected)
        try:
            pdf = pikepdf.open(input_path, allow_overwriting_input=True)
        except pikepdf.PasswordError:
            print_error("PDF is already password-protected. Please unlock it first.")
            raise
        
        # Save with password protection
        # Using AES-256 encryption (strongest available)
        pdf.save(
            output_path,
            encryption=pikepdf.Encryption(
                owner=password,  # Owner password (can be different from user password)
                user=password,   # User password (required to open)
                R=6,            # Revision 6 = AES-256 encryption
                allow=pikepdf.Permissions(
                    extract=True,  # Allow text extraction
                    print_lowres=True,  # Allow low-res printing
                    print_highres=True,  # Allow high-res printing
                    modify_annotation=True,  # Allow annotation modification
                    modify_form=True,  # Allow form modification
                    modify_other=True,  # Allow other modifications
                ),
            ),
        )
        
        print_success(f"✓ Successfully locked PDF: {output_path}")
    
    except pikepdf.PdfError as e:
        print_error(f"Failed to lock PDF: {str(e)}")
        raise
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        raise

