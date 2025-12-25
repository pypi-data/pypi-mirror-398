#!/usr/bin/env python3
"""
Command Line Interface for airun-hwp package
"""

import sys
import os
import argparse
from pathlib import Path

# Add project to path for development
if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from airun_hwp.reader.hwpx_reader_ordered import HWPXReaderOrdered


def process_hwpx_to_markdown(hwpx_path, output_dir=None):
    """
    Convert HWPX file to Markdown format

    Args:
        hwpx_path: Path to HWPX file
        output_dir: Output directory for results
    """
    hwpx_path = Path(hwpx_path)

    if not hwpx_path.exists():
        print(f"❌ Error: File not found - {hwpx_path}")
        return False

    # Setup output directory
    if output_dir is None:
        output_dir = Path.cwd() / "output"
    else:
        output_dir = Path(output_dir)

    doc_output_dir = output_dir / hwpx_path.stem
    doc_output_dir.mkdir(parents=True, exist_ok=True)

    print(f"🔄 Processing {hwpx_path.name}...")

    try:
        # Parse HWPX
        reader = HWPXReaderOrdered()
        document = reader.parse(str(hwpx_path))

        # Extract images
        images_dir = doc_output_dir / "images"
        images_dir.mkdir(exist_ok=True)
        extracted_images = document.extract_images(str(images_dir))

        # Convert to Markdown
        markdown_content = document.to_markdown_ordered(
            include_metadata=True,
            images_dir="images"  # Relative path
        )

        # Save Markdown file
        md_path = doc_output_dir / f"{hwpx_path.stem}.md"
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)

        print(f"✅ Conversion completed successfully!")
        print(f"   📄 Markdown: {md_path}")
        print(f"   🖼️  Images extracted: {len(extracted_images)}")

        return True

    except Exception as e:
        print(f"❌ Error during conversion: {e}")
        return False


def process_hwpx_to_pdf(hwpx_path, output_dir=None):
    """
    Convert HWPX file to PDF format

    Args:
        hwpx_path: Path to HWPX file
        output_dir: Output directory for results
    """
    try:
        import markdown
        import weasyprint
        import re
        import base64
    except ImportError as e:
        print(f"❌ Missing dependencies for PDF conversion: {e}")
        print("   Please install with: pip install airun-hwp[pdf]")
        return False

    hwpx_path = Path(hwpx_path)

    if not hwpx_path.exists():
        print(f"❌ Error: File not found - {hwpx_path}")
        return False

    # Setup output directory
    if output_dir is None:
        output_dir = Path.cwd() / "output"
    else:
        output_dir = Path(output_dir)

    doc_output_dir = output_dir / hwpx_path.stem
    doc_output_dir.mkdir(parents=True, exist_ok=True)
    images_dir = doc_output_dir / "images"
    images_dir.mkdir(exist_ok=True)

    print(f"🔄 Processing {hwpx_path.name} for PDF conversion...")

    try:
        # Parse HWPX
        reader = HWPXReaderOrdered()
        document = reader.parse(str(hwpx_path))

        # Extract images
        extracted_images = document.extract_images(str(images_dir))

        # Convert to Markdown
        markdown_content = document.to_markdown_ordered(
            include_metadata=True,
            images_dir="images"
        )

        # Convert Markdown to HTML
        md_converter = markdown.Markdown(extensions=['tables', 'fenced_code'])
        html_content = md_converter.convert(markdown_content)

        # Embed images as base64
        def embed_images(html_text, img_dir):
            def replace_img_tag(match):
                img_tag = match.group(0)
                src_match = re.search(r'src="([^"]*)"', img_tag)
                if src_match:
                    src = src_match.group(1)
                    if not src.startswith(('http', 'data:')):
                        img_path = Path(img_dir) / src
                        if img_path.exists():
                            with open(img_path, 'rb') as f:
                                img_data = f.read()
                            ext = img_path.suffix.lower().lstrip('.')
                            mime_type = {
                                'png': 'image/png',
                                'jpg': 'image/jpeg',
                                'jpeg': 'image/jpeg',
                                'gif': 'image/gif',
                                'bmp': 'image/bmp'
                            }.get(ext, 'image/png')
                            b64_data = base64.b64encode(img_data).decode()
                            data_url = f"data:{mime_type};base64,{b64_data}"
                            return img_tag.replace(f'src="{src}"', f'src="{data_url}"')
                return img_tag

            return re.sub(r'<img[^>]*src="[^"]*"[^>]*>', replace_img_tag, html_text)

        # CSS styling
        css = """
        <style>
            @page { margin: 2cm; }
            body {
                font-family: 'Malgun Gothic', Arial, sans-serif;
                font-size: 11pt;
                line-height: 1.6;
                margin: 0;
                padding: 0;
            }
            h1, h2, h3, h4, h5, h6 {
                font-family: 'Malgun Gothic', Arial, sans-serif;
                font-weight: bold;
                margin-top: 1.5em;
                margin-bottom: 0.8em;
            }
            img {
                max-width: 100%;
                height: auto;
                display: block;
                margin: 1em auto;
                page-break-inside: avoid;
            }
            table {
                border-collapse: collapse;
                width: 100%;
                margin: 1em 0;
                font-size: 10pt;
            }
            th, td {
                border: 1px solid #333;
                padding: 6px 8px;
                text-align: left;
                vertical-align: top;
            }
            th { background-color: #f0f0f0; font-weight: bold; }
        </style>
        """

        # Create full HTML
        html_with_images = embed_images(html_content, images_dir)
        full_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{hwpx_path.stem}</title>
    {css}
