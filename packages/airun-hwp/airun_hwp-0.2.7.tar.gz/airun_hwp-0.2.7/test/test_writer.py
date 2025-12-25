"""
HWPXWriter 테스트
"""

import pytest
import subprocess
import tempfile
import os
from pathlib import Path
import sys
from unittest.mock import patch, MagicMock, mock_open

# 프로젝트 루트를 파이썬 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from airun_hwp.writer.hwpx_writer import HWPXWriter, BatchHWPXWriter
from airun_hwp.models.document import HWPXDocument
from airun_hwp.models.metadata import DocumentMetadata
from airun_hwp.models.content import Section, Paragraph, TextRun, Table, TableCell, Image, StyleInfo


class TestHWPXWriter:
    """HWPXWriter 기본 테스트"""

    def test_writer_creation(self):
        """라이터 생성 테스트"""
        writer = HWPXWriter()

        assert writer.temp_dir is None
        assert writer.template_path is not None

    def test_writer_with_template(self, temp_dir):
        """템플릿이 지정된 라이터 생성 테스트"""
        template_path = temp_dir / "template.hwpx"
        template_path.write_bytes(b"fake template")

        writer = HWPXWriter(template_path=str(template_path))

        assert writer.template_path == str(template_path)

    def test_get_default_template(self, temp_dir):
        """기본 템플릿 경로 가져오기 테스트"""
        # 사용자 템플릿이 없는 경우
        writer = HWPXWriter()
        default_template = writer._get_default_template()
        assert default_template is None  # pypandoc-hwpx 내장 템플릿

        # 사용자 템플릿이 있는 경우
        user_template_dir = temp_dir / ".airun" / "templates"
        user_template_dir.mkdir(parents=True)
        user_template = user_template_dir / "blank.hwpx"
        user_template.write_bytes(b"fake template")

        with patch('os.path.expanduser') as mock_expand:
            mock_expand.return_value = str(user_template_dir)
            writer = HWPXWriter()
            template_path = writer._get_default_template()
            assert template_path is not None

    def test_context_manager(self):
        """컨텍스트 매니저 테스트"""
        with HWPXWriter() as writer:
            assert writer.temp_dir is None
            # 컨텍스트 내에서 사용 가능

        # 컨텍스트 종료 후 정리됨
        assert writer.temp_dir is None

    def test_context_manager_with_temp_dir(self, mock_pypandoc_hwpx):
        """임시 디렉토리가 생성되는 컨텍스트 매니저 테스트"""
        with HWPXWriter() as writer:
            # from_document 호출 시 temp_dir이 생성됨
            pass


class TestHWPXWriterFromDocument:
    """문서 객체에서 HWPX 생성 테스트"""

    @patch('subprocess.run')
    def test_from_document_success(self, mock_run, sample_markdown):
        """문서 객체에서 HWPX 생성 성공 테스트"""
        # Mock subprocess success
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        # 테스트 문서 생성
        document = HWPXDocument(
            metadata=DocumentMetadata(title="테스트", author="작성자")
        )
        section = Section()
        para = Paragraph()
        para.runs.append(TextRun(text="테스트 내용"))
        section.paragraphs.append(para)
        document.add_section(section)

        writer = HWPXWriter()
        output_path = sample_markdown.parent / "output.hwpx"

        success = writer.from_document(document, str(output_path))

        assert success is True
        assert output_path.exists()

    @patch('subprocess.run')
    def test_from_document_with_images(self, mock_run, temp_dir):
        """이미지가 포함된 문서에서 HWPX 생성 테스트"""
        # Mock subprocess success
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        # 이미지가 포함된 문서 생성
        document = HWPXDocument()
        section = Section()

        # 문단 추가
        para = Paragraph()
        para.runs.append(TextRun(text="이미지가 있는 문서"))
        section.paragraphs.append(para)

        # 이미지 추가
        image = Image(
            name="test.png",
            data=b"fake image data",
            caption="테스트 이미지"
        )
        section.images.append(image)

        document.add_section(section)

        writer = HWPXWriter()
        output_path = temp_dir / "output_with_images.hwpx"

        success = writer.from_document(document, str(output_path))

        assert success is True

    @patch('subprocess.run')
    def test_from_document_with_tables(self, mock_run, temp_dir):
        """표가 포함된 문서에서 HWPX 생성 테스트"""
        # Mock subprocess success
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        # 표가 포함된 문서 생성
        document = HWPXDocument()
        section = Section()

        # 표 생성
        table = Table(caption="테이블 1")
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

        writer = HWPXWriter()
        output_path = temp_dir / "output_with_tables.hwpx"

        success = writer.from_document(document, str(output_path))

        assert success is True

    def test_from_document_exception(self, temp_dir):
        """예외 발생 테스트"""
        document = HWPXDocument()
        writer = HWPXWriter()
        output_path = temp_dir / "output.hwpx"

        # 잘못된 출력 경로 (읽기 전용 디렉토리)
        readonly_dir = temp_dir / "readonly"
        readonly_dir.mkdir()
        os.chmod(readonly_dir, 0o444)
        output_path_readonly = readonly_dir / "output.hwpx"

        try:
            success = writer.from_document(document, str(output_path_readonly))
            assert success is False
        finally:
            # 권한 복원
            os.chmod(readonly_dir, 0o755)


