"""Module for converting DOCX files to PDF format."""

from pathlib import Path
from typing import Optional

try:
    from docx2pdf import convert
except ImportError:
    # Fallback if docx2pdf is not available
    convert = None

from offlinepdf.utils import (
    ensure_pdf_extension,
    print_error,
    print_success,
    validate_input_file,
)


def docx_to_pdf(
    input_path: Path,
    output_path: Optional[Path] = None,
) -> None:
    """
    Convert a DOCX file to PDF format.
    
    Creates a new file with "_pdf" appended to the filename if output_path is not provided.
    For example: "document.docx" -> "document_pdf.pdf"
    
    Args:
        input_path: Path to the DOCX file
        output_path: Optional path for the output file. If not provided, uses default naming.
    
    Raises:
        FileNotFoundError: If input file doesn't exist
        ImportError: If docx2pdf library is not installed
        Exception: If conversion fails
    """
    validate_input_file(input_path, [".docx"])
    
    if convert is None:
        raise ImportError(
            "docx2pdf library is required for DOCX to PDF conversion. "
            "Install it with: pip install docx2pdf"
        )
    
    # Generate output path if not provided
    if output_path is None:
        input_path_obj = Path(input_path)
        output_path = input_path_obj.parent / f"{input_path_obj.stem}_pdf.pdf"
    else:
        output_path = ensure_pdf_extension(Path(output_path))
    
    try:
        # Convert DOCX to PDF
        convert(str(input_path), str(output_path))
        
        print_success(f"✓ Successfully converted DOCX to PDF: {output_path}")
    
    except Exception as e:
        print_error(f"Failed to convert DOCX to PDF: {str(e)}")
        raise

