"""
Main document model for HWPX files.
"""

import os
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from pathlib import Path

from .metadata import DocumentMetadata
from .content import Section, Image


@dataclass
class HWPXDocument:
    """HWPX 문서 전체를 나타내는 클래스"""
    metadata: DocumentMetadata = field(default_factory=DocumentMetadata)
    sections: List[Section] = field(default_factory=list)
    resources: Dict[str, Any] = field(default_factory=dict)
    styles: Dict[str, Any] = field(default_factory=dict)
    fonts: List[Dict[str, str]] = field(default_factory=list)

    def add_section(self, section: Section):
        """섹션 추가"""
        section.section_id = len(self.sections)
        self.sections.append(section)

    def get_all_text(self) -> str:
        """모든 텍스트 추출"""
        texts = []
        for section in self.sections:
            # 먼저 tokens에서 텍스트 추출 (HWPXReaderOrdered 방식)
            if hasattr(section, 'tokens') and section.tokens:
                for token in section.tokens:
                    if token.type == 'text_run':
                        if token.content and token.content.text:
                            texts.append(token.content.text)
                    elif token.type == 'paragraph_break':
                        if token.content and token.content.get_text():
                            text = token.content.get_text()
                            if text.strip():
                                texts.append(text)
                    elif token.type == 'table':
                        if token.content:
                            table = token.content
                            data = table.get_data()
                            if data:
                                for row in data:
                                    row_text = ' '.join(cell for cell in row if cell)
                                    if row_text.strip():
                                        texts.append(row_text)

            # paragraphs에서도 텍스트 추출 (기존 방식)
            for para in section.paragraphs:
                text = para.get_text()
                if text.strip():
                    texts.append(text)

        # 중복 제거 및 공백 정리
        unique_texts = []
        seen = set()
        for text in texts:
            cleaned = text.strip()
            if cleaned and cleaned not in seen:
                seen.add(cleaned)
                unique_texts.append(cleaned)

        return '\n\n'.join(unique_texts)

    def get_metadata_as_yaml(self) -> str:
        """YAML 형식으로 메타데이터 반환"""
        try:
            import yaml
            metadata_dict = self.metadata.to_dict()
            yaml_str = yaml.dump(metadata_dict, default_flow_style=False, sort_keys=False)
            return yaml_str.strip()
        except ImportError:
            # yaml이 설치되지 않은 경우
            return str(self.metadata.to_dict())

    def extract_images(self, output_dir: str) -> List[str]:
        """이미지 추출"""
        extracted_images = []
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        for section in self.sections:
            # 토큰 스트림에서 이미지도 추출
            images_to_extract = []

            # 기존 방식의 이미지
            for img in section.images:
                images_to_extract.append(img)

            # 토큰 스트림의 이미지
            if hasattr(section, 'tokens') and section.tokens:
                for token in section.tokens:
                    if token.type == 'image' and token.content and token.content not in images_to_extract:
                        images_to_extract.append(token.content)

            # 이미지 추출
            for img in images_to_extract:
                # 이미지 데이터가 있는 경우에만 추출
                if img.data:
                    # 원래 파일명에서 확장자 분리
                    name_without_ext, ext = os.path.splitext(img.name)

                    # 안전한 파일명 생성 (확장자 제외)
                    safe_name = "".join(c for c in name_without_ext if c.isalnum() or c in ('-', '_')).rstrip()
                    if not safe_name:
                        safe_name = f"image_{len(extracted_images)}"

                    # 확장자 결정
                    if ext.lower() in ('.png', '.jpg', '.jpeg', '.gif', '.bmp'):
                        # 원래 확장자 사용
                        filename = f"{safe_name}{ext}"
                    else:
                        # 확장자 감지
                        detected_ext = self._detect_image_extension(img.data)
                        filename = f"{safe_name}{detected_ext}"
                    filepath = output_path / filename

                    # 이미지 저장
                    with open(filepath, 'wb') as f:
                        f.write(img.data)

                    # 이미지 경로 업데이트
                    img.path = filename
                    extracted_images.append(img.path)

        return extracted_images

    def _detect_image_extension(self, data: bytes) -> str:
        """이미지 확장자 감지"""
        if data.startswith(b'\x89PNG'):
            return '.png'
        elif data.startswith(b'\xff\xd8\xff'):
            return '.jpg'
        elif data.startswith(b'GIF'):
            return '.gif'
        elif data.startswith(b'BM'):
            return '.bmp'
        else:
            return '.bin'

    def to_markdown(self, include_metadata: bool = True) -> str:
        """Markdown으로 변환"""
        markdown_parts = []

        # YAML front matter
        if include_metadata and self.metadata:
            markdown_parts.append("---")
            markdown_parts.append(self.get_metadata_as_yaml())
            markdown_parts.append("---")
            markdown_parts.append("")

        # 콘텐츠 섹션
        for i, section in enumerate(self.sections):
            if i > 0:
                markdown_parts.append("\n---\n")

            # 문단
            for para in section.paragraphs:
                text = para.get_text()
                if text.strip():
                    markdown_parts.append(text)

            # 표
            for table in section.tables:
                markdown_parts.append("\n### Table")
                data = table.get_data()
                if data:
                    # 헤더 행
                    header = data[0]
                    markdown_parts.append("| " + " | ".join(header) + " |")
                    markdown_parts.append("|" + "---|" * len(header))

                    # 데이터 행
                    for row in data[1:]:
                        markdown_parts.append("| " + " | ".join(row) + " |")

            # 이미지
            for img in section.images:
                alt_text = img.caption or img.name or "Image"
                path = img.path or img.name
                if path:
                    markdown_parts.append(f"![{alt_text}]({path})")

        return '\n'.join(markdown_parts)

    def to_markdown_ordered(self, include_metadata: bool = True, images_dir: str = None) -> str:
        """토큰 스트림을 사용하여 원문 순서대로 Markdown으로 변환"""
        from pathlib import Path
        import re
        from urllib.parse import quote

        markdown_parts = []

        # YAML front matter
        if include_metadata and self.metadata:
            markdown_parts.append("---")
            markdown_parts.append(self.get_metadata_as_yaml())
            markdown_parts.append("---")
            markdown_parts.append("")

        # 섹션별 토큰 스트림 처리
        for i, section in enumerate(self.sections):
            if i > 0:
                markdown_parts.append("\n---\n")

            # 토큰 스트림이 있는 경우
            if hasattr(section, 'tokens') and section.tokens:
                for token in section.tokens:
                    if token.type == 'text_run':
                        # 텍스트 런 처리
                        if token.content and token.content.text:
                            markdown_parts.append(token.content.text)
                    elif token.type == 'paragraph_break':
                        # 문단 구분
                        if token.content and token.content.get_text():
                            text = token.content.get_text()
                            if text.strip():
                                markdown_parts.append(text)
                                markdown_parts.append("")  # 문단 후 빈 줄
                    elif token.type == 'table':
                        # 표 처리
                        if token.content:
                            table = token.content
                            data = table.get_data()
                            if data:
                                # GFM 표 형식으로 변환
                                header = data[0]
                                markdown_parts.append("| " + " | ".join(header) + " |")
                                markdown_parts.append("|" + "---|" * len(header))
                                for row in data[1:]:
                                    markdown_parts.append("| " + " | ".join(row) + " |")
                                markdown_parts.append("")
                    elif token.type == 'image':
                        # 이미지 처리
                        if token.content:
                            img = token.content
                            alt_text = img.caption or img.name or "Image"

                            # 이미지 경로 처리
                            if img.path:
                                img_path = img.path
                            elif img.name:
                                img_path = img.name
                            else:
                                continue

                            # 이미지 경로 처리 (상대 경로 사용)
                            if images_dir and not img_path.startswith(('http://', 'https://', '/')):
                                # images_dir이 있고 상대 경로인 경우
                                full_img_path = f"{images_dir}/{img_path}"
                                markdown_parts.append(f"![{alt_text}]({full_img_path})")
                            else:
                                markdown_parts.append(f"![{alt_text}]({img_path})")

                            markdown_parts.append("")  # 이미지 후 빈 줄
            else:
                # 토큰 스트림이 없는 경우 기존 방식으로 처리
                for para in section.paragraphs:
                    text = para.get_text()
                    if text.strip():
                        markdown_parts.append(text)
                        markdown_parts.append("")

                for table in section.tables:
                    data = table.get_data()
                    if data:
                        header = data[0]
                        markdown_parts.append("| " + " | ".join(header) + " |")
                        markdown_parts.append("|" + "---|" * len(header))
                        for row in data[1:]:
                            markdown_parts.append("| " + " | ".join(row) + " |")
                        markdown_parts.append("")

                for img in section.images:
                    alt_text = img.caption or img.name or "Image"
                    path = img.path or img.name
                    if path:
                        # images_dir이 있고 상대 경로인 경우
                        if images_dir and not path.startswith(('http://', 'https://', '/')):
                            full_path = f"{images_dir}/{path}"
                            markdown_parts.append(f"![{alt_text}]({full_path})")
                        else:
                            markdown_parts.append(f"![{alt_text}]({path})")
                        markdown_parts.append("")

        return '\n'.join(markdown_parts)

    def validate(self) -> List[str]:
        """문서 유효성 검증"""
        issues = []

        if not self.metadata.title:
            issues.append("Warning: Document has no title")

        if not self.sections:
            issues.append("Error: Document has no content sections")

        for i, section in enumerate(self.sections):
            if not section.paragraphs and not section.tables and not section.images:
                issues.append(f"Warning: Section {i} is empty")

        return issues