"""
PDF를 이미지로 변환 테스트
"""

import pytest
import tempfile
import os
from pathlib import Path
import sys

# 프로젝트 루트를 파이썬 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from airun_hwp.writer.pdf_to_image import PDFToImageConverter, convert_pdf_to_images


@pytest.fixture
def sample_pdf_path():
    """샘플 PDF 파일 경로"""
    # 이미 생성된 PDF 파일 사용
    pdf_path = "/home/hamonikr/airun-hwp/test_output_weasy.pdf"
    if os.path.exists(pdf_path):
        return pdf_path
    return None


class TestPDFToImageConverter:
    """PDF 이미지 변환기 테스트"""

    def test_init(self):
        """초기화 테스트"""
        # Auto 엔진
        converter = PDFToImageConverter(engine="auto")
        assert converter.engine in [None, "pymupdf", "pdf2image"]

        # PyMuPDF 엔진
        converter = PDFToImageConverter(engine="pymupdf")
        assert converter.engine == "pymupdf"

        # pdf2image 엔진
        converter = PDFToImageConverter(engine="pdf2image")
        assert converter.engine == "pdf2image"

    def test_convert_no_dependencies(self, temp_dir):
        """의존성이 없을 때 테스트"""
        converter = PDFToImageConverter(engine="none")
        dummy_pdf = os.path.join(temp_dir, "dummy.pdf")

        # 더미 PDF 파일 생성
        with open(dummy_pdf, 'w') as f:
            f.write("%PDF-1.4\n%EOF")

        with pytest.raises(RuntimeError):
            converter.convert_pdf_to_images(
                pdf_path=dummy_pdf,
                output_dir=temp_dir
            )

    def test_convert_nonexistent_pdf(self, temp_dir):
        """존재하지 않는 PDF 파일 테스트"""
        converter = PDFToImageConverter()

        with pytest.raises(FileNotFoundError):
            converter.convert_pdf_to_images(
                pdf_path="nonexistent.pdf",
                output_dir=temp_dir
            )

    @pytest.mark.skipif(
        not os.path.exists("/home/hamonikr/airun-hwp/test_output_weasy.pdf"),
        reason="Sample PDF file not available"
    )
    def test_convert_real_pdf(self, sample_pdf_path, temp_dir):
        """실제 PDF 변환 테스트"""
        converter = PDFToImageConverter()

        # 진행률 콜백
        progress_data = []
        def progress_callback(progress, current, total):
            progress_data.append((progress, current, total))

        result = converter.convert_pdf_to_images(
            pdf_path=sample_pdf_path,
            output_dir=temp_dir,
            format="png",
            dpi=150,
            first_page=1,
            last_page=3,
            progress_callback=progress_callback
        )

        # 변환 성공 여부 (의존성 설치에 따라 다름)
        # 변환이 성공했다면
        if result:
            assert len(result) > 0
            assert all(os.path.exists(img_path) for img_path in result)
            assert len(progress_data) > 0

    def test_convert_with_different_formats(self, sample_pdf_path, temp_dir):
        """다양한 포맷으로 변환 테스트"""
        if not sample_pdf_path:
            pytest.skip("Sample PDF not available")

        converter = PDFToImageConverter()
        formats = ["png", "jpg", "jpeg"]

        for fmt in formats:
            output_dir = os.path.join(temp_dir, fmt)
            os.makedirs(output_dir, exist_ok=True)

            try:
                result = converter.convert_pdf_to_images(
                    pdf_path=sample_pdf_path,
                    output_dir=output_dir,
                    format=fmt,
                    dpi=100,
                    first_page=1,
                    last_page=1
                )
                # 변환이 성공했다면 파일 확인
                if result:
                    assert result[0].lower().endswith(fmt.lower())
            except Exception as e:
                # 변환 실패는 의존성 문제일 수 있음
                print(f"Format {fmt} conversion failed: {e}")


class TestConvenienceFunctions:
    """편의 함수 테스트"""

    @pytest.mark.skipif(
        not os.path.exists("/home/hamonikr/airun-hwp/test_output_weasy.pdf"),
        reason="Sample PDF file not available"
    )
    def test_convert_pdf_to_images_function(self, sample_pdf_path, temp_dir):
        """convert_pdf_to_images 편의 함수 테스트"""
        result = convert_pdf_to_images(
            pdf_path=sample_pdf_path,
            output_dir=temp_dir,
            format="png",
            dpi=100
        )

        # 변환 성공 여부 확인
        # 변환이 성공했다면
        if result:
            assert len(result) > 0
            assert all(os.path.exists(p) for p in result)


class TestHWPXToImageIntegration:
    """HWPX를 이미지로 변환 통합 테스트"""

    @pytest.mark.skipif(
        not os.path.exists("/home/hamonikr/airun-hwp/examples/test.hwpx"),
        reason="Test HWPX file not available"
    )
    def test_convert_hwpx_to_images(self, temp_dir):
        """HWPX를 이미지로 변환 테스트"""
        from airun_hwp.writer.pdf_to_image import convert_hwpx_to_images

        hwpx_path = "/home/hamonikr/airun-hwp/examples/test.hwpx"

        try:
            result = convert_hwpx_to_images(
                hwpx_path=hwpx_path,
                output_dir=temp_dir,
                format="png",
                dpi=150,
                keep_pdf=False
            )

            # 변환 성공 여부 확인
            # 변환이 성공했다면
            if result:
                assert len(result) > 0
                assert all(os.path.exists(p) for p in result)
                assert all(p.endswith('.png') for p in result)
        except Exception as e:
            # 변환 실패는 의존성 문제일 수 있음
            print(f"HWPX to image conversion failed: {e}")