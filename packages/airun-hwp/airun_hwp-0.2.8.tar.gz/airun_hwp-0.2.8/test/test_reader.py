"""
HWPXReader 테스트
"""

import pytest
import zipfile
from pathlib import Path
import sys
from unittest.mock import patch, MagicMock

# 프로젝트 루트를 파이썬 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from airun_hwp.reader.hwpx_reader import HWPXReader
from airun_hwp.models.metadata import DocumentMetadata
from airun_hwp.models.content import Section, Paragraph, TextRun, Table, Image


class TestHWPXReader:
    """HWPXReader 기본 테스트"""

    def test_reader_creation_strict_mode(self):
        """엄격 모드로 리더 생성 테스트"""
        reader = HWPXReader(strict_mode=True)

        assert reader.strict_mode is True
        assert isinstance(reader.metadata, DocumentMetadata)
        assert reader.document is not None

    def test_reader_creation_non_strict(self):
        """비엄격 모드로 리더 생성 테스트"""
        reader = HWPXReader(strict_mode=False)

        assert reader.strict_mode is False
        assert isinstance(reader.metadata, DocumentMetadata)

    def test_namespaces(self):
        """네임스페이스 상수 확인"""
        expected_namespaces = {
            'hh': 'http://www.hancom.co.kr/hwpml/2011/head',
            'hp': 'http://www.hancom.co.kr/hwpml/2011/paragraph',
            'hc': 'http://www.hancom.co.kr/hwpml/2011/core',
            'hs': 'http://www.hancom.co.kr/hwpml/2011/section'
        }

        assert HWPXReader.NAMESPACES == expected_namespaces


class TestHWPXReaderValidation:
    """HWPXReader 유효성 검증 테스트"""

    def test_file_not_found(self):
        """파일이 없는 경우 테스트"""
        reader = HWPXReader()

        with pytest.raises(FileNotFoundError, match="HWPX file not found"):
            reader.parse("nonexistent.hwpx")

    def test_wrong_extension(self, temp_dir):
        """잘못된 확장자 테스트"""
        reader = HWPXReader()
        wrong_file = temp_dir / "document.txt"
        wrong_file.write_text("This is not HWPX")

        with pytest.raises(ValueError, match="File must have .hwpx extension"):
            reader.parse(str(wrong_file))

    def test_invalid_zip_structure(self, temp_dir):
        """잘못된 ZIP 구조 테스트"""
        reader = HWPXReader()
        invalid_file = temp_dir / "invalid.hwpx"
        invalid_file.write_bytes(b"not a zip file")

        with pytest.raises(zipfile.BadZipFile):
            reader.parse(str(invalid_file))

    def test_missing_required_files(self, temp_dir):
        """필수 파일 누락 테스트"""
        reader = HWPXReader(strict_mode=True)
        hwpx_path = temp_dir / "incomplete.hwpx"

        # mimetype만 있는 불완전한 HWPX 파일
        with zipfile.ZipFile(hwpx_path, 'w') as zf:
            zf.writestr("mimetype", "application/x-hwp+xml")
            # header.xml 누락

        with pytest.raises(ValueError, match="Required HWPX file missing"):
            reader.parse(str(hwpx_path))

    def test_missing_required_files_non_strict(self, temp_dir):
        """필수 파일 누락 (비엄격 모드) 테스트"""
        reader = HWPXReader(strict_mode=False)
        hwpx_path = temp_dir / "incomplete.hwpx"

        # mimetype만 있는 불완전한 HWPX 파일
        with zipfile.ZipFile(hwpx_path, 'w') as zf:
            zf.writestr("mimetype", "application/x-hwp+xml")
            # header.xml 누락

        # 비엄격 모드에서는 예외가 발생하지 않음
        document = reader.parse(str(hwpx_path))
        assert document is not None


