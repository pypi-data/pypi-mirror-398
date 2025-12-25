"""
실제 문서를 이용한 테스트

준비된 실제 HWP/HWPX 파일을 테스트합니다.
"""

import pytest
import os
from pathlib import Path
import sys

# 프로젝트 루트를 파이썬 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from airun_hwp.reader.hwpx_reader import HWPXReader
from airun_hwp.writer.hwpx_writer import HWPXWriter
from airun_hwp.models.document import HWPXDocument


@pytest.mark.integration
class TestRealDocuments:
    """실제 문서 테스트"""

    @pytest.fixture
    def test_hwpx_file(self):
        """테스트용 HWPX 파일 경로"""
        hwpx_path = Path("/home/hamonikr/airun-hwp/examples/test.hwpx")
        if not hwpx_path.exists():
            pytest.skip(f"Test HWPX file not found: {hwpx_path}")
        return hwpx_path

    @pytest.fixture
    def test_hwp_file(self):
        """테스트용 HWP 파일 경로"""
        hwp_path = Path("/home/hamonikr/airun-hwp/examples/test.hwp")
        if not hwp_path.exists():
            pytest.skip(f"Test HWP file not found: {hwp_path}")
        return hwp_path

    def test_parse_real_hwpx(self, test_hwpx_file):
        """실제 HWPX 파일 파싱 테스트"""
        print(f"\nParsing HWPX file: {test_hwpx_file}")
        print(f"File size: {test_hwpx_file.stat().st_size} bytes")

        reader = HWPXReader(strict_mode=False)
        document = reader.parse(str(test_hwpx_file))

        # 기본 구조 확인
        assert document is not None
        assert isinstance(document, HWPXDocument)

        # 메타데이터 확인
        print(f"\nMetadata:")
        print(f"- Title: {document.metadata.title}")
        print(f"- Author: {document.metadata.author}")
        print(f"- Created: {document.metadata.created}")
        print(f"- Modified: {document.metadata.modified}")

        # 섹션 확인
        print(f"\nDocument structure:")
        print(f"- Sections: {len(document.sections)}")
        total_paragraphs = sum(len(s.paragraphs) for s in document.sections)
        total_tables = sum(len(s.tables) for s in document.sections)
        total_images = sum(len(s.images) for s in document.sections)
        print(f"- Total paragraphs: {total_paragraphs}")
        print(f"- Total tables: {total_tables}")
        print(f"- Total images: {total_images}")

        # 리소스 확인
        print(f"- Resources: {len(document.resources)}")
        if document.resources:
            for name, info in list(document.resources.items())[:5]:
                print(f"  - {name}: {info['size']} bytes ({info['type']})")

        # 텍스트 추출 확인
        text = document.get_all_text()
        print(f"\nExtracted text length: {len(text)} characters")
        if text:
            print(f"First 200 chars: {text[:200]}...")

        # 유효성 검증
        issues = document.validate()
        print(f"\nValidation issues: {len(issues)}")
        for issue in issues[:3]:  # 처음 3개만 표시
            print(f"  - {issue}")

        # 최소한의 콘텐츠가 있어야 함
        assert len(document.sections) > 0 or len(document.resources) > 0

    def test_parse_real_hwpx_with_images(self, test_hwpx_file):
        """이미지가 포함된 실제 HWPX 파일 테스트"""
        reader = HWPXReader(strict_mode=False)
        document = reader.parse(str(test_hwpx_file))

        # 이미지 정보 확인
        total_images = sum(len(section.images) for section in document.sections)
        print(f"\nImages found in sections: {total_images}")

        # BinData에 이미지 리소스가 있는지 확인
        image_resources = {
            name: info for name, info in document.resources.items()
            if info.get('type') == 'image' or name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))
        }
        print(f"Image resources in BinData: {len(image_resources)}")

        # 이미지 리소스 목록
        for name in list(image_resources.keys())[:5]:
            print(f"  - {name}")

        # 이미지 추출 테스트
        if image_resources:
            import tempfile
            with tempfile.TemporaryDirectory() as temp_dir:
                print(f"\nExtracting images to: {temp_dir}")
                extracted_paths = document.extract_images(temp_dir)
                print(f"Extracted images: {len(extracted_paths)}")
                for path in extracted_paths[:3]:
                    print(f"  - {path}")

    def test_markdown_conversion(self, test_hwpx_file):
        """Markdown 변환 테스트"""
        reader = HWPXReader(strict_mode=False)
        document = reader.parse(str(test_hwpx_file))

        # Markdown으로 변환
        markdown_content = document.to_markdown(include_metadata=True)

        # 기본 확인
        assert len(markdown_content) > 0

        # 메타데이터 포함 확인
        assert "---" in markdown_content

        # 파일로 저장
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write(markdown_content)
            md_path = f.name

        try:
            print(f"\nMarkdown file saved: {md_path}")
            print(f"File size: {os.path.getsize(md_path)} bytes")

            # 일부 내용 출력
            lines = markdown_content.split('\n')[:20]
            print("\nFirst 20 lines of Markdown:")
            for i, line in enumerate(lines, 1):
                if line.strip():
                    print(f"{i:2d}: {line[:100]}...")
        finally:
            # 정리
            if os.path.exists(md_path):
                os.unlink(md_path)

    def test_roundtrip_conversion(self, test_hwpx_file):
        """라운드트립 변환 테스트 (HWPX → Markdown → HWPX)"""
        pytest.skip("pypandoc-hwpx not installed for full roundtrip test")

        # 1. HWPX 파싱
        reader = HWPXReader(strict_mode=False)
        original_document = reader.parse(str(test_hwpx_file))

        # 2. Markdown 변환
        markdown_content = original_document.to_markdown()
        assert len(markdown_content) > 0

        # 3. Markdown에서 HWPX 생성 (pypandoc-hwpx 필요)
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write(markdown_content)
            md_path = f.name

        try:
            output_hwpx = tempfile.mktemp(suffix='.hwpx')
            writer = HWPXWriter()

            # 실제 pypandoc-hwpx가 있어야 함
            success = writer.from_markdown(md_path, output_hwpx)

            if success:
                print(f"\nRoundtrip successful: {output_hwpx}")
                print(f"Output file size: {os.path.getsize(output_hwpx)} bytes")

                # 4. 생성된 HWPX 다시 파싱
                new_reader = HWPXReader(strict_mode=False)
                new_document = new_reader.parse(output_hwpx)

                # 5. 기본 비교
                assert new_document is not None
                print(f"Original paragraphs: {sum(len(s.paragraphs) for s in original_document.sections)}")
                print(f"New paragraphs: {sum(len(s.paragraphs) for s in new_document.sections)}")

                # 정리
                os.unlink(output_hwpx)
        finally:
            if os.path.exists(md_path):
                os.unlink(md_path)

    def test_hwp_file_info(self, test_hwp_file):
        """HWP 파일 정보 확인"""
        print(f"\nHWP file: {test_hwp_file}")
        print(f"File size: {test_hwp_file.stat().st_size} bytes")

        # HWP 파일은 직접 파싱할 수 없고 외부 도구가 필요
        # 이 테스트는 파일이 존재하는지만 확인
        assert test_hwp_file.exists()
        assert test_hwp_file.suffix.lower() == '.hwp'

        print("Note: HWP files require external tool (hwp5txt) for parsing")


