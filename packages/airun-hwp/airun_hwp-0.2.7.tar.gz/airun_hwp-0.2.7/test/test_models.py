"""
데이터 모델 테스트
"""

import pytest
from datetime import datetime
from pathlib import Path
import sys

# 프로젝트 루트를 파이썬 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from airun_hwp.models.metadata import DocumentMetadata
from airun_hwp.models.content import (
    StyleInfo, TextRun, Paragraph, TableCell, Table, Image, Section
)
from airun_hwp.models.document import HWPXDocument


class TestDocumentMetadata:
    """DocumentMetadata 모델 테스트"""

    def test_metadata_creation(self):
        """메타데이터 생성 테스트"""
        metadata = DocumentMetadata()

        assert metadata.title is None
        assert metadata.author is None
        assert metadata.subject is None
        assert metadata.keywords is None
        assert metadata.created is None
        assert metadata.modified is None
        assert metadata.application is None
        assert metadata.encrypted is False
        assert metadata.password_protected is False

    def test_metadata_with_values(self):
        """값이 있는 메타데이터 테스트"""
        now = datetime.now()
        metadata = DocumentMetadata(
            title="테스트 문서",
            author="테스트 작성자",
            subject="테스트 주제",
            keywords="키워드1, 키워드2",
            created=now,
            modified=now,
            application="Hwp",
            encrypted=True,
            password_protected=True
        )

        assert metadata.title == "테스트 문서"
        assert metadata.author == "테스트 작성자"
        assert metadata.subject == "테스트 주제"
        assert metadata.keywords == "키워드1, 키워드2"
        assert metadata.created == now
        assert metadata.modified == now
        assert metadata.application == "Hwp"
        assert metadata.encrypted is True
        assert metadata.password_protected is True

    def test_to_dict(self):
        """메타데이터를 딕셔너리로 변환 테스트"""
        now = datetime.now()
        metadata = DocumentMetadata(
            title="테스트",
            author="작성자",
            created=now
        )

        data = metadata.to_dict()

        assert isinstance(data, dict)
        assert data["title"] == "테스트"
        assert data["author"] == "작성자"
        assert "created" in data


class TestStyleInfo:
    """StyleInfo 모델 테스트"""

    def test_style_creation(self):
        """스타일 생성 테스트"""
        style = StyleInfo()

        assert style.char_style_id is None
        assert style.para_style_id is None
        assert style.font_name is None
        assert style.font_size is None
        assert style.color is None
        assert style.bold is False
        assert style.italic is False
        assert style.underline is False
        assert style.strike_through is False

    def test_style_with_values(self):
        """값이 있는 스타일 테스트"""
        style = StyleInfo(
            font_name="굴림",
            font_size=12,
            color="#000000",
            bold=True,
            italic=True,
            underline=True
        )

        assert style.font_name == "굴림"
        assert style.font_size == 12
        assert style.color == "#000000"
        assert style.bold is True
        assert style.italic is True
        assert style.underline is True

    def test_style_equality(self):
        """스타일 동등성 비교 테스트"""
        style1 = StyleInfo(bold=True)
        style2 = StyleInfo(bold=True)
        style3 = StyleInfo(bold=False)

        # dataclass는 __eq__를 자동으로 생성
        assert style1 == style2
        assert style1 != style3


class TestTextRun:
    """TextRun 모델 테스트"""

    def test_text_run_creation(self):
        """텍스트 런 생성 테스트"""
        run = TextRun(text="테스트")

        assert run.text == "테스트"
        assert isinstance(run.style, StyleInfo)
        assert run.position == 0
        assert run.char_style_id is None

    def test_text_run_with_style(self):
        """스타일이 있는 텍스트 런 테스트"""
        style = StyleInfo(bold=True)
        run = TextRun(text="굵은 텍스트", style=style)

        assert run.text == "굵은 텍스트"
        assert run.style.bold is True

    def test_empty_text(self):
        """빈 텍스트 테스트"""
        run = TextRun(text="")

        assert run.text == ""
        # 빈 텍스트도 유효함
        assert run is not None


class TestParagraph:
    """Paragraph 모델 테스트"""

    def test_paragraph_creation(self):
        """문단 생성 테스트"""
        para = Paragraph()

        assert para.runs == []
        assert isinstance(para.style, StyleInfo)
        assert para.paragraph_id is None
        assert para.para_style_id is None

    def test_add_runs(self):
        """런 추가 테스트"""
        para = Paragraph()
        run1 = TextRun(text="첫 번째 ")
        run2 = TextRun(text="두 번째")

        para.runs.extend([run1, run2])

        assert len(para.runs) == 2
        assert para.get_text() == "첫 번째 두 번째"

    def test_get_text_with_empty(self):
        """빈 문단에서 텍스트 가져오기 테스트"""
        para = Paragraph()

        assert para.get_text() == ""

    def test_get_text_with_spaces(self):
        """공백이 있는 텍스트 테스트"""
        para = Paragraph()
        para.runs = [
            TextRun(text="앞 "),
            TextRun(text=" 중간 "),
            TextRun(text=" 뒤")
        ]

        text = para.get_text()
        assert text == "앞  중간  뒤"

    def test_paragraph_style(self):
        """문단 스타일 테스트"""
        style = StyleInfo(font_size=14)
        para = Paragraph(style=style)

        assert para.style.font_size == 14


