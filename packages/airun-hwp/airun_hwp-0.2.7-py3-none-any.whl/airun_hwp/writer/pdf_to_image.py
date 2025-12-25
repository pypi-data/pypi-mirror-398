"""
PDF를 이미지로 변환 - PDF 페이지별 이미지 추출
"""

import os
import tempfile
import logging
from pathlib import Path
from typing import List, Optional, Union, Dict, Any
import time

logger = logging.getLogger(__name__)

try:
    from pdf2image import convert_from_path
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False


class PDFToImageConverter:
    """PDF를 페이지별 이미지로 변환하는 컨버터"""

    def __init__(self, engine: str = "auto"):
        """초기화

        Args:
            engine: 변환 엔진 ('pdf2image', 'pymupdf', 'auto')
        """
        self.engine = engine
        self.temp_dir = None

        # 엔진 자동 선택
        if engine == "auto":
            if PYMUPDF_AVAILABLE:
                self.engine = "pymupdf"
            elif PDF2IMAGE_AVAILABLE:
                self.engine = "pdf2image"
            else:
                self.engine = None

    def convert_pdf_to_images(
        self,
        pdf_path: str,
        output_dir: str,
        format: str = "png",
        dpi: int = 200,
        first_page: Optional[int] = None,
        last_page: Optional[int] = None,
        progress_callback: Optional[callable] = None
    ) -> List[str]:
        """PDF를 페이지별 이미지로 변환

        Args:
            pdf_path: PDF 파일 경로
            output_dir: 출력 디렉토리
            format: 이미지 포맷 ('png', 'jpg', 'jpeg')
            dpi: 해상도 (DPI)
            first_page: 시작 페이지 (1부터 시작)
            last_page: 끝 페이지
            progress_callback: 진행률 콜백 함수

        Returns:
            생성된 이미지 파일 경로 리스트
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF 파일을 찾을 수 없습니다: {pdf_path}")

        # 출력 디렉토리 생성
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # 파일명 추출
        pdf_name = Path(pdf_path).stem

        # 엔진별 변환 실행
        if self.engine == "pdf2image" and PDF2IMAGE_AVAILABLE:
            return self._convert_with_pdf2image(
                pdf_path, output_dir, pdf_name, format, dpi,
                first_page, last_page, progress_callback
            )
        elif self.engine == "pymupdf" and PYMUPDF_AVAILABLE:
            return self._convert_with_pymupdf(
                pdf_path, output_dir, pdf_name, format, dpi,
                first_page, last_page, progress_callback
            )
        else:
            # 자동으로 사용 가능한 엔진 시도
            if PYMUPDF_AVAILABLE:
                self.engine = "pymupdf"
                return self._convert_with_pymupdf(
                    pdf_path, output_dir, pdf_name, format, dpi,
                    first_page, last_page, progress_callback
                )
            elif PDF2IMAGE_AVAILABLE:
                self.engine = "pdf2image"
                return self._convert_with_pdf2image(
                    pdf_path, output_dir, pdf_name, format, dpi,
                    first_page, last_page, progress_callback
                )
            else:
                raise RuntimeError(
                    "PDF를 이미지로 변환하려면 pdf2image 또는 PyMuPDF를 설치해야 합니다.\n"
                    "설치 명령어:\n"
                    "  pip install pdf2image poppler-utils\n"
                    "  또는\n"
                    "  pip install pymupdf"
                )

    def _convert_with_pdf2image(
        self,
        pdf_path: str,
        output_dir: str,
        pdf_name: str,
        format: str,
        dpi: int,
        first_page: Optional[int],
        last_page: Optional[int],
        progress_callback: Optional[callable]
    ) -> List[str]:
        """pdf2image를 사용하여 변환"""
        try:
            logger.info(f"pdf2image로 변환 시작: {pdf_path}")

            # 페이지 범위 설정
            pages_kwargs = {}
            if first_page is not None:
                pages_kwargs['first_page'] = first_page
            if last_page is not None:
                pages_kwargs['last_page'] = last_page

            # PDF를 이미지로 변환
            images = convert_from_path(
                pdf_path,
                dpi=dpi,
                output_folder=output_dir,
                fmt='ppm',  # 임시 포맷
                thread_count=4,
                **pages_kwargs
            )

            # 이미지 파일 저장
            image_paths = []
            total_pages = len(images)

            for i, image in enumerate(images):
                page_num = i + (first_page or 1)
                filename = f"{pdf_name}_page_{page_num:04d}.{format.lower()}"
                output_path = os.path.join(output_dir, filename)

                # 포맷에 따라 저장
                if format.lower() in ['jpg', 'jpeg']:
                    # JPEG는 RGB로 변환 필요
                    if image.mode in ('RGBA', 'LA', 'P'):
                        rgb_image = image.convert('RGB')
                    else:
                        rgb_image = image
                    rgb_image.save(output_path, 'JPEG', quality=95)
                else:
                    image.save(output_path, format.upper())

                image_paths.append(output_path)

                # 진행률 콜백
                if progress_callback:
                    progress = (i + 1) / total_pages * 100
                    progress_callback(progress, page_num, total_pages)

            logger.info(f"변환 완료: {len(image_paths)}개 이미지 생성")
            return image_paths

        except Exception as e:
            logger.error(f"pdf2image 변환 오류: {str(e)}")
            raise

    def _convert_with_pymupdf(
        self,
        pdf_path: str,
        output_dir: str,
        pdf_name: str,
        format: str,
        dpi: int,
        first_page: Optional[int],
        last_page: Optional[int],
        progress_callback: Optional[callable]
    ) -> List[str]:
        """PyMuPDF를 사용하여 변환"""
        try:
            logger.info(f"PyMuPDF로 변환 시작: {pdf_path}")

            # PDF 문서 열기
            doc = fitz.open(pdf_path)
            total_pages = doc.page_count

            # 페이지 범위 계산
            start_page = (first_page or 1) - 1
            end_page = min(last_page or total_pages, total_pages)

            # DPI에 따른 zoom 계산 (DPI 72 = zoom 1.0)
            zoom = dpi / 72.0
            matrix = fitz.Matrix(zoom, zoom)

            image_paths = []

            # 페이지별로 변환
            for page_num in range(start_page, end_page):
                page = doc.load_page(page_num)

                # 페이지를 이미지로 렌더링
                pix = page.get_pixmap(matrix=matrix)

                # 파일명 생성
                filename = f"{pdf_name}_page_{page_num + 1:04d}.{format.lower()}"
                output_path = os.path.join(output_dir, filename)

                # 이미지 저장
                if format.lower() in ['jpg', 'jpeg']:
                    pix.save(output_path, "jpeg")
                else:
                    pix.save(output_path, format.lower())

                image_paths.append(output_path)

                # 진행률 콜백
                if progress_callback:
                    progress = (page_num - start_page + 1) / (end_page - start_page) * 100
                    progress_callback(progress, page_num + 1, end_page)

            doc.close()
            logger.info(f"변환 완료: {len(image_paths)}개 이미지 생성")
            return image_paths

        except Exception as e:
            logger.error(f"PyMuPDF 변환 오류: {str(e)}")
            raise


def convert_hwpx_to_images(
    hwpx_path: str,
    output_dir: str,
    engine: str = "auto",
    format: str = "png",
    dpi: int = 200,
    keep_pdf: bool = False
) -> List[str]:
    """HWPX 파일을 페이지별 이미지로 변환

    Args:
        hwpx_path: HWPX 파일 경로
        output_dir: 출력 디렉토리
        engine: PDF 변환 엔진
        format: 이미지 포맷
        dpi: 이미지 해상도
        keep_pdf: 중간 생성된 PDF 파일 보존 여부

    Returns:
        생성된 이미지 파일 경로 리스트
    """
    try:
        # PDF 변환기 임포트
        from .pdf_converter import convert_hwpx_to_pdf

        # 임시 PDF 생성
        temp_pdf_path = os.path.join(output_dir, "temp_document.pdf")

        logger.info(f"HWPX를 PDF로 변환: {hwpx_path}")
        pdf_success = convert_hwpx_to_pdf(
            hwpx_path=hwpx_path,
            output_path=temp_pdf_path,
            engine="weasyprint",  # WeasyPrint가 더 안정적
            options={}
        )

        if not pdf_success:
            raise RuntimeError("HWPX를 PDF로 변환하는 데 실패했습니다")

        # PDF를 이미지로 변환
        converter = PDFToImageConverter(engine=engine)

        # 진행률 표시 함수
        def progress_callback(progress, current, total):
            print(f"\r변환 중: {current}/{total} 페이지 ({progress:.1f}%)", end='', flush=True)

        image_paths = converter.convert_pdf_to_images(
            pdf_path=temp_pdf_path,
            output_dir=output_dir,
            format=format,
            dpi=dpi,
            progress_callback=progress_callback
        )

        print()  # 개행

        # PDF 파일 삭제 (선택)
        if not keep_pdf:
            try:
                os.remove(temp_pdf_path)
                logger.info("임시 PDF 파일 삭제")
            except:
                pass

        return image_paths

    except Exception as e:
        logger.error(f"HWPX를 이미지로 변환하는 중 오류: {str(e)}")
        raise


# 편의 함수
def convert_pdf_to_images(
    pdf_path: str,
    output_dir: str,
    format: str = "png",
    dpi: int = 200,
    engine: str = "auto"
) -> List[str]:
    """PDF를 이미지로 변환하는 편의 함수

    Args:
        pdf_path: PDF 파일 경로
        output_dir: 출력 디렉토리
        format: 이미지 포맷
        dpi: 해상도
        engine: 변환 엔진

    Returns:
        생성된 이미지 파일 경로 리스트
    """
    converter = PDFToImageConverter(engine=engine)
    return converter.convert_pdf_to_images(
        pdf_path=pdf_path,
        output_dir=output_dir,
        format=format,
        dpi=dpi
    )