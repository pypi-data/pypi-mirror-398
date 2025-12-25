"""
HWPX 문서 작성기 - Markdown에서 HWPX로 변환
"""

import os
import subprocess
import tempfile
import shutil
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

from ..models.document import HWPXDocument

logger = logging.getLogger(__name__)


class HWPXWriter:
    """pypandoc-hwpx를 사용한 HWPX 문서 작성기"""

    def __init__(self, template_path: Optional[str] = None):
        """초기화

        Args:
            template_path: HWPX 템플릿 파일 경로
        """
        self.template_path = template_path or self._get_default_template()
        self.temp_dir = None

    def _get_default_template(self) -> str:
        """기본 HWPX 템플릿 경로"""
        # 사용자의 .airun 디렉토리에서 템플릿 확인
        user_template = os.path.expanduser('~/.airun/templates/blank.hwpx')
        if os.path.exists(user_template):
            return user_template

        # pypandoc-hwpx의 내장 템플릿 사용
        return None

    def from_document(self, document: HWPXDocument, output_path: str) -> bool:
        """구조화된 문서 객체에서 HWPX 생성

        Args:
            document: HWPXDocument 객체
            output_path: 출력 HWPX 파일 경로

        Returns:
            bool: 성공 여부
        """
        logger.info(f"Creating HWPX: {output_path}")

        try:
            # 임시 디렉토리 생성
            self.temp_dir = tempfile.mkdtemp(prefix='hwpx_writer_')

            # 문서를 Markdown으로 변환
            md_path = os.path.join(self.temp_dir, 'document.md')
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(document.to_markdown())

            # 이미지 추출 (있는 경우)
            image_paths = []
            if document.resources:
                images_dir = os.path.join(self.temp_dir, 'images')
                os.makedirs(images_dir, exist_ok=True)
                image_paths = document.extract_images(images_dir)

            # pypandoc-hwpx로 HWPX 변환
            success = self._convert_with_pandoc(md_path, output_path)

            # 정리
            self._cleanup()

            return success

        except Exception as e:
            logger.error(f"Error creating HWPX: {str(e)}")
            self._cleanup()
            return False

    def from_markdown(self, markdown_path: str, output_path: str) -> bool:
        """Markdown 파일에서 HWPX 생성

        Args:
            markdown_path: Markdown 파일 경로
            output_path: 출력 HWPX 파일 경로

        Returns:
            bool: 성공 여부
        """
        logger.info(f"Converting Markdown to HWPX: {markdown_path} -> {output_path}")

        if not os.path.exists(markdown_path):
            logger.error(f"Markdown file not found: {markdown_path}")
            return False

        return self._convert_with_pandoc(markdown_path, output_path)

    def _convert_with_pandoc(self, input_path: str, output_path: str) -> bool:
        """pypandoc-hwpx를 사용하여 변환"""
        try:
            # 명령어 생성
            cmd = [
                'pypandoc-hwpx',
                input_path,
                '-o', output_path
            ]

            # 템플릿이 지정된 경우 추가
            if self.template_path:
                cmd.extend(['--reference-doc', self.template_path])

            # 명령어 실행
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30  # 30초 타임아웃
            )

            if result.returncode != 0:
                logger.error(f"pypandoc-hwpx error: {result.stderr}")
                return False

            logger.info(f"Successfully created HWPX: {output_path}")
            return True

        except subprocess.TimeoutExpired:
            logger.error("pypandoc-hwpx conversion timed out")
            return False
        except FileNotFoundError:
            logger.error("pypandoc-hwpx not found. Please install with: pip install pypandoc-hwpx")
            return False
        except Exception as e:
            logger.error(f"Error in pypandoc-hwpx conversion: {str(e)}")
            return False

    def _cleanup(self):
        """임시 파일 정리"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
                logger.debug(f"Cleaned up temporary directory: {self.temp_dir}")
            except Exception as e:
                logger.warning(f"Error cleaning up temp dir: {str(e)}")

            self.temp_dir = None

    def __enter__(self):
        """컨텍스트 매니저 진입"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """컨텍스트 매니저 종료"""
        self._cleanup()


class BatchHWPXWriter:
    """여러 HWPX 파일을 일괄 처리하는 배치 처리기"""

    def __init__(self, output_dir: str):
        """초기화

        Args:
            output_dir: 출력 HWPX 파일 디렉토리
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def process_directory(self, input_dir: str, pattern: str = "*.md") -> List[str]:
        """디렉토리의 파일 패턴과 일치하는 모든 파일 처리

        Args:
            input_dir: 입력 디렉토리
            pattern: 파일 패턴 (기본: "*.md")

        Returns:
            List[str]: 성공적으로 처리된 파일 목록
        """
        input_path = Path(input_dir)
        if not input_path.exists():
            logger.error(f"Input directory not found: {input_dir}")
            return []

        successful_files = []

        with HWPXWriter() as writer:
            for input_file in input_path.glob(pattern):
                output_file = self.output_dir / f"{input_file.stem}.hwpx"

                if writer.from_markdown(str(input_file), str(output_file)):
                    successful_files.append(str(output_file))
                    logger.info(f"Processed: {input_file.name} -> {output_file.name}")

        return successful_files

    def process_files(self, files: List[str]) -> Dict[str, bool]:
        """파일 목록 처리

        Args:
            files: 처리할 파일 경로 목록

        Returns:
            Dict[str, bool]: 파일 경로와 성공 여부의 딕셔너리
        """
        results = {}

        with HWPXWriter() as writer:
            for input_file in files:
                input_path = Path(input_file)
                if not input_path.exists():
                    results[input_file] = False
                    continue

                output_file = self.output_dir / f"{input_path.stem}.hwpx"

                if input_file.endswith('.md'):
                    success = writer.from_markdown(input_file, str(output_file))
                else:
                    logger.warning(f"Unsupported file type: {input_file}")
                    success = False

                results[input_file] = success

        return results