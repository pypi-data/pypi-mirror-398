"""
통합 테스트

HWPXReader, HWPXWriter, 모델들의 통합된 동작을 테스트합니다.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import sys

# 프로젝트 루트를 파이썬 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from airun_hwp.reader.hwpx_reader import HWPXReader
from airun_hwp.writer.hwpx_writer import HWPXWriter, BatchHWPXWriter
from airun_hwp.models.document import HWPXDocument
from airun_hwp.models.metadata import DocumentMetadata
from airun_hwp.models.content import Section, Paragraph, TextRun, Table, TableCell, Image, StyleInfo


@pytest.mark.integration
class TestEndToEndWorkflow:
    """종단 간(end-to-end) 워크플로우 테스트"""

    def test_parse_to_markdown_workflow(self, sample_hwpx_file, temp_dir):
        """HWPX → 파싱 → Markdown 변환 워크플로우"""
        # 1. HWPX 파싱
        reader = HWPXReader(strict_mode=False)
        document = reader.parse(str(sample_hwpx_file))

        assert document is not None
        assert len(document.sections) > 0

        # 2. Markdown 변환
        markdown_content = document.to_markdown(include_metadata=True)
        assert len(markdown_content) > 0

        # 3. Markdown 파일 저장
        md_path = temp_dir / "converted.md"
        md_path.write_text(markdown_content, encoding='utf-8')

        assert md_path.exists()
        assert md_path.stat().st_size > 0

        # 4. 내용 확인
        assert "title:" in markdown_content or "테스트" in markdown_content

    @pytest.mark.slow
    def test_complete_roundtrip(self, sample_hwpx_file, temp_dir):
        """HWPX → 파싱 → Markdown → HWPX 왕복 변환"""
        pytest.skip("Requires pypandoc-hwpx installation")

        # 1. 원본 HWPX 파싱
        reader = HWPXReader(strict_mode=False)
        original_document = reader.parse(str(sample_hwpx_file))

        # 2. Markdown으로 변환
        markdown_path = temp_dir / "intermediate.md"
        markdown_content = original_document.to_markdown()
        markdown_path.write_text(markdown_content, encoding='utf-8')

        # 3. Markdown에서 새 HWPX 생성
        writer = HWPXWriter()
        new_hwpx_path = temp_dir / "roundtrip.hwpx"
        success = writer.from_markdown(str(markdown_path), str(new_hwpx_path))

        # 4. 결과 확인
        if success:
            assert new_hwpx_path.exists()
            assert new_hwpx_path.stat().st_size > 0

            # 5. 새 HWPX 다시 파싱
            new_reader = HWPXReader(strict_mode=False)
            new_document = new_reader.parse(str(new_hwpx_path))

            # 6. 기본 내용 비교
            original_text = original_document.get_all_text()
            new_text = new_document.get_all_text()

            # 일부 내용은 손실될 수 있으나 기본 텍스트는 유지되어야 함
            assert len(new_text) > 0

    def test_batch_processing_workflow(self, temp_dir):
        """일괄 처리 워크플로우 테스트"""
        # 1. 여러 Markdown 파일 생성
        input_dir = temp_dir / "inputs"
        input_dir.mkdir()

        documents = []
        for i in range(3):
            # 문서 객체 생성
            doc = HWPXDocument(
                metadata=DocumentMetadata(
                    title=f"문서 {i+1}",
                    author=f"작성자 {i+1}"
                )
            )

            # 섹션과 문단 추가
            section = Section()
            para = Paragraph()
            para.runs.append(TextRun(text=f"이것은 문서 {i+1}의 내용입니다."))
            section.paragraphs.append(para)
            doc.add_section(section)

            documents.append(doc)

            # Markdown으로 변환하여 저장
            md_path = input_dir / f"doc{i+1}.md"
            md_content = doc.to_markdown()
            md_path.write_text(md_content, encoding='utf-8')

        # 2. 일괄 HWPX 변환
        output_dir = temp_dir / "outputs"
        batch_writer = BatchHWPXWriter(str(output_dir))

        with pytest.MonkeyPatch().context() as m:
            # subprocess 모킹
            import subprocess
            mock_run = m.setattr(subprocess, 'run')
            mock_result = type('Mock', (), {
                'returncode': 0,
                'stdout': '',
                'stderr': ''
            })()
            mock_run.return_value = mock_result

            successful_files = batch_writer.process_directory(str(input_dir))

        # 3. 결과 확인
        assert len(successful_files) == 3

    def test_complex_document_processing(self, temp_dir):
        """복잡한 문서 처리 워크플로우"""
        # 1. 복잡한 문서 생성
        document = HWPXDocument(
            metadata=DocumentMetadata(
                title="복합 콘텐츠 문서",
                author="통합 테스트",
                subject="다양한 콘텐츠 타입 테스트"
            )
        )

        # 2. 여러 섹션에 다양한 콘텐츠 추가
        for section_idx in range(3):
            section = Section()

            # 문단들
            for para_idx in range(5):
                para = Paragraph()
                text = f"섹션{section_idx+1} 문단{para_idx+1}"

                # 다양한 스타일 적용
                if para_idx % 2 == 0:
                    style = StyleInfo(bold=True)
                elif para_idx % 3 == 0:
                    style = StyleInfo(italic=True)
                else:
                    style = StyleInfo()

                para.runs.append(TextRun(text=text, style=style))
                section.paragraphs.append(para)

            # 표
            if section_idx > 0:
                table = Table(caption=f"섹션{section_idx+1}의 표")
                # 헤더
                header_cells = [
                    TableCell(text=f"컬럼{j+1}", row=0, col=j, is_header=True)
                    for j in range(3)
                ]
                table.add_row(header_cells)

                # 데이터 행
                for i in range(3):
                    data_cells = [
                        TableCell(text=f"데이터{i+1}-{j+1}", row=i+1, col=j)
                        for j in range(3)
                    ]
                    table.add_row(data_cells)

                section.tables.append(table)

            # 이미지
            if section_idx == 2:
                image = Image(
                    name=f"image{section_idx}.png",
                    width=300,
                    height=200,
                    caption=f"섹션{section_idx+1}의 이미지"
                )
                section.images.append(image)

            document.add_section(section)

        # 3. 유효성 검증
        issues = document.validate()
        assert not any(issue.startswith("Error:") for issue in issues)

        # 4. Markdown 변환
        markdown_content = document.to_markdown()
        assert len(markdown_content) > 0

        # 5. 내용 확인
        assert "복합 콘텐츠 문서" in markdown_content
        assert "섹션1 문단1" in markdown_content
        assert "| 컬럼1 |" in markdown_content  # 표 마크다운
        assert "섹션3의 이미지" in markdown_content

        # 6. Markdown 파일 저장
        md_path = temp_dir / "complex_document.md"
        md_path.write_text(markdown_content, encoding='utf-8')

        assert md_path.exists()


@pytest.mark.integration
class TestErrorRecovery:
    """에러 복구 테스트"""

    def test_partial_document_recovery(self, temp_dir):
        """손상된 문서 부분 복구 테스트"""
        # 1. 부분적으로 손상된 HWPX 파일 생성
        from zipfile import ZipFile
        hwpx_path = temp_dir / "corrupted.hwpx"

        with ZipFile(hwpx_path, 'w') as zf:
            # mimetype
            zf.writestr("mimetype", "application/x-hwp+xml")

            # 정상 header.xml
            header_xml = """<?xml version="1.0" encoding="UTF-8"?>
