"""
HWPX 문서 리더 - 원문 순서 보존을 위한 개선 버전
"""

import os
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, List, Optional, Iterator, Union
import logging
from pathlib import Path

from ..models.document import HWPXDocument
from ..models.metadata import DocumentMetadata
from ..models.content import Section, Paragraph, TextRun, Table, TableCell, Image, StyleInfo, DocumentToken

logger = logging.getLogger(__name__)


class HWPXReaderOrdered:
    """HWPX 문서 파서 - 원문 순서 보존 버전"""

    # HWPX XML 네임스페이스
    NAMESPACES = {
        'hh': 'http://www.hancom.co.kr/hwpml/2011/head',
        'hp': 'http://www.hancom.co.kr/hwpml/2011/paragraph',
        'hc': 'http://www.hancom.co.kr/hwpml/2011/core',
        'hs': 'http://www.hancom.co.kr/hwpml/2011/section'
    }

    def __init__(self, strict_mode: bool = False):
        """초기화"""
        self.strict_mode = strict_mode
        self.metadata = DocumentMetadata()
        self.document = HWPXDocument(metadata=self.metadata)

    def parse(self, file_path: str) -> HWPXDocument:
        """HWPX/HWP 파일 파싱"""
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

        if not str(file_path).lower().endswith('.hwpx'):
            raise ValueError(f"File must have .hwpx extension: {file_path}")

        try:
            with zipfile.ZipFile(file_path, 'r') as zf:
                # HWPX 구조 검증
                self._validate_hwpx_structure(zf)

                # 1. 메타데이터 파싱 (header.xml)
                self._parse_metadata(zf)

                # 2. 리소스 파싱 (이미지 등)
                self._parse_resources(zf)

                # 3. 콘텐츠 섹션 파싱 (순서 보존 방식)
                self._parse_sections_ordered(zf)

                # 4. 스타일 정의 파싱
                self._parse_styles(zf)

                logger.info(f"Successfully parsed HWPX: {len(self.document.sections)} sections")

                return self.document

        except Exception as e:
            logger.error(f"Error parsing HWPX file {file_path}: {str(e)}")
            if self.strict_mode:
                raise
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

    def _parse_sections_ordered(self, zf: zipfile.ZipFile):
        """섹션을 순서대로 파싱 (텍스트와 컨트롤이 혼합된 순서 보존)"""
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
                section = self._parse_section_ordered(section_content)
                if section:
                    self.document.add_section(section)
            except Exception as e:
                logger.error(f"Error parsing section {section_file}: {str(e)}")
                if self.strict_mode:
                    raise

        # content.hpf에서 이미지 참조 파싱 (주석 처리 - 섹션 XML에서 직접 처리)
        # self._parse_content_hpf_images(zf)

    def _parse_section_ordered(self, xml_content: bytes) -> Optional[Section]:
        """섹션을 원문 순서대로 파싱"""
        try:
            root = ET.fromstring(xml_content)
            section = Section()

            # 섹션의 모든 자식 요소를 순서대로 순회
            for elem in root:
                tag_name = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
                if tag_name == 'p':  # 문단
                    self._process_paragraph_ordered(elem, section)
                elif tag_name == 'tbl':  # 표
                    table = self._parse_table(elem)
                    if table:
                        section.tokens.append(DocumentToken(
                            DocumentToken.TABLE,
                            content=table
                        ))
                elif elem.tag.endswith('img'):  # 이미지
                    image = self._parse_image(elem)
                    if image:
                        section.tokens.append(DocumentToken(
                            DocumentToken.IMAGE,
                            content=image
                        ))
                elif elem.tag.endswith('pic'):  # 그림 (다른 형태)
                    image = self._parse_pic(elem)
                    if image:
                        section.tokens.append(DocumentToken(
                            DocumentToken.IMAGE,
                            content=image
                        ))

            return section

        except Exception as e:
            logger.error(f"Error parsing section content: {str(e)}")
            return None

    def _process_paragraph_ordered(self, para_elem, section: Section):
        """문단을 순서대로 처리 (run 내부의 컨트롤 포함)"""
        paragraph = Paragraph()
        para_style_id = para_elem.get('paraPrIDRef', '0')
        style_id = para_elem.get('styleIDRef', '0')

        # 문단의 모든 자식 요소를 순서대로 처리
        for elem in para_elem:
            tag_name = elem.tag.split('}')[-1]  # 네임스페이스 제거

            if tag_name == 'run':  # 텍스트 런
                # 런 내부를 순회하며 텍스트와 컨트롤을 혼합 처리
                self._process_run_ordered(elem, paragraph, section)
            elif tag_name == 'ctrl':  # 컨트롤 (이미지, 표 등)
                ctrl_type = elem.get('id', '')
                if ctrl_type in ['pic', 'img', 'tbl']:  # 이미지나 표
                    self._process_inline_control(elem, section)
            elif tag_name == 'pic':  # 직접적인 그림 요소
                image = self._parse_pic(elem)
                if image:
                    section.tokens.append(DocumentToken(
                        DocumentToken.IMAGE,
                        content=image
                    ))
            elif tag_name == 'img':  # 직접적인 이미지 요소
                image = self._parse_image(elem)
                if image:
                    section.tokens.append(DocumentToken(
                        DocumentToken.IMAGE,
                        content=image
                    ))

        # 문단이 끝나면 문단 토큰 추가
        if paragraph.runs or paragraph.get_text().strip():
            section.tokens.append(DocumentToken(
                DocumentToken.PARAGRAPH_BREAK,
                content=paragraph
            ))

    def _process_run_ordered(self, run_elem, paragraph: Paragraph, section: Section):
        """런을 순서대로 처리 (내부 컨트롤 포함)"""
        # 런의 속성 파싱
        char_style_id = run_elem.get('charPrIDRef', '0')
        char_pr = run_elem.find('.//hp:charPr', self.NAMESPACES)
        style = StyleInfo(char_style_id=char_style_id)

        if char_pr is not None:
            # 서식 정보 파싱
            if char_pr.find('.//hc:bold', self.NAMESPACES) is not None:
                style.bold = True
            if char_pr.find('.//hc:italic', self.NAMESPACES) is not None:
                style.italic = True
            if char_pr.find('.//hc:underline', self.NAMESPACES) is not None:
                style.underline = True

        # 런 내부의 모든 요소를 순서대로 처리
        text_parts = []
        for elem in run_elem:
            tag_name = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
            if tag_name == 't':  # 텍스트
                if elem.text:
                    text_parts.append(elem.text)
            elif tag_name == 'ctrl':  # 컨트롤
                ctrl_id = elem.get('id', '')
                if ctrl_id:
                    # 이미지 컨트롤인 경우
                    image_counter = getattr(self, '_image_counter', 0)
                    image_name = f"image{image_counter + 1}.png"
                    self._image_counter = image_counter + 1

                    # 현재까지의 텍스트를 TextRun으로 추가
                    if text_parts:
                        text_run = TextRun(text=''.join(text_parts), style=style)
                        paragraph.runs.append(text_run)
                        text_parts = []

                    # 이미지 생성 및 토큰 추가
                    image = Image(name=image_name, path=image_name)
                    section.tokens.append(DocumentToken(
                        DocumentToken.IMAGE,
                        content=image,
                        source_index=len(section.tokens)
                    ))
            elif tag_name == 'pic':  # 런 내부의 그림
                # 현재까지의 텍스트를 TextRun으로 추가
                if text_parts:
                    text_run = TextRun(text=''.join(text_parts), style=style)
                    paragraph.runs.append(text_run)
                    text_parts = []

                # 그림을 이미지 토큰으로 추가
                image = self._parse_pic(elem)
                if image:
                    section.tokens.append(DocumentToken(
                        DocumentToken.IMAGE,
                        content=image,
                        source_index=len(section.tokens)
                    ))
            elif tag_name == 'tbl':  # 런 내부의 표
                # 현재까지의 텍스트를 TextRun으로 추가
                if text_parts:
                    text_run = TextRun(text=''.join(text_parts), style=style)
                    paragraph.runs.append(text_run)
                    text_parts = []

                # 표를 테이블 토큰으로 추가
                table = self._parse_table(elem)
                if table:
                    section.tokens.append(DocumentToken(
                        DocumentToken.TABLE,
                        content=table,
                        source_index=len(section.tokens)
                    ))

        # 남은 텍스트 처리
        if text_parts:
            text_run = TextRun(text=''.join(text_parts), style=style)
            paragraph.runs.append(text_run)

    def _process_inline_control(self, ctrl_elem, section: Section):
        """인라인 컨트롤 처리"""
        ctrl_id = ctrl_elem.get('id')

        if ctrl_id == 'tbl':  # 표
            table = self._parse_table(ctrl_elem)
            if table:
                section.tokens.append(DocumentToken(
                    DocumentToken.TABLE,
                    content=table
                ))
        elif ctrl_id in ['pic', 'img']:  # 이미지
            image = self._parse_image(ctrl_elem) or self._parse_pic(ctrl_elem)
            if image:
                section.tokens.append(DocumentToken(
                    DocumentToken.IMAGE,
                    content=image
                ))

    def _parse_table(self, table_elem) -> Optional[Table]:
        """테이블 요소 파싱"""
        try:
            table = Table()
            rows = table_elem.findall('.//hp:tr', self.NAMESPACES)

            if not rows:
                return None

            for row_elem in rows:
                row_cells = []
                cells = row_elem.findall('.//hp:tc', self.NAMESPACES)

                for cell_elem in cells:
                    text_parts = []
                    for para in cell_elem.findall('.//hp:p', self.NAMESPACES):
                        for txt in para.findall('.//hp:t', self.NAMESPACES):
                            if txt.text:
                                text_parts.append(txt.text)

                    cell_text = ''.join(text_parts).strip()
                    row_span = int(cell_elem.get('rowSpan', '1'))
                    col_span = int(cell_elem.get('colSpan', '1'))

                    cell = TableCell(
                        text=cell_text,
                        row=0,
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
            name = img_elem.get('name', '')
            if not name:
                return None

            rect = img_elem.find('.//hp:rect', self.NAMESPACES)
            if rect is not None:
                width = int(rect.get('width', '0'))
                height = int(rect.get('height', '0'))
            else:
                width = height = None

            pos = img_elem.find('.//hp:pos', self.NAMESPACES)
            if pos is not None:
                x = int(pos.get('x', '0'))
                y = int(pos.get('y', '0'))
                position = {'x': x, 'y': y}
            else:
                position = None

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

    def _parse_pic(self, pic_elem) -> Optional[Image]:
        """그림 요소 파싱 (hp:pic)"""
        try:
            # 이미지 ID 추출
            pic_id = pic_elem.get('id')
            if not pic_id:
                return None

            # 이미지 크기 정보
            rect = pic_elem.find('.//hp:rect', self.NAMESPACES)
            width = int(rect.get('width', '0')) if rect is not None else None
            height = int(rect.get('height', '0')) if rect is not None else None

            # 이미지 이름 생성 (ID를 기반으로)
            # 예: pic ID 1000001 -> image1.png
            try:
                num = int(pic_id) - 1000000  # 1000001 -> 1, 1000002 -> 2
                img_name = f"image{num}.png"
            except:
                img_name = f"image_{pic_id}.png"

            # 리소스에서 해당 이미지 찾기
            if img_name in self.document.resources:
                resource = self.document.resources[img_name]
                return Image(
                    name=img_name,
                    data=resource.get('data'),
                    width=width,
                    height=height
                )
            else:
                # 다른 이름으로도 찾아보기
                for res_name in self.document.resources:
                    if str(num) in res_name or pic_id in res_name:
                        resource = self.document.resources[res_name]
                        return Image(
                            name=res_name,
                            data=resource.get('data'),
                            width=width,
                            height=height
                        )

                # 리소스에 없으면 기본 이미지 생성
                return Image(
                    name=img_name,
                    width=width,
                    height=height
                )

        except Exception as e:
            logger.error(f"Error parsing pic: {str(e)}")
            return None

    def _find_image_by_bin_id(self, bin_id: str) -> Optional[str]:
        """bin ID로 이미지 파일명 찾기"""
        for img_name in self.document.resources:
            if img_name.startswith(bin_id):
                return img_name
        return None

    def _parse_resources(self, zf: zipfile.ZipFile):
        """임베드 리소스(이미지 등) 파싱"""
        bin_data_files = [
            name for name in zf.namelist()
            if name.startswith('BinData/') and not name.endswith('/')
        ]

        for bin_file in bin_data_files:
            try:
                data = zf.read(bin_file)
                filename = os.path.basename(bin_file)

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

            import re
            image_pattern = r'(image\d+\.(?:png|jpg|jpeg|gif|bmp))'
            found_images = re.findall(image_pattern, content_text)

            logger.info(f"Found {len(found_images)} image references in content.hpf")

            # 이미지 정보를 리소스에서 찾아 토큰에 추가
            if found_images and self.document.sections:
                first_section = self.document.sections[0]
                if not hasattr(first_section, 'tokens'):
                    first_section.tokens = []

                for img_name in found_images:
                    if img_name in self.document.resources:
                        resource = self.document.resources[img_name]
                        image = Image(
                            name=img_name,
                            data=resource.get('data')
                        )
                        # 토큰 스트림에 이미지 추가
                        first_section.tokens.append(DocumentToken(
                            DocumentToken.IMAGE,
                            content=image
                        ))

        except Exception as e:
            logger.error(f"Error parsing content.hpf images: {str(e)}")
            if self.strict_mode:
                raise

    def _parse_styles(self, zf: zipfile.ZipFile):
        """스타일 정의 파싱"""
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
            if dt_str.endswith('Z'):
                dt_str = dt_str[:-1]
            return datetime.fromisoformat(dt_str)
        except:
            logger.warning(f"Could not parse datetime: {dt_str}")
            return None

    def get_validation_report(self) -> List[str]:
        """파싱된 문서의 유효성 보고서"""
        return self.document.validate()