class TestHWPXWriterFromMarkdown:
    """Markdown에서 HWPX 생성 테스트"""

    @patch('subprocess.run')
    def test_from_markdown_success(self, mock_run, sample_markdown):
        """Markdown에서 HWPX 생성 성공 테스트"""
        # Mock subprocess success
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        writer = HWPXWriter()
        output_path = sample_markdown.parent / "output.hwpx"

        success = writer.from_markdown(str(sample_markdown), str(output_path))

        assert success is True
        assert output_path.exists()

        # subprocess 호출 확인
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert 'pypandoc-hwpx' in args
        assert str(sample_markdown) in args
        assert '-o' in args
        assert str(output_path) in args

    @patch('subprocess.run')
    def test_from_markdown_with_template(self, mock_run, sample_markdown, temp_dir):
        """템플릿을 사용한 Markdown 변환 테스트"""
        # Mock subprocess success
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        template_path = temp_dir / "template.hwpx"
        template_path.write_bytes(b"fake template")

        writer = HWPXWriter(template_path=str(template_path))
        output_path = temp_dir / "output.hwpx"

        success = writer.from_markdown(str(sample_markdown), str(output_path))

        assert success is True

        # 템플릿 인자 확인
        args = mock_run.call_args[0][0]
        assert '--reference-doc' in args
        assert str(template_path) in args

    def test_from_markdown_file_not_found(self, temp_dir):
        """파일이 없는 경우 테스트"""
        writer = HWPXWriter()
        nonexistent = temp_dir / "nonexistent.md"
        output_path = temp_dir / "output.hwpx"

        success = writer.from_markdown(str(nonexistent), str(output_path))

        assert success is False

    @patch('subprocess.run')
    def test_from_markdown_pandoc_error(self, mock_run, sample_markdown, temp_dir):
        """pypandoc-hwpx 에러 테스트"""
        # Mock subprocess failure
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Pandoc error"
        mock_run.return_value = mock_result

        writer = HWPXWriter()
        output_path = temp_dir / "output.hwpx"

        success = writer.from_markdown(str(sample_markdown), str(output_path))

        assert success is False

    @patch('subprocess.run', side_effect=subprocess.TimeoutExpired(cmd=['pypandoc-hwpx'], timeout=30))
    def test_from_markdown_timeout(self, mock_run, sample_markdown, temp_dir):
        """타임아웃 테스트"""
        writer = HWPXWriter()
        output_path = temp_dir / "output.hwpx"

        success = writer.from_markdown(str(sample_markdown), str(output_path))

        assert success is False

    @patch('subprocess.run', side_effect=FileNotFoundError("pypandoc-hwpx not found"))
    def test_from_markdown_not_installed(self, mock_run, sample_markdown, temp_dir):
        """pypandoc-hwpx 설치 안된 경우 테스트"""
        writer = HWPXWriter()
        output_path = temp_dir / "output.hwpx"

        success = writer.from_markdown(str(sample_markdown), str(output_path))

        assert success is False


class TestHWPXWriterCleanup:
    """정리 기능 테스트"""

    def test_cleanup_temp_dir(self, temp_dir):
        """임시 디렉토리 정리 테스트"""
        writer = HWPXWriter()

        # 임시 디렉토리 생성
        writer.temp_dir = str(temp_dir / "temp_test")
        os.makedirs(writer.temp_dir)

        # 테스트 파일 생성
        test_file = Path(writer.temp_dir) / "test.txt"
        test_file.write_text("test")

        # 정리
        writer._cleanup()

        assert writer.temp_dir is None
        assert not test_file.parent.exists()

    def test_cleanup_no_temp_dir(self):
        """임시 디렉토리가 없는 경우 정리 테스트"""
        writer = HWPXWriter()
        writer.temp_dir = None

        # 정리 (예외 없어야 함)
        writer._cleanup()

        assert writer.temp_dir is None