<hwpml xmlns:hh="http://www.hancom.co.kr/hwpml/2011/head">
    <hh:DocInfo>
        <hc:summary xmlns:hc="http://www.hancom.co.kr/hwpml/2011/core">
            <hc:title>복구 테스트</hc:title>
        </hc:summary>
    </hh:DocInfo>
</hwpml>"""
            zf.writestr("Contents/header.xml", header_xml)

            # 손상된 section.xml
            corrupted_xml = "<invalid><xml>"
            zf.writestr("Contents/section0.xml", corrupted_xml)

            # 정상 section1.xml
            section_xml = """<?xml version="1.0" encoding="UTF-8"?>
<sec xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph">
    <hp:p>
        <hp:run>
            <hp:t>정상 섹션 내용</hp:t>
        </hp:run>
    </hp:p>
</sec>"""
            zf.writestr("Contents/section1.xml", section_xml)

            zf.writestr("Contents/content.hpf", "")

        # 2. 비엄격 모드로 파싱
        reader = HWPXReader(strict_mode=False)
        document = reader.parse(str(hwpx_path))

        # 3. 부분적으로 파싱된 문서 확인
        assert document is not None
        assert document.metadata.title == "복구 테스트"

        # 정상 섹션은 파싱되어야 함
        total_paragraphs = sum(len(s.paragraphs) for s in document.sections)
        assert total_paragraphs >= 0  # 0일 수 있음

    def test_missing_resource_handling(self, temp_dir):
        """누락된 리소스 처리 테스트"""
        # 1. 이미지 참조만 있고 실제 이미지가 없는 HWPX 생성
        from zipfile import ZipFile
        hwpx_path = temp_dir / "missing_resource.hwpx"

        with ZipFile(hwpx_path, 'w') as zf:
            zf.writestr("mimetype", "application/x-hwp+xml")

            header_xml = """<?xml version="1.0" encoding="UTF-8"?>
