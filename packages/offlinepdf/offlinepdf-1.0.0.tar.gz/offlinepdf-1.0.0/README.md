# OfflinePDF

**Privacy-first CLI tool for offline PDF processing**

OfflinePDF is a command-line utility that provides common PDF manipulation tools (similar to iLovePDF) but runs **100% locally on your machine** with **zero network access**. All processing happens offline, ensuring your documents never leave your computer.

## 🔒 Privacy Guarantee

- ✅ **No internet access** - All processing is local-only
- ✅ **No telemetry or analytics** - We don't track anything
- ✅ **No file uploads** - Files are never sent anywhere
- ✅ **No data storage** - Files are processed and immediately discarded
- ✅ **Open source** - You can audit the code yourself

## ✨ Features

- **Unlock PDFs** - Remove password protection from PDF files
- **Lock PDFs** - Add password protection to PDF files
- **Compress PDFs** - Reduce PDF file size
- **Merge PDFs** - Combine multiple PDF files into one
- **PDF to DOCX** - Convert PDF documents to Word format
- **DOCX to PDF** - Convert Word documents to PDF format
- **Image to PDF** - Convert images (JPG, PNG, etc.) to PDF format

## 📦 Installation

### Using pip (recommended)

```bash
pip install offlinepdf
```

### Using pipx (isolated environment)

```bash
pipx install offlinepdf
```

After installation, the `offlinepdf` command will be available globally from anywhere in your terminal.

## 🚀 Usage

### Unlock a PDF

```bash
offlinepdf unlock input.pdf --password mypassword
```

### Merge multiple PDFs

```bash
offlinepdf merge a.pdf b.pdf c.pdf -o merged.pdf
```

### Convert PDF to DOCX

```bash
offlinepdf pdf2docx input.pdf output.docx
```

### Convert image to PDF

```bash
# Single image
offlinepdf image2pdf image.jpg output.pdf

# Multiple images (merged into one PDF)
offlinepdf images2pdf img1.jpg img2.png img3.jpg -o combined.pdf
```

## 📋 Command Reference

### `unlock`
Remove password protection from a PDF.

```bash
offlinepdf unlock <input.pdf> --password <password> [--output <output.pdf>]
```

### `merge`
Merge multiple PDF files into one.

```bash
offlinepdf merge <pdf1> <pdf2> ... -o <output.pdf>
```

### `pdf2docx`
Convert a PDF file to DOCX format.

```bash
offlinepdf pdf2docx <input.pdf> [--output <output.docx>]
```

### `image2pdf`
Convert image file(s) to PDF format.

```bash
# Single image
offlinepdf image2pdf <image.jpg> [--output <output.pdf>]

# Multiple images
offlinepdf images2pdf <img1> <img2> ... -o <output.pdf> [--overwrite]
```

Supported image formats: JPG, JPEG, PNG, BMP, GIF, TIFF, WEBP

## 🛠️ Requirements

- Python 3.10 or higher
- All dependencies are automatically installed with the package

## 🔧 Development

If you want to contribute or modify the code:

```bash
# Clone the repository
git clone https://github.com/yourusername/offlinepdf.git
cd offlinepdf

# Install in development mode
pip install -e .

# Run tests (if available)
pytest
```

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## ⚠️ Limitations

- **PDF to DOCX conversion**: Quality depends heavily on document structure. Complex layouts (multi-column, tables, icons, vector graphics) may not convert correctly. This is a known limitation of open-source PDF parsers. The tool will automatically try LibreOffice as a fallback if available.
- Large files may take longer to process
- DOCX to PDF conversion requires Microsoft Word (macOS/Windows) or LibreOffice (Linux) to be installed

## 🐛 Troubleshooting

**Command not found after installation:**
- Make sure your Python `bin` directory is in your PATH
- Try using `pipx` instead of `pip` for isolated installation
- Restart your terminal after installation

**Permission errors:**
- Make sure you have read access to input files
- Make sure you have write access to the output directory

**Conversion errors:**
- Verify that input files are not corrupted
- Check that file formats are supported
- Ensure sufficient disk space is available

## 📚 Dependencies

- [Typer](https://typer.tiangolo.com/) - Modern CLI framework
- [Rich](https://rich.readthedocs.io/) - Beautiful terminal output
- [pikepdf](https://github.com/pikepdf/pikepdf) - PDF manipulation
- [pdf2docx](https://github.com/dothinking/pdf2docx) - PDF to DOCX conversion
- [Pillow](https://pillow.readthedocs.io/) - Image processing

---

**Made with ❤️ for privacy-conscious users**