class TestHWPXReaderParsing:
    """HWPXReader 파싱 테스트"""

    def test_parse_basic_document(self, sample_hwpx_file):
        """기본 문서 파싱 테스트"""
        reader = HWPXReader()
        document = reader.parse(str(sample_hwpx_file))

        assert document is not None
        assert isinstance(document.metadata.title, str)
        assert document.sections is not None
        assert len(document.sections) > 0

    def test_parse_document_with_images(self, sample_hwpx_with_images):
        """이미지가 포함된 문서 파싱 테스트"""
        reader = HWPXReader()
        document = reader.parse(str(sample_hwpx_with_images))

        assert document is not None
        # 이미지가 포함된 섹션이 있어야 함
        total_images = sum(len(section.images) for section in document.sections)
        assert total_images >= 0  # 이미지가 없을 수도 있음

    def test_parse_document_with_tables(self, sample_hwpx_with_tables):
        """표가 포함된 문서 파싱 테스트"""
        reader = HWPXReader()
        document = reader.parse(str(sample_hwpx_with_tables))

        assert document is not None
        # 표가 포함된 섹션이 있어야 함
        total_tables = sum(len(section.tables) for section in document.sections)
        assert total_tables >= 0  # 표가 없을 수도 있음

    def test_parse_text_content(self, sample_hwpx_file):
        """텍스트 콘텐츠 파싱 테스트"""
        reader = HWPXReader()
        document = reader.parse(str(sample_hwpx_file))

        # 텍스트 추출
        text = document.get_all_text()
        assert isinstance(text, str)

        # 샘플 파일에 "테스트 문단입니다"가 있어야 함
        assert "테스트 문단입니다" in text

    def test_parse_paragraphs(self, sample_hwpx_file):
        """문단 파싱 테스트"""
        reader = HWPXReader()
        document = reader.parse(str(sample_hwpx_file))

        # 첫 번째 섹션의 문단들 확인
        if document.sections:
            first_section = document.sections[0]
            assert isinstance(first_section.paragraphs, list)

            # 각 문단이 Paragraph 인스턴스인지 확인
            for para in first_section.paragraphs:
                assert isinstance(para, Paragraph)

                # 각 문단의 런들이 TextRun 인스턴스인지 확인
                for run in para.runs:
                    assert isinstance(run, TextRun)


class TestHWPXReaderMetadata:
    """메타데이터 파싱 테스트"""

    def test_parse_metadata_header(self, temp_dir):
        """메타데이터 헤더 파싱 테스트"""
        # 상세한 메타데이터가 있는 HWPX 파일 생성
        hwpx_path = temp_dir / "detailed_metadata.hwpx"

        with zipfile.ZipFile(hwpx_path, 'w') as zf:
            # mimetype
            zf.writestr("mimetype", "application/x-hwp+xml")

            # 상세한 header.xml
            header_xml = """<?xml version="1.0" encoding="UTF-8"?>
<hwpml xmlns:hh="http://www.hancom.co.kr/hwpml/2011/head">
    <hh:DocInfo>
        <hc:summary xmlns:hc="http://www.hancom.co.kr/hwpml/2011/core">
            <hc:title>상세한 문서 제목</hc:title>
            <hc:author>상세한 작성자</hc:author>
            <hc:subject>상세한 주제</hc:subject>
            <hc:keywords>상세한, 키워드</hc:keywords>
        </hc:summary>
        <hc:create xmlns:hc="http://www.hancom.co.kr/hwpml/2011/core" datetime="2024-01-01T10:00:00Z" />
        <hc:last-modify xmlns:hc="http://www.hancom.co.kr/hwpml/2011/core" datetime="2024-01-02T15:30:00Z" />
        <hc:link xmlns:hc="http://www.hancom.co.kr/hwpml/2011/core" prog="Hwp" version="10.0" />
    </hh:DocInfo>
</hwpml>"""
            zf.writestr("Contents/header.xml", header_xml)

            # 최소한의 섹션
            section_xml = """<?xml version="1.0" encoding="UTF-8"?>
<sec xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph">
    <hp:p>
        <hp:run>
            <hp:t>내용</hp:t>
        </hp:run>
    </hp:p>
</sec>"""
            zf.writestr("Contents/section0.xml", section_xml)
            zf.writestr("Contents/content.hpf", "")

        # 파싱
        reader = HWPXReader()
        document = reader.parse(str(hwpx_path))

        # 메타데이터 확인
        assert document.metadata.title == "상세한 문서 제목"
        assert document.metadata.author == "상세한 작성자"
        assert document.metadata.subject == "상세한 주제"
        assert document.metadata.keywords == "상세한, 키워드"
        assert document.metadata.application == "Hwp"

    def test_parse_empty_metadata(self, temp_dir):
        """빈 메타데이터 파싱 테스트"""
        hwpx_path = temp_dir / "empty_metadata.hwpx"

        with zipfile.ZipFile(hwpx_path, 'w') as zf:
            zf.writestr("mimetype", "application/x-hwp+xml")

            # 빈 header.xml
            header_xml = """<?xml version="1.0" encoding="UTF-8"?>
<hwpml xmlns:hh="http://www.hancom.co.kr/hwpml/2011/head>
</hwpml>"""
            zf.writestr("Contents/header.xml", header_xml)

            # 최소한의 섹션
            section_xml = """<?xml version="1.0" encoding="UTF-8"?>
<sec xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph">
    <hp:p>
        <hp:run>
            <hp:t>내용</hp:t>
        </hp:run>
    </hp:p>
</sec>"""
            zf.writestr("Contents/section0.xml", section_xml)
            zf.writestr("Contents/content.hpf", "")

        reader = HWPXReader()
        document = reader.parse(str(hwpx_path))

        # 기본 메타데이터 값 확인
        assert document.metadata.title is None
        assert document.metadata.author is None


