"""
HWPX 파일 순서 보존 리더 v2 - 정확한 위치 보존 개선
"""

import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging

from ..models.document import HWPXDocument, DocumentMetadata
from ..models.content import Section, Paragraph, TextRun, Image, Table, DocumentToken

logger = logging.getLogger(__name__)


class HWPXReaderOrderedV2:
    """HWPX 파일을 원문 순서대로 읽는 리더 v2 - 개선된 위치 보존"""

    def __init__(self):
        self.ns = {
            'hh': 'http://www.hancom.co.kr/hwp/2009/paragraph',
            'hp': 'http://www.hancom.co.kr/hwp/2009/presentation',
            'hu': 'http://www.hancom.co.kr/hwp/2009/unicode',
            'sl': 'http://www.hancom.co.kr/hwp/2009/shape-layout',
            'mf': 'http://www.hancom.co.kr/hwp/2009/math-formula',
            'ol': 'http://www.hancom.co.kr/hwp/2009/outline'
        }

    def parse(self, file_path: str) -> HWPXDocument:
        """HWPX 파일 파싱"""
        logger.info(f"Parsing HWPX file: {file_path}")

        # ZIP 파일 열기
        with zipfile.ZipFile(file_path, 'r') as zf:
            # 메타데이터 읽기
            metadata = self._parse_metadata(zf)

            # 문서 내용 읽기
            sections = self._parse_content_v2(zf)

        # 문서 생성
        document = HWPXDocument(
            metadata=metadata,
            sections=sections
        )

        logger.info(f"Successfully parsed HWPX: {len(sections)} sections")
        return document

    def _parse_metadata(self, zf: zipfile.ZipFile) -> DocumentMetadata:
        """HWPX 파일 메타데이터 파싱"""
        metadata = DocumentMetadata()

        # Content/hwpmeta.xml에서 메타데이터 읽기
        try:
            with zf.open('Content/content.hpf') as f:
                content = f.read().decode('utf-8')
                # 메타데이터 XML은 생략하고 기본값 사용
                metadata.title = "HWPX Document"
                metadata.author = "Unknown"
        except:
            # 기본값
            metadata.title = "HWPX Document"
            metadata.author = "Unknown"

        return metadata

    def _parse_content_v2(self, zf: zipfile.ZipFile) -> List[Section]:
        """문서 내용 파싱 v2 - 개선된 위치 보존"""
        sections = []

        # Section 파일 목록 가져오기
        section_files = [f for f in zf.namelist() if f.startswith('Contents/Section') and f.endswith('.xml')]

        logger.info(f"Found {len(section_files)} section files")

        # 각 섹션 파싱
        for section_file in sorted(section_files):
            section = self._parse_section_file_v2(zf, section_file)
            if section:
                sections.append(section)

        return sections

    def _parse_section_file_v2(self, zf: zipfile.ZipFile, section_file: str) -> Optional[Section]:
        """섹션 파일 파싱 v2"""
        try:
            with zf.open(section_file) as f:
                tree = ET.parse(f)
                root = tree.getroot()

            section = Section()
            self.current_position = 0  # 문서 내 현재 위치 추적

            # 섹션의 모든 요소를 순서대로 처리
            for elem in root:
                tag_name = elem.tag.split('}')[-1]

                if tag_name == 'para':
                    self._process_paragraph_v2(elem, section)
                elif tag_name == 'tbl':
                    # 표 처리
                    table = self._parse_table(elem)
                    if table:
                        section.tokens.append(DocumentToken(
                            DocumentToken.TABLE,
                            content=table,
                            source_index=self.current_position
                        ))
                        self.current_position += 1

            return section

        except Exception as e:
            logger.error(f"Error parsing section {section_file}: {e}")
            return None

    def _process_paragraph_v2(self, para_elem, section: Section):
        """문단 처리 v2 - 정확한 이미지 위치 보존"""
        paragraph = Paragraph()
        current_text_runs = []  # 현재까지의 텍스트 런
        inline_objects = []  # 인라인 객체 목록 (위치 정보 포함)

        # 문단의 모든 자식 요소를 순서대로 처리
        for elem in para_elem:
            tag_name = elem.tag.split('}')[-1]

            if tag_name == 'run':  # 텍스트 런
                # 런 내부를 순회하며 텍스트와 컨트롤을 혼합 처리
                self._process_run_v2(elem, paragraph, section, current_text_runs, inline_objects)
            elif tag_name == 'ctrl':  # 컨트롤 (이미지, 표 등)
                # 문단 레벨의 컨트롤은 현재 문단 후에 배치
                self._process_paragraph_control(elem, section)
            elif tag_name == 'pic':  # 직접적인 그림 요소
                # 문단 내의 직접 그림도 처리
                image = self._parse_pic(elem)
                if image:
                    # 현재까지의 텍스트를 저장
                    if current_text_runs:
                        paragraph.runs.extend(current_text_runs)
                        current_text_runs = []
                    # 이미지를 문단 후에 배치
                    section.tokens.append(DocumentToken(
                        DocumentToken.IMAGE,
                        content=image,
                        source_index=self.current_position
                    ))
                    self.current_position += 1

        # 남아있는 텍스트 런을 문단에 추가
        if current_text_runs:
            paragraph.runs.extend(current_text_runs)

        # 문단이 비어있지 않으면 토큰에 추가
        if paragraph.runs or inline_objects:
            # 인라인 객체가 있는 경우, 복합 토큰 생성
            if inline_objects:
                self._create_mixed_tokens(paragraph, inline_objects, section)
            else:
                # 일반 문단 토큰
                section.tokens.append(DocumentToken(
                    DocumentToken.PARAGRAPH_BREAK,
                    content=paragraph,
                    source_index=self.current_position
                ))
                self.current_position += 1

    def _process_run_v2(self, run_elem, paragraph: Paragraph, section: Section,
                        current_text_runs: List[TextRun], inline_objects: List[Dict]):
        """텍스트 런 처리 v2 - 인라인 객체 위치 추적"""
        text_parts = []
        style = None

        # 런의 모든 자식 요소를 순회
        for elem in run_elem:
            tag_name = elem.tag.split('}')[-1]

            if tag_name == 'text':  # 텍스트
                if elem.text:
                    # 현재까지의 텍스트 수집
                    char_pos = len(text_parts)  # 런 내에서의 문자 위치
                    text_parts.append(elem.text)

            elif tag_name == 'pic':  # 런 내부의 그림
                # 텍스트가 있으면 현재까지를 하나의 TextRun으로 저장
                if text_parts:
                    current_text_runs.append(TextRun(
                        text=''.join(text_parts),
                        style=style
                    ))
                    text_parts = []

                # 그림 정보 저장 (위치 정보 포함)
                image = self._parse_pic(elem)
                if image:
                    # 인라인 객체 정보 저장
                    inline_objects.append({
                        'type': 'image',
                        'object': image,
                        'position': len(current_text_runs),  # 현재까지의 TextRun 수
                        'char_offset': 0  # 다음 TextRun의 시작 위치
                    })

            elif tag_name == 'ctrl':  # 런 내부의 컨트롤
                ctrl_type = elem.get('id', '')
                if ctrl_type in ['pic', 'img']:
                    # 텍스트가 있으면 저장
                    if text_parts:
                        current_text_runs.append(TextRun(
                            text=''.join(text_parts),
                            style=style
                        ))
                        text_parts = []

                    # 컨트롤 이미지 처리
                    image = self._process_image_control(elem)
                    if image:
                        inline_objects.append({
                            'type': 'image',
                            'object': image,
                            'position': len(current_text_runs),
                            'char_offset': 0
                        })

        # 남아있는 텍스트 처리
        if text_parts:
            current_text_runs.append(TextRun(
                text=''.join(text_parts),
                style=style
            ))

    def _create_mixed_tokens(self, paragraph: Paragraph, inline_objects: List[Dict], section: Section):
        """텍스트와 인라인 객체가 혼합된 토큰 생성"""
        runs = paragraph.runs
        obj_index = 0
        current_run_index = 0

        # 텍스트 런과 인라인 객체를 순서대로 배치
        while current_run_index < len(runs) or obj_index < len(inline_objects):
            if obj_index < len(inline_objects):
                obj = inline_objects[obj_index]
                obj_pos = obj['position']

                # 현재 위치에 텍스트 런이 있으면 먼저 추가
                if current_run_index < obj_pos and current_run_index < len(runs):
                    # 텍스트 런 추가
                    temp_para = Paragraph()
                    temp_para.runs = [runs[current_run_index]]
                    section.tokens.append(DocumentToken(
                        DocumentToken.TEXT_RUN,
                        content=temp_para,
                        source_index=self.current_position
                    ))
                    self.current_position += 1
                    current_run_index += 1

                # 이제 인라인 객체를 추가할 차례
                if current_run_index == obj_pos:
                    # 인라인 객체 추가
                    if obj['type'] == 'image':
                        section.tokens.append(DocumentToken(
                            DocumentToken.IMAGE,
                            content=obj['object'],
                            source_index=self.current_position
                        ))
                    self.current_position += 1
                    obj_index += 1
            else:
                # 남은 텍스트 런 추가
                temp_para = Paragraph()
                temp_para.runs = [runs[current_run_index]]
                section.tokens.append(DocumentToken(
                    DocumentToken.TEXT_RUN,
                    content=temp_para,
                    source_index=self.current_position
                ))
                self.current_position += 1
                current_run_index += 1

    def _process_paragraph_control(self, ctrl_elem, section: Section):
        """문단 레벨의 컨트롤 처리"""
        ctrl_type = ctrl_elem.get('id', '')
        if ctrl_type in ['tbl']:  # 표
            table = self._parse_table_from_control(ctrl_elem)
            if table:
                section.tokens.append(DocumentToken(
                    DocumentToken.TABLE,
                    content=table,
                    source_index=self.current_position
                ))
                self.current_position += 1

    def _parse_pic(self, pic_elem) -> Optional[Image]:
        """그림 요소 파싱 (hp:pic)"""
        try:
            # 이미지 ID 추출
            pic_id = pic_elem.get('id')
            if not pic_id:
                return None

            # 이미지 이름 생성 (ID를 기반으로)
            try:
                num = int(pic_id) - 1000000 + 1  # 1000001 -> 1
                img_name = f"image{num}.png"
            except:
                img_name = f"image_{pic_id}.png"

            # 이미지 객체 생성 (데이터는 나중에 채움)
            return Image(
                name=img_name,
                path=img_name,
                pic_id=pic_id
            )

        except Exception as e:
            logger.error(f"Error parsing picture: {e}")
            return None

    def _process_image_control(self, ctrl_elem) -> Optional[Image]:
        """컨트롤 요소에서 이미지 처리"""
        # 컨트롤 ID 파싱
        ctrl_id = ctrl_elem.get('id', '')
        if ctrl_id:
            # 이미지 이름 생성
            try:
                num = int(ctrl_id) - 1000000 + 1
                img_name = f"image{num}.png"
            except:
                img_name = f"image_{ctrl_id}.png"

            return Image(
                name=img_name,
                path=img_name,
                pic_id=ctrl_id
            )
        return None

    def _parse_table(self, tbl_elem) -> Optional[Table]:
        """표 요소 파싱"""
        # 간단한 표 파싱 구현
        # 실제 HWPX에서는 더 복잡한 구조
        return Table(rows=1, cols=1, data=[[]])

    def _parse_table_from_control(self, ctrl_elem) -> Optional[Table]:
        """컨트롤에서 표 파싱"""
        return Table(rows=1, cols=1, data=[[]])