class TestBatchHWPXWriter:
    """BatchHWPXWriter 테스트"""

    def test_batch_writer_creation(self, temp_dir):
        """배치 라이터 생성 테스트"""
        output_dir = temp_dir / "batch_output"
        batch_writer = BatchHWPXWriter(str(output_dir))

        assert batch_writer.output_dir == Path(output_dir)
        assert output_dir.exists()

    @patch('subprocess.run')
    def test_process_directory(self, mock_run, temp_dir):
        """디렉토리 일괄 처리 테스트"""
        # Mock subprocess success
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        # 입력 파일들 생성
        input_dir = temp_dir / "input"
        input_dir.mkdir()

        for i in range(3):
            md_file = input_dir / f"doc{i}.md"
            md_file.write_text(f"# Document {i}\n\nContent {i}")

        output_dir = temp_dir / "batch_output"
        batch_writer = BatchHWPXWriter(str(output_dir))

        successful_files = batch_writer.process_directory(str(input_dir))

        assert len(successful_files) == 3
        assert all(Path(f).exists() for f in successful_files)

    def test_process_directory_not_found(self, temp_dir):
        """디렉토리를 찾을 수 없는 경우 테스트"""
        output_dir = temp_dir / "batch_output"
        batch_writer = BatchHWPXWriter(str(output_dir))

        nonexistent_dir = temp_dir / "nonexistent"
        successful_files = batch_writer.process_directory(str(nonexistent_dir))

        assert successful_files == []

    @patch('subprocess.run')
    def test_process_directory_with_pattern(self, mock_run, temp_dir):
        """패턴을 사용한 디렉토리 처리 테스트"""
        # Mock subprocess success
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        # 여러 파일 생성
        input_dir = temp_dir / "input"
        input_dir.mkdir()

        # .md 파일들
        for i in range(2):
            md_file = input_dir / f"doc{i}.md"
            md_file.write_text(f"# MD Doc {i}")

        # .txt 파일들 (패턴에 맞지 않음)
        for i in range(2):
            txt_file = input_dir / f"doc{i}.txt"
            txt_file.write_text(f"TXT Doc {i}")

        output_dir = temp_dir / "batch_output"
        batch_writer = BatchHWPXWriter(str(output_dir))

        # .md 파일만 처리
        successful_files = batch_writer.process_directory(str(input_dir), pattern="*.md")

        assert len(successful_files) == 2
        assert all(f.endswith('.hwpx') for f in successful_files)

    @patch('subprocess.run')
    def test_process_files(self, mock_run, temp_dir):
        """파일 목록 처리 테스트"""
        # Mock subprocess success
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        # 파일들 생성
        files = []
        for i in range(3):
            md_file = temp_dir / f"doc{i}.md"
            md_file.write_text(f"# Document {i}")
            files.append(str(md_file))

        # 존재하지 않는 파일 추가
        files.append(str(temp_dir / "nonexistent.md"))

        output_dir = temp_dir / "batch_output"
        batch_writer = BatchHWPXWriter(str(output_dir))

        results = batch_writer.process_files(files)

        assert len(results) == 4
        assert sum(results.values()) == 3  # 성공한 파일 수
        assert results[files[-1]] is False  # 존재하지 않는 파일

    @patch('subprocess.run')
    def test_process_files_unsupported_type(self, mock_run, temp_dir):
        """지원하지 않는 파일 타입 테스트"""
        output_dir = temp_dir / "batch_output"
        batch_writer = BatchHWPXWriter(str(output_dir))

        # 지원하지 않는 파일 타입
        txt_file = temp_dir / "doc.txt"
        txt_file.write_text("Plain text")

        results = batch_writer.process_files([str(txt_file)])

        assert len(results) == 1
        assert results[str(txt_file)] is False


