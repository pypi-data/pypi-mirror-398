"""OSIS format parser for Bible XML files."""

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


class OsisParser(BaseParser):
    """Parser for OSIS (Open Scripture Information Standard) Bible format.

    OSIS is a comprehensive XML standard for encoding Biblical texts and related materials.
    """

    def check_format(self, content: str) -> bool:
        """Check if content is in OSIS format.

        Args:
            content: XML content to check.

        Returns:
            True if content appears to be OSIS format.
        """
        return "<osis" in content.lower() or "<osisText" in content.lower()

    def _parse_osis_id(self, osis_id: str) -> tuple[str, int, int]:
        """Parse OSIS verse ID (e.g., 'Gen.1.1' or 'Matt.5.3').

        Args:
            osis_id: OSIS verse identifier.

        Returns:
            Tuple of (book_id, chapter_num, verse_num).
        """
        parts = osis_id.split(".")
        if len(parts) >= 3:
            book_id = parts[0].lower()
            chapter_num = int(parts[1]) if parts[1].isdigit() else 1
            verse_num = int(parts[2]) if parts[2].isdigit() else 1
            return book_id, chapter_num, verse_num
        return "", 1, 1

    def parse_books(self) -> Generator[Book, None, None]:
        """Parse OSIS content and yield Book objects.

        Yields:
            Book objects with chapters and verses.

        Raises:
            ParseError: If parsing fails.
        """
        content = self.get_content()
        content_bytes = content.encode("utf-8")

        books_dict = {}  # Store books by ID
        current_book_id: Optional[str] = None
        current_verse_data: Optional[dict] = None  # Store verse being built
        verse_text_parts = []  # Collect text for current verse
        inside_note = False
        inside_book_title = False

        try:
            for event, elem in iterparse(BytesIO(content_bytes), events=("start", "end")):
                tag = elem.tag.split("}")[-1]  # Remove namespace

                if event == "start":
                    if tag == "div" and elem.get("type") == "book":
                        # Start of a book
                        osis_id = elem.get("osisID", "")
                        if osis_id:
                            current_book_id = osis_id.lower()
                            if current_book_id not in books_dict:
                                # Create book with default title (will be updated if <title> element found)
                                books_dict[current_book_id] = Book(
                                    id=current_book_id,
                                    num=len(books_dict) + 1,
                                    title=current_book_id.capitalize(),
                                )

                    elif tag == "title" and current_book_id and current_book_id in books_dict:
                        # Mark that we're inside a title element
                        inside_book_title = True

                    elif tag == "verse":
                        # Check for sID (start of verse with sID/eID pattern)
                        sid = elem.get("sID")
                        if sid and current_book_id:
                            # Extract osisID from sID or use osisID attribute
                            osis_id = elem.get("osisID", "")
                            if not osis_id:
                                # Parse from sID (format: Book.Chapter.Verse.seID.xxxxx)
                                osis_id = ".".join(sid.split(".")[:3])

                            book_id, chapter_num, verse_num = self._parse_osis_id(
                                osis_id)

                            # Start collecting text for this verse
                            current_verse_data = {
                                "book_id": book_id or current_book_id,
                                "chapter_num": chapter_num,
                                "verse_num": verse_num,
                            }
                            verse_text_parts = []

                        # Check for eID (end of verse with sID/eID pattern)
                        elif elem.get("eID") and current_verse_data:
                            # Verse is complete, create it
                            verse_text = " ".join(verse_text_parts).strip()
                            verse = Verse(
                                num=current_verse_data["verse_num"],
                                chapter_num=current_verse_data["chapter_num"],
                                text=verse_text,
                                book_id=current_verse_data["book_id"],
                            )

                            # Add to book
                            if current_verse_data["book_id"] in books_dict:
                                books_dict[current_verse_data["book_id"]].verses.append(
                                    verse)

                            current_verse_data = None
                            verse_text_parts = []

                        # Handle old-style OSIS (osisID without sID/eID)
                        elif elem.get("osisID") and not sid and current_book_id:
                            osis_id = elem.get("osisID", "")
                            book_id, chapter_num, verse_num = self._parse_osis_id(
                                osis_id)

                            # Get text content from the element and its children
                            verse_text = "".join(elem.itertext()).strip()

                            verse = Verse(
                                num=verse_num,
                                chapter_num=chapter_num,
                                text=verse_text,
                                book_id=book_id or current_book_id,
                            )

                            if (book_id or current_book_id) in books_dict:
                                books_dict[book_id or current_book_id].verses.append(
                                    verse)

                    elif tag == "note":
                        inside_note = True

                    # Collect text if we're inside a verse (sID/eID pattern)
                    if current_verse_data and not inside_note and tag != "verse":
                        if elem.text:
                            verse_text_parts.append(elem.text)

                elif event == "end":
                    # Update book title when we finish parsing a title element
                    if tag == "title" and inside_book_title and current_book_id:
                        if elem.text and current_book_id in books_dict:
                            books_dict[current_book_id].title = elem.text
                        inside_book_title = False

                    # Collect tail text if we're inside a verse
                    if current_verse_data and not inside_note:
                        if elem.tail:
                            verse_text_parts.append(elem.tail)

                    if tag == "note":
                        inside_note = False

                    elem.clear()

            # Organize verses into chapters and yield books
            for book in books_dict.values():
                # Group verses by chapter
                chapters_dict = {}
                for verse in book.verses:
                    if verse.chapter_num not in chapters_dict:
                        chapters_dict[verse.chapter_num] = Chapter(
                            num=verse.chapter_num)
                    chapters_dict[verse.chapter_num].verses.append(verse)

                # Add chapters to book in order
                book.chapters = [chapters_dict[num]
                                 for num in sorted(chapters_dict.keys())]

                yield book

        except Exception as e:
            raise ParseError(f"Error parsing OSIS books: {e}")

    def parse_verses(self) -> Generator[Verse, None, None]:
        """Parse OSIS content and yield Verse objects directly.

        Yields:
            Verse objects.

        Raises:
            ParseError: If parsing fails.
        """
        for book in self.parse_books():
            for verse in book.verses:
                yield verse