@pytest.mark.integration
@pytest.mark.slow
class TestDocumentAnalysis:
    """문서 상세 분석 테스트"""

    def test_analyze_document_structure(self):
        """문서 구조 분석 테스트"""
        hwpx_path = Path("/home/hamonikr/airun-hwp/examples/test.hwpx")
        if not hwpx_path.exists():
            pytest.skip("Test HWPX file not found")

        reader = HWPXReader(strict_mode=False)
        document = reader.parse(str(hwpx_path))

        # 상세 분석
        analysis = {
            "metadata": {
                "has_title": bool(document.metadata.title),
                "has_author": bool(document.metadata.author),
                "has_creation_date": bool(document.metadata.created)
            },
            "content": {
                "section_count": len(document.sections),
                "total_paragraphs": sum(len(s.paragraphs) for s in document.sections),
                "total_tables": sum(len(s.tables) for s in document.sections),
                "total_images": sum(len(s.images) for s in document.sections)
            },
            "resources": {
                "total_count": len(document.resources),
                "image_count": len([r for r in document.resources.values() if r.get('type') == 'image']),
                "font_count": len([r for r in document.resources.values() if r.get('type') == 'font'])
            }
        }

        print("\n=== Document Analysis ===")
        print(f"Metadata: {analysis['metadata']}")
        print(f"Content: {analysis['content']}")
        print(f"Resources: {analysis['resources']}")

        # 문서 유형 추론
        if analysis['content']['total_images'] > analysis['content']['total_tables']:
            doc_type = "Image-heavy document"
        elif analysis['content']['total_tables'] > 5:
            doc_type = "Table-heavy document"
        elif analysis['content']['total_paragraphs'] > 100:
            doc_type = "Long text document"
        else:
            doc_type = "General document"

        print(f"\nDocument type: {doc_type}")

        # 최소한 하나의 섹션이 있거나 리소스가 있어야 함
        assert analysis['content']['section_count'] > 0 or analysis['resources']['total_count'] > 0

    def test_extract_text_with_formatting(self):
        """서식 정보와 함께 텍스트 추출"""
        hwpx_path = Path("/home/hamonikr/airun-hwp/examples/test.hwpx")
        if not hwpx_path.exists():
            pytest.skip("Test HWPX file not found")

        reader = HWPXReader(strict_mode=False)
        document = reader.parse(str(hwpx_path))

        # 서식이 있는 텍스트 추출
        formatted_text = []
        for section_idx, section in enumerate(document.sections[:2]):  # 처음 2개 섹션만
            for para_idx, para in enumerate(section.paragraphs[:5]):  # 섹션당 처음 5개 문단만
                for run_idx, run in enumerate(para.runs):
                    text_info = {
                        "section": section_idx,
                        "paragraph": para_idx,
                        "run": run_idx,
                        "text": run.text[:50],  # 처음 50자만
                        "bold": run.style.bold if run.style else False,
                        "italic": run.style.italic if run.style else False,
                        "font_size": run.style.font_size if run.style else None
                    }
                    if text_info["text"]:
                        formatted_text.append(text_info)

        print(f"\nExtracted {len(formatted_text)} text segments with formatting")
        for info in formatted_text[:10]:  # 처음 10개만 출력
            print(f"  S{info['section']}:P{info['paragraph']}:R{info['run']} - "
                  f"'{info['text']}' "
                  f"(B:{info['bold']}, I:{info['italic']}, Size:{info['font_size']})")

        # 텍스트가 추출되었는지 확인
        assert len(formatted_text) > 0

    def test_table_structure_analysis(self):
        """표 구조 분석 테스트"""
        hwpx_path = Path("/home/hamonikr/airun-hwp/examples/test.hwpx")
        if not hwpx_path.exists():
            pytest.skip("Test HWPX file not found")

        reader = HWPXReader(strict_mode=False)
        document = reader.parse(str(hwpx_path))

        tables_info = []
        for section_idx, section in enumerate(document.sections):
            for table_idx, table in enumerate(section.tables):
                table_info = {
                    "section": section_idx,
                    "table_index": table_idx,
                    "caption": table.caption,
                    "rows": len(table.rows),
                    "columns": max(len(row) for row in table.rows) if table.rows else 0,
                    "has_header": any(
                        any(cell.is_header for cell in row)
                        for row in table.rows
                    ),
                    "has_merged_cells": any(
                        any(cell.merged for cell in row)
                        for row in table.rows
                    )
                }
                tables_info.append(table_info)

        print(f"\nFound {len(tables_info)} tables")
        for info in tables_info:
            print(f"  Section {info['section']}, Table {info['table_index']}: "
                  f"{info['rows']}x{info['columns']} "
                  f"(Header: {info['has_header']}, Merged: {info['has_merged_cells']})")
            if info['caption']:
                print(f"    Caption: {info['caption']}")

        # 표가 있다면 기본 정보 확인
        if tables_info:
            assert all(info['rows'] > 0 for info in tables_info)
            assert all(info['columns'] > 0 for info in tables_info)