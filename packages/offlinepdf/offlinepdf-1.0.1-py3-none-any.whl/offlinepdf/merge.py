"""Module for merging multiple PDF files into one."""

from pathlib import Path
from typing import Optional, Sequence

import pikepdf

from offlinepdf.utils import (
    ensure_pdf_extension,
    print_error,
    print_success,
    validate_input_file,
)


def merge_pdfs(
    input_paths: Sequence[Path],
    output_path: Optional[Path] = None,
) -> None:
    """
    Merge multiple PDF files into a single PDF.
    
    Creates a new file with "_merged" appended to the filename based on the first input file if output_path is not provided.
    For example: merging "a.pdf" and "b.pdf" -> "a_merged.pdf"
    
    Args:
        input_paths: Sequence of paths to PDF files to merge
        output_path: Optional path for the output file. If not provided, uses default naming.
    
    Raises:
        FileNotFoundError: If any input file doesn't exist
        pikepdf.PdfError: If PDF processing fails
        ValueError: If no input files provided
    """
    if not input_paths:
        raise ValueError("At least one input PDF file is required")
    
    # Validate all input files
    for input_path in input_paths:
        validate_input_file(input_path, [".pdf"])
    
    # Generate output path if not provided
    if output_path is None:
        first_input = Path(input_paths[0])
        output_path = first_input.parent / f"{first_input.stem}_merged{first_input.suffix}"
    else:
        output_path = ensure_pdf_extension(Path(output_path))
    
    try:
        # Create a new PDF for merging
        merged_pdf = pikepdf.Pdf.new()
        
        # Append all pages from each input PDF
        for input_path in input_paths:
            with pikepdf.open(input_path) as pdf:
                merged_pdf.pages.extend(pdf.pages)
        
        # Save the merged PDF
        merged_pdf.save(output_path)
        
        print_success(
            f"✓ Successfully merged {len(input_paths)} PDF(s) into: {output_path}"
        )
    
    except pikepdf.PdfError as e:
        print_error(f"Failed to merge PDFs: {str(e)}")
        raise
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        raise

