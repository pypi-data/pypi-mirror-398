#!/usr/bin/env python3
"""
Command Line Interface for airun-hwp package with Click and auto-completion support
"""

import sys
import os
from pathlib import Path
import click

# Add project to path for development
if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from airun_hwp.reader.hwpx_reader_ordered import HWPXReaderOrdered


@click.group(context_settings=dict(auto_envvar_prefix='AIRUN_HWP'))
@click.version_option(version='0.2.7', prog_name='airun-hwp')
@click.pass_context
def cli(ctx):
    """AI-powered HWP/HWPX document processor for Hamonize

    Process Korean HWP/HWPX documents with ease.
    """
    # Ensure ctx.obj exists and is a dict
    ctx.ensure_object(dict)


@cli.command()
@click.argument('input', type=click.Path(exists=True), required=True)
@click.option('--format', '-f',
              type=click.Choice(['markdown', 'md', 'pdf'], case_sensitive=False),
              default='markdown',
              help='Output format (default: markdown)')
@click.option('--output', '-o',
              type=click.Path(),
              help='Output directory (default: ./output)')
@click.pass_context
def convert(ctx, input, format, output):
    """Convert HWPX file to different formats

    INPUT: Path to the HWPX file to convert

    Examples:
        airun-hwp convert document.hwpx --format markdown
        airun-hwp convert document.hwpx -f pdf -o ./results
    """
    if format in ['markdown', 'md']:
        success = process_hwpx_to_markdown(input, output)
    elif format.lower() == 'pdf':
        success = process_hwpx_to_pdf(input, output)

    sys.exit(0 if success else 1)


@cli.command()
@click.argument('input', type=click.Path(exists=True), required=True)
@click.option('--output', '-o',
              type=click.Path(),
              help='Output directory (default: ./output)')
@click.pass_context
def process(ctx, input, output):
    """Process HWPX file (convert to both MD and PDF)

    INPUT: Path to the HWPX file to process

    This command creates both Markdown and PDF outputs.

    Example:
        airun-hwp process document.hwpx --output ./results
    """
    click.echo("Processing to both formats...")

    # Convert to both formats
    md_success = process_hwpx_to_markdown(input, output)
    pdf_success = process_hwpx_to_pdf(input, output)

    if md_success and pdf_success:
        click.echo("\n✅ All conversions completed successfully!")
    else:
        click.echo("\n❌ Some conversions failed.")
        sys.exit(1)


@cli.command()
@click.option('--shell',
              type=click.Choice(['bash', 'zsh', 'fish'], case_sensitive=False),
              default='bash',
              help='Shell type for completion (default: bash)')
def completion(shell):
    """Generate shell completion script

    Install the completion script:

    For bash:
        eval "$(_AIRUN_HWP_COMPLETE=bash_source airun-hwp)"

        Or add to ~/.bashrc:
        echo 'eval "$(_AIRUN_HWP_COMPLETE=bash_source airun-hwp)"' >> ~/.bashrc

    For zsh:
        eval "$(_AIRUN_HWP_COMPLETE=zsh_source airun-hwp)"

        Or add to ~/.zshrc:
        echo 'eval "$(_AIRUN_HWP_COMPLETE=zsh_source airun-hwp)"' >> ~/.zshrc
    """
    # Click handles this automatically
    click.echo(f"To enable {shell} completion, run:")
    click.echo()
    if shell.lower() == 'bash':
        click.echo("  # Add to ~/.bashrc:")
        click.echo('  echo \'eval "$(_AIRUN_HWP_COMPLETE=bash_source airun-hwp)"\' >> ~/.bashrc')
        click.echo()
        click.echo("  # Or run for current session:")
        click.echo('  eval "$(_AIRUN_HWP_COMPLETE=bash_source airun-hwp)"')
    elif shell.lower() == 'zsh':
        click.echo("  # Add to ~/.zshrc:")
        click.echo('  echo \'eval "$(_AIRUN_HWP_COMPLETE=zsh_source airun-hwp)"\' >> ~/.zshrc')
        click.echo()
        click.echo("  # Or run for current session:")
        click.echo('  eval "$(_AIRUN_HWP_COMPLETE=zsh_source airun-hwp)"')
    elif shell.lower() == 'fish':
        click.echo("  # Add to ~/.config/fish/completions/airun-hwp.fish:")
        click.echo("  airun-hwp --completion=bash > ~/.config/fish/completions/airun-hwp.fish")


