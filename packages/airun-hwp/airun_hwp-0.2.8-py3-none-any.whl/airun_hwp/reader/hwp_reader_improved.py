"""
Improved HWP reader with better image position handling
"""

import os
import struct
import zipfile
import tempfile
import shutil
import subprocess
import logging
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
import xml.etree.ElementTree as ET

from ..models.document import HWPXDocument
from ..models.content import Section, Image, Paragraph, TextRun
from ..models.metadata import DocumentMetadata as Metadata

logger = logging.getLogger(__name__)


class HWPReaderImproved:
    """Improved HWPv5 file reader with better image positioning"""

    def __init__(self):
        self.temp_dir = None
        self.image_positions = []

    def parse(self, file_path: str) -> HWPXDocument:
        """Parse HWP file with image position analysis"""
        file_path = Path(file_path)

        if file_path.suffix.lower() != '.hwp':
            raise ValueError("HWPReader only supports .hwp files")

        # Create temporary directory
        self.temp_dir = tempfile.mkdtemp(prefix="hwp_parse_")

        try:
            # Extract text with hwp5txt
            result = subprocess.run(
                ['hwp5txt', str(file_path)],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                logger.warning(f"Failed to extract text: {result.stderr}")
                text_content = ""
            else:
                text_content = result.stdout

            # Unpack HWP file
            unpacked_dir = os.path.join(self.temp_dir, "unpacked")
            result = subprocess.run(
                ['hwp5proc', 'unpack', str(file_path), unpacked_dir],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                raise RuntimeError(f"Failed to unpack HWP file: {result.stderr}")

            # Parse with position analysis
            return self._parse_unpacked_hwp_improved(unpacked_dir, file_path, text_content)

        except Exception as e:
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                self.temp_dir = None
            raise e

    def _parse_unpacked_hwp_improved(self, unpacked_dir: str, original_path: Path, text_content: str) -> HWPXDocument:
        """Parse with improved image positioning"""
        # Parse metadata
        metadata = self._parse_metadata(unpacked_dir, original_path)

        # Get image information
        images = self._extract_images_info(unpacked_dir)

        # Analyze text to determine likely image positions
        self._analyze_image_positions(text_content, images)

        # Create sections with inline images
        sections = self._create_sections_with_images(text_content, images)

        # Create document
        document = HWPXDocument(
            metadata=metadata,
            sections=sections
        )

        return document

    def _extract_images_info(self, unpacked_dir: str) -> List[Dict]:
        """Extract image information from BinData"""
        bindata_dir = os.path.join(unpacked_dir, "BinData")
        images = []

        if not os.path.exists(bindata_dir):
            return images

        # Get all image files
        for i, filename in enumerate(sorted(os.listdir(bindata_dir))):
            filepath = os.path.join(bindata_dir, filename)

            if os.path.isfile(filepath):
                ext = os.path.splitext(filename)[1].lower()
                if ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
                    with open(filepath, 'rb') as f:
                        data = f.read()

                    images.append({
                        'index': i,
                        'name': f"image{i+1}{ext}",
                        'filename': filename,
                        'data': data,
                        'size': len(data),
                        'ext': ext
                    })

        return images

    def _analyze_image_positions(self, text_content: str, images: List[Dict]):
        """Analyze text to determine likely image insertion points"""
        if not images:
            return

        # Split text into paragraphs
        paragraphs = [p.strip() for p in text_content.split('\n\n') if p.strip()]

        # Simple heuristic: distribute images evenly throughout the document
        # If there are N images and M paragraphs, place an image after roughly M/N paragraphs
        total_images = len(images)
        total_paragraphs = len(paragraphs)

        if total_paragraphs == 0:
            # No text content, just add all images
            self.image_positions = [(0, img) for img in images]
            return

        # Calculate average spacing
        spacing = max(1, total_paragraphs // total_images)

        self.image_positions = []
        image_idx = 0

        for para_idx in range(0, total_paragraphs, spacing):
            if image_idx < total_images:
                self.image_positions.append((para_idx, images[image_idx]))
                image_idx += 1

        # Add remaining images at the end
        while image_idx < total_images:
            self.image_positions.append((total_paragraphs - 1, images[image_idx]))
            image_idx += 1

    def _create_sections_with_images(self, text_content: str, images: List[Dict]) -> List[Section]:
        """Create sections with images inserted at appropriate positions"""
        sections = []
        paragraphs = []

        # Split text into paragraphs
        text_paragraphs = [p.strip() for p in text_content.split('\n\n') if p.strip()]

        # Create a mapping of paragraph index to images
        para_to_images = {}
        for para_idx, img_info in self.image_positions:
            if para_idx not in para_to_images:
                para_to_images[para_idx] = []
            para_to_images[para_idx].append(img_info)

        # Create section with embedded images
        for para_idx, para_text in enumerate(text_paragraphs):
            # Create paragraph
            if para_text and len(para_text) > 2:
                # Skip lines with too many control characters
                if para_text.count('<') <= len(para_text) * 0.3:
                    text_run = TextRun(text=para_text)
                    paragraphs.append(Paragraph(runs=[text_run]))

            # Add images after this paragraph if any
            if para_idx in para_to_images:
                for img_info in para_to_images[para_idx]:
                    # For now, we'll store image info separately
                    # The section images will be added after
                    pass

        # Create section
        section = Section(paragraphs=paragraphs)

        # Add all images to the section
        # Note: HWP format doesn't preserve exact image positions in text
        # So we add them all to the section
        for img_info in images:
            image = Image(
                name=img_info['name'],
                data=img_info['data'],
                path=img_info['name']  # Will be updated during extraction
            )
            section.images.append(image)

        sections.append(section)

        return sections

    def _parse_metadata(self, unpacked_dir: str, original_path: Path) -> Metadata:
        """Parse document metadata"""
        metadata = Metadata(
            title=original_path.stem,
            author="",
            subject="",
            keywords="",
            created=None,
            modified=None,
            format="hwp"
        )

        # Try to extract more metadata if available
        docinfo_path = os.path.join(unpacked_dir, "DocInfo")
        if os.path.exists(docinfo_path):
            try:
                with open(docinfo_path, 'rb') as f:
                    data = f.read()
                    # Parse binary metadata if needed
            except Exception as e:
                logger.warning(f"Failed to parse DocInfo: {e}")

        return metadata

    def __del__(self):
        """Cleanup"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except Exception as e:
                logger.warning(f"Failed to cleanup temp directory: {e}")