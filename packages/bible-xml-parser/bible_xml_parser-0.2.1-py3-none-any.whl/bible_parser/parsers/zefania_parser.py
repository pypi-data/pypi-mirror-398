"""Zefania XML format parser for Bible files."""

import sys
from typing import Optional
from io import BytesIO

# Python 3.9+ uses collections.abc, Python 3.8 uses typing
if sys.version_info >= (3, 9):
    from collections.abc import Generator
else:
    from typing import Generator

from defusedxml.ElementTree import iterparse

from bible_parser.models import Book, Chapter, Verse
from bible_parser.parsers.base_parser import BaseParser
from bible_parser.errors import ParseError


class ZefaniaParser(BaseParser):
    """Parser for Zefania XML Bible Markup Language format.
    
    Zefania XML is a simple XML format used by various Bible software applications.
    """

    def check_format(self, content: str) -> bool:
        """Check if content is in Zefania format.
        
        Args:
            content: XML content to check.
            
        Returns:
            True if content appears to be Zefania format.
        """
        return "<xmlbible" in content.lower() or "<XMLBIBLE" in content

    def parse_books(self) -> Generator[Book, None, None]:
        """Parse Zefania content and yield Book objects.
        
        Yields:
            Book objects with chapters and verses.
            
        Raises:
            ParseError: If parsing fails.
        """
        content = self.get_content()
        content_bytes = content.encode("utf-8")
        
        current_book: Optional[Book] = None
        current_chapter: Optional[Chapter] = None
        current_verse: Optional[Verse] = None
        
        try:
            for event, elem in iterparse(BytesIO(content_bytes), events=("start", "end")):
                tag = elem.tag.upper()  # Zefania can use mixed case
                
                if event == "start":
                    if tag == "BIBLEBOOK":
                        # Start of a book
                        book_num_str = elem.get("bnumber", "0")
                        book_num = int(book_num_str) if book_num_str.isdigit() else 0
                        book_name = elem.get("bname", f"Book{book_num}")
                        book_id = elem.get("bsname", book_name.lower())
                        
                        current_book = Book(
                            id=book_id.lower(),
                            num=book_num,
                            title=book_name,
                        )
                    
                    elif tag == "CHAPTER" and current_book is not None:
                        # Start of a chapter
                        chapter_num_str = elem.get("cnumber", "1")
                        chapter_num = int(chapter_num_str) if chapter_num_str.isdigit() else 1
                        
                        current_chapter = Chapter(num=chapter_num)
                    
                    elif tag == "VERS" and current_book is not None and current_chapter is not None:
                        # Start of a verse
                        verse_num_str = elem.get("vnumber", "1")
                        verse_num = int(verse_num_str) if verse_num_str.isdigit() else 1
                        
                        # Text is in the element's text content
                        verse_text = elem.text or ""
                        
                        current_verse = Verse(
                            num=verse_num,
                            chapter_num=current_chapter.num,
                            text=verse_text.strip(),
                            book_id=current_book.id,
                        )
                
                elif event == "end":
                    if tag == "BIBLEBOOK" and current_book is not None:
                        # End of book - add last chapter if exists
                        if current_chapter is not None:
                            current_book.chapters.append(current_chapter)
                        
                        # Flatten verses
                        for chapter in current_book.chapters:
                            current_book.verses.extend(chapter.verses)
                        
                        yield current_book
                        current_book = None
                        current_chapter = None
                    
                    elif tag == "CHAPTER" and current_chapter is not None and current_book is not None:
                        # End of chapter
                        current_book.chapters.append(current_chapter)
                        current_chapter = None
                    
                    elif tag == "VERS" and current_verse is not None and current_chapter is not None:
                        # End of verse - get text if not already set
                        if not current_verse.text and elem.text:
                            current_verse.text = elem.text.strip()
                        
                        current_chapter.verses.append(current_verse)
                        current_verse = None
                    
                    elem.clear()
        
        except Exception as e:
            raise ParseError(f"Error parsing Zefania books: {e}")

    def parse_verses(self) -> Generator[Verse, None, None]:
        """Parse Zefania content and yield Verse objects directly.
        
        Yields:
            Verse objects.
            
        Raises:
            ParseError: If parsing fails.
        """
        for book in self.parse_books():
            for verse in book.verses:
                yield verse
