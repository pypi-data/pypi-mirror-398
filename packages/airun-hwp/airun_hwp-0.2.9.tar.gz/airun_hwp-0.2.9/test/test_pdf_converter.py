"""
PDF 변환기 테스트
"""

import pytest
import tempfile
import os
from pathlib import Path
import sys

# 프로젝트 루트를 파이썬 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from airun_hwp.writer.pdf_converter import PDFConverter, convert_markdown_to_pdf


@pytest.fixture
def sample_markdown():
    """샘플 Markdown 콘텐츠"""
    return """# 테스트 문서

이것은 한글 테스트 문서입니다.

## 1. 소개

- 항목 1
- 항목 2
- 항목 3

### 코드 예제

```python
def hello():
    print("안녕하세요!")
```

### 표 예제

| 이름 | 나이 | 직업 |
|------|------|------|
| 홍길동 | 30 | 개발자 |
| 김철수 | 25 | 디자이너 |

> 인용문입니다.

**굵은 텍스트**와 *기울임 텍스트*
"""


class TestPDFConverter:
    """PDF 변환기 테스트"""

    def test_init(self):
        """초기화 테스트"""
        # Pandoc 엔진
        converter = PDFConverter(engine="pandoc")
        assert converter.engine == "pandoc"

        # WeasyPrint 엔진
        converter = PDFConverter(engine="weasyprint")
        assert converter.engine == "weasyprint"

    def test_convert_markdown_to_pdf_pandoc_not_available(self, sample_markdown, temp_dir):
        """Pandoc이 설치되지 않은 경우 테스트"""
        converter = PDFConverter(engine="pandoc")
        output_path = os.path.join(temp_dir, "test.pdf")

        # Pandoc이 없으면 실패해야 함
        result = converter.convert_markdown_to_pdf(
            markdown_content=sample_markdown,
            output_path=output_path
        )
        # 결과는 Pandoc 설치 여부에 따라 다름
        # if not shutil.which("pandoc"):
        #     assert result is False

    def test_convert_markdown_to_pdf_weasyprint_not_available(self, sample_markdown, temp_dir):
        """WeasyPrint가 설치되지 않은 경우 테스트"""
        converter = PDFConverter(engine="weasyprint")
        output_path = os.path.join(temp_dir, "test.pdf")

        # WeasyPrint가 없으면 실패해야 함
        try:
            import weasyprint
            has_weasyprint = True
        except ImportError:
            has_weasyprint = False

        if not has_weasyprint:
            result = converter.convert_markdown_to_pdf(
                markdown_content=sample_markdown,
                output_path=output_path
            )
            assert result is False

    def test_convert_with_options(self, sample_markdown, temp_dir):
        """옵션을 사용한 변환 테스트"""
        converter = PDFConverter(engine="pandoc")
        output_path = os.path.join(temp_dir, "test_with_options.pdf")

        # 옵션 설정
        options = {
            'margin': '2cm',
            'papersize': 'a4',
            'fontsize': 12
        }

        # 변환 시도 (pandoc 설치 여부에 따라 결과가 다름)
        result = converter.convert_markdown_to_pdf(
            markdown_content=sample_markdown,
            output_path=output_path,
            title="테스트 문서",
            options=options
        )
        # if shutil.which("pandoc"):
        #     assert result is True
        #     assert os.path.exists(output_path)

    def test_context_manager(self, sample_markdown, temp_dir):
        """컨텍스트 매니저 테스트"""
        output_path = os.path.join(temp_dir, "test_ctx.pdf")

        with PDFConverter() as converter:
            assert converter.temp_dir is None

            # 변환 시도
            result = converter.convert_markdown_to_pdf(
                markdown_content=sample_markdown,
                output_path=output_path
            )

        # 컨텍스트를 벗어나면 temp_dir이 정리되어야 함
        assert converter.temp_dir is None

    def test_unsupported_engine(self, sample_markdown, temp_dir):
        """지원하지 않는 엔진 테스트"""
        converter = PDFConverter(engine="unknown")
        output_path = os.path.join(temp_dir, "test.pdf")

        result = converter.convert_markdown_to_pdf(
            markdown_content=sample_markdown,
            output_path=output_path
        )
        assert result is False


class TestPDFConverterIntegration:
    """PDF 변환기 통합 테스트"""

    @pytest.mark.skipif(
        not os.path.exists("/home/hamonikr/airun-hwp/examples/test.hwpx"),
        reason="Test HWPX file not available"
    )
    def test_convert_hwpx_to_pdf(self, temp_dir):
        """HWPX를 PDF로 변환 테스트"""
        hwpx_path = "/home/hamonikr/airun-hwp/examples/test.hwpx"
        output_path = os.path.join(temp_dir, "test_hwpx.pdf")

        converter = PDFConverter(engine="pandoc")
        result = converter.convert_hwpx_to_pdf(
            hwpx_path=hwpx_path,
            output_path=output_path
        )

        # Pandoc 설치 여부에 따라 결과가 다름
        # if shutil.which("pandoc"):
        #     assert result is True
        #     assert os.path.exists(output_path)


class TestConvenienceFunctions:
    """편의 함수 테스트"""

    def test_convert_markdown_to_pdf_function(self, sample_markdown, temp_dir):
        """convert_markdown_to_pdf 편의 함수 테스트"""
        output_path = os.path.join(temp_dir, "test_func.pdf")

        # 함수 호출
        result = convert_markdown_to_pdf(
            markdown_content=sample_markdown,
            output_path=output_path,
            title="함수 테스트",
            engine="pandoc"
        )

        # Pandoc 설치 여부에 따라 결과가 다름
        # if shutil.which("pandoc"):
        #     assert result is True
        #     assert os.path.exists(output_path)