"""Base parser class for all Bible format parsers."""

import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Union

# Python 3.9+ uses collections.abc, Python 3.8 uses typing
if sys.version_info >= (3, 9):
    from collections.abc import Generator
else:
    from typing import Generator

from bible_parser.models import Book, Verse
from bible_parser.errors import ParseError


class BaseParser(ABC):
    """Abstract base class for all Bible format parsers.
    
    This class defines the interface that all format-specific parsers must implement.
    It handles reading content from files or strings and provides abstract methods
    for parsing.
    
    Attributes:
        source: The source of Bible data (file path or XML string).
    """

    def __init__(self, source: Union[str, Path]):
        """Initialize the parser with a data source.
        
        Args:
            source: Either a file path (str/Path) or XML content string.
        """
        self.source = source

    @abstractmethod
    def parse_books(self) -> Generator[Book, None, None]:
        """Parse the Bible data and yield Book objects.
        
        This method should use streaming/iterative parsing to minimize memory usage.
        
        Yields:
            Book objects containing chapters and verses.
            
        Raises:
            ParseError: If parsing fails.
        """
        pass

    @abstractmethod
    def parse_verses(self) -> Generator[Verse, None, None]:
        """Parse the Bible data and yield Verse objects directly.
        
        This method should use streaming/iterative parsing to minimize memory usage.
        Useful when you only need verses without the book/chapter structure.
        
        Yields:
            Verse objects.
            
        Raises:
            ParseError: If parsing fails.
        """
        pass

    @abstractmethod
    def check_format(self, content: str) -> bool:
        """Check if the given content matches this parser's format.
        
        Args:
            content: XML content to check.
            
        Returns:
            True if the content matches this parser's format, False otherwise.
        """
        pass

    def get_content(self) -> str:
        """Get the XML content from the source.
        
        Returns:
            The XML content as a string.
            
        Raises:
            ParseError: If the content cannot be read.
        """
        try:
            # Check if source is a Path object or string path
            if isinstance(self.source, (Path, str)):
                path = Path(self.source)
                # Check if it's an existing file
                if path.exists() and path.is_file():
                    return path.read_text(encoding="utf-8")
                # Otherwise, treat as XML content string
                elif isinstance(self.source, str):
                    return self.source
                else:
                    raise ParseError(f"Source is not a valid file: {self.source}")
            else:
                raise ParseError(f"Unsupported source type: {type(self.source)}")
        except Exception as e:
            if isinstance(e, ParseError):
                raise
            raise ParseError(f"Failed to read content: {e}")