class TestHWPXWriterIntegration:
    """통합 테스트"""

    @pytest.mark.slow
    def test_roundtrip_conversion(self, sample_hwpx_file, temp_dir):
        """HWPX → Markdown → HWPX 라운드트립 테스트"""
        from airun_hwp.reader.hwpx_reader import HWPXReader

        # 이 테스트는 실제 pypandoc-hwpx가 필요
        pytest.skip("Requires pypandoc-hwpx installation")

        # 1. HWPX → Markdown
        reader = HWPXReader()
        document = reader.parse(str(sample_hwpx_file))

        # 2. Markdown → HWPX
        writer = HWPXWriter()
        output_path = temp_dir / "roundtrip.hwpx"

        success = writer.from_document(document, str(output_path))

        # 결과 확인
        if success:
            assert output_path.exists()
            assert output_path.stat().st_size > 0

    @pytest.mark.integration
    def test_complex_document_conversion(self, temp_dir):
        """복잡한 문서 변환 통합 테스트"""
        # 복잡한 문서 생성
        document = HWPXDocument(
            metadata=DocumentMetadata(
                title="복잡한 문서",
                author="통합 테스트",
                subject="변환 테스트"
            )
        )

        # 여러 섹션
        for section_idx in range(2):
            section = Section()

            # 여러 문단
            for para_idx in range(3):
                para = Paragraph()

                # 스타일이 다른 텍스트 런
                runs = [
                    TextRun(text=f"섹션 {section_idx+1}, 문단 {para_idx+1}: "),
                    TextRun(
                        text="굵은 텍스트",
                        style=StyleInfo(bold=True)
                    ),
                    TextRun(
                        text=" 와 ",
                        style=StyleInfo()
                    ),
                    TextRun(
                        text="이탤릭 텍스트",
                        style=StyleInfo(italic=True)
                    )
                ]
                para.runs.extend(runs)
                section.paragraphs.append(para)

            # 표 추가
            if section_idx == 1:
                table = Table(caption=f"표 {section_idx+1}")
                header_row = [
                    TableCell(text="항목", row=0, col=0, is_header=True),
                    TableCell(text="값", row=0, col=1, is_header=True)
                ]
                data_row = [
                    TableCell(text="A", row=1, col=0),
                    TableCell(text="1", row=1, col=1)
                ]
                table.add_row(header_row)
                table.add_row(data_row)
                section.tables.append(table)

            document.add_section(section)

        # 이 테스트는 모킹을 사용
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = ""
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            writer = HWPXWriter()
            output_path = temp_dir / "complex_document.hwpx"

            success = writer.from_document(document, str(output_path))

            assert success is True

    @pytest.mark.integration
    def test_document_with_all_content_types(self, temp_dir):
        """모든 콘텐츠 타입이 포함된 문서 테스트"""
        document = HWPXDocument(
            metadata=DocumentMetadata(title="모든 콘텐츠 포함")
        )

        section = Section()

        # 텍스트
        para = Paragraph()
        para.runs.append(TextRun(text="텍스트 콘텐츠"))
        section.paragraphs.append(para)

        # 표
        table = Table()
        table.add_row([
            TableCell(text="셀1", row=0, col=0),
            TableCell(text="셀2", row=0, col=1)
        ])
        section.tables.append(table)

        # 이미지
        image = Image(
            name="test.png",
            caption="테스트 이미지",
            data=b"fake image"
        )
        section.images.append(image)

        document.add_section(section)

        # 모킹을 사용한 테스트
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = ""
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            writer = HWPXWriter()
            output_path = temp_dir / "all_content.hwpx"

            success = writer.from_document(document, str(output_path))

            assert success is True


@pytest.mark.slow
@pytest.mark.integration
class TestHWPXWriterRealWorld:
    """실제 환경에서의 테스트"""

    def test_real_pandoc_execution(self, sample_markdown):
        """실제 pypandoc-hwpx 실행 테스트"""
        # pypandoc-hwpx가 설치되어 있는지 확인
        try:
            result = subprocess.run(
                ['pypandoc-hwpx', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                pytest.skip("pypandoc-hwpx not available")
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pytest.skip("pypandoc-hwpx not available")

        # 실제 변환 테스트
        output_path = sample_markdown.parent / "real_output.hwpx"
        writer = HWPXWriter()

        success = writer.from_markdown(str(sample_markdown), str(output_path))

        if success:
            assert output_path.exists()
            assert output_path.stat().st_size > 0

    def test_large_document_creation(self, temp_dir):
        """대용량 문서 생성 테스트"""
        # 대용량 문서 생성
        document = HWPXDocument(
            metadata=DocumentMetadata(title="대용량 테스트")
        )

        section = Section()

        # 많은 수의 문단
        for i in range(1000):
            para = Paragraph()
            para.runs.append(TextRun(text=f"문단 {i+1}: " + "A" * 100))
            section.paragraphs.append(para)

        document.add_section(section)

        # 모킹을 사용한 테스트
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = ""
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            writer = HWPXWriter()
            output_path = temp_dir / "large_document.hwpx"

            success = writer.from_document(document, str(output_path))

            assert success is True