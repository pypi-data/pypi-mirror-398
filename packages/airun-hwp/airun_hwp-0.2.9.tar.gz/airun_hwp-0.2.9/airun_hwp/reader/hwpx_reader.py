"""
HWPX 문서 리더 - 텍스트, 이미지, 표 파싱
"""

import os
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, List, Optional
import logging
from pathlib import Path

from ..models.document import HWPXDocument
from ..models.metadata import DocumentMetadata
from ..models.content import Section, Paragraph, TextRun, Table, TableCell, Image, StyleInfo

logger = logging.getLogger(__name__)


class HWPXReader:
    """HWPX 문서 파서"""

    # HWPX XML 네임스페이스
    NAMESPACES = {
        'hh': 'http://www.hancom.co.kr/hwpml/2011/head',
        'hp': 'http://www.hancom.co.kr/hwpml/2011/paragraph',
        'hc': 'http://www.hancom.co.kr/hwpml/2011/core',
        'hs': 'http://www.hancom.co.kr/hwpml/2011/section'
    }

    def __init__(self, strict_mode: bool = False):
        """초기화

        Args:
            strict_mode: 엄격 모드 여부
        """
        self.strict_mode = strict_mode
        self.metadata = DocumentMetadata()
        self.document = HWPXDocument(metadata=self.metadata)

    def parse(self, file_path: str) -> HWPXDocument:
        """HWPX/HWP 파일 파싱

        Args:
            file_path: HWPX 또는 HWP 파일 경로

        Returns:
            HWPXDocument: 파싱된 문서 객체
        """
        file_path = Path(file_path)

        # HWP 파일인 경우 HWPReader 사용
        if file_path.suffix.lower() == '.hwp':
            from .hwp_reader import HWPReader
            logger.info(f"Parsing HWP file: {file_path}")
            hwp_reader = HWPReader()
            return hwp_reader.parse(str(file_path))

        # HWPX 파일인 경우 기존 로직 사용
        logger.info(f"Parsing HWPX file: {file_path}")

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"HWPX file not found: {file_path}")

        if not file_path.lower().endswith('.hwpx'):
            raise ValueError(f"File must have .hwpx extension: {file_path}")

        try:
            with zipfile.ZipFile(file_path, 'r') as zf:
                # HWPX 구조 검증
                self._validate_hwpx_structure(zf)

                # 1. 메타데이터 파싱 (header.xml)
                self._parse_metadata(zf)

                # 2. 리소스 파싱 (이미지 등) - 섹션 파싱보다 먼저
                self._parse_resources(zf)

                # 3. 콘텐츠 섹션 파싱
                self._parse_sections(zf)

                # 4. 스타일 정의 파싱
                self._parse_styles(zf)

                logger.info(f"Successfully parsed HWPX: {len(self.document.sections)} sections, "
                          f"{sum(len(s.paragraphs) for s in self.document.sections)} paragraphs")

                return self.document

        except Exception as e:
            logger.error(f"Error parsing HWPX file {file_path}: {str(e)}")
            if self.strict_mode:
                raise
            # 비엄격 모드에서는 부분적으로 파싱된 문서 반환
            logger.warning("Returning partially parsed document")
            return self.document

    def _validate_hwpx_structure(self, zf: zipfile.ZipFile):
        """HWPX 파일 구조 검증"""
        required_files = [
            'mimetype',
            'Contents/header.xml',
            'Contents/content.hpf'
        ]

        for file_path in required_files:
            if file_path not in zf.namelist():
                error_msg = f"Required HWPX file missing: {file_path}"
                if self.strict_mode:
                    raise ValueError(error_msg)
                else:
                    logger.warning(error_msg)

    def _parse_metadata(self, zf: zipfile.ZipFile):
        """header.xml에서 메타데이터 파싱"""
        if 'Contents/header.xml' not in zf.namelist():
            logger.warning("No header.xml found")
            return

        try:
            header_content = zf.read('Contents/header.xml')
            root = ET.fromstring(header_content)

            # 문서 정보
            doc_info = root.find('.//hh:DocInfo', self.NAMESPACES)
            if doc_info is not None:
                self._extract_document_info(doc_info)

            # 폰트 정의
            font_faces = root.findall('.//hh:FaceName', self.NAMESPACES)
            for font_face in font_faces:
                self.document.fonts.append({
                    'id': font_face.get('id'),
                    'name': font_face.get('name', ''),
                    'type': font_face.get('type', 'TTF')
                })

        except Exception as e:
            logger.error(f"Error parsing metadata: {str(e)}")
            if self.strict_mode:
                raise

    def _extract_document_info(self, doc_info):
        """문서 정보 추출"""
        try:
            # 기본 메타데이터
            summary_info = doc_info.find('.//hc:summary', self.NAMESPACES)
            if summary_info is not None:
                self.metadata.title = self._get_element_text(summary_info, './/hc:title')
                self.metadata.subject = self._get_element_text(summary_info, './/hc:subject')
                self.metadata.author = self._get_element_text(summary_info, './/hc:author')
                self.metadata.keywords = self._get_element_text(summary_info, './/hc:keywords')

            # 생성/수정 일자
            create_info = doc_info.find('.//hc:create', self.NAMESPACES)
            if create_info is not None:
                self.metadata.created = self._parse_datetime(create_info.get('datetime'))

            last_modify_info = doc_info.find('.//hc:last-modify', self.NAMESPACES)
            if last_modify_info is not None:
                self.metadata.modified = self._parse_datetime(last_modify_info.get('datetime'))

            # 애플리케이션 정보
            link_info = doc_info.find('.//hc:link', self.NAMESPACES)
            if link_info is not None:
                self.metadata.application = link_info.get('prog', 'Hwp')

        except Exception as e:
            logger.error(f"Error extracting document info: {str(e)}")

    def _parse_sections(self, zf: zipfile.ZipFile):
        """모든 콘텐츠 섹션 파싱 (section0.xml, section1.xml 등)"""
        section_files = sorted([
            name for name in zf.namelist()
            if name.startswith('Contents/section') and name.endswith('.xml')
        ])

        if not section_files:
            logger.warning("No section files found in HWPX")
            return

        logger.info(f"Found {len(section_files)} section files")

        for section_file in section_files:
            try:
                section_content = zf.read(section_file)
                section = self._parse_section_content(section_content)
                if section:
                    self.document.add_section(section)
            except Exception as e:
                logger.error(f"Error parsing section {section_file}: {str(e)}")
                if self.strict_mode:
                    raise

        # content.hpf에서 이미지 참조 파싱 (HWPX 특수 구조)
        self._parse_content_hpf_images(zf)

    def _parse_section_content(self, xml_content: bytes) -> Optional[Section]:
        """섹션의 XML 콘텐츠 파싱"""
        try:
            root = ET.fromstring(xml_content)
            section = Section()

            # 문단 파싱 (메인 콘텐츠)
            for para_elem in root.findall('.//hp:p', self.NAMESPACES):
                paragraph = self._parse_paragraph(para_elem)
                if paragraph and paragraph.get_text().strip():
                    section.paragraphs.append(paragraph)

            # 표 파싱
            for table_elem in root.findall('.//hp:tbl', self.NAMESPACES):
                table = self._parse_table(table_elem)
                if table:
                    section.tables.append(table)

            # 이미지 파싱
            for img_elem in root.findall('.//hp:img', self.NAMESPACES):
                image = self._parse_image(img_elem)
                if image:
                    section.images.append(image)

            return section if section.paragraphs or section.tables or section.images else None

        except Exception as e:
            logger.error(f"Error parsing section content: {str(e)}")
            return None

    def _parse_paragraph(self, para_elem) -> Optional[Paragraph]:
        """문단 요소 파싱"""
        try:
            # 문단 스타일 ID
            para_style_id = para_elem.get('paraPrIDRef', '0')
            style_id = para_elem.get('styleIDRef', '0')

            paragraph = Paragraph(
                para_style_id=para_style_id
            )

            # 런(텍스트와 일관된 서식) 파싱
            runs = para_elem.findall('.//hp:run', self.NAMESPACES)
            for run in runs:
                text_run = self._parse_run(run)
                if text_run and text_run.text.strip():
                    paragraph.runs.append(text_run)

            return paragraph

        except Exception as e:
            logger.error(f"Error parsing paragraph: {str(e)}")
            return None

    def _parse_run(self, run_elem) -> Optional[TextRun]:
        """런 요소 파싱"""
        try:
            # 텍스트 콘텐츠 추출
            text_parts = []
            for txt in run_elem.findall('.//hp:t', self.NAMESPACES):
                if txt.text:
                    text_parts.append(txt.text)

            if not text_parts:
                return None

            text = ''.join(text_parts)
            if not text.strip():
                return None

            # 문자 스타일 ID
            char_style_id = run_elem.get('charPrIDRef', '0')

            # 서식 체크
            char_pr = run_elem.find('.//hp:charPr', self.NAMESPACES)
            style = StyleInfo(char_style_id=char_style_id)

            if char_pr is not None:
                # 볼드
                if char_pr.find('.//hc:bold', self.NAMESPACES) is not None:
                    style.bold = True

                # 이탤릭
                if char_pr.find('.//hc:italic', self.NAMESPACES) is not None:
                    style.italic = True

                # 밑줄
                if char_pr.find('.//hc:underline', self.NAMESPACES) is not None:
                    style.underline = True

                # 폰트 크기
                size_elem = char_pr.find('.//hc:height', self.NAMESPACES)
                if size_elem is not None:
                    try:
                        style.font_size = int(size_elem.text) // 100  # HWP 단위에서 변환
                    except:
                        pass

                # 색상
                color_elem = char_pr.find('.//hc:color', self.NAMESPACES)
                if color_elem is not None:
                    color_value = color_elem.get('value')
                    if color_value:
                        style.color = color_value

            return TextRun(text=text, style=style, char_style_id=char_style_id)

        except Exception as e:
            logger.error(f"Error parsing run: {str(e)}")
            return None

    def _parse_table(self, table_elem) -> Optional[Table]:
        """테이블 요소 파싱"""
        try:
            table = Table()

            # 테이블 행 파싱
            rows = table_elem.findall('.//hp:tr', self.NAMESPACES)
            if not rows:
                return None

            for row_elem in rows:
                row_cells = []

                # 행의 셀 파싱
                cells = row_elem.findall('.//hp:tc', self.NAMESPACES)
                for cell_elem in cells:
                    # 셀 텍스트 가져오기
                    text_parts = []
                    for para in cell_elem.findall('.//hp:p', self.NAMESPACES):
                        for txt in para.findall('.//hp:t', self.NAMESPACES):
                            if txt.text:
                                text_parts.append(txt.text)

                    cell_text = ''.join(text_parts).strip()

                    # 병합된 셀 확인
                    row_span = int(cell_elem.get('rowSpan', '1'))
                    col_span = int(cell_elem.get('colSpan', '1'))

                    cell = TableCell(
                        text=cell_text,
                        row=0,  # 나중에 설정
                        col=len(row_cells),
                        rowspan=row_span,
                        colspan=col_span,
                        merged=(row_span > 1 or col_span > 1)
                    )

                    row_cells.append(cell)

                if row_cells:
                    table.add_row(row_cells)

            return table if table.rows else None

        except Exception as e:
            logger.error(f"Error parsing table: {str(e)}")
            return None

    def _parse_image(self, img_elem) -> Optional[Image]:
        """이미지 요소 파싱"""
        try:
            # 이미지 속성
            name = img_elem.get('name', '')
            if not name:
                return None

            # 이미지 크기
            rect = img_elem.find('.//hp:rect', self.NAMESPACES)
            if rect is not None:
                width = int(rect.get('width', '0'))
                height = int(rect.get('height', '0'))
            else:
                width = height = None

            # 위치
            pos = img_elem.find('.//hp:pos', self.NAMESPACES)
            if pos is not None:
                x = int(pos.get('x', '0'))
                y = int(pos.get('y', '0'))
                position = {'x': x, 'y': y}
            else:
                position = None

            # 캡션 확인
            caption = None
            caption_elem = img_elem.find('.//hp:caption', self.NAMESPACES)
            if caption_elem is not None:
                for txt in caption_elem.findall('.//hp:t', self.NAMESPACES):
                    if txt.text:
                        caption = txt.text
                        break

            return Image(
                name=name,
                width=width,
                height=height,
                position=position,
                caption=caption
            )

        except Exception as e:
            logger.error(f"Error parsing image: {str(e)}")
            return None

    def _parse_resources(self, zf: zipfile.ZipFile):
        """임베드 리소스(이미지 등) 파싱"""
        # BinData 디렉토리에서 이미지 데이터 추출
        bin_data_files = [
            name for name in zf.namelist()
            if name.startswith('BinData/') and not name.endswith('/')
        ]

        for bin_file in bin_data_files:
            try:
                data = zf.read(bin_file)
                filename = os.path.basename(bin_file)

                # 리소스 딕셔너리에 저장
                self.document.resources[filename] = {
                    'data': data,
                    'size': len(data),
                    'type': self._get_resource_type(filename)
                }

            except Exception as e:
                logger.error(f"Error extracting resource {bin_file}: {str(e)}")

    def _get_resource_type(self, filename: str) -> str:
        """리소스 타입 확인"""
        ext = os.path.splitext(filename)[1].lower()
        if ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
            return 'image'
        elif ext in ['.ttf', '.otf']:
            return 'font'
        else:
            return 'unknown'

    def _parse_content_hpf_images(self, zf: zipfile.ZipFile):
        """content.hpf에서 이미지 참조 파싱"""
        if 'Contents/content.hpf' not in zf.namelist():
            return

        try:
            content = zf.read('Contents/content.hpf')
            content_text = content.decode('utf-8', errors='replace')

            # 이미지 파일명 패턴 찾기
            import re
            image_pattern = r'(image\d+\.(?:png|jpg|jpeg|gif|bmp))'

            found_images = re.findall(image_pattern, content_text)

            logger.info(f"Found {len(found_images)} image references in content.hpf")

            # 이미지 정보를 첫 번째 섹션에 추가
            # 섹션이 없으면 새로 생성
            if not self.document.sections:
                from ..models.content import Section
                self.document.add_section(Section())
                logger.info("Created new section for images from content.hpf")

            if found_images:
                first_section = self.document.sections[0]

                for img_name in found_images:
                    # 이미지 객체 생성
                    from ..models.content import Image
                    image = Image(name=img_name)

                    # 리소스에 이미지 데이터가 있는지 확인
                    if img_name in self.document.resources:
                        resource = self.document.resources[img_name]
                        image.data = resource.get('data')
                        logger.debug(f"Loaded image data for {img_name}: {len(image.data) if image.data else 0} bytes")
                    else:
                        logger.warning(f"Image resource not found: {img_name}")
                        logger.debug(f"Available resources: {list(self.document.resources.keys())[:5]}...")  # Show first 5

                    # 섹션에 이미지 추가
                    first_section.images.append(image)
                    logger.debug(f"Added image from content.hpf: {img_name}")

        except Exception as e:
            logger.error(f"Error parsing content.hpf images: {str(e)}")
            if self.strict_mode:
                raise

    def _parse_styles(self, zf: zipfile.ZipFile):
        """스타일 정의 파싱"""
        # 스타일 정의는 header.xml에 이미 파싱됨
        # 이 메서드는 복잡한 스타일 처리를 위해 확장 가능
        pass

    def _get_element_text(self, element, path: str) -> Optional[str]:
        """요소에서 텍스트 가져오기"""
        if element is None:
            return None

        found = element.find(path, self.NAMESPACES)
        if found is not None and found.text:
            return found.text.strip()
        return None

    def _get_element_attr(self, element, path: str, attr: str) -> Optional[str]:
        """요소에서 속성값 가져오기"""
        if element is None:
            return None

        found = element.find(path, self.NAMESPACES)
        if found is not None:
            return found.get(attr)
        return None

    def _parse_datetime(self, dt_str: Optional[str]) -> Optional[datetime]:
        """HWPX 형식의 날짜시간 파싱"""
        if not dt_str:
            return None

        try:
            # HWPX 날짜시간 형식: "YYYY-MM-DDTHH:MM:SSZ"
            # 'Z' 제거하고 파싱
            if dt_str.endswith('Z'):
                dt_str = dt_str[:-1]
            return datetime.fromisoformat(dt_str)
        except:
            logger.warning(f"Could not parse datetime: {dt_str}")
            return None

    def get_validation_report(self) -> List[str]:
        """파싱된 문서의 유효성 보고서"""
        return self.document.validate()