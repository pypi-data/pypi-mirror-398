"""Main BibleParser class with automatic format detection."""

import sys
from pathlib import Path
from typing import Union, Optional

# Python 3.9+ uses collections.abc, Python 3.8 uses typing
if sys.version_info >= (3, 9):
    from collections.abc import Generator
else:
    from typing import Generator

from bible_parser.models import Book, Verse
from bible_parser.parsers import UsfxParser, OsisParser, ZefaniaParser, BaseParser
from bible_parser.errors import FormatDetectionError, ParserUnavailableError


class BibleParser:
    """Main parser class for Bible XML files with automatic format detection.
    
    This class provides a unified interface for parsing Bible files in various
    formats (USFX, OSIS, ZEFANIA). It automatically detects the format or allows
    explicit format specification.
    
    Attributes:
        source: The source of Bible data (file path or XML string).
        format: The detected or specified Bible format.
    
    Example:
        >>> parser = BibleParser('path/to/bible.xml')
        >>> for book in parser.books:
        ...     print(f"{book.title}: {len(book.verses)} verses")
    """

    def __init__(self, source: Union[str, Path], format: Optional[str] = None):
        """Initialize the Bible parser.
        
        Args:
            source: Either a file path or XML content string.
            format: Optional format specification ('USFX', 'OSIS', or 'ZEFANIA').
                   If not provided, format will be auto-detected.
        """
        self.source = source
        self.format = format.upper() if format else self._detect_format()
        self._parser = self._get_parser()

    @classmethod
    def from_string(cls, xml_content: str, format: Optional[str] = None) -> "BibleParser":
        """Create a BibleParser from an XML content string.
        
        Args:
            xml_content: XML content as a string.
            format: Optional format specification.
            
        Returns:
            A new BibleParser instance.
        """
        return cls(xml_content, format=format)

    @property
    def books(self) -> Generator[Book, None, None]:
        """Iterate over all books in the Bible.
        
        Yields:
            Book objects containing chapters and verses.
        """
        yield from self._parser.parse_books()

    @property
    def verses(self) -> Generator[Verse, None, None]:
        """Iterate over all verses in the Bible.
        
        Yields:
            Verse objects.
        """
        yield from self._parser.parse_verses()

    def _detect_format(self) -> str:
        """Auto-detect the Bible format from content.
        
        Returns:
            The detected format ('USFX', 'OSIS', or 'ZEFANIA').
            
        Raises:
            FormatDetectionError: If format cannot be detected.
        """
        try:
            # Get a sample of the content for detection
            if isinstance(self.source, (str, Path)):
                path = Path(self.source)
                if path.exists() and path.is_file():
                    # Read first 2000 characters from file
                    with open(path, "r", encoding="utf-8") as f:
                        sample = f.read(2000)
                else:
                    # Assume it's XML content string
                    sample = str(self.source)[:2000] if isinstance(self.source, str) else ""
            else:
                sample = ""
            
            sample_lower = sample.lower()
            
            # Check for format markers
            if "<usfx" in sample_lower or ("<book" in sample_lower and "<c" in sample_lower):
                return "USFX"
            elif "<osis" in sample_lower or "<osistext" in sample_lower:
                return "OSIS"
            elif "<xmlbible" in sample_lower or "<biblebook" in sample_lower:
                return "ZEFANIA"
            
            # Default to OSIS if no clear markers found
            raise FormatDetectionError(
                "Could not detect Bible format. Please specify format explicitly."
            )
        
        except FormatDetectionError:
            raise
        except Exception as e:
            raise FormatDetectionError(f"Error detecting format: {e}")

    def _get_parser(self) -> BaseParser:
        """Get the appropriate parser for the detected/specified format.
        
        Returns:
            A parser instance for the format.
            
        Raises:
            ParserUnavailableError: If parser for format is not available.
        """
        parsers = {
            "USFX": UsfxParser,
            "OSIS": OsisParser,
            "ZEFANIA": ZefaniaParser,
        }
        
        parser_class = parsers.get(self.format)
        if parser_class is None:
            raise ParserUnavailableError(
                f"Parser for format '{self.format}' is not available. "
                f"Supported formats: {', '.join(parsers.keys())}"
            )
        
        return parser_class(self.source)
