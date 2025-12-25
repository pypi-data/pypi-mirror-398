"""
Content models for HWPX documents.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class StyleInfo:
    """스타일 정보"""
    char_style_id: Optional[str] = None
    para_style_id: Optional[str] = None
    font_name: Optional[str] = None
    font_size: Optional[int] = None
    color: Optional[str] = None
    bold: bool = False
    italic: bool = False
    underline: bool = False
    strike_through: bool = False


@dataclass
class DocumentToken:
    """문서 내의 토큰(텍스트, 표, 이미지 등)을 표현하는 클래스"""
    TEXT_RUN = "text_run"
    PARAGRAPH_BREAK = "paragraph_break"
    TABLE = "table"
    IMAGE = "image"
    PAGE_BREAK = "page_break"

    def __init__(self, token_type: str, content=None, **kwargs):
        self.type = token_type
        self.content = content
        self.source_index = kwargs.get('source_index', -1)
        self.anchor_info = kwargs.get('anchor_info', {})
        self.attributes = kwargs


@dataclass
class TextRun:
    """텍스트 런"""
    text: str
    style: StyleInfo = field(default_factory=StyleInfo)
    position: int = 0
    char_style_id: Optional[str] = None


@dataclass
class Paragraph:
    """문단"""
    runs: List[TextRun] = field(default_factory=list)
    style: StyleInfo = field(default_factory=StyleInfo)
    paragraph_id: Optional[str] = None
    para_style_id: Optional[str] = None

    def get_text(self) -> str:
        """문단의 전체 텍스트 반환"""
        return ''.join(run.text for run in self.runs)


@dataclass
class TableCell:
    """테이블 셀"""
    text: str
    row: int
    col: int
    rowspan: int = 1
    colspan: int = 1
    style: StyleInfo = field(default_factory=StyleInfo)
    is_header: bool = False
    merged: bool = False


@dataclass
class Table:
    """테이블"""
    rows: List[List[TableCell]] = field(default_factory=list)
    caption: Optional[str] = None
    style_id: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None

    def add_row(self, cells: List[Any]):
        """행 추가"""
        row = []
        for i, cell in enumerate(cells):
            if isinstance(cell, str):
                table_cell = TableCell(
                    text=cell,
                    row=len(self.rows),
                    col=i,
                    is_header=(len(self.rows) == 0)
                )
                row.append(table_cell)
            else:
                cell.row = len(self.rows)
                row.append(cell)
        self.rows.append(row)

    def get_data(self) -> List[List[str]]:
        """테이블 데이터 반환"""
        return [[cell.text for cell in row] for row in self.rows]


@dataclass
class Image:
    """이미지"""
    name: str
    data: Optional[bytes] = None
    path: Optional[str] = None
    caption: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    position: Optional[Dict[str, int]] = None
    img_type: Optional[str] = None


@dataclass
class Section:
    """섹션"""
    paragraphs: List[Paragraph] = field(default_factory=list)
    tables: List[Table] = field(default_factory=list)
    images: List[Image] = field(default_factory=list)
    page_info: Dict[str, Any] = field(default_factory=dict)
    section_id: Optional[int] = None
    tokens: List['DocumentToken'] = field(default_factory=list)  # 원문 순서를 보존하는 토큰 스트림