class TestTableCell:
    """TableCell 모델 테스트"""

    def test_cell_creation(self):
        """셀 생성 테스트"""
        cell = TableCell(text="셀 내용", row=0, col=0)

        assert cell.text == "셀 내용"
        assert cell.row == 0
        assert cell.col == 0
        assert cell.rowspan == 1
        assert cell.colspan == 1
        assert cell.is_header is False
        assert cell.merged is False

    def test_merged_cell(self):
        """병합된 셀 테스트"""
        cell = TableCell(
            text="병합된 셀",
            row=0,
            col=0,
            rowspan=2,
            colspan=3,
            merged=True
        )

        assert cell.rowspan == 2
        assert cell.colspan == 3
        assert cell.merged is True

    def test_header_cell(self):
        """헤더 셀 테스트"""
        cell = TableCell(text="헤더", row=0, col=0, is_header=True)

        assert cell.is_header is True


class TestTable:
    """Table 모델 테스트"""

    def test_table_creation(self):
        """테이블 생성 테스트"""
        table = Table()

        assert table.rows == []
        assert table.caption is None
        assert table.style_id is None

    def test_add_row(self):
        """행 추가 테스트"""
        table = Table()

        # 첫 번째 행
        row1 = [
            TableCell(text="A1", row=0, col=0),
            TableCell(text="B1", row=0, col=1)
        ]
        table.add_row(row1)

        # 두 번째 행
        row2 = [
            TableCell(text="A2", row=1, col=0),
            TableCell(text="B2", row=1, col=1)
        ]
        table.add_row(row2)

        assert len(table.rows) == 2
        assert len(table.rows[0]) == 2
        assert table.rows[0][0].text == "A1"
        assert table.rows[1][1].text == "B2"

    def test_get_data(self):
        """테이블 데이터 가져오기 테스트"""
        table = Table()

        # 헤더 행
        header_row = [
            TableCell(text="컬럼1", row=0, col=0),
            TableCell(text="컬럼2", row=0, col=1)
        ]
        table.add_row(header_row)

        # 데이터 행
        data_row = [
            TableCell(text="값1", row=1, col=0),
            TableCell(text="값2", row=1, col=1)
        ]
        table.add_row(data_row)

        data = table.get_data()

        assert len(data) == 2
        assert data[0] == ["컬럼1", "컬럼2"]
        assert data[1] == ["값1", "값2"]

    def test_table_with_caption(self):
        """캡션이 있는 테이블 테스트"""
        table = Table(caption="테이블 1: 데이터")

        assert table.caption == "테이블 1: 데이터"

    def test_empty_table(self):
        """빈 테이블 테스트"""
        table = Table()

        data = table.get_data()
        assert data == []


class TestImage:
    """Image 모델 테스트"""

    def test_image_creation(self):
        """이미지 생성 테스트"""
        img = Image(name="test.png")

        assert img.name == "test.png"
        assert img.width is None
        assert img.height is None
        assert img.position is None
        assert img.caption is None
        assert img.path is None
        assert img.data is None

    def test_image_with_data(self):
        """데이터가 있는 이미지 테스트"""
        img_data = b"fake_image_data"
        position = {"x": 100, "y": 200}

        img = Image(
            name="image.jpg",
            width=300,
            height=200,
            position=position,
            caption="테스트 이미지",
            data=img_data
        )

        assert img.name == "image.jpg"
        assert img.width == 300
        assert img.height == 200
        assert img.position == position
        assert img.caption == "테스트 이미지"
        assert img.data == img_data

    def test_image_with_path(self):
        """경로가 있는 이미지 테스트"""
        img = Image(
            name="diagram.png",
            path="images/diagram.png"
        )

        assert img.name == "diagram.png"
        assert img.path == "images/diagram.png"


class TestSection:
    """Section 모델 테스트"""

    def test_section_creation(self):
        """섹션 생성 테스트"""
        section = Section()

        assert section.paragraphs == []
        assert section.tables == []
        assert section.images == []
        assert section.section_id is None

    def test_add_paragraph(self):
        """문단 추가 테스트"""
        section = Section()

        para1 = Paragraph()
        para1.runs.append(TextRun(text="첫 번째 문단"))

        para2 = Paragraph()
        para2.runs.append(TextRun(text="두 번째 문단"))

        section.paragraphs.extend([para1, para2])

        assert len(section.paragraphs) == 2
        assert section.paragraphs[0].get_text() == "첫 번째 문단"
        assert section.paragraphs[1].get_text() == "두 번째 문단"

    def test_add_table(self):
        """표 추가 테스트"""
        section = Section()

        table = Table()
        table.add_row([TableCell(text="셀1", row=0, col=0)])

        section.tables.append(table)

        assert len(section.tables) == 1
        assert section.tables[0].rows[0][0].text == "셀1"

    def test_add_image(self):
        """이미지 추가 테스트"""
        section = Section()

        img = Image(name="test.png", caption="테스트")
        section.images.append(img)

        assert len(section.images) == 1
        assert section.images[0].name == "test.png"
        assert section.images[0].caption == "테스트"

    def test_section_id_assignment(self):
        """섹션 ID 할당 테스트"""
        section = Section()
        section.section_id = 5

        assert section.section_id == 5

    def test_is_empty(self):
        """섹션이 비어있는지 확인 테스트"""
        section = Section()

        # 내용이 없으면 비어있음
        assert not section.paragraphs
        assert not section.tables
        assert not section.images

        # 문단이 있으면 비어있지 않음
        para = Paragraph()
        para.runs.append(TextRun(text="내용"))
        section.paragraphs.append(para)

        assert section.paragraphs