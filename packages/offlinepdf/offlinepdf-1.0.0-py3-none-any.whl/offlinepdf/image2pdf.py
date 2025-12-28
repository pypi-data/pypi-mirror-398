"""Module for converting image files to PDF format."""

from pathlib import Path
from typing import List, Optional, Sequence

from PIL import Image

from offlinepdf.utils import (
    ensure_pdf_extension,
    print_error,
    print_success,
    validate_input_file,
)

# Supported image formats
SUPPORTED_IMAGE_FORMATS = [".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp"]


def image_to_pdf(
    input_path: Path,
    output_path: Optional[Path] = None,
) -> None:
    """
    Convert a single image file to PDF format.
    
    Creates a new file with "_pdf" appended to the filename if output_path is not provided.
    For example: "image.jpg" -> "image_pdf.pdf"
    
    Args:
        input_path: Path to the image file
        output_path: Optional path for the output file. If not provided, uses default naming.
    
    Raises:
        FileNotFoundError: If input file doesn't exist
        ValueError: If image format is not supported
        Exception: If conversion fails
    """
    validate_input_file(input_path, SUPPORTED_IMAGE_FORMATS)
    
    # Generate output path if not provided
    if output_path is None:
        input_path_obj = Path(input_path)
        output_path = input_path_obj.parent / f"{input_path_obj.stem}_pdf.pdf"
    else:
        output_path = ensure_pdf_extension(Path(output_path))
    
    try:
        # Open and convert image to PDF
        with Image.open(input_path) as img:
            # Convert RGBA to RGB if necessary (PDF doesn't support transparency)
            if img.mode == "RGBA":
                rgb_img = Image.new("RGB", img.size, (255, 255, 255))
                rgb_img.paste(img, mask=img.split()[3])  # Use alpha channel as mask
                img = rgb_img
            elif img.mode not in ("RGB", "L"):
                img = img.convert("RGB")
            
            img.save(output_path, "PDF", resolution=100.0)
        
        print_success(f"✓ Successfully converted image to PDF: {output_path}")
    
    except Exception as e:
        print_error(f"Failed to convert image to PDF: {str(e)}")
        raise


def images_to_pdf(
    input_paths: Sequence[Path],
    output_path: Optional[Path] = None,
) -> None:
    """
    Convert multiple image files into a single PDF.
    
    Creates a new file with "_merged_pdf" appended to the filename based on the first input file if output_path is not provided.
    For example: merging "img1.jpg" and "img2.png" -> "img1_merged_pdf.pdf"
    
    Args:
        input_paths: Sequence of paths to image files
        output_path: Optional path for the output file. If not provided, uses default naming.
    
    Raises:
        FileNotFoundError: If any input file doesn't exist
        ValueError: If no input files provided or format not supported
        Exception: If conversion fails
    """
    if not input_paths:
        raise ValueError("At least one input image file is required")
    
    # Validate all input files
    for input_path in input_paths:
        validate_input_file(input_path, SUPPORTED_IMAGE_FORMATS)
    
    # Generate output path if not provided
    if output_path is None:
        first_input = Path(input_paths[0])
        output_path = first_input.parent / f"{first_input.stem}_merged_pdf.pdf"
    else:
        output_path = ensure_pdf_extension(Path(output_path))
    
    try:
        images: List[Image.Image] = []
        
        # Load all images
        for input_path in input_paths:
            img = Image.open(input_path)
            
            # Convert RGBA to RGB if necessary
            if img.mode == "RGBA":
                rgb_img = Image.new("RGB", img.size, (255, 255, 255))
                rgb_img.paste(img, mask=img.split()[3])
                images.append(rgb_img)
            elif img.mode not in ("RGB", "L"):
                images.append(img.convert("RGB"))
            else:
                images.append(img)
        
        # Save all images as a single PDF
        if images:
            images[0].save(
                output_path,
                "PDF",
                resolution=100.0,
                save_all=True,
                append_images=images[1:] if len(images) > 1 else [],
            )
            
            # Close all images
            for img in images:
                img.close()
        
        print_success(
            f"✓ Successfully converted {len(input_paths)} image(s) to PDF: {output_path}"
        )
    
    except Exception as e:
        print_error(f"Failed to convert images to PDF: {str(e)}")
        raise

