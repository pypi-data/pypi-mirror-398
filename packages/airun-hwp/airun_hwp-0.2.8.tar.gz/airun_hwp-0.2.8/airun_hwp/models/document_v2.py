"""
Main document model for HWPX files v2 - improved positioning
"""

import os
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from pathlib import Path

from .metadata import DocumentMetadata
from .content import Section, Image, Paragraph


@dataclass
class InlineObject:
    """인라인 객체 (텍스트 내에 삽입되는 객체)"""
    object_type: str  # 'image', 'table', etc.
    content: Any  # Image, Table 등
    position: int  # 문단 내에서의 위치 (문자 오프셋)
    width: Optional[int] = None
    height: Optional[int] = None
    alignment: str = 'inline'  # 'inline', 'left', 'right', 'center'


@dataclass
class EnhancedTextRun:
    """향상된 텍스트 런 (인라인 객체 지원)"""
    text: str = ""
    style: Optional[Dict[str, Any]] = None
    inline_objects: List[InlineObject] = field(default_factory=list)

    def get_full_text(self) -> str:
        """인라인 객체를 제외한 순수 텍스트 반환"""
        return self.text

    def has_inline_objects(self) -> bool:
        """인라인 객체가 있는지 확인"""
        return len(self.inline_objects) > 0


@dataclass
class EnhancedParagraph:
    """향상된 문단 (정확한 객체 위치 보존)"""
    runs: List[EnhancedTextRun] = field(default_factory=list)

    def get_text(self) -> str:
        """문단의 모든 텍스트 반환"""
        return ''.join(run.get_full_text() for run in self.runs)

    def get_all_inline_objects(self) -> List[InlineObject]:
        """문단의 모든 인라인 객체 반환"""
        objects = []
        for run in self.runs:
            objects.extend(run.inline_objects)
        return objects


@dataclass
class HWPXDocumentV2:
    """HWPX 문서 전체를 나타내는 클래스 v2"""
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
            for para in section.paragraphs:
                if para.get_text().strip():
                    texts.append(para.get_text())
        return '\n\n'.join(texts)

    def get_metadata_as_yaml(self) -> str:
        """YAML 형식으로 메타데이터 반환"""
        try:
            import yaml
            metadata_dict = self.metadata.to_dict()
            yaml_str = yaml.dump(metadata_dict, default_flow_style=False, sort_keys=False)
            return yaml_str.strip()
        except ImportError:
            return str(self.metadata.to_dict())

    def extract_images(self, output_dir: str) -> List[str]:
        """이미지 추출"""
        extracted_images = []
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        for section in self.sections:
            # 토큰 스트림에서 이미지 추출
            images_to_extract = []

            # 섹션의 기존 이미지
            for img in section.images:
                images_to_extract.append(img)

            # 토큰 스트림의 이미지
            if hasattr(section, 'tokens') and section.tokens:
                for token in section.tokens:
                    if token.type == 'image' and token.content and token.content not in images_to_extract:
                        images_to_extract.append(token.content)

            # 이미지 추출
            for img in images_to_extract:
                if img.data:
                    # 파일명 처리
                    name_without_ext, ext = os.path.splitext(img.name)
                    safe_name = "".join(c for c in name_without_ext if c.isalnum() or c in ('-', '_')).rstrip()
                    if not safe_name:
                        safe_name = f"image_{len(extracted_images)}"

                    # 확장자 결정
                    if ext.lower() in ('.png', '.jpg', '.jpeg', '.gif', '.bmp'):
                        filename = f"{safe_name}{ext}"
                    else:
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

    def to_markdown_with_positioning(self, include_metadata: bool = True, images_dir: str = None) -> str:
        """정확한 위치 보존으로 Markdown으로 변환"""
        from pathlib import Path
        import re

        markdown_parts = []

        # YAML front matter
        if include_metadata and self.metadata:
            markdown_parts.append("---")
            markdown_parts.append(self.get_metadata_as_yaml())
            markdown_parts.append("---")
            markdown_parts.append("")

        # 섹션별 처리
        for i, section in enumerate(self.sections):
            if i > 0:
                markdown_parts.append("\n---\n")

            # 토큰 스트림이 있는 경우
            if hasattr(section, 'tokens') and section.tokens:
                for token in section.tokens:
                    if token.type == DocumentToken.TEXT_RUN:
                        # 텍스트 런 처리
                        if token.content and hasattr(token.content, 'get_text'):
                            text = token.content.get_text()
                            if text.strip():
                                markdown_parts.append(text)
                    elif token.type == DocumentToken.PARAGRAPH_BREAK:
                        # 문단 구분
                        if token.content and hasattr(token.content, 'get_text'):
                            text = token.content.get_text()
                            if text.strip():
                                markdown_parts.append(text)
                                markdown_parts.append("")  # 문단 후 빈 줄
                    elif token.type == DocumentToken.TABLE:
                        # 표 처리
                        if token.content:
                            table = token.content
                            data = table.get_data()
                            if data:
                                header = data[0]
                                markdown_parts.append("| " + " | ".join(header) + " |")
                                markdown_parts.append("|" + "---|" * len(header))
                                for row in data[1:]:
                                    markdown_parts.append("| " + " | ".join(row) + " |")
                                markdown_parts.append("")
                    elif token.type == DocumentToken.IMAGE:
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

                            # 상대 경로 사용
                            if images_dir and not img_path.startswith(('http://', 'https://', '/')):
                                # images_dir이 있고 상대 경로인 경우
                                full_img_path = f"{images_dir}/{img_path}"
                                markdown_parts.append(f"![{alt_text}]({full_img_path})")
                            else:
                                markdown_parts.append(f"![{alt_text}]({img_path})")

                            # 이미지 후 빈 줄 (Markdown에서 이미지를 새 줄에 표시)
                            markdown_parts.append("")
            else:
                # 기존 방식으로 처리
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