</head>
<body>
    {html_with_images}
</body>
</html>"""

        # Generate PDF
        pdf_path = doc_output_dir / f"{hwpx_path.stem}.pdf"
        weasyprint.HTML(string=full_html).write_pdf(str(pdf_path))

        print(f"✅ PDF conversion completed successfully!")
        print(f"   📄 PDF: {pdf_path}")
        print(f"   📏 Size: {pdf_path.stat().st_size / 1024:.1f} KB")
        print(f"   🖼️  Images embedded: {len(extracted_images)}")

        return True

    except Exception as e:
        print(f"❌ Error during PDF conversion: {e}")
        return False


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        prog="airun-hwp",
        description="AI-powered HWP/HWPX document processor for Hamonize",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert to Markdown
  airun-hwp convert document.hwpx --format markdown

  # Convert to PDF
  airun-hwp convert document.hwpx --format pdf --output ./results

  # Process document
  airun-hwp process document.hwpx
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Convert command
    convert_parser = subparsers.add_parser('convert', help='Convert HWPX file to different formats')
    convert_parser.add_argument('input', help='Input HWPX file path')
    convert_parser.add_argument('--format', choices=['markdown', 'md', 'pdf'],
                               default='markdown', help='Output format (default: markdown)')
    convert_parser.add_argument('--output', '-o', help='Output directory (default: ./output)')

    # Process command
    process_parser = subparsers.add_parser('process', help='Process HWPX file (convert to both MD and PDF)')
    process_parser.add_argument('input', help='Input HWPX file path')
    process_parser.add_argument('--output', '-o', help='Output directory (default: ./output)')

    # Parse arguments
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Execute command
    if args.command == 'convert':
        if args.format in ['markdown', 'md']:
            success = process_hwpx_to_markdown(args.input, args.output)
        elif args.format == 'pdf':
            success = process_hwpx_to_pdf(args.input, args.output)

        sys.exit(0 if success else 1)

    elif args.command == 'process':
        # Convert to both formats
        md_success = process_hwpx_to_markdown(args.input, args.output)
        pdf_success = process_hwpx_to_pdf(args.input, args.output)

        if md_success and pdf_success:
            print("\n✅ All conversions completed successfully!")
        else:
            print("\n❌ Some conversions failed.")
            sys.exit(1)


if __name__ == "__main__":
    main()