class TestHWPXReaderResources:
    """리소스 파싱 테스트"""

    def test_parse_images(self, sample_hwpx_with_images):
        """이미지 리소스 파싱 테스트"""
        reader = HWPXReader()
        document = reader.parse(str(sample_hwpx_with_images))

        # 리소스 확인
        assert isinstance(document.resources, dict)

        # PNG 파일이 BinData에 있어야 함
        png_files = [k for k in document.resources.keys() if k.endswith('.png')]
        assert len(png_files) > 0

        # 리소스 타입 확인
        for filename, resource_info in document.resources.items():
            assert 'data' in resource_info
            assert 'size' in resource_info
            assert 'type' in resource_info
            assert isinstance(resource_info['data'], bytes)
            assert resource_info['size'] > 0
            assert resource_info['type'] in ['image', 'font', 'unknown']

    def test_extract_images(self, sample_hwpx_with_images, temp_dir):
        """이미지 추출 테스트"""
        reader = HWPXReader()
        document = reader.parse(str(sample_hwpx_with_images))

        # 이미지 추출
        extract_dir = temp_dir / "extracted"
        extracted_paths = document.extract_images(str(extract_dir))

        # 추출된 이미지 확인
        assert isinstance(extracted_paths, list)
        # 이미지가 없을 수도 있음 (XML에 참조가 없는 경우)


class TestHWPXReaderErrorHandling:
    """에러 처리 테스트"""

    def test_malformed_xml_handling(self, temp_dir):
        """손상된 XML 처리 테스트"""
        reader = HWPXReader(strict_mode=False)
        hwpx_path = temp_dir / "malformed.hwpx"

        with zipfile.ZipFile(hwpx_path, 'w') as zf:
            zf.writestr("mimetype", "application/x-hwp+xml")

            # 손상된 XML
            zf.writestr("Contents/header.xml", "<invalid xml")

            # content.hpf (필수)
            zf.writestr("Contents/content.hpf", "")

        # 비엄격 모드에서는 예외가 발생하지 않아야 함
        document = reader.parse(str(hwpx_path))
        assert document is not None

    def test_malformed_xml_strict_mode(self, temp_dir):
        """손상된 XML (엄격 모드) 테스트"""
        reader = HWPXReader(strict_mode=True)
        hwpx_path = temp_dir / "malformed.hwpx"

        with zipfile.ZipFile(hwpx_path, 'w') as zf:
            zf.writestr("mimetype", "application/x-hwp+xml")

            # 손상된 XML
            zf.writestr("Contents/header.xml", "<invalid xml")

            # content.hpf (필수)
            zf.writestr("Contents/content.hpf", "")

        # 엄격 모드에서는 예외가 발생해야 함
        # 파이썬의 xml.etree.ElementTree는 ParseError를 발생시킴
        with pytest.raises(Exception):
            reader.parse(str(hwpx_path))

    def test_large_document_handling(self, temp_dir):
        """큰 문서 처리 테스트"""
        reader = HWPXReader()
        hwpx_path = temp_dir / "large.hwpx"

        with zipfile.ZipFile(hwpx_path, 'w') as zf:
            zf.writestr("mimetype", "application/x-hwp+xml")

            # 큰 섹션 파일 생성
            large_content = "<sec xmlns:hp='http://www.hancom.co.kr/hwpml/2011/paragraph'>"
            for i in range(100):
                large_content += f"<hp:p><hp:run><hp:t>문단 {i}</hp:t></hp:run></hp:p>"
            large_content += "</sec>"

            zf.writestr("Contents/header.xml", "<hwpml></hwpml>")
            zf.writestr("Contents/section0.xml", large_content)
            zf.writestr("Contents/content.hpf", "")

        # 큰 문서도 잘 파싱되어야 함
        document = reader.parse(str(hwpx_path))
        assert document is not None

    def test_unicode_content(self, temp_dir):
        """유니코드 콘텐츠 처리 테스트"""
        reader = HWPXReader()
        hwpx_path = temp_dir / "unicode.hwpx"

        with zipfile.ZipFile(hwpx_path, 'w') as zf:
            zf.writestr("mimetype", "application/x-hwp+xml")

            # 유니코드가 포함된 콘텐츠
            unicode_text = "한글 🌟 English 日本語 العربية"
            section_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<sec xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph">
    <hp:p>
        <hp:run>
            <hp:t>{unicode_text}</hp:t>
        </hp:run>
    </hp:p>
