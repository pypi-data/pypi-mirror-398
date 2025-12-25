# airun-hwp

AI-powered HWP/HWPX document processing library for Hamonize

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![PyPI Version](https://img.shields.io/pypi/v/airun-hwp.svg)](https://pypi.org/project/airun-hwp/)

## Features

- **HWPX Parsing**: Parse HWPX files with full document structure preservation
- **HWP Text Extraction**: Extract plain text from HWP files (structure not preserved)
- **Ordered Content Extraction**: Maintain original document flow with mixed content types (HWPX only)
- **Image Extraction**: Extract and save all images from documents
- **Table Processing**: Extract tables with proper formatting (HWPX only)
- **Markdown Conversion**: Convert documents to well-structured Markdown
- **PDF Export**: Generate PDF files with embedded images (included by default)
- **CLI Tool**: Easy-to-use command-line interface

## Installation

```bash
pip install airun-hwp
```

Note: PDF export functionality is included by default.

### Development Installation

```bash
git clone https://github.com/chaeya/airun-hwp.git
cd airun-hwp
pip install -e ".[dev]"
```

## Quick Start

### Command Line Interface

```bash
# Convert to Markdown
airun-hwp convert document.hwpx --format markdown

# Convert to PDF
airun-hwp convert document.hwpx --format pdf --output ./results

# Process to both formats
airun-hwp process document.hwpx
```

### Python API

```python
from airun_hwp.reader.hwpx_reader_ordered import HWPXReaderOrdered
from airun_hwp.reader.hwpx_to_markdown import extract_text_from_file

# Parse HWPX file (full structure preserved)
reader = HWPXReaderOrdered()
document = reader.parse("document.hwpx")

# Extract text
text = document.get_all_text()
print(f"Total text length: {len(text)} characters")

# Extract images
images = document.extract_images("./output/images")
print(f"Extracted {len(images)} images")

# Convert to Markdown with tables
markdown_content = document.to_markdown_ordered(
    include_metadata=True,
    images_dir="./output/images"
)

# Save Markdown
with open("document.md", "w", encoding="utf-8") as f:
    f.write(markdown_content)

# For HWP files (plain text only)
hwp_text = extract_text_from_file("document.hwp")
print(f"HWP text (tables not preserved): {len(hwp_text)} characters")
```

## Advanced Usage

### PDF Generation with Custom Styling

```python
import markdown
import weasyprint
from airun_hwp.reader.hwpx_reader_ordered import HWPXReaderOrdered

# Parse document
reader = HWPXReaderOrdered()
document = reader.parse("document.hwpx")

# Extract images
document.extract_images("./output/images")

# Get Markdown content
md_content = document.to_markdown_ordered(
    include_metadata=True,
    images_dir="./output/images"
)

# Convert to HTML
html = markdown.markdown(md_content, extensions=['tables', 'fenced_code'])

# Add custom CSS
css = """
<style>
    body { font-family: 'Malgun Gothic', Arial, sans-serif; }
    img { max-width: 100%; height: auto; }
    table { border-collapse: collapse; width: 100%; }
    th, td { border: 1px solid #333; padding: 8px; }
</style>
"""

# Generate PDF
pdf = weasyprint.HTML(string=css + html).write_pdf("document.pdf")
```

## Document Structure

The library processes HWPX documents using a token-stream approach that preserves the original document order:

- **Text Runs**: Consecutive text segments
- **Images**: Embedded images with proper positioning
- **Tables**: Structured table data
- **Paragraph Breaks**: Logical document divisions
- **Page Breaks**: Document pagination

## CLI Commands

### Convert Command

Convert HWPX files to different formats:

```bash
airun-hwp convert <input_file> [options]

Options:
  --format {markdown,md,pdf}  Output format (default: markdown)
  --output, -o PATH           Output directory (default: ./output)
```

### Process Command

Process document to multiple formats:

```bash
airun-hwp process <input_file> [options]

Options:
  --output, -o PATH           Output directory (default: ./output)
```

## HWP vs HWPX: Important Differences

This library handles HWP and HWPX files differently due to their fundamental format differences:

### HWPX Files (Recommended)
- **Format**: XML-based, open standard
- **Structure**: Preserves full document structure
- **Tables**: ✅ Extracted with proper formatting
- **Images**: ✅ Extracted with positioning
- **Layout**: Maintains original document flow

### HWP Files (Limited Support)
- **Format**: Binary, proprietary format
- **Structure**: Only plain text extraction available
- **Tables**: ❌ Not preserved (extracted as plain text only)
- **Images**: ❌ Cannot preserve original position/sequence
- **Layout**: Original structure and order lost

### Recommendation
For best results, use HWPX files. If you have HWP files:
1. Convert HWP to HWPX in Hanword (한글) before processing
2. Or use for plain text extraction only

## Output Structure

When processing a document named `document.hwpx`:

```
output/
└── document/
    ├── images/
    │   ├── image1.png
    │   ├── image2.png
    │   └── ...
    ├── document.md
    └── document.pdf
```

## Dependencies

- `pypandoc-hwpx>=0.1.0`: HWPX file format support
- `PyYAML>=6.0`: YAML configuration parsing
- `Pillow>=10.0.0`: Image processing
- `weasyprint>=60.0`: HTML to PDF conversion (included)
- `markdown>=3.5.0`: Markdown processing (included)

## Development

### Running Tests

```bash
pytest
```

### Code Coverage

```bash
pytest --cov=airun_hwp
```

### Code Formatting

```bash
black airun_hwp/
ruff check airun_hwp/
```

### Type Checking

```bash
mypy airun_hwp/
```

## Building for Distribution

```bash
# Build source and wheel distributions
python -m build

# Build with twine
twine build dist/
```

## Publishing to PyPI

```bash
# Upload to Test PyPI
twine upload --repository testpypi dist/*

# Upload to PyPI
twine upload dist/*
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Support

- 📧 Email: chaeya@gmail.com (Kevin Kim)
- 🐛 Issues: [GitHub Issues](https://github.com/hamonize/airun-hwp/issues)
- 📖 Documentation: [GitHub Wiki](https://github.com/hamonize/airun-hwp/wiki)

## Changelog

### Version 0.2.5
- Fixed `get_all_text()` method to properly extract text from token stream
- Improved text extraction to handle both tokens and paragraphs
- Added deduplication to prevent duplicate text extraction
- Updated documentation to clarify HWP vs HWPX limitations

### Version 0.2.0
- HWPX parsing support
- Markdown conversion
- PDF export functionality
- CLI tool
- Image extraction
- Table processing

### Version 0.1.0
- Initial release

---

**Made with ❤️ for the Hamonize project**