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

### Using pipx (recommended for global installation)

**pipx** is the recommended way to install OfflinePDF globally. It installs the package in an isolated environment, preventing dependency conflicts with other Python packages.

#### Install pipx first

**macOS:**
```bash
brew install pipx
pipx ensurepath
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install pipx
pipx ensurepath
```

**Linux (Fedora/RHEL):**
```bash
sudo dnf install pipx
pipx ensurepath
```

**Windows:**
```powershell
# Using pip
python -m pip install --user pipx
python -m pipx ensurepath

# Or using winget
winget install pipx
```

**Alternative (all platforms):**
```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath
```

After installing pipx, restart your terminal or run:
```bash
source ~/.bashrc  # Linux/macOS
# or
source ~/.zshrc   # macOS with zsh
```

#### Install OfflinePDF with pipx

```bash
pipx install offlinepdf
```

After installation, the `offlinepdf` command will be available globally from anywhere in your terminal.

### Using pip (alternative)

If you prefer to use pip directly:

```bash
pip install offlinepdf
```

**Note:** Using pip may cause dependency conflicts with other Python packages. pipx is recommended for CLI tools.

## 🚀 Usage

### Unlock a PDF

```bash
offlinepdf unlock input.pdf --password mypassword
```

### Lock a PDF

```bash
offlinepdf lock input.pdf --password mypassword
```

### Compress a PDF

```bash
offlinepdf compress document.pdf
```

### Merge multiple PDFs

```bash
offlinepdf merge a.pdf b.pdf c.pdf -o merged.pdf
```

### Convert PDF to DOCX

```bash
offlinepdf pdf2docx input.pdf
# Creates: input_docx.docx

offlinepdf pdf2docx input.pdf -o output.docx
```

### Convert DOCX to PDF

```bash
offlinepdf docx2pdf document.docx
# Creates: document_pdf.pdf
```

### Convert image to PDF

```bash
# Single image
offlinepdf image2pdf image.jpg
# Creates: image_pdf.pdf

# Multiple images (merged into one PDF)
offlinepdf images2pdf img1.jpg img2.png img3.jpg -o combined.pdf
```

## 📋 Command Reference

### `unlock`
Remove password protection from a PDF.

```bash
offlinepdf unlock <input.pdf> --password <password> [--output <output.pdf>]
```

### `lock`
Add password protection to a PDF.

```bash
offlinepdf lock <input.pdf> --password <password> [--output <output.pdf>]
```

### `compress`
Compress a PDF file to reduce its size.

```bash
offlinepdf compress <input.pdf> [--output <output.pdf>]
```

### `merge`
Merge multiple PDF files into one.

```bash
offlinepdf merge <pdf1> <pdf2> ... [--output <output.pdf>]
```

### `pdf2docx`
Convert a PDF file to DOCX format.

```bash
offlinepdf pdf2docx <input.pdf> [--output <output.docx>]
```

### `docx2pdf`
Convert a DOCX file to PDF format.

```bash
offlinepdf docx2pdf <input.docx> [--output <output.pdf>]
```

### `image2pdf`
Convert image file(s) to PDF format.

```bash
# Single image
offlinepdf image2pdf <image.jpg> [--output <output.pdf>]

# Multiple images
offlinepdf images2pdf <img1> <img2> ... [--output <output.pdf>]
```

Supported image formats: JPG, JPEG, PNG, BMP, GIF, TIFF, WEBP

## 🛠️ Requirements

- Python 3.11 or higher
- pipx (recommended) or pip
- All dependencies are automatically installed with the package

## 🔧 Development

If you want to contribute or modify the code:

```bash
# Clone the repository
git clone https://github.com/Daniyal-Qureshi/offlinepdf.git
cd offlinepdf

# Install in development mode
pip install -e .

# Or using pipx for development
pipx install -e .


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
- If using pipx: Make sure you ran `pipx ensurepath` and restarted your terminal
- If using pip: Make sure your Python `bin` directory is in your PATH
- **Recommended:** Use `pipx` for global installation to avoid PATH issues
- Restart your terminal after installation

**pipx not found:**
- Install pipx using the instructions in the Installation section above
- After installing pipx, run `pipx ensurepath` to add it to your PATH
- Restart your terminal

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
- [docx2pdf](https://github.com/AlJohri/docx2pdf) - DOCX to PDF conversion
- [Pillow](https://pillow.readthedocs.io/) - Image processing

## 🔄 Updating

To update to the latest version:

```bash
# Using pipx (recommended)
pipx upgrade offlinepdf

# Using pip
pip install --upgrade offlinepdf
```

## 🗑️ Uninstalling

To uninstall:

```bash
# Using pipx
pipx uninstall offlinepdf

# Using pip
pip uninstall offlinepdf
```

---

**Made with ❤️ for privacy-conscious users**