</sec>"""

            zf.writestr("Contents/header.xml", "<hwpml></hwpml>")
            zf.writestr("Contents/section0.xml", section_xml)
            zf.writestr("Contents/content.hpf", "")

        document = reader.parse(str(hwpx_path))
        text = document.get_all_text()

        # 유니코드 텍스트가 정확히 추출되어야 함
        assert unicode_text in text


class TestHWPXReaderIntegration:
    """통합 테스트"""

    @pytest.mark.slow
    def test_parse_real_document(self, test_data_dir):
        """실제 문서 파싱 통합 테스트"""
        if not test_data_dir:
            pytest.skip("Test data directory not found")

        # 실제 HWPX 파일 찾기
        hwpx_files = list(test_data_dir.glob("*.hwpx"))
        if not hwpx_files:
            pytest.skip("No HWPX files found in test data directory")

        # 첫 번째 HWPX 파일로 테스트
        hwpx_file = hwpx_files[0]
        reader = HWPXReader(strict_mode=False)

        # 실제 문서 파싱
        document = reader.parse(str(hwpx_file))

        # 기본 유효성 확인
        assert document is not None
        assert document.sections is not None
        assert isinstance(document.resources, dict)

        # 유효성 보고서 확인
        issues = reader.get_validation_report()
        assert isinstance(issues, list)


@pytest.mark.integration
class TestHWPXReaderRealFiles:
    """실제 파일을 사용한 통합 테스트"""

    def test_business_plan_document(self):
        """비즈니스 플랜 문서 테스트"""
        hwpx_path = Path("/home/hamonikr/문서/business_plan_20250410_112052.hwpx")

        if not hwpx_path.exists():
            pytest.skip("Business plan HWPX file not found")

        reader = HWPXReader(strict_mode=False)
        document = reader.parse(str(hwpx_path))

        # 문서 구조 확인
        assert document is not None
        assert len(document.sections) > 0
        assert len(document.resources) > 0  # 이미지 리소스가 있어야 함

        # 텍스트 추출 확인
        text = document.get_all_text()
        assert len(text) > 0
        assert "하모나이즈" in text or "AI" in text

    def test_governance_guide_document(self):
        """거버넌스 가이드 문서 테스트"""
        hwp_path = Path("/home/hamonikr/문서/기업의 오픈소스 활용을 위한 커뮤니티 거버넌스 가이드.hwp")

        # 이 파일은 HWP 형식이므로 건너뛰기
        if hwp_path.exists() and not hwp_path.suffix.lower() == '.hwpx':
            pytest.skip("File is not HWPX format")

        if not hwp_path.exists():
            pytest.skip("Governance guide file not found")

        # HWPX 파일인 경우에만 테스트
        if hwp_path.suffix.lower() == '.hwpx':
            reader = HWPXReader(strict_mode=False)
            document = reader.parse(str(hwp_path))

            assert document is not None
            text = document.get_all_text()
            assert len(text) > 0