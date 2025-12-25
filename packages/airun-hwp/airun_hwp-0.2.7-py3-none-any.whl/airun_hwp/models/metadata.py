"""
Metadata models for HWPX documents.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class DocumentMetadata:
    """메타데이터 정보를 담는 클래스"""
    title: Optional[str] = None
    author: Optional[str] = None
    subject: Optional[str] = None
    keywords: Optional[str] = None
    created: Optional[datetime] = None
    modified: Optional[datetime] = None
    application: Optional[str] = None
    encrypted: bool = False
    password_protected: bool = False
    track_changes: bool = False
    page_count: Optional[int] = None
    word_count: Optional[int] = None
    char_count: Optional[int] = None
    section_count: Optional[int] = None
    format: str = "hwpx"
    version: Optional[str] = None
    kogl: bool = False
    ccl: bool = False

    def to_dict(self) -> dict:
        """메타데이터를 딕셔너리로 변환"""
        return {
            'title': self.title,
            'author': self.author,
            'subject': self.subject,
            'keywords': self.keywords,
            'created': self.created.isoformat() if self.created else None,
            'modified': self.modified.isoformat() if self.modified else None,
            'application': self.application,
            'encrypted': self.encrypted,
            'password_protected': self.password_protected,
            'track_changes': self.track_changes,
            'page_count': self.page_count,
            'word_count': self.word_count,
            'char_count': self.char_count,
            'section_count': self.section_count,
            'format': self.format,
            'version': self.version,
            'kogl': self.kogl,
            'ccl': self.ccl
        }