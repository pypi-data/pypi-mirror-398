"""Data models for Bible content."""

import sys
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

# Python 3.9+ uses collections.abc, Python 3.8 uses typing
if sys.version_info >= (3, 9):
    pass  # Can use list[Verse] directly in 3.9+
else:
    pass  # Use List[Verse] from typing


@dataclass
class Verse:
    """Represents a single verse in the Bible.
    
    Attributes:
        num: The verse number within the chapter.
        chapter_num: The chapter number this verse belongs to.
        text: The text content of the verse.
        book_id: The book identifier (e.g., 'gen', 'mat').
    """

    num: int
    chapter_num: int
    text: str
    book_id: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert verse to dictionary representation.
        
        Returns:
            Dictionary with verse data suitable for database storage.
        """
        return {
            "verse_num": self.num,
            "chapter_num": self.chapter_num,
            "text": self.text,
            "book_id": self.book_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Verse":
        """Create a Verse instance from a dictionary.
        
        Args:
            data: Dictionary containing verse data (typically from database).
            
        Returns:
            A new Verse instance.
        """
        return cls(
            num=data["verse_num"],
            chapter_num=data["chapter_num"],
            text=data["text"],
            book_id=data["book_id"],
        )

    def __str__(self) -> str:
        """Return a human-readable string representation."""
        return f"{self.book_id} {self.chapter_num}:{self.num} - {self.text}"


@dataclass
class Chapter:
    """Represents a chapter in a Bible book.
    
    Attributes:
        num: The chapter number.
        verses: List of verses in this chapter.
    """

    num: int
    verses: List[Verse] = field(default_factory=list)

    def __str__(self) -> str:
        """Return a human-readable string representation."""
        return f"Chapter {self.num} ({len(self.verses)} verses)"


@dataclass
class Book:
    """Represents a book of the Bible.
    
    Attributes:
        id: The book identifier (e.g., 'gen', 'exo', 'mat').
        num: The book number (1-66 for Protestant canon).
        title: The full title of the book (e.g., 'Genesis', 'Matthew').
        chapters: List of chapters in this book.
        verses: Flat list of all verses in this book.
    """

    id: str
    num: int
    title: str
    chapters: List[Chapter] = field(default_factory=list)
    verses: List[Verse] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert book to dictionary representation.
        
        Returns:
            Dictionary with book data suitable for database storage.
        """
        return {
            "id": self.id,
            "num": self.num,
            "title": self.title,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Book":
        """Create a Book instance from a dictionary.
        
        Args:
            data: Dictionary containing book data (typically from database).
            
        Returns:
            A new Book instance (without chapters/verses).
        """
        return cls(
            id=data["id"],
            num=data["num"],
            title=data["title"],
        )

    def __str__(self) -> str:
        """Return a human-readable string representation."""
        return f"{self.title} ({self.id}) - {len(self.chapters)} chapters, {len(self.verses)} verses"


@dataclass
class VerseRange:
    """Represents a range of verses within a chapter.
    
    Used for complex reference patterns like "John 3:16,18,20-22" where
    additional verses beyond the primary reference need to be tracked.
    
    Attributes:
        chapter_num: Optional chapter number (defaults to primary reference chapter).
        start_verse: The starting verse number.
        end_verse: The ending verse number (None for single verse).
    
    Examples:
        >>> # Single verse: verse 18
        >>> VerseRange(start_verse=18)
        
        >>> # Verse range: verses 20-22
        >>> VerseRange(start_verse=20, end_verse=22)
        
        >>> # Cross-chapter reference
        >>> VerseRange(chapter_num=2, start_verse=1, end_verse=5)
    """
    
    chapter_num: Optional[int] = None
    start_verse: Optional[int] = None
    end_verse: Optional[int] = None
    
    def __str__(self) -> str:
        """Return a human-readable string representation."""
        if self.chapter_num:
            if self.end_verse:
                return f"{self.chapter_num}:{self.start_verse}-{self.end_verse}"
            return f"{self.chapter_num}:{self.start_verse}"
        else:
            if self.end_verse:
                return f"{self.start_verse}-{self.end_verse}"
            return f"{self.start_verse}"


@dataclass
class BibleReference:
    """Represents a parsed Bible reference with all its components.
    
    This class encapsulates all information extracted from parsing a Bible
    reference string, including book, chapter, verse ranges, and additional
    verses for complex patterns.
    
    Attributes:
        book_id: The book identifier (e.g., 'gen', 'jhn', 'mat').
        chapter_num: The starting chapter number.
        verse_num: The starting verse number (None for chapter-only references).
        end_chapter_num: The ending chapter number for multi-chapter ranges.
        end_verse_num: The ending verse number for verse ranges.
        is_chapter_only: True if reference is chapter-only (e.g., "Psalm 23").
        additional_verses: List of additional verse ranges for complex patterns.
    
    Examples:
        >>> # Single verse: "John 3:16"
        >>> BibleReference(book_id='jhn', chapter_num=3, verse_num=16)
        
        >>> # Verse range: "John 3:16-18"
        >>> BibleReference(book_id='jhn', chapter_num=3, verse_num=16, end_verse_num=18)
        
        >>> # Multi-chapter: "Genesis 1:1-2:3"
        >>> BibleReference(book_id='gen', chapter_num=1, verse_num=1, 
        ...                end_chapter_num=2, end_verse_num=3)
        
        >>> # Chapter only: "Psalm 23"
        >>> BibleReference(book_id='psa', chapter_num=23, is_chapter_only=True)
        
        >>> # Complex pattern: "John 3:16,18,20-22"
        >>> BibleReference(book_id='jhn', chapter_num=3, verse_num=16,
        ...                additional_verses=[
        ...                    VerseRange(start_verse=18),
        ...                    VerseRange(start_verse=20, end_verse=22)
        ...                ])
    """
    
    book_id: str
    chapter_num: int
    verse_num: Optional[int] = None
    end_chapter_num: Optional[int] = None
    end_verse_num: Optional[int] = None
    is_chapter_only: bool = False
    additional_verses: List[VerseRange] = field(default_factory=list)
    
    def __str__(self) -> str:
        """Return a human-readable string representation."""
        if self.is_chapter_only:
            if self.end_chapter_num:
                return f"{self.book_id} {self.chapter_num}-{self.end_chapter_num}"
            return f"{self.book_id} {self.chapter_num}"
        
        result = f"{self.book_id} {self.chapter_num}:{self.verse_num}"
        
        if self.end_chapter_num:
            result += f"-{self.end_chapter_num}:{self.end_verse_num}"
        elif self.end_verse_num:
            result += f"-{self.end_verse_num}"
        
        if self.additional_verses:
            additional = ",".join(str(vr) for vr in self.additional_verses)
            result += f",{additional}"
        
        return result