def process_hwpx_to_markdown(hwpx_path, output_dir=None):
    """
    Convert HWPX file to Markdown format

    Args:
        hwpx_path: Path to HWPX file
        output_dir: Output directory for results
    """
    hwpx_path = Path(hwpx_path)

    # Setup output directory
    if output_dir is None:
        output_dir = Path.cwd() / "output"
    else:
        output_dir = Path(output_dir)

    doc_output_dir = output_dir / hwpx_path.stem
    doc_output_dir.mkdir(parents=True, exist_ok=True)

    click.echo(f"🔄 Processing {hwpx_path.name}...")

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

        click.echo(f"✅ Conversion completed successfully!")
        click.echo(f"   📄 Markdown: {md_path}")
        click.echo(f"   🖼️  Images extracted: {len(extracted_images)}")

        return True

    except Exception as e:
        click.echo(f"❌ Error during conversion: {e}", err=True)
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
        click.echo(f"❌ Missing dependencies for PDF conversion: {e}", err=True)
        click.echo("   Please install with: pip install airun-hwp[pdf]")
        return False

    hwpx_path = Path(hwpx_path)

    # Setup output directory
    if output_dir is None:
        output_dir = Path.cwd() / "output"
    else:
        output_dir = Path(output_dir)

    doc_output_dir = output_dir / hwpx_path.stem
    doc_output_dir.mkdir(parents=True, exist_ok=True)
    images_dir = doc_output_dir / "images"
    images_dir.mkdir(exist_ok=True)

    click.echo(f"🔄 Processing {hwpx_path.name} for PDF conversion...")

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

        click.echo(f"✅ PDF conversion completed successfully!")
        click.echo(f"   📄 PDF: {pdf_path}")
        click.echo(f"   📏 Size: {pdf_path.stat().st_size / 1024:.1f} KB")
        click.echo(f"   🖼️  Images embedded: {len(extracted_images)}")

        return True

    except Exception as e:
        click.echo(f"❌ Error during PDF conversion: {e}", err=True)
        return False


def completion_install():
    """Install shell completion automatically"""
    import subprocess

    # Detect shell
    shell = os.environ.get('SHELL', '')
    if 'bash' in shell:
        completion_type = 'bash'
        config_file = os.path.expanduser('~/.bashrc')
    elif 'zsh' in shell:
        completion_type = 'zsh'
        config_file = os.path.expanduser('~/.zshrc')
    else:
        completion_type = 'bash'  # default
        config_file = os.path.expanduser('~/.bashrc')

    completion_line = f'eval "$(_AIRUN_HWP_COMPLETE={completion_type}_source airun-hwp)"'

    # Check if already added
    try:
        with open(config_file, 'r') as f:
            content = f.read()
            if '_AIRUN_HWP_COMPLETE' in content:
                click.echo(f"✅ Completion already configured in {config_file}")
                return
    except FileNotFoundError:
        pass

    # Add to config file
    try:
        with open(config_file, 'a') as f:
            f.write(f'\n# airun-hwp shell completion\n{completion_line}\n')
        click.echo(f"✅ Added completion to {config_file}")
        click.echo(f"\nPlease run the following or restart your terminal:")
        click.echo(f"  source {config_file}")
    except Exception as e:
        click.echo(f"❌ Failed to add completion: {e}", err=True)
        click.echo(f"\nPlease manually add this line to your shell config:")
        click.echo(f"  {completion_line}")


# Enable shell completion
def _complete_install():
    """Internal function for completion installation"""
    return cli


if __name__ == "__main__":
    cli()