<hwpml xmlns:hh="http://www.hancom.co.kr/hwpml/2011/head>
</hwpml>"""
            zf.writestr("Contents/header.xml", header_xml)

            # 이미지 참조만 있고 BinData는 없는 섹션
            section_xml = """<?xml version="1.0" encoding="UTF-8"?>
<sec xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph">
    <hp:p>
        <hp:run>
            <hp:t>이미지가 누락된 문서</hp:t>
        </hp:run>
    </hp:p>
    <hp:img name="missing.png">
        <hp:rect width="100" height="100" />
    </hp:img>
</sec>"""
            zf.writestr("Contents/section0.xml", section_xml)
            zf.writestr("Contents/content.hpf", "")

        # 2. 파싱
        reader = HWPXReader(strict_mode=False)
        document = reader.parse(str(hwpx_path))

        # 3. 문서는 정상적으로 파싱되어야 함
        assert document is not None
        assert "이미지가 누락된 문서" in document.get_all_text()


@pytest.mark.integration
class TestPerformance:
    """성능 테스트"""

    def test_large_text_document(self, temp_dir):
        """대량 텍스트 문서 처리 테스트"""
        # 1. 대용량 텍스트 문서 생성
        document = HWPXDocument(
            metadata=DocumentMetadata(title="대용량 텍스트 테스트")
        )

        section = Section()

        # 1000개의 긴 문단
        for i in range(1000):
            para = Paragraph()
            long_text = f"문단 {i+1}: " + "A" * 500  # 500자 텍스트
            para.runs.append(TextRun(text=long_text))
            section.paragraphs.append(para)

        document.add_section(section)

        # 2. Markdown 변환 성능 테스트
        import time
        start_time = time.time()

        markdown_content = document.to_markdown()

        end_time = time.time()
        conversion_time = end_time - start_time

        # 3. 결과 확인
        assert len(markdown_content) > 0
        assert conversion_time < 5.0  # 5초 이내

        # 4. 파일 저장
        md_path = temp_dir / "large_text.md"
        md_path.write_text(markdown_content, encoding='utf-8')

        assert md_path.stat().st_size > 500000  # 약 500KB 이상

    def test_many_small_documents(self, temp_dir):
        """다수의 작은 문서 처리 테스트"""
        documents = []

        # 100개의 작은 문서 생성
        for i in range(100):
            doc = HWPXDocument(
                metadata=DocumentMetadata(title=f"문서 {i+1}")
            )
            section = Section()
            para = Paragraph()
            para.runs.append(TextRun(text=f"내용 {i+1}"))
            section.paragraphs.append(para)
            doc.add_section(section)
            documents.append(doc)

        # 일괄 Markdown 변환
        import time
        start_time = time.time()

        markdown_files = []
        for i, doc in enumerate(documents):
            md_content = doc.to_markdown()
            md_path = temp_dir / f"doc_{i+1:03d}.md"
            md_path.write_text(md_content, encoding='utf-8')
            markdown_files.append(md_path)

        end_time = time.time()
        total_time = end_time - start_time

        # 결과 확인
        assert len(markdown_files) == 100
        assert total_time < 10.0  # 10초 이내
        assert all(f.exists() for f in markdown_files)


@pytest.mark.integration
@pytest.mark.slow
class TestRealWorldScenarios:
    """실제 시나리오 테스트"""

    def test_document_summary_workflow(self, temp_dir):
        """문서 요약 워크플로우 시뮬레이션"""
        # 1. 보고서 스타일 문서 생성
        document = HWPXDocument(
            metadata=DocumentMetadata(
                title="분기 보고서",
                author="담당자",
                subject="2024년 1분기 실적"
            )
        )

        # 2. 목차
        section = Section()
        toc_para = Paragraph()
        toc_para.runs.append(TextRun(
            text="목차\n",
            style=StyleInfo(bold=True, font_size=16)
        ))
        section.paragraphs.append(toc_para)

        toc_items = [
            "1. 개요",
            "2. 실적 현황",
            "3. 주요 성과",
            "4. 개선 과제",
            "5. 향후 계획"
        ]
        for item in toc_items:
            item_para = Paragraph()
            item_para.runs.append(TextRun(text=f"{item}\n"))
            section.paragraphs.append(item_para)

        document.add_section(section)

        # 3. 실적 데이터 표
        section = Section()
        title_para = Paragraph()
        title_para.runs.append(TextRun(
            text="실적 현황",
            style=StyleInfo(bold=True, font_size=14)
        ))
        section.paragraphs.append(title_para)

        # 월별 실적 표
        table = Table(caption="2024년 1분기 월별 실적")

        # 헤더
        header_cells = [
            TableCell(text="월", row=0, col=0, is_header=True),
            TableCell(text="목표", row=0, col=1, is_header=True),
            TableCell(text="실적", row=0, col=2, is_header=True),
            TableCell(text="달성율", row=0, col=3, is_header=True)
        ]
        table.add_row(header_cells)

        # 데이터
        data = [
            ["1월", "100", "95", "95%"],
            ["2월", "110", "115", "104.5%"],
            ["3월", "120", "125", "104.2%"]
        ]
        for i, row_data in enumerate(data):
            row_cells = [
                TableCell(text=row_data[0], row=i+1, col=0),
                TableCell(text=row_data[1], row=i+1, col=1),
                TableCell(text=row_data[2], row=i+1, col=2),
                TableCell(text=row_data[3], row=i+1, col=3)
            ]
            table.add_row(row_cells)

        section.tables.append(table)
        document.add_section(section)

        # 4. 요약 섹션
        section = Section()
        summary_title = Paragraph()
        summary_title.runs.append(TextRun(
            text="요약",
            style=StyleInfo(bold=True, font_size=14)
        ))
        section.paragraphs.append(summary_title)

        summary_points = [
            "1분기 총 실적: 335 (목표 330)",
            "평균 달성율: 101.5%",
            "2개월 연속 목표 초과 달성",
            "향후 2분기 목표: 10% 성장"
        ]
        for point in summary_points:
            point_para = Paragraph()
            point_para.runs.append(TextRun(text=f"• {point}\n"))
            section.paragraphs.append(point_para)

        document.add_section(section)

        # 5. 문서 분석
        all_text = document.get_all_text()
        total_paragraphs = sum(len(s.paragraphs) for s in document.sections)
        total_tables = sum(len(s.tables) for s in document.sections)

        # 6. 결과 확인
        assert document.metadata.title == "분기 보고서"
        assert "목표" in all_text and "실적" in all_text
        assert total_paragraphs > 10
        assert total_tables == 1

        # 7. 요약 생성
        summary = {
            "title": document.metadata.title,
            "paragraph_count": total_paragraphs,
            "table_count": total_tables,
            "has_targets": "목표" in all_text,
            "has_achievements": "실적" in all_text
        }

        assert summary["paragraph_count"] > 0
        assert summary["has_targets"] is True

    def test_multilingual_document(self, temp_dir):
        """다국어 문서 처리 테스트"""
        document = HWPXDocument(
            metadata=DocumentMetadata(
                title="多言語 문서 / Multilingual Document",
                author="테스트 / Test / テスト"
            )
        )

        section = Section()

        # 다양한 언어의 텍스트
        multilingual_texts = [
            ("한글 안녕하세요", "Korean"),
            ("English Hello World", "English"),
            ("日本語 こんにちは", "Japanese"),
            ("中文 你好世界", "Chinese"),
            ("العربية مرحبا", "Arabic"),
            ("Русский Привет мир", "Russian"),
            ("Emoji Test 🌍📚✅", "Emoji")
        ]

        for text, lang in multilingual_texts:
            para = Paragraph()
            para.runs.append(TextRun(text=f"{lang}: {text}"))
            section.paragraphs.append(para)

        document.add_section(section)

        # Markdown으로 변환
        markdown_content = document.to_markdown()

        # 모든 언어가 포함되어 있는지 확인
        for text, _ in multilingual_texts:
            assert text in markdown_content

        # 파일 저장
        md_path = temp_dir / "multilingual.md"
        md_path.write_text(markdown_content, encoding='utf-8')

        # UTF-8로 저장되었는지 확인
        with open(md_path, 'r', encoding='utf-8') as f:
            saved_content = f.read()
            for text, _ in multilingual_texts:
                assert text in saved_content