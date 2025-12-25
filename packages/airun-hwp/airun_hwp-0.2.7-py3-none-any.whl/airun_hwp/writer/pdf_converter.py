"""
PDF 변환기 - Markdown을 PDF로 변환
"""

import os
import subprocess
import tempfile
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import time

logger = logging.getLogger(__name__)


class PDFConverter:
    """Markdown을 PDF로 변환하는 컨버터"""

    def __init__(self, engine: str = "pandoc"):
        """초기화

        Args:
            engine: 변환 엔진 ('pandoc' 또는 'weasyprint')
        """
        self.engine = engine
        self.temp_dir = None

    def convert_markdown_to_pdf(
        self,
        markdown_content: str,
        output_path: str,
        title: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Markdown을 PDF로 변환

        Args:
            markdown_content: Markdown 콘텐츠
            output_path: 출력 PDF 파일 경로
            title: PDF 제목 (선택 사항)
            options: 추가 옵션 (선택 사항)

        Returns:
            성공 여부
        """
        try:
            # 임시 디렉토리 생성
            self.temp_dir = tempfile.mkdtemp(prefix="airun_pdf_")

            # Markdown 파일 저장
            md_path = os.path.join(self.temp_dir, "content.md")
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)

            # 변환 옵션 설정
            if options is None:
                options = {}

            # 엔진별 변환 실행
            if self.engine == "pandoc":
                success = self._convert_with_pandoc(md_path, output_path, title, options)
            elif self.engine == "weasyprint":
                success = self._convert_with_weasyprint(md_path, output_path, title, options)
            else:
                logger.error(f"Unsupported engine: {self.engine}")
                return False

            # 정리
            self._cleanup()

            if success and os.path.exists(output_path):
                logger.info(f"PDF created successfully: {output_path}")
                return True
            else:
                logger.error("PDF conversion failed")
                return False

        except Exception as e:
            logger.error(f"Error converting to PDF: {str(e)}")
            self._cleanup()
            return False

    def _convert_with_pandoc(
        self,
        md_path: str,
        output_path: str,
        title: Optional[str] = None,
        options: Dict[str, Any] = None
    ) -> bool:
        """Pandoc을 사용하여 PDF 변환"""
        try:
            # 기본 명령어
            cmd = [
                'pandoc',
                md_path,
                '-o', output_path,
                '--pdf-engine=xelatex',  # 한글 지원을 위해 xelatex 사용
                '-V', 'mainfont="NanumGothic"',  # 한글 폰트
                '-V', 'CJKmainfont="NanumGothic"',  # CJK 지원
                '--metadata', 'lang=ko',  # 한국어
            ]

            # 제목 설정
            if title:
                cmd.extend(['--metadata', f'title={title}'])

            # 추가 옵션
            if options:
                # 페이지 여백
                if 'margin' in options:
                    cmd.extend(['-V', f'geometry:margin={options["margin"]}'])

                # 페이지 크기
                if 'papersize' in options:
                    cmd.extend(['-V', f'geometry:paper={options["papersize"]}'])

                # 폰트 크기
                if 'fontsize' in options:
                    cmd.extend(['-V', f'fontsize={options["fontsize"]}pt'])

                # 테마/CSS
                if 'css' in options:
                    css_path = options['css']
                    if os.path.exists(css_path):
                        cmd.extend(['--css', css_path])

            # 실행
            logger.info(f"Running pandoc: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120  # 2분 타임아웃
            )

            if result.returncode == 0:
                logger.info("Pandoc conversion successful")
                return True
            else:
                logger.error(f"Pandoc error: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            logger.error("Pandoc conversion timed out")
            return False
        except FileNotFoundError:
            logger.error("Pandoc not found. Please install pandoc with LaTeX support")
            return False
        except Exception as e:
            logger.error(f"Error in pandoc conversion: {str(e)}")
            return False

    def _convert_with_weasyprint(
        self,
        md_path: str,
        output_path: str,
        title: Optional[str] = None,
        options: Dict[str, Any] = None
    ) -> bool:
        """WeasyPrint를 사용하여 PDF 변환"""
        try:
            # WeasyPrint가 설치되었는지 확인
            try:
                import weasyprint
            except ImportError:
                logger.error("WeasyPrint not installed. Please install with: pip install weasyprint")
                return False

            # Markdown을 HTML로 변환 (간단한 방식)
            import markdown
            md = markdown.Markdown(extensions=['tables', 'fenced_code'])

            # CSS 스타일 (한글 지원)
            css = """
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Nanum+Gothic&display=swap');
                body {
                    font-family: 'NanumGothic', sans-serif;
                    font-size: 12pt;
                    line-height: 1.6;
                    margin: 2cm;
                }
                h1, h2, h3, h4, h5, h6 {
                    font-family: 'NanumGothic', sans-serif;
                    font-weight: bold;
                    margin-top: 1.5em;
                    margin-bottom: 0.5em;
                }
                table {
                    border-collapse: collapse;
                    width: 100%;
                    margin: 1em 0;
                }
                th, td {
                    border: 1px solid #ddd;
                    padding: 8px;
                    text-align: left;
                }
                th {
                    background-color: #f5f5f5;
                }
                img {
                    max-width: 100%;
                    height: auto;
                }
                code {
                    background-color: #f5f5f5;
                    padding: 2px 4px;
                    border-radius: 3px;
                }
                pre {
                    background-color: #f5f5f5;
                    padding: 10px;
                    border-radius: 5px;
                    overflow-x: auto;
                }
            </style>
            """

            # HTML 생성
            with open(md_path, 'r', encoding='utf-8') as f:
                md_content = f.read()

            html_content = md.convert(md_content)

            # 전체 HTML 문서
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                {css}
                {f'<title>{title}</title>' if title else ''}
            </head>
            <body>
                {html_content}
            </body>
            </html>
            """

            # 이미지 경로를 절대 경로로 변환
            import re
            base_dir = Path(self.temp_dir).parent  # 출력 디렉토리

            def replace_image_urls(html_text):
                # 이미지 URL을 절대 경로로 변환
                def replacer(match):
                    alt_text = match.group(1)
                    img_path = match.group(2)

                    # 상대 경로인 경우 절대 경로로 변환
                    if not img_path.startswith(('http://', 'https://', '/')):
                        full_path = base_dir / img_path
                        if full_path.exists():
                            abs_path = full_path.absolute()
                            return f'![{alt_text}]({abs_path})'
                    return match.group(0)

                # 마크다운 이미지 패턴 찾기
                pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
                return re.sub(pattern, replacer, html_text)

            html = replace_image_urls(html)

            # WeasyPrint로 PDF 변환
            logger.info("Converting with WeasyPrint...")
            html_doc = weasyprint.HTML(string=html)
            html_doc.write_pdf(output_path)

            logger.info("WeasyPrint conversion successful")
            return True

        except Exception as e:
            logger.error(f"Error in WeasyPrint conversion: {str(e)}")
            return False

    def convert_hwpx_to_pdf(
        self,
        hwpx_path: str,
        output_path: str,
        options: Optional[Dict[str, Any]] = None
    ) -> bool:
        """HWPX 파일을 PDF로 직접 변환

        Args:
            hwpx_path: HWPX 파일 경로
            output_path: 출력 PDF 파일 경로
            options: 변환 옵션

        Returns:
            성공 여부
        """
        try:
            # HWPXReader 임포트
            from ..reader.hwpx_reader import HWPXReader

            # HWPX 파일 파싱
            reader = HWPXReader()
            document = reader.parse(hwpx_path)

            # Markdown 변환
            markdown_content = document.to_markdown(include_metadata=True)

            # PDF 변환
            return self.convert_markdown_to_pdf(
                markdown_content=markdown_content,
                output_path=output_path,
                title=document.metadata.title,
                options=options
            )

        except Exception as e:
            logger.error(f"Error converting HWPX to PDF: {str(e)}")
            return False

    def _cleanup(self):
        """임시 파일 정리"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            import shutil
            try:
                shutil.rmtree(self.temp_dir)
                self.temp_dir = None
            except Exception as e:
                logger.warning(f"Failed to cleanup temp directory: {str(e)}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._cleanup()


# 편의 함수
def convert_markdown_to_pdf(
    markdown_content: str,
    output_path: str,
    title: Optional[str] = None,
    engine: str = "pandoc",
    options: Optional[Dict[str, Any]] = None
) -> bool:
    """Markdown을 PDF로 변환하는 편의 함수

    Args:
        markdown_content: Markdown 콘텐츠
        output_path: 출력 PDF 파일 경로
        title: PDF 제목 (선택 사항)
        engine: 변환 엔진 ('pandoc' 또는 'weasyprint')
        options: 추가 옵션

    Returns:
        성공 여부
    """
    with PDFConverter(engine=engine) as converter:
        return converter.convert_markdown_to_pdf(
            markdown_content=markdown_content,
            output_path=output_path,
            title=title,
            options=options
        )


def convert_hwpx_to_pdf(
    hwpx_path: str,
    output_path: str,
    engine: str = "pandoc",
    options: Optional[Dict[str, Any]] = None
) -> bool:
    """HWPX 파일을 PDF로 변환하는 편의 함수

    Args:
        hwpx_path: HWPX 파일 경로
        output_path: 출력 PDF 파일 경로
        engine: 변환 엔진
        options: 변환 옵션

    Returns:
        성공 여부
    """
    with PDFConverter(engine=engine) as converter:
        return converter.convert_hwpx_to_pdf(
            hwpx_path=hwpx_path,
            output_path=output_path,
            options=options
        )