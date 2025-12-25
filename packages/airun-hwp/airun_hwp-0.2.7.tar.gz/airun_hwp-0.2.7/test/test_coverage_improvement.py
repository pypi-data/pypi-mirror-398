"""
커버리지 개선을 위한 추가 테스트

테스트 커버리지를 높이기 위해 누락된 기능들을 테스트합니다.
"""

import pytest
import tempfile
import os
from pathlib import Path
import sys
from unittest.mock import patch, mock_open, MagicMock

# 프로젝트 루트를 파이썬 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from airun_hwp.reader.hwpx_reader import HWPXReader
from airun_hwp.writer.hwpx_writer import HWPXWriter, BatchHWPXWriter
from airun_hwp.models.document import HWPXDocument
from airun_hwp.models.metadata import DocumentMetadata
from airun_hwp.models.content import Section, Paragraph, TextRun, StyleInfo


class TestHWPXReaderCoverage:
    """HWPXReader 커버리지 개선 테스트"""

    def test_parse_datetime_valid(self):
        """유효한 날짜시간 파싱 테스트"""
        reader = HWPXReader()

        # ISO 8601 형식
        dt = reader._parse_datetime("2024-01-01T10:00:00Z")
        assert dt is not None
        assert dt.year == 2024
        assert dt.month == 1
        assert dt.day == 1
        assert dt.hour == 10

        # Z 없는 형식
        dt2 = reader._parse_datetime("2024-01-01T10:00:00")
        assert dt2 is not None

    def test_parse_datetime_invalid(self):
        """유효하지 않은 날짜시간 파싱 테스트"""
        reader = HWPXReader()

        # 빈 문자열
        dt = reader._parse_datetime("")
        assert dt is None

        # None
        dt = reader._parse_datetime(None)
        assert dt is None

        # 잘못된 형식
        dt = reader._parse_datetime("invalid")
        assert dt is None

    def test_get_element_text_with_element(self):
        """요소에서 텍스트 가져오기 테스트"""
        reader = HWPXReader()

        # Mock element
        element = MagicMock()
        element.find.return_value = MagicMock()
        element.find.return_value.text = "테스트 텍스트"

        text = reader._get_element_text(element, ".//hc:title")
        assert text == "테스트 텍스트"

    def test_get_element_text_without_element(self):
        """요소가 없을 때 텍스트 가져오기 테스트"""
        reader = HWPXReader()

        text = reader._get_element_text(None, ".//hc:title")
        assert text is None

    def test_get_element_text_no_text(self):
        """텍스트가 없을 때 테스트"""
        reader = HWPXReader()

        element = MagicMock()
        element.find.return_value = None

        text = reader._get_element_text(element, ".//hc:title")
        assert text is None

    def test_get_element_attr_with_element(self):
        """요소에서 속성값 가져오기 테스트"""
        reader = HWPXReader()

        element = MagicMock()
        element.find.return_value = MagicMock()
        element.find.return_value.get.return_value = "attribute_value"

        attr = reader._get_element_attr(element, ".//hc:link", "prog")
        assert attr == "attribute_value"

    def test_get_element_attr_without_element(self):
        """요소가 없을 때 속성값 가져오기 테스트"""
        reader = HWPXReader()

        attr = reader._get_element_attr(None, ".//hc:link", "prog")
        assert attr is None

    def test_get_resource_type_image(self):
        """이미지 리소스 타입 확인 테스트"""
        reader = HWPXReader()

        res_type = reader._get_resource_type("test.png")
        assert res_type == "image"

        res_type = reader._get_resource_type("test.jpg")
        assert res_type == "image"

        res_type = reader._get_resource_type("test.jpeg")
        assert res_type == "image"

        res_type = reader._get_resource_type("test.gif")
        assert res_type == "image"

        res_type = reader._get_resource_type("test.bmp")
        assert res_type == "image"

    def test_get_resource_type_font(self):
        """폰트 리소스 타입 확인 테스트"""
        reader = HWPXReader()

        res_type = reader._get_resource_type("font.ttf")
        assert res_type == "font"

        res_type = reader._get_resource_type("font.otf")
        assert res_type == "font"

    def test_get_resource_type_unknown(self):
        """알 수 없는 리소스 타입 테스트"""
        reader = HWPXReader()

        res_type = reader._get_resource_type("file.dat")
        assert res_type == "unknown"

    def test_parse_run_without_text(self):
        """텍스트가 없는 런 파싱 테스트"""
        reader = HWPXReader()

        # Mock run element without text
        run_elem = MagicMock()
        run_elem.findall.return_value = []  # No text elements

        run = reader._parse_run(run_elem)
        assert run is None

    def test_parse_run_with_empty_text(self):
        """빈 텍스트를 가진 런 파싱 테스트"""
        reader = HWPXReader()

        # Mock run element with empty text
        run_elem = MagicMock()
        txt_elem = MagicMock()
        txt_elem.text = ""
        run_elem.findall.return_value = [txt_elem]

        run = reader._parse_run(run_elem)
        assert run is None

    def test_parse_table_no_rows(self):
        """행이 없는 표 파싱 테스트"""
        reader = HWPXReader()

        table_elem = MagicMock()
        table_elem.findall.return_value = []  # No rows

        table = reader._parse_table(table_elem)
        assert table is None

    def test_parse_image_no_name(self):
        """이름이 없는 이미지 파싱 테스트"""
        reader = HWPXReader()

        img_elem = MagicMock()
        img_elem.get.return_value = None  # No name

        image = reader._parse_image(img_elem)
        assert image is None


class TestHWPXWriterCoverage:
    """HWPXWriter 커버리지 개선 테스트"""

    def test_get_default_template_user_template(self):
        """사용자 템플릿 경로 확인 테스트"""
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = True

            writer = HWPXWriter()
            template = writer._get_default_template()

            # 사용자 템플릿 경로를 확인해야 함
            assert template is not None

    def test_cleanup_without_temp_dir(self):
        """임시 디렉토리가 없을 때 정리 테스트"""
        writer = HWPXWriter()
        writer.temp_dir = None

        # 예외 없어야 함
        writer._cleanup()

    def test_cleanup_with_nonexistent_dir(self):
        """존재하지 않는 임시 디렉토리 정리 테스트"""
        writer = HWPXWriter()
        writer.temp_dir = "/nonexistent/directory"

        # 예외 없어야 함
        writer._cleanup()

    def test_context_manager_with_exception(self):
        """예외 발생 시 컨텍스트 매니저 테스트"""
        writer = HWPXWriter()

        with pytest.raises(ValueError):
            with writer:
                raise ValueError("Test exception")

        # 정리되어야 함
        assert writer.temp_dir is None

    def test_from_markdown_with_template(self, sample_markdown, temp_dir):
        """템플릿을 사용한 Markdown 변환 테스트"""
        template_path = temp_dir / "template.hwpx"
        template_path.write_bytes(b"template")

        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result

            writer = HWPXWriter(template_path=str(template_path))
            output_path = temp_dir / "output.hwpx"

            success = writer.from_markdown(str(sample_markdown), str(output_path))

            assert success is True
            # subprocess 호출 확인
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            assert '--reference-doc' in args
            assert str(template_path) in args


class TestDocumentCoverage:
    """HWPXDocument 커버리지 개선 테스트"""

    def test_get_metadata_as_yaml_without_yaml(self):
        """YAML이 설치되지 않았을 때 메타데이터 변환 테스트"""
        metadata = DocumentMetadata(title="테스트")
        document = HWPXDocument(metadata=metadata)

        with patch.dict('sys.modules', {'yaml': None}):
            result = document.get_metadata_as_yaml()
            # YAML 없이도 동작해야 함
            assert "테스트" in result

    def test_detect_image_extension_png(self):
        """PNG 확장자 감지 테스트"""
        document = HWPXDocument()

        ext = document._detect_image_extension(b'\x89PNG\r\n\x1a\n')
        assert ext == '.png'

    def test_detect_image_extension_jpeg(self):
        """JPEG 확장자 감지 테스트"""
        document = HWPXDocument()

        ext = document._detect_image_extension(b'\xff\xd8\xff')
        assert ext == '.jpg'

    def test_detect_image_extension_gif(self):
        """GIF 확장자 감지 테스트"""
        document = HWPXDocument()

        ext = document._detect_image_extension(b'GIF87a')
        assert ext == '.gif'

    def test_detect_image_extension_bmp(self):
        """BMP 확장자 감지 테스트"""
        document = HWPXDocument()

        ext = document._detect_image_extension(b'BM')
        assert ext == '.bmp'

    def test_detect_image_extension_unknown(self):
        """알 수 없는 확장자 감지 테스트"""
        document = HWPXDocument()

        ext = document._detect_image_extension(b'unknown')
        assert ext == '.bin'

    def test_to_markdown_with_empty_sections(self, temp_dir):
        """빈 섹션이 있는 Markdown 변환 테스트"""
        document = HWPXDocument()
        section = Section()  # 빈 섹션
        document.add_section(section)

        markdown = document.to_markdown()
        # 빈 섹션은 포함되지 않아야 함
        assert markdown.count("---") == 2  # 시작과 끝만

    def test_validate_with_issues(self):
        """여러 유효성 문제가 있는 테스트"""
        document = HWPXDocument()
        # 제목 없음
        section = Section()  # 빈 섹션
        document.add_section(section)

        issues = document.validate()
        assert len(issues) >= 2
        assert any("no title" in issue.lower() for issue in issues)
        assert any("empty" in issue.lower() for issue in issues)


class TestStyleInfoCoverage:
    """StyleInfo 커버리지 개선 테스트"""

    def test_style_info_with_all_attributes(self):
        """모든 속성이 있는 스타일 정보 테스트"""
        style = StyleInfo(
            char_style_id="1",
            para_style_id="2",
            font_name="Arial",
            font_size=12,
            color="#FF0000",
            bold=True,
            italic=True,
            underline=True,
            strike_through=True
        )

        assert style.char_style_id == "1"
        assert style.para_style_id == "2"
        assert style.font_name == "Arial"
        assert style.font_size == 12
        assert style.color == "#FF0000"
        assert style.bold is True
        assert style.italic is True
        assert style.underline is True
        assert style.strike_through is True


class TestBatchWriterCoverage:
    """BatchHWPXWriter 커버리지 개선 테스트"""

    def test_process_directory_empty(self, temp_dir):
        """빈 디렉토리 처리 테스트"""
        input_dir = temp_dir / "empty"
        input_dir.mkdir()

        output_dir = temp_dir / "output"
        batch_writer = BatchHWPXWriter(str(output_dir))

        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result

            successful_files = batch_writer.process_directory(str(input_dir))

            assert successful_files == []

    def test_process_files_with_nonexistent_file(self, temp_dir):
        """존재하지 않는 파일 처리 테스트"""
        output_dir = temp_dir / "output"
        batch_writer = BatchHWPXWriter(str(output_dir))

        files = [
            str(temp_dir / "exists.md"),
            str(temp_dir / "nonexistent.md")
        ]

        # 존재하는 파일 생성
        Path(files[0]).touch()

        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result

            results = batch_writer.process_files(files)

            assert len(results) == 2
            assert results[files[0]] is True
            assert results[files[1]] is False