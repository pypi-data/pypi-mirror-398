"""Module for compressing PDF files."""

from pathlib import Path
from typing import Optional

import pikepdf

from offlinepdf.utils import (
    ensure_pdf_extension,
    print_error,
    print_success,
    validate_input_file,
)


def compress_pdf(
    input_path: Path,
    output_path: Optional[Path] = None,
) -> None:
    """
    Compress a PDF file to reduce its size.
    
    Creates a new file with "_compressed" appended to the filename if output_path is not provided.
    For example: "document.pdf" -> "document_compressed.pdf"
    
    Args:
        input_path: Path to the PDF file
        output_path: Optional path for the output file. If not provided, uses default naming.
    
    Raises:
        FileNotFoundError: If input file doesn't exist
        pikepdf.PdfError: If PDF processing fails
    """
    validate_input_file(input_path, [".pdf"])
    
    # Generate output path if not provided
    if output_path is None:
        input_path_obj = Path(input_path)
        output_path = input_path_obj.parent / f"{input_path_obj.stem}_compressed{input_path_obj.suffix}"
    else:
        output_path = ensure_pdf_extension(Path(output_path))
    
    try:
        # Open the PDF
        pdf = pikepdf.open(input_path, allow_overwriting_input=True)
        
        # Compress by using object stream compression
        # This reduces file size by compressing the PDF's internal structure
        pdf.save(
            output_path,
            compress_streams=True,  # Compress content streams
            object_stream_mode=pikepdf.ObjectStreamMode.generate,  # Use object streams for compression
        )
        
        # Get file sizes for comparison
        input_size = input_path.stat().st_size
        output_size = output_path.stat().st_size
        reduction = ((input_size - output_size) / input_size) * 100 if input_size > 0 else 0
        
        print_success(
            f"✓ Successfully compressed PDF: {output_path} "
            f"({reduction:.1f}% size reduction)"
        )
    
    except pikepdf.PdfError as e:
        print_error(f"Failed to compress PDF: {str(e)}")
        raise
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        raise

