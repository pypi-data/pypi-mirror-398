"""
Bible Parser - A Python package for parsing Bible texts in various XML formats.

This package provides tools to parse Bible texts in USFX, OSIS, and ZEFANIA formats
with both direct parsing and database-backed approaches.
"""

__version__ = "0.1.0"

from bible_parser.models import Verse, Book, Chapter, BibleReference, VerseRange
from bible_parser.errors import (
    BibleParserException,
    ParseError,
    FormatDetectionError,
    ParserUnavailableError,
    ReferenceFormatError,
)
from bible_parser.bible_parser import BibleParser
from bible_parser.bible_repository import BibleRepository
from bible_parser.reference_formatter import BibleReferenceFormatter

__all__ = [
    "Verse",
    "Book",
    "Chapter",
    "BibleReference",
    "VerseRange",
    "BibleParserException",
    "ParseError",
    "FormatDetectionError",
    "ParserUnavailableError",
    "ReferenceFormatError",
    "BibleParser",
    "BibleRepository",
    "BibleReferenceFormatter",
]
