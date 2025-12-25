"""
Airun-HWP: 한글 문서(HWP/HWPX) 처리 라이브러리

주요 기능:
- HWPX 문서 파싱
- 텍스트, 이미지, 표 추출
- Markdown 변환
- PDF 변환
"""

from .reader.hwpx_reader import HWPXReader
from .reader.hwp_reader import HWPReader
from .models.document import HWPXDocument
from .writer.hwpx_writer import HWPXWriter
from .writer.pdf_converter import PDFConverter, convert_markdown_to_pdf, convert_hwpx_to_pdf
from .writer.pdf_to_image import PDFToImageConverter, convert_pdf_to_images, convert_hwpx_to_images

__version__ = "1.0.0"
__author__ = "AI.RUN Team"

__all__ = [
    'HWPXReader',
    'HWPReader',
    'HWPXDocument',
    'HWPXWriter',
    'PDFConverter',
    'PDFToImageConverter',
    'convert_markdown_to_pdf',
    'convert_hwpx_to_pdf',
    'convert_pdf_to_images',
    'convert_hwpx_to_images'
]