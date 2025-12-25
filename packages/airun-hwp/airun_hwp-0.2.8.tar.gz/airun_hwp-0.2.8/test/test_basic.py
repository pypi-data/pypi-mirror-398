"""
기본 기능 테스트

기존 기본 테스트를 개선하고 pytest 마커를 추가합니다.
"""

import pytest
import tempfile
import os
from pathlib import Path
import sys

# 프로젝트 루트를 파이썬 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from airun_hwp.models.document import HWPXDocument
from airun_hwp.models.metadata import DocumentMetadata
from airun_hwp.models.content import Section, Paragraph, TextRun, Table, TableCell, Image, StyleInfo
from airun_hwp.reader.hwpx_reader import HWPXReader
from airun_hwp.writer.hwpx_writer import HWPXWriter, BatchHWPXWriter


@pytest.mark.unit
class TestHWPXDocumentBasic:
    """HWPXDocument 기본 단위 테스트"""

    def test_document_creation_default(self):
        """기본값으로 문서 생성 테스트"""
        document = HWPXDocument()

        assert document.metadata is not None
        assert isinstance(document.metadata, DocumentMetadata)
        assert document.sections == []
        assert document.resources == {}
        assert document.styles == {}
        assert document.fonts == []

    def test_document_creation_with_metadata(self):
        """메타데이터와 문서 생성 테스트"""
        metadata = DocumentMetadata(title="테스트", author="작성자")
        document = HWPXDocument(metadata=metadata)

        assert document.metadata == metadata
        assert document.sections == []

    def test_add_section_single(self):
        """단일 섹션 추가 테스트"""
        document = HWPXDocument()
        section = Section()

        document.add_section(section)

        assert len(document.sections) == 1
        assert document.sections[0] == section
        assert section.section_id == 0

    def test_add_section_multiple(self):
        """여러 섹션 추가 테스트"""
        document = HWPXDocument()

        sections = [Section() for _ in range(3)]
        for section in sections:
            document.add_section(section)

        assert len(document.sections) == 3
        assert document.sections[0].section_id == 0
        assert document.sections[1].section_id == 1
        assert document.sections[2].section_id == 2

    def test_get_all_text_empty(self):
        """빈 문서에서 텍스트 추출 테스트"""
        document = HWPXDocument()

        text = document.get_all_text()
        assert text == ""

    def test_get_all_text_with_paragraphs(self):
        """문단이 있는 문서에서 텍스트 추출 테스트"""
        document = HWPXDocument()

        # 첫 번째 섹션
        section1 = Section()
        para1 = Paragraph()
        para1.runs.append(TextRun(text="첫 번째 문단"))
        para2 = Paragraph()
        para2.runs.append(TextRun(text="두 번째 문단"))
        section1.paragraphs.extend([para1, para2])
        document.add_section(section1)

        # 두 번째 섹션
        section2 = Section()
        para3 = Paragraph()
        para3.runs.append(TextRun(text="세 번째 문단"))
        section2.paragraphs.append(para3)
        document.add_section(section2)

        text = document.get_all_text()
        expected = "첫 번째 문단\n\n두 번째 문단\n\n세 번째 문단"
        assert text == expected

    def test_get_all_text_with_empty_paragraphs(self):
        """빈 문단이 있는 경우 텍스트 추출 테스트"""
        document = HWPXDocument()

        section = Section()
        para1 = Paragraph()
        para1.runs.append(TextRun(text="내용"))
        para2 = Paragraph()  # 빈 문단
        para3 = Paragraph()
        para3.runs.append(TextRun(text="내용"))
        section.paragraphs.extend([para1, para2, para3])

        document.add_section(section)

        text = document.get_all_text()
        # 빈 문단은 필터링됨
        assert text == "내용\n\n내용"

    @pytest.mark.parametrize("include_metadata", [True, False])
    def test_to_markdown_metadata_toggle(self, include_metadata):
        """메타데이터 포함/제외 Markdown 변환 테스트"""
        metadata = DocumentMetadata(
            title="테스트 문서",
            author="작성자"
        )
        document = HWPXDocument(metadata=metadata)

        markdown = document.to_markdown(include_metadata=include_metadata)

        if include_metadata:
            assert "title:" in markdown
            assert "author:" in markdown
            assert "---" in markdown
        else:
            # 메타데이터가 없으면 바로 콘텐츠로 시작
            assert markdown.strip() == ""

    def test_validate_perfect_document(self):
        """완벽한 문서 유효성 검증 테스트"""
        metadata = DocumentMetadata(
            title="완벽한 문서",
            author="작성자"
        )
        document = HWPXDocument(metadata=metadata)

        section = Section()
        para = Paragraph()
        para.runs.append(TextRun(text="내용"))
        section.paragraphs.append(para)
        document.add_section(section)

        issues = document.validate()
        # 경고는 있을 수 있으나 에러는 없어야 함
        assert not any(issue.startswith("Error:") for issue in issues)

    def test_validate_empty_document(self):
        """빈 문서 유효성 검증 테스트"""
        document = HWPXDocument()

        issues = document.validate()

        assert any("no title" in issue.lower() for issue in issues)
        assert any("no content sections" in issue.lower() for issue in issues)


@pytest.mark.unit
class TestStyleInfoBasic:
    """StyleInfo 기본 테스트"""

    def test_style_info_defaults(self):
        """스타일 정보 기본값 테스트"""
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

    @pytest.mark.parametrize("attr", [
        "bold", "italic", "underline", "strike_through"
    ])
    def test_boolean_attributes(self, attr):
        """불리언 속성 테스트"""
        style = StyleInfo()
        assert getattr(style, attr) is False

        # 값 설정
        setattr(style, attr, True)
        assert getattr(style, attr) is True

    def test_font_attributes(self):
        """폰트 속성 테스트"""
        style = StyleInfo(
            font_name="Arial",
            font_size=12,
            color="#FF0000"
        )

        assert style.font_name == "Arial"
        assert style.font_size == 12
        assert style.color == "#FF0000"


@pytest.mark.unit
class TestParagraphBasic:
    """Paragraph 기본 테스트"""

    def test_paragraph_defaults(self):
        """문단 기본값 테스트"""
        para = Paragraph()

        assert para.runs == []
        assert isinstance(para.style, StyleInfo)
        assert para.paragraph_id is None
        assert para.para_style_id is None

    def test_get_text_single_run(self):
        """단일 런 텍스트 추출 테스트"""
        para = Paragraph()
        run = TextRun(text="테스트")
        para.runs.append(run)

        text = para.get_text()
        assert text == "테스트"

    def test_get_text_multiple_runs(self):
        """여러 런 텍스트 추출 테스트"""
        para = Paragraph()
        runs = [
            TextRun(text="첫"),
            TextRun(text="번"),
            TextRun(text="째"),
        ]
        para.runs.extend(runs)

        text = para.get_text()
        assert text == "첫번째"

    def test_get_text_empty_runs(self):
        """빈 런이 있는 경우 테스트"""
        para = Paragraph()
        para.runs.extend([
            TextRun(text="앞"),
            TextRun(text=""),
            TextRun(text="뒤")
        ])

        text = para.get_text()
        assert text == "앞뒤"

    def test_get_text_with_spaces(self):
        """공백 포함 텍스트 테스트"""
        para = Paragraph()
        para.runs.extend([
            TextRun(text="단어 "),
            TextRun(text="사이"),
            TextRun(text=" 공백")
        ])

        text = para.get_text()
        assert text == "단어 사이 공백"


@pytest.mark.reader
@pytest.mark.unit
class TestHWPXReaderBasic:
    """HWPXReader 기본 테스트"""

    def test_reader_creation_default(self):
        """기본 리더 생성 테스트"""
        reader = HWPXReader()

        assert reader.strict_mode is False
        assert reader.metadata is not None
        assert reader.document is not None

    def test_reader_strict_mode(self):
        """엄격 모드 리더 생성 테스트"""
        reader = HWPXReader(strict_mode=True)

        assert reader.strict_mode is True

    def test_namespaces_constant(self):
        """네임스페이스 상수 테스트"""
        namespaces = HWPXReader.NAMESPACES

        assert 'hh' in namespaces
        assert 'hp' in namespaces
        assert 'hc' in namespaces
        assert 'hs' in namespaces

        # 네임스페이스 URL 확인
        assert 'hancom.co.kr' in namespaces['hh']
        assert 'hwpml/2011' in namespaces['hp']

    def test_parse_nonexistent_file(self):
        """존재하지 않는 파일 파싱 테스트"""
        reader = HWPXReader()

        with pytest.raises(FileNotFoundError):
            reader.parse("nonexistent.hwpx")

    def test_parse_wrong_extension(self, temp_dir):
        """잘못된 확장자 테스트"""
        reader = HWPXReader()
        wrong_file = temp_dir / "document.txt"
        wrong_file.write_text("not HWPX")

        with pytest.raises(ValueError, match="hwpx"):
            reader.parse(str(wrong_file))

    def test_get_validation_report_empty(self, sample_hwpx_file):
        """빈 유효성 검증 보고서 테스트"""
        reader = HWPXReader()
        reader.parse(str(sample_hwpx_file))

        report = reader.get_validation_report()
        assert isinstance(report, list)


@pytest.mark.writer
@pytest.mark.unit
class TestHWPXWriterBasic:
    """HWPXWriter 기본 테스트"""

    def test_writer_creation(self):
        """라이터 생성 테스트"""
        writer = HWPXWriter()

        assert writer.temp_dir is None
        assert writer.template_path is not None

    def test_writer_with_template(self, temp_dir):
        """템플릿 지정 라이터 생성 테스트"""
        template = temp_dir / "template.hwpx"
        template.write_bytes(b"template")

        writer = HWPXWriter(template_path=str(template))

        assert writer.template_path == str(template)

    def test_context_manager_basic(self):
        """컨텍스트 매니저 기본 테스트"""
        with HWPXWriter() as writer:
            assert writer.temp_dir is None

        # 컨텍스트 종료 후
        assert writer.temp_dir is None

    @pytest.fixture
    def mock_subprocess(self):
        """subprocess 모킹"""
        import subprocess
        original_run = subprocess.run

        def mock_run(cmd, *args, **kwargs):
            result = type('MockResult', (), {})()
            result.returncode = 0
            result.stdout = ""
            result.stderr = ""
            return result

        subprocess.run = mock_run
        yield
        subprocess.run = original_run

    def test_from_markdown_basic(self, sample_markdown, mock_subprocess):
        """기본 Markdown 변환 테스트"""
        writer = HWPXWriter()
        output = sample_markdown.parent / "output.hwpx"

        success = writer.from_markdown(str(sample_markdown), str(output))

        assert success is True

    def test_from_markdown_nonexistent(self, temp_dir):
        """존재하지 않는 Markdown 파일 테스트"""
        writer = HWPXWriter()
        output = temp_dir / "output.hwpx"

        success = writer.from_markdown("nonexistent.md", str(output))

        assert success is False


@pytest.mark.unit
class TestBatchHWPXWriterBasic:
    """BatchHWPXWriter 기본 테스트"""

    def test_batch_writer_creation(self, temp_dir):
        """배치 라이터 생성 테스트"""
        output_dir = temp_dir / "outputs"
        batch_writer = BatchHWPXWriter(str(output_dir))

        assert batch_writer.output_dir == Path(output_dir)
        assert output_dir.exists()

    def test_process_directory_nonexistent(self, temp_dir):
        """존재하지 않는 디렉토리 처리 테스트"""
        output_dir = temp_dir / "outputs"
        batch_writer = BatchHWPXWriter(str(output_dir))

        results = batch_writer.process_directory("nonexistent")

        assert results == []

    def test_process_files_empty_list(self, temp_dir):
        """빈 파일 목록 처리 테스트"""
        output_dir = temp_dir / "outputs"
        batch_writer = BatchHWPXWriter(str(output_dir))

        results = batch_writer.process_files([])

        assert results == {}

    @pytest.fixture
    def mock_batch_subprocess(self):
        """배치 처리용 subprocess 모킹"""
        import subprocess
        original_run = subprocess.run

        def mock_run(cmd, *args, **kwargs):
            result = type('MockResult', (), {})()
            result.returncode = 0
            result.stdout = ""
            result.stderr = ""
            return result

        subprocess.run = mock_run
        yield
        subprocess.run = original_run

    def test_process_files_unsupported_types(self, temp_dir, mock_batch_subprocess):
        """지원하지 않는 파일 타입 처리 테스트"""
        output_dir = temp_dir / "outputs"
        batch_writer = BatchHWPXWriter(str(output_dir))

        # 지원하지 않는 파일
        txt_file = temp_dir / "doc.txt"
        txt_file.write_text("plain text")

        results = batch_writer.process_files([str(txt_file)])

        assert len(results) == 1
        assert results[str(txt_file)] is False


@pytest.mark.unit
class TestImageBasic:
    """Image 모델 기본 테스트"""

    def test_image_creation_minimal(self):
        """최소 이미지 생성 테스트"""
        img = Image(name="test.png")

        assert img.name == "test.png"
        assert img.width is None
        assert img.height is None
        assert img.position is None
        assert img.caption is None
        assert img.path is None
        assert img.data is None

    def test_image_creation_full(self):
        """전체 속성 이미지 생성 테스트"""
        position = {"x": 100, "y": 200}
        img_data = b"fake image data"

        img = Image(
            name="full.png",
            width=300,
            height=200,
            position=position,
            caption="테스트 이미지",
            path="images/full.png",
            data=img_data
        )

        assert img.name == "full.png"
        assert img.width == 300
        assert img.height == 200
        assert img.position == position
        assert img.caption == "테스트 이미지"
        assert img.path == "images/full.png"
        assert img.data == img_data


@pytest.mark.unit
class TestTableBasic:
    """Table 모델 기본 테스트"""

    def test_table_creation_empty(self):
        """빈 테이블 생성 테스트"""
        table = Table()

        assert table.rows == []
        assert table.caption is None
        assert table.style_id is None

    def test_add_row_empty(self):
        """빈 행 추가 테스트"""
        table = Table()
        empty_row = []

        table.add_row(empty_row)

        assert len(table.rows) == 1
        assert table.rows[0] == []

    def test_add_row_single_cell(self):
        """단일 셀 행 추가 테스트"""
        table = Table()
        cell = TableCell(text="셀", row=0, col=0)
        row = [cell]

        table.add_row(row)

        assert len(table.rows) == 1
        assert len(table.rows[0]) == 1
        assert table.rows[0][0].text == "셀"

    def test_get_data_empty(self):
        """빈 테이블 데이터 가져오기 테스트"""
        table = Table()

        data = table.get_data()

        assert data == []

    def test_get_data_with_rows(self):
        """행이 있는 테이블 데이터 가져오기 테스트"""
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

        data = table.get_data()

        assert len(data) == 2
        assert data[0] == ["A1", "B1"]
        assert data[1] == ["A2", "B2"]

    def test_get_data_with_merged_cells(self):
        """병합된 셀이 있는 테이블 데이터 테스트"""
        table = Table()

        # 병합된 셀
        merged_cell = TableCell(
            text="병합",
            row=0,
            col=0,
            rowspan=2,
            colspan=2,
            merged=True
        )
        table.add_row([merged_cell])

        data = table.get_data()

        # 데이터는 실제 행에 있는 셀들만 반환
        assert data == [["병합"]]


@pytest.mark.unit
class TestDocumentMarkdown:
    """문서 Markdown 변환 상세 테스트"""

    def test_to_markdown_with_tables(self):
        """표가 포함된 Markdown 변환 테스트"""
        document = HWPXDocument()
        section = Section()

        # 표 추가
        table = Table(caption="테스트 표")
        header_row = [
            TableCell(text="컬럼1", row=0, col=0, is_header=True),
            TableCell(text="컬럼2", row=0, col=1, is_header=True)
        ]
        data_row = [
            TableCell(text="값1", row=1, col=0),
            TableCell(text="값2", row=1, col=1)
        ]
        table.add_row(header_row)
        table.add_row(data_row)
        section.tables.append(table)

        document.add_section(section)

        markdown = document.to_markdown()

        assert "### Table" in markdown
        assert "| 컬럼1 | 컬럼2 |" in markdown
        assert "| 값1 | 값2 |" in markdown

    def test_to_markdown_with_images(self):
        """이미지가 포함된 Markdown 변환 테스트"""
        document = HWPXDocument()
        section = Section()

        # 이미지 추가
        img = Image(
            name="test.png",
            path="images/test.png",
            caption="테스트 이미지"
        )
        section.images.append(img)

        document.add_section(section)

        markdown = document.to_markdown()

        assert "![테스트 이미지](images/test.png)" in markdown

    def test_to_markdown_multiple_sections(self):
        """여러 섹션 Markdown 변환 테스트"""
        document = HWPXDocument()

        # 첫 번째 섹션
        section1 = Section()
        para1 = Paragraph()
        para1.runs.append(TextRun(text="첫 번째 섹션"))
        section1.paragraphs.append(para1)
        document.add_section(section1)

        # 두 번째 섹션
        section2 = Section()
        para2 = Paragraph()
        para2.runs.append(TextRun(text="두 번째 섹션"))
        section2.paragraphs.append(para2)
        document.add_section(section2)

        markdown = document.to_markdown()

        assert "첫 번째 섹션" in markdown
        assert "두 번째 섹션" in markdown
        assert "\n---\n" in markdown  # 섹션 구분자