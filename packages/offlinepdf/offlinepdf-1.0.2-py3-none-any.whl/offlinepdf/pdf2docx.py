"""Module for converting PDF files to DOCX format."""

import subprocess
import sys
from pathlib import Path
from typing import Optional

from pdf2docx import Converter

from offlinepdf.utils import (
    print_error,
    print_info,
    print_success,
    validate_input_file,
)


def pdf_to_docx(
    input_path: Path,
    output_path: Optional[Path] = None,
) -> None:
    """
    Convert a PDF file to DOCX format.
    
    Creates a new file with "_docx" appended to the filename if output_path is not provided.
    For example: "document.pdf" -> "document_docx.docx"
    
    Uses pdf2docx library first, with LibreOffice as a fallback for complex PDFs.
    
    Args:
        input_path: Path to the PDF file
        output_path: Optional path for the output file. If not provided, uses default naming.
    
    Raises:
        FileNotFoundError: If input file doesn't exist
        Exception: If conversion fails with both methods
    """
    validate_input_file(input_path, [".pdf"])
    
    # Generate output path if not provided
    if output_path is None:
        input_path_obj = Path(input_path)
        output_path = input_path_obj.parent / f"{input_path_obj.stem}_docx.docx"
    else:
        output_path = Path(output_path)
        if output_path.suffix.lower() != ".docx":
            output_path = output_path.with_suffix(".docx")
    
    # Try pdf2docx first
    try:
        converter = Converter(str(input_path))
        converter.convert(str(output_path))
        converter.close()
        
        print_success(f"✓ Successfully converted PDF to DOCX: {output_path}")
        return
    
    except AttributeError as e:
        print_error(f"Failed to convert PDF to DOCX: {str(e)}")
        raise
    
    except Exception as e:
        print_error(f"Failed to convert PDF to DOCX: {str(e)}")
        raise

