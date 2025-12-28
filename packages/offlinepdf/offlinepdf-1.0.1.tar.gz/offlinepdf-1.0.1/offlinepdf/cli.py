"""Command-line interface for OfflinePDF using Typer."""

import sys
from pathlib import Path
from typing import List

import typer
from rich.console import Console

from offlinepdf import __version__
from offlinepdf import lock as lock_module
from offlinepdf import compress as compress_module
from offlinepdf import docx2pdf as docx2pdf_module
from offlinepdf import image2pdf as image2pdf_module
from offlinepdf import merge as merge_module
from offlinepdf import pdf2docx as pdf2docx_module
from offlinepdf import unlock as unlock_module
from offlinepdf.utils import print_error, print_info

app = typer.Typer(
    name="offlinepdf",
    help="Privacy-first CLI tool for offline PDF processing",
    add_completion=False,
)
console = Console()


def version_callback(value: bool) -> None:
    """Print version information and exit."""
    if value:
        console.print(f"OfflinePDF version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
) -> None:
    """
    OfflinePDF - Privacy-first PDF processing tool.
    
    All processing happens locally on your machine with no network access.
    """
    pass


@app.command()
def unlock(
    input_pdf: Path = typer.Argument(..., help="Path to PDF file"),
    password: str = typer.Option(..., "--password", "-p", help="Password required to decrypt the password-protected PDF"),
    output: Path = typer.Option(None, "--output", "-o", help="Output file path (default: input_unlocked.pdf)"),
) -> None:
    """
    Remove password protection from a PDF file.
    
    Creates a new file with "_unlocked" appended to the filename if output is not specified.
    Password is required to decrypt password-protected PDFs.
    
    Example:
        offlinepdf unlock input.pdf --password mypassword
        # Creates: input_unlocked.pdf
        offlinepdf unlock input.pdf --password mypassword -o output.pdf
        # Creates: output.pdf
    """
    try:
        unlock_module.unlock_pdf(input_pdf, password, output)
    except Exception as e:
        print_error(str(e))
        sys.exit(1)


@app.command()
def lock(
    input_pdf: Path = typer.Argument(..., help="Path to PDF file"),
    password: str = typer.Option(..., "--password", "-p", help="Password to lock the PDF with"),
    output: Path = typer.Option(None, "--output", "-o", help="Output file path (default: input_locked.pdf)"),
) -> None:
    """
    Lock a PDF file with password protection.
    
    Creates a new file with "_locked" appended to the filename if output is not specified.
    
    Example:
        offlinepdf lock input.pdf --password mypassword
        # Creates: input_locked.pdf
        offlinepdf lock input.pdf --password mypassword -o locked.pdf
        # Creates: locked.pdf
    """
    try:
        lock_module.lock_pdf(input_pdf, password, output)
    except Exception as e:
        print_error(str(e))
        sys.exit(1)


@app.command()
def compress(
    input_pdf: Path = typer.Argument(..., help="Path to PDF file"),
    output: Path = typer.Option(None, "--output", "-o", help="Output file path (default: input_compressed.pdf)"),
) -> None:
    """
    Compress a PDF file to reduce its size.
    
    Creates a new file with "_compressed" appended to the filename if output is not specified.
    
    Example:
        offlinepdf compress document.pdf
        # Creates: document_compressed.pdf
        offlinepdf compress document.pdf -o compressed.pdf
        # Creates: compressed.pdf
    """
    try:
        compress_module.compress_pdf(input_pdf, output)
    except Exception as e:
        print_error(str(e))
        sys.exit(1)


@app.command()
def merge(
    input_pdfs: List[Path] = typer.Argument(..., help="PDF files to merge"),
    output: Path = typer.Option(None, "--output", "-o", help="Output file path (default: first_input_merged.pdf)"),
) -> None:
    """
    Merge multiple PDF files into one.
    
    Creates a new file with "_merged" appended to the filename based on the first input file if output is not specified.
    
    Example:
        offlinepdf merge a.pdf b.pdf c.pdf
        # Creates: a_merged.pdf
        offlinepdf merge a.pdf b.pdf c.pdf -o merged.pdf
        # Creates: merged.pdf
    """
    try:
        merge_module.merge_pdfs(input_pdfs, output)
    except Exception as e:
        print_error(str(e))
        sys.exit(1)


@app.command()
def pdf2docx(
    input_pdf: Path = typer.Argument(..., help="PDF file to convert"),
    output: Path = typer.Option(None, "--output", "-o", help="Output file path (default: input_docx.docx)"),
) -> None:
    """
    Convert a PDF file to DOCX format.
    
    Creates a new file with "_docx" appended to the filename if output is not specified.
    
    Example:
        offlinepdf pdf2docx input.pdf
        # Creates: input_docx.docx
        offlinepdf pdf2docx input.pdf -o output.docx
        # Creates: output.docx
    """
    try:
        pdf2docx_module.pdf_to_docx(input_pdf, output)
    except Exception as e:
        print_error(str(e))
        sys.exit(1)


@app.command()
def docx2pdf(
    input_docx: Path = typer.Argument(..., help="DOCX file to convert"),
    output: Path = typer.Option(None, "--output", "-o", help="Output file path (default: input_pdf.pdf)"),
) -> None:
    """
    Convert a DOCX file to PDF format.
    
    Creates a new file with "_pdf" appended to the filename if output is not specified.
    
    Example:
        offlinepdf docx2pdf document.docx
        # Creates: document_pdf.pdf
        offlinepdf docx2pdf document.docx -o output.pdf
        # Creates: output.pdf
    """
    try:
        docx2pdf_module.docx_to_pdf(input_docx, output)
    except Exception as e:
        print_error(str(e))
        sys.exit(1)


@app.command()
def image2pdf(
    input_image: Path = typer.Argument(..., help="Image file to convert"),
    output: Path = typer.Option(None, "--output", "-o", help="Output file path (default: input_pdf.pdf)"),
) -> None:
    """
    Convert an image file to PDF format.
    
    Creates a new file with "_pdf" appended to the filename if output is not specified.
    Supports: JPG, PNG, BMP, GIF, TIFF, WEBP
    
    Example:
        offlinepdf image2pdf image.jpg
        # Creates: image_pdf.pdf
        offlinepdf image2pdf image.jpg -o output.pdf
        # Creates: output.pdf
    """
    try:
        image2pdf_module.image_to_pdf(input_image, output)
    except Exception as e:
        print_error(str(e))
        sys.exit(1)


# Add a command that accepts multiple images
@app.command(name="images2pdf")
def images2pdf(
    input_images: List[Path] = typer.Argument(..., help="Image files to convert"),
    output: Path = typer.Option(None, "--output", "-o", help="Output file path (default: first_input_merged_pdf.pdf)"),
) -> None:
    """
    Convert multiple image files into a single PDF.
    
    Creates a new file with "_merged_pdf" appended to the filename based on the first input file if output is not specified.
    Supports: JPG, PNG, BMP, GIF, TIFF, WEBP
    
    Example:
        offlinepdf images2pdf img1.jpg img2.png img3.jpg
        # Creates: img1_merged_pdf.pdf
        offlinepdf images2pdf img1.jpg img2.png img3.jpg -o merged.pdf
        # Creates: merged.pdf
    """
    try:
        image2pdf.images_to_pdf(input_images, output)
    except Exception as e:
        print_error(str(e))
        sys.exit(1)


if __name__ == "__main__":
    app()

