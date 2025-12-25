"""
HWP 파일 리더 - HWPv5 파일을 직접 파싱하여 HWPX와 호환되는 형식으로 변환
"""

import os
import struct
import zipfile
import tempfile
import shutil
import subprocess
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
import xml.etree.ElementTree as ET

from ..models.document import HWPXDocument
from ..models.content import Section, Image, Paragraph, TextRun
from ..models.metadata import DocumentMetadata as Metadata

logger = logging.getLogger(__name__)


class HWPReader:
    """HWPv5 파일을 읽는 리더"""

    def __init__(self):
        self.temp_dir = None

    def parse(self, file_path: str) -> HWPXDocument:
        """HWP 파일을 파싱하여 HWPXDocument 객체 반환"""
        file_path = Path(file_path)

        if file_path.suffix.lower() != '.hwp':
            raise ValueError("HWPReader only supports .hwp files")

        # 임시 디렉토리 생성
        self.temp_dir = tempfile.mkdtemp(prefix="hwp_parse_")

        try:
            # hwp5txt를 사용하여 텍스트 추출
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

            # hwp5proc를 사용하여 HWP 파일 압축 해제
            unpacked_dir = os.path.join(self.temp_dir, "unpacked")
            result = subprocess.run(
                ['hwp5proc', 'unpack', str(file_path), unpacked_dir],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                raise RuntimeError(f"Failed to unpack HWP file: {result.stderr}")

            # 압축 해제된 파일들 파싱
            return self._parse_unpacked_hwp(unpacked_dir, file_path, text_content)

        except Exception as e:
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                self.temp_dir = None
            raise e

    def _parse_unpacked_hwp(self, unpacked_dir: str, original_path: Path, text_content: str = "") -> HWPXDocument:
        """압축 해제된 HWP 파일 구조를 파싱"""
        # 메타데이터 파싱
        metadata = self._parse_hwpx_metadata(unpacked_dir, original_path)

        # 섹션 파싱
        sections = self._parse_hwpx_sections(unpacked_dir, text_content)

        # HWPXDocument 생성
        document = HWPXDocument(
            metadata=metadata,
            sections=sections
        )

        # 이미지 정보 설정
        self._extract_hwpx_images(document, unpacked_dir)

        return document

    def _parse_hwpx_metadata(self, unpacked_dir: str, original_path: Path) -> Metadata:
        """HWP 메타데이터를 파싱하여 Metadata 객체로 변환"""
        # 기본값 설정
        metadata = Metadata(
            title=original_path.stem,
            author="",
            subject="",
            keywords="",
            created=None,
            modified=None,
            format="hwp"
        )

        # DocInfo 파일에서 메타데이터 추출 시도
        docinfo_path = os.path.join(unpacked_dir, "DocInfo")
        if os.path.exists(docinfo_path):
            try:
                with open(docinfo_path, 'rb') as f:
                    # HWP DocInfo 구조 파싱 (단순화된 버전)
                    data = f.read()
                    # 여기서는 바이너리 파싱이 복잡하므로 기본값 사용
            except Exception as e:
                logger.warning(f"Failed to parse DocInfo: {e}")

        return metadata

    def _parse_hwpx_sections(self, unpacked_dir: str, text_content: str = "") -> List[Section]:
        """HWP 본문을 파싱하여 Section 리스트로 변환"""
        sections = []
        paragraphs = []

        # hwp5txt로 추출한 텍스트를 문단으로 나누기
        if text_content.strip():
            # 텍스트를 줄 단위로 나누고 빈 줄은 제거
            lines = [line.strip() for line in text_content.strip().split('\n') if line.strip()]

            # 연속된 텍스트를 하나의 문단으로 합치기
            current_paragraph = ""
            for line in lines:
                # 특수 문자나 제어 문자가 많은 줄은 무시
                if len(line) < 3 or line.count('<') > len(line) * 0.3:
                    continue

                if current_paragraph:
                    # 문단이 길어지면 새 문단 시작
                    if len(current_paragraph) > 500:
                        # TextRun 생성
                        text_run = TextRun(text=current_paragraph.strip())
                        paragraphs.append(Paragraph(runs=[text_run]))
                        current_paragraph = line
                    else:
                        current_paragraph += " " + line
                else:
                    current_paragraph = line

            # 마지막 문단 추가
            if current_paragraph.strip():
                text_run = TextRun(text=current_paragraph.strip())
                paragraphs.append(Paragraph(runs=[text_run]))

        # 빈 섹션이면 기본 텍스트 추가
        if not paragraphs:
            text_run = TextRun(text="문서 내용을 추출할 수 없습니다.")
            paragraphs.append(Paragraph(runs=[text_run]))

        # 섹션 생성
        section = Section(paragraphs=paragraphs)
        sections.append(section)

        return sections

    def _parse_section_content(self, section_file: str, unpacked_dir: str) -> Section:
        """섹션 콘텐츠 파싱"""
        paragraphs = []

        try:
            # hwp5proc를 사용하여 섹션 파일에서 텍스트 추출
            result = subprocess.run(
                ['hwp5proc', 'cat', section_file],
                capture_output=True
            )

            if result.returncode == 0:
                # 바이너리 데이터에서 텍스트 추출 (단순화된 방식)
                content = result.stdout

                # 텍스트 부분 추출 (UTF-16 인코딩 시도)
                try:
                    # 먼저 UTF-8로 시도
                    text = content.decode('utf-8', errors='ignore')
                except:
                    try:
                        # UTF-16LE로 시도
                        text = content.decode('utf-16le', errors='ignore')
                    except:
                        # Latin-1로 시도
                        text = content.decode('latin-1', errors='ignore')

                # 텍스트 정리 및 문단 분리
                if text.strip():
                    # 개행 문자로 문단 분리
                    lines = text.strip().split('\n')
                    for line in lines:
                        line = line.strip()
                        if line and len(line) > 1:  # 의미 있는 텍스트만 추가
                            paragraphs.append(Paragraph(text=line))

            else:
                logger.warning(f"Failed to extract text from section: {result.stderr.decode('utf-8', errors='ignore')}")

        except Exception as e:
            logger.warning(f"Failed to parse section content: {e}")

        return Section(paragraphs=paragraphs)

    def _extract_text_from_paragraph(self, para_elem: ET.Element) -> str:
        """XML 문단 요소에서 텍스트 추출"""
        text_parts = []

        for text_elem in para_elem.findall('.//Text'):
            if text_elem.text:
                text_parts.append(text_elem.text)

        return ''.join(text_parts)

    def _extract_raw_text(self, section_file: str) -> str:
        """섹션 파일에서 원시 텍스트 추출"""
        try:
            # hwp5txt를 사용하여 텍스트 추출
            result = subprocess.run(
                ['hwp5txt', section_file],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                return result.stdout
            else:
                return ""
        except Exception as e:
            logger.warning(f"Failed to extract raw text: {e}")
            return ""

    def _extract_hwpx_images(self, document: HWPXDocument, unpacked_dir: str):
        """HWP 이미지 정보 추출"""
        bindata_dir = os.path.join(unpacked_dir, "BinData")

        if not os.path.exists(bindata_dir):
            return

        # 모든 섹션에 대해 이미지 정보 추가
        for section in document.sections:
            images = []

            # BinData 폴더의 이미지 파일들
            for i, filename in enumerate(sorted(os.listdir(bindata_dir))):
                filepath = os.path.join(bindata_dir, filename)

                if os.path.isfile(filepath):
                    # 확장자 추출
                    ext = os.path.splitext(filename)[1].lower()
                    if ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
                        # 이미지 데이터 읽기
                        with open(filepath, 'rb') as f:
                            data = f.read()

                        # Image 객체 생성
                        image = Image(
                            name=f"image{i+1}{ext}",  # image1.png, image2.jpg 등
                            data=data,
                            path=f"Section/Images/{filename}"
                        )
                        images.append(image)

            section.images = images

    def __del__(self):
        """소멸자 - 임시 파일 정리"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except Exception as e:
                logger.warning(f"Failed to cleanup temp directory: {e}")