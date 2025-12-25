"""Bible reference parsing and formatting utilities.

This module provides tools for parsing Bible reference strings into structured
data and retrieving verses based on those references.
"""

import re
from typing import List, Optional, TYPE_CHECKING

from bible_parser.models import BibleReference, VerseRange, Verse
from bible_parser.errors import ReferenceFormatError

if TYPE_CHECKING:
    from bible_parser.bible_repository import BibleRepository


class BibleReferenceFormatter:
    """Utility class for parsing and formatting Bible references.
    
    This class provides static methods to parse Bible reference strings in various
    formats and convert them into structured BibleReference objects that can be
    used to query a BibleRepository.
    
    Supported reference formats:
        - Single verse: "John 3:16"
        - Verse range (same chapter): "John 3:16-18"
        - Multi-chapter range: "Genesis 1:1-2:3"
        - Complex patterns: "John 3:16,18,20-22"
        - Chapter-only: "Psalm 23"
        - Multi-chapter no verses: "Ruth 1-4"
        - Semicolon-separated: "Genesis 1:1-3;2:3-4"
        - With descriptions: "1 Samuel 17:1-58 (David and Goliath)"
    
    Example:
        >>> from bible_parser import BibleReferenceFormatter, BibleRepository
        >>> 
        >>> with BibleRepository(xml_path='bible.xml') as repo:
        ...     repo.initialize('bible.db')
        ...     
        ...     # Parse a reference
        ...     ref = BibleReferenceFormatter.parse("John 3:16", repo)
        ...     print(ref.book_id, ref.chapter_num, ref.verse_num)
        ...     
        ...     # Get verses directly
        ...     verses = BibleReferenceFormatter.get_verses_from_reference(
        ...         "John 3:16-18", repo
        ...     )
    """
    
    # Book name to canonical book title mapping for repository lookups
    # Maps common book names to standardized book titles (case-insensitive)
    # 
    # NOTE: Uses full book names (e.g., "genesis", "1 samuel") rather than IDs
    # because different Bible formats use different book IDs:
    #   - OSIS: gen, ps, 1sam, 2cor
    #   - USFX: gen, psa, 1sa, 2co
    # The flexible matching in _get_book_id_from_book_name() handles both formats.
    _CANONICAL_BOOK_NAMES = {
        'genesis': 'genesis',
        'exodus': 'exodus',
        'leviticus': 'leviticus',
        'numbers': 'numbers',
        'deuteronomy': 'deuteronomy',
        'joshua': 'joshua',
        'judges': 'judges',
        'ruth': 'ruth',
        '1 samuel': '1 samuel',
        '2 samuel': '2 samuel',
        '1 kings': '1 kings',
        '2 kings': '2 kings',
        '1 chronicles': '1 chronicles',
        '2 chronicles': '2 chronicles',
        'ezra': 'ezra',
        'nehemiah': 'nehemiah',
        'esther': 'esther',
        'job': 'job',
        'psalm': 'psalms',
        'psalms': 'psalms',
        'proverbs': 'proverbs',
        'ecclesiastes': 'ecclesiastes',
        'song of solomon': 'song of solomon',
        'songs of solomon': 'song of solomon',
        'song of songs': 'song of solomon',
        'isaiah': 'isaiah',
        'jeremiah': 'jeremiah',
        'lamentations': 'lamentations',
        'ezekiel': 'ezekiel',
        'daniel': 'daniel',
        'hosea': 'hosea',
        'joel': 'joel',
        'amos': 'amos',
        'obadiah': 'obadiah',
        'jonah': 'jonah',
        'micah': 'micah',
        'nahum': 'nahum',
        'habakkuk': 'habakkuk',
        'zephaniah': 'zephaniah',
        'haggai': 'haggai',
        'zechariah': 'zechariah',
        'malachi': 'malachi',
        'matthew': 'matthew',
        'mark': 'mark',
        'luke': 'luke',
        'john': 'john',
        'acts': 'acts',
        'romans': 'romans',
        '1 corinthians': '1 corinthians',
        '2 corinthians': '2 corinthians',
        'galatians': 'galatians',
        'ephesians': 'ephesians',
        'philippians': 'philippians',
        'colossians': 'colossians',
        '1 thessalonians': '1 thessalonians',
        '2 thessalonians': '2 thessalonians',
        '1 timothy': '1 timothy',
        '2 timothy': '2 timothy',
        'titus': 'titus',
        'philemon': 'philemon',
        'hebrews': 'hebrews',
        'james': 'james',
        '1 peter': '1 peter',
        '2 peter': '2 peter',
        '1 john': '1 john',
        '2 john': '2 john',
        '3 john': '3 john',
        'jude': 'jude',
        'revelation': 'revelation',
    }
    
    @staticmethod
    def is_valid_book(book_name: str) -> bool:
        """Check if a book name is valid.
        
        Args:
            book_name: The book name to validate (case-insensitive).
            
        Returns:
            True if the book name is recognized, False otherwise.
            
        Example:
            >>> BibleReferenceFormatter.is_valid_book("John")
            True
            >>> BibleReferenceFormatter.is_valid_book("Foo")
            False
        """
        return book_name.lower() in BibleReferenceFormatter._CANONICAL_BOOK_NAMES
    
    @staticmethod
    def get_first_verse_in_reference(reference: str) -> str:
        """Extract the first verse from a complex Bible reference.
        
        This method handles all supported reference formats and returns a simple
        reference string pointing to the first verse.
        
        Args:
            reference: The Bible reference string to parse.
            
        Returns:
            A simple reference string (e.g., "John 3:16") pointing to the first verse.
            
        Raises:
            ReferenceFormatError: If the reference is empty, invalid, or cannot be parsed.
            
        Examples:
            >>> BibleReferenceFormatter.get_first_verse_in_reference("John 3:16,18,20-22")
            'John 3:16'
            >>> BibleReferenceFormatter.get_first_verse_in_reference("Genesis 1:1-2:3")
            'Genesis 1:1'
            >>> BibleReferenceFormatter.get_first_verse_in_reference("Ruth 1-4")
            'Ruth 1:1'
            >>> BibleReferenceFormatter.get_first_verse_in_reference("Psalm 23")
            'Psalm 23:1'
        """
        # Normalize the reference
        normalized_ref = reference.strip()
        if not normalized_ref:
            raise ReferenceFormatError("Bible reference cannot be empty")
        
        # Input validation
        if len(normalized_ref) > 500:
            raise ReferenceFormatError("Reference too long (max 500 characters)")
        
        # Remove any descriptions in parentheses
        normalized_ref = BibleReferenceFormatter._remove_parenthetical_descriptions(normalized_ref)
        
        # Handle semicolon-separated references - take only the first part
        if ';' in normalized_ref:
            normalized_ref = normalized_ref.split(';')[0].strip()
        
        # Extract the book name
        book_name_end_index = BibleReferenceFormatter._find_book_name_end_index(normalized_ref)
        if book_name_end_index == -1:
            raise ReferenceFormatError(
                f"Could not identify book name in reference: {reference}"
            )
        
        book_name = normalized_ref[:book_name_end_index].strip()
        remaining_part = normalized_ref[book_name_end_index:].strip()
        
        # Handle multi-chapter reference with no verse specifications (e.g., "Ruth 1-4")
        if ':' not in remaining_part and '-' in remaining_part:
            first_chapter = remaining_part.split('-')[0].strip()
            return f"{book_name} {first_chapter}:1"
        
        # Handle chapter-only reference (e.g., "Psalm 23")
        if ':' not in remaining_part and re.match(r'^\d+$', remaining_part):
            return f"{book_name} {remaining_part}:1"
        
        # Handle complex verse patterns with commas (e.g., "3:16,18,20-22")
        # Take only the first verse or range
        if ',' in remaining_part:
            first_part = remaining_part.split(',')[0].strip()
            # If the first part is a range, extract just the start
            if '-' in first_part:
                chapter_verse = first_part.split(':')
                if len(chapter_verse) == 2:
                    start_verse = chapter_verse[1].split('-')[0].strip()
                    return f"{book_name} {chapter_verse[0]}:{start_verse}"
            return f"{book_name} {first_part}"
        
        # Handle multi-chapter references (e.g., "1:1-2:3")
        if '-' in remaining_part:
            range_parts = remaining_part.split('-')
            start_part = range_parts[0].strip()
            
            # If it's a verse range within the same chapter (e.g., "3:16-18")
            if ':' in start_part:
                chapter_verse = start_part.split(':')
                return f"{book_name} {chapter_verse[0]}:{chapter_verse[1]}"
        
        # Handle single verse reference (e.g., "3:16")
        if ':' in remaining_part:
            return f"{book_name} {remaining_part}"
        
        # Default case - shouldn't reach here if reference is valid
        raise ReferenceFormatError(f"Unable to parse reference: {reference}")
    
    @staticmethod
    def _find_book_name_end_index(reference: str) -> int:
        """Find where the book name ends in a reference string.
        
        This uses regex to locate the first digit that's followed by a colon,
        dash, space, or end of string, which indicates the start of chapter/verse info.
        
        Args:
            reference: The reference string to search.
            
        Returns:
            The index where the book name ends, or -1 if not found.
        """
        # Find the first digit that's followed by either another digit, a colon, a dash, or a space
        match = re.search(r'\s\d+(?::|\s|-|$)', reference)
        if match is None:
            return -1
        return match.start()
    
    @staticmethod
    def _remove_parenthetical_descriptions(reference: str) -> str:
        """Remove any descriptions in parentheses from a Bible reference.
        
        Args:
            reference: The reference string that may contain parenthetical descriptions.
            
        Returns:
            The reference string with parenthetical content removed.
            
        Example:
            >>> BibleReferenceFormatter._remove_parenthetical_descriptions(
            ...     "1 Samuel 17:1-58 (David and Goliath)"
            ... )
            '1 Samuel 17:1-58'
        """
        # Use a regex to match content within parentheses and remove it
        return re.sub(r'\s*\([^)]*\)\s*', ' ', reference).strip()
    
    @staticmethod
    def _parse_simple_verse_range(book_id: str, reference: str) -> BibleReference:
        """Parse a simple verse range like '3:16-18'.
        
        Args:
            book_id: The book identifier.
            reference: The chapter:verse range string.
            
        Returns:
            A BibleReference object with verse range information.
            
        Raises:
            ReferenceFormatError: If the format is invalid.
        """
        parts = reference.split(':')
        if len(parts) != 2:
            raise ReferenceFormatError(f"Invalid chapter:verse format: {reference}")
        
        try:
            chapter_num = int(parts[0])
            verse_parts = parts[1].split('-')
            
            if len(verse_parts) != 2:
                raise ReferenceFormatError(f"Invalid verse range format: {reference}")
            
            return BibleReference(
                book_id=book_id,
                chapter_num=chapter_num,
                verse_num=int(verse_parts[0]),
                end_verse_num=int(verse_parts[1]),
            )
        except ValueError as e:
            raise ReferenceFormatError(f"Invalid number in reference: {reference}") from e
    
    @staticmethod
    def _parse_multi_chapter_reference(book_id: str, reference: str) -> BibleReference:
        """Parse a multi-chapter reference like '1:1-2:3'.
        
        Args:
            book_id: The book identifier.
            reference: The multi-chapter range string.
            
        Returns:
            A BibleReference object with multi-chapter range information.
            
        Raises:
            ReferenceFormatError: If the format is invalid.
        """
        range_parts = reference.split('-')
        if len(range_parts) != 2:
            raise ReferenceFormatError(f"Invalid verse range format: {reference}")
        
        start_parts = range_parts[0].split(':')
        end_parts = range_parts[1].split(':')
        
        if len(start_parts) != 2 or len(end_parts) != 2:
            raise ReferenceFormatError(
                f"Invalid chapter:verse format in range: {reference}"
            )
        
        try:
            return BibleReference(
                book_id=book_id,
                chapter_num=int(start_parts[0]),
                verse_num=int(start_parts[1]),
                end_chapter_num=int(end_parts[0]),
                end_verse_num=int(end_parts[1]),
            )
        except ValueError as e:
            raise ReferenceFormatError(f"Invalid number in reference: {reference}") from e
    
    @staticmethod
    def _parse_multi_chapter_only_reference(book_id: str, reference: str) -> BibleReference:
        """Parse a multi-chapter reference with no verses like 'Ruth 1-4'.
        
        Args:
            book_id: The book identifier.
            reference: The chapter range string.
            
        Returns:
            A BibleReference object with chapter-only range information.
            
        Raises:
            ReferenceFormatError: If the format is invalid.
        """
        range_parts = reference.split('-')
        if len(range_parts) != 2:
            raise ReferenceFormatError(f"Invalid chapter range format: {reference}")
        
        try:
            start_chapter = int(range_parts[0])
            end_chapter = int(range_parts[1])
            
            return BibleReference(
                book_id=book_id,
                chapter_num=start_chapter,
                end_chapter_num=end_chapter,
                is_chapter_only=True,
            )
        except ValueError as e:
            raise ReferenceFormatError(f"Invalid chapter number in reference: {reference}") from e
    
    @staticmethod
    def _parse_complex_verse_pattern(book_id: str, reference: str) -> BibleReference:
        """Parse a complex verse pattern like '3:16,18,20-22'.
        
        Args:
            book_id: The book identifier.
            reference: The complex verse pattern string.
            
        Returns:
            A BibleReference object with additional verses information.
            
        Raises:
            ReferenceFormatError: If the format is invalid.
        """
        parts = reference.split(':')
        if len(parts) != 2:
            raise ReferenceFormatError(f"Invalid chapter:verse format: {reference}")
        
        try:
            chapter_num = int(parts[0])
            verse_patterns = parts[1].split(',')
            
            if not verse_patterns:
                raise ReferenceFormatError(f"No verse numbers found: {reference}")
            
            # Limit complexity to prevent DoS
            if len(verse_patterns) > 50:
                raise ReferenceFormatError(
                    f"Too many comma-separated verses (max 50): {reference}"
                )
            
            # Get the first verse or range as the primary verse
            first_pattern = verse_patterns[0]
            additional_verses = []
            
            # Process additional verses and ranges
            for i in range(1, len(verse_patterns)):
                pattern = verse_patterns[i].strip()
                if '-' in pattern:
                    range_parts = pattern.split('-')
                    if len(range_parts) != 2:
                        raise ReferenceFormatError(f"Invalid verse range: {pattern}")
                    additional_verses.append(VerseRange(
                        start_verse=int(range_parts[0]),
                        end_verse=int(range_parts[1]),
                    ))
                else:
                    additional_verses.append(VerseRange(
                        start_verse=int(pattern),
                    ))
            
            # Process the first pattern
            if '-' in first_pattern:
                range_parts = first_pattern.split('-')
                if len(range_parts) != 2:
                    raise ReferenceFormatError(f"Invalid verse range: {first_pattern}")
                return BibleReference(
                    book_id=book_id,
                    chapter_num=chapter_num,
                    verse_num=int(range_parts[0]),
                    end_verse_num=int(range_parts[1]),
                    additional_verses=additional_verses,
                )
            else:
                return BibleReference(
                    book_id=book_id,
                    chapter_num=chapter_num,
                    verse_num=int(first_pattern),
                    additional_verses=additional_verses,
                )
        except ValueError as e:
            raise ReferenceFormatError(f"Invalid number in reference: {reference}") from e
    
    @staticmethod
    def _parse_chapter_and_verses(book_id: str, chapter_verse_part: str) -> BibleReference:
        """Route to appropriate parser based on reference format.
        
        Args:
            book_id: The book identifier.
            chapter_verse_part: The chapter and verse portion of the reference.
            
        Returns:
            A BibleReference object.
            
        Raises:
            ReferenceFormatError: If the format is invalid.
        """
        # Handle multi-chapter references (e.g., "1:1-2:3")
        if '-' in chapter_verse_part and ':' in chapter_verse_part.split('-')[1]:
            return BibleReferenceFormatter._parse_multi_chapter_reference(
                book_id, chapter_verse_part
            )
        
        # Handle complex verse patterns with commas (e.g., "3:16,18,20-22")
        if ',' in chapter_verse_part:
            return BibleReferenceFormatter._parse_complex_verse_pattern(
                book_id, chapter_verse_part
            )
        
        # Handle simple verse range (e.g., "3:16-18")
        if '-' in chapter_verse_part:
            return BibleReferenceFormatter._parse_simple_verse_range(
                book_id, chapter_verse_part
            )
        
        # Handle single verse reference (e.g., "3:16")
        parts = chapter_verse_part.split(':')
        if len(parts) != 2:
            raise ReferenceFormatError(
                f"Invalid chapter:verse format: {chapter_verse_part}"
            )
        
        try:
            return BibleReference(
                book_id=book_id,
                chapter_num=int(parts[0]),
                verse_num=int(parts[1]),
            )
        except ValueError as e:
            raise ReferenceFormatError(
                f"Invalid number in reference: {chapter_verse_part}"
            ) from e
    
    @staticmethod
    def _get_book_id_from_book_name(
        book_name: str, bible_repository: "BibleRepository"
    ) -> str:
        """Get the book ID from a book name using the repository.
        
        Args:
            book_name: The book name (case-insensitive).
            bible_repository: The repository to query for book information.
            
        Returns:
            The book ID (e.g., 'gen', 'jhn').
            
        Raises:
            ReferenceFormatError: If the book name is not found.
        """
        canonical_title = BibleReferenceFormatter._CANONICAL_BOOK_NAMES.get(
            book_name.lower()
        )
        if not canonical_title:
            raise ReferenceFormatError(f"Unknown book name: {book_name}")
        
        # Find the book by matching title (works across different Bible formats)
        # Try multiple matching strategies to handle different formats:
        # 1. Exact match (e.g., "Genesis" == "Genesis")
        # 2. Abbreviated match (e.g., "Genesis" starts with "Gen")
        # 3. Normalized match (e.g., "1 Samuel" == "1sam")
        books = bible_repository.get_books()
        canonical_lower = canonical_title.lower()
        canonical_normalized = canonical_lower.replace(' ', '')
        
        for book in books:
            book_title_lower = book.title.lower()
            book_id_lower = book.id.lower()
            
            # Strategy 1: Exact title match
            if book_title_lower == canonical_lower:
                return book.id
            
            # Strategy 2: Book title starts with canonical (for abbreviated titles like "Gen")
            if canonical_lower.startswith(book_title_lower) or book_title_lower.startswith(canonical_lower):
                return book.id
            
            # Strategy 3: Normalized match (remove spaces for numbered books like "1 Samuel" -> "1samuel")
            book_title_normalized = book_title_lower.replace(' ', '')
            if book_id_lower == canonical_normalized or book_title_normalized == canonical_normalized:
                return book.id
            
            # Strategy 4: Check if canonical starts with book title (for "1 samuel" matching "1sam")
            if canonical_normalized.startswith(book_title_normalized) or canonical_normalized.startswith(book_id_lower):
                return book.id
        
        raise ReferenceFormatError(f"Book not found in repository: {book_name}")
    
    @staticmethod
    def parse(reference: str, bible_repository: "BibleRepository") -> BibleReference:
        """Parse a Bible reference string into a structured BibleReference object.
        
        This is the main entry point for parsing Bible references. It handles all
        supported reference formats and returns a BibleReference object that can
        be used to query verses from the repository.
        
        Args:
            reference: The Bible reference string to parse.
            bible_repository: The repository to use for book lookups.
            
        Returns:
            A BibleReference object with all parsed components.
            
        Raises:
            ReferenceFormatError: If the reference is invalid or cannot be parsed.
            
        Examples:
            >>> ref = BibleReferenceFormatter.parse("John 3:16", repo)
            >>> print(ref.book_id, ref.chapter_num, ref.verse_num)
            jhn 3 16
            
            >>> ref = BibleReferenceFormatter.parse("Genesis 1:1-2:3", repo)
            >>> print(ref.end_chapter_num, ref.end_verse_num)
            2 3
        """
        try:
            # Normalize the reference
            normalized_ref = reference.strip()
            if not normalized_ref:
                raise ReferenceFormatError("Bible reference cannot be empty")
            
            # Input validation
            if len(normalized_ref) > 500:
                raise ReferenceFormatError("Reference too long (max 500 characters)")
            
            # Remove any descriptions in parentheses
            normalized_ref = BibleReferenceFormatter._remove_parenthetical_descriptions(
                normalized_ref
            )
            
            # Check for semicolon-separated references (e.g., "Genesis 1:1-3;2:3-4")
            if ';' in normalized_ref:
                return BibleReferenceFormatter._parse_semicolon_separated_reference(
                    normalized_ref, bible_repository
                )
            
            # Extract the book name
            book_name_end_index = BibleReferenceFormatter._find_book_name_end_index(
                normalized_ref
            )
            if book_name_end_index == -1:
                raise ReferenceFormatError(
                    f"Could not identify book name in reference: {reference}"
                )
            
            book_name = normalized_ref[:book_name_end_index].strip()
            remaining_part = normalized_ref[book_name_end_index:].strip()
            
            # Get book ID from the repository
            book_id = BibleReferenceFormatter._get_book_id_from_book_name(
                book_name, bible_repository
            )
            
            # Check if this is a multi-chapter reference with no verse specifications
            if ':' not in remaining_part and '-' in remaining_part:
                return BibleReferenceFormatter._parse_multi_chapter_only_reference(
                    book_id, remaining_part
                )
            
            # Check if this is a chapter-only reference (e.g., "Psalm 23")
            if ':' not in remaining_part and re.match(r'^\d+$', remaining_part):
                try:
                    return BibleReference(
                        book_id=book_id,
                        chapter_num=int(remaining_part),
                        is_chapter_only=True,
                    )
                except ValueError as e:
                    raise ReferenceFormatError(
                        f"Invalid chapter number: {remaining_part}"
                    ) from e
            
            # Parse the chapter and verse parts
            return BibleReferenceFormatter._parse_chapter_and_verses(
                book_id, remaining_part
            )
            
        except ReferenceFormatError:
            raise
        except Exception as e:
            raise ReferenceFormatError(
                f"Error parsing Bible reference '{reference}': {str(e)}"
            ) from e
    
    @staticmethod
    def _parse_semicolon_separated_reference(
        reference: str, bible_repository: "BibleRepository"
    ) -> BibleReference:
        """Parse a semicolon-separated reference like 'Genesis 1:1-3;2:3-4'.
        
        Args:
            reference: The semicolon-separated reference string.
            bible_repository: The repository to use for book lookups.
            
        Returns:
            A BibleReference object with additional verses information.
            
        Raises:
            ReferenceFormatError: If the format is invalid.
        """
        # Split the reference by semicolon
        parts = reference.split(';')
        if len(parts) < 2:
            raise ReferenceFormatError(
                f"Invalid semicolon-separated reference: {reference}"
            )
        
        # Limit complexity
        if len(parts) > 20:
            raise ReferenceFormatError(
                f"Too many semicolon-separated parts (max 20): {reference}"
            )
        
        # Extract the book name from the first part
        book_name_end_index = BibleReferenceFormatter._find_book_name_end_index(parts[0])
        if book_name_end_index == -1:
            raise ReferenceFormatError(
                f"Could not identify book name in reference: {reference}"
            )
        
        book_name = parts[0][:book_name_end_index].strip()
        first_part = parts[0][book_name_end_index:].strip()
        
        # Get book ID from the repository
        book_id = BibleReferenceFormatter._get_book_id_from_book_name(
            book_name, bible_repository
        )
        
        # Parse the first part to get the initial chapter and verse information
        if '-' in first_part:
            if ':' in first_part:
                # Handle verse range like "1:1-3"
                query = BibleReferenceFormatter._parse_simple_verse_range(book_id, first_part)
            else:
                # Handle chapter range like "1-3"
                query = BibleReferenceFormatter._parse_multi_chapter_only_reference(
                    book_id, first_part
                )
        elif ':' in first_part:
            # Handle single verse like "1:1"
            chapter_verse = first_part.split(':')
            try:
                query = BibleReference(
                    book_id=book_id,
                    chapter_num=int(chapter_verse[0]),
                    verse_num=int(chapter_verse[1]),
                )
            except ValueError as e:
                raise ReferenceFormatError(f"Invalid number in reference: {first_part}") from e
        else:
            # Handle chapter only like "1"
            try:
                query = BibleReference(
                    book_id=book_id,
                    chapter_num=int(first_part),
                    is_chapter_only=True,
                )
            except ValueError as e:
                raise ReferenceFormatError(f"Invalid chapter number: {first_part}") from e
        
        # Process additional parts and add them as verse ranges
        additional_verses = []
        
        for i in range(1, len(parts)):
            part = parts[i].strip()
            
            # Check if it contains chapter:verse format
            if ':' in part:
                if '-' in part:
                    # Handle range like "2:3-4"
                    range_parts = part.split('-')
                    chapter_verse = range_parts[0].split(':')
                    end_verse = range_parts[1]
                    
                    try:
                        # If the end part also has a chapter specification
                        if ':' in end_verse:
                            # Cross-chapter range - add as separate range
                            end_parts = end_verse.split(':')
                            additional_verses.append(VerseRange(
                                chapter_num=int(chapter_verse[0]),
                                start_verse=int(chapter_verse[1]),
                            ))
                        else:
                            # Simple verse range within same chapter
                            additional_verses.append(VerseRange(
                                chapter_num=int(chapter_verse[0]),
                                start_verse=int(chapter_verse[1]),
                                end_verse=int(end_verse),
                            ))
                    except ValueError as e:
                        raise ReferenceFormatError(f"Invalid number in reference: {part}") from e
                else:
                    # Single verse like "2:3"
                    chapter_verse = part.split(':')
                    try:
                        additional_verses.append(VerseRange(
                            chapter_num=int(chapter_verse[0]),
                            start_verse=int(chapter_verse[1]),
                        ))
                    except ValueError as e:
                        raise ReferenceFormatError(f"Invalid number in reference: {part}") from e
            elif '-' in part:
                # Handle chapter range like "2-3"
                range_parts = part.split('-')
                try:
                    # For chapter ranges, use start_verse=1 as convention
                    additional_verses.append(VerseRange(
                        chapter_num=int(range_parts[0]),
                        start_verse=1,
                    ))
                except ValueError as e:
                    raise ReferenceFormatError(f"Invalid chapter number: {part}") from e
            else:
                # Single chapter like "2"
                try:
                    additional_verses.append(VerseRange(
                        chapter_num=int(part),
                        start_verse=1,
                    ))
                except ValueError as e:
                    raise ReferenceFormatError(f"Invalid chapter number: {part}") from e
        
        # Add the additional verses to the query
        if additional_verses:
            query.additional_verses = additional_verses
        
        return query
    
    @staticmethod
    def get_verses_from_reference(
        reference: str, bible_repository: "BibleRepository"
    ) -> List[Verse]:
        """Parse a reference and retrieve all matching verses in one call.
        
        This is a convenience method that combines parsing and verse retrieval.
        It handles all supported reference formats and returns the actual verse
        objects from the repository.
        
        Args:
            reference: Bible reference string (e.g., "John 3:16-18").
            bible_repository: Repository to fetch verses from.
            
        Returns:
            List of Verse objects matching the reference. Returns empty list if
            no verses found.
            
        Raises:
            ReferenceFormatError: If the reference format is invalid.
            
        Examples:
            >>> verses = BibleReferenceFormatter.get_verses_from_reference(
            ...     "John 3:16", repo
            ... )
            >>> print(verses[0].text)
            
            >>> verses = BibleReferenceFormatter.get_verses_from_reference(
            ...     "John 3:16-18", repo
            ... )
            >>> print(len(verses))
            3
        """
        ref = BibleReferenceFormatter.parse(reference, bible_repository)
        
        # Single verse
        if (not ref.end_verse_num and not ref.end_chapter_num and 
            not ref.additional_verses and ref.verse_num is not None):
            verse = bible_repository.get_verse(
                ref.book_id, ref.chapter_num, ref.verse_num
            )
            return [verse] if verse else []
        
        # Chapter only
        if ref.is_chapter_only and not ref.end_chapter_num:
            return bible_repository.get_verses(ref.book_id, ref.chapter_num)
        
        # Verse range (same chapter)
        if ref.end_verse_num and not ref.end_chapter_num:
            all_verses = bible_repository.get_verses(ref.book_id, ref.chapter_num)
            return [
                v for v in all_verses 
                if ref.verse_num <= v.num <= ref.end_verse_num
            ]
        
        # Multi-chapter range
        if ref.end_chapter_num:
            verses = []
            
            # Start chapter
            start_verses = bible_repository.get_verses(ref.book_id, ref.chapter_num)
            if ref.verse_num:
                verses.extend([v for v in start_verses if v.num >= ref.verse_num])
            else:
                verses.extend(start_verses)
            
            # Middle chapters
            for chapter in range(ref.chapter_num + 1, ref.end_chapter_num):
                verses.extend(bible_repository.get_verses(ref.book_id, chapter))
            
            # End chapter
            end_verses = bible_repository.get_verses(ref.book_id, ref.end_chapter_num)
            if ref.end_verse_num:
                verses.extend([v for v in end_verses if v.num <= ref.end_verse_num])
            else:
                verses.extend(end_verses)
            
            return verses
        
        # Complex patterns with additional verses
        if ref.additional_verses:
            verses = []
            
            # Primary verse
            if ref.verse_num:
                verse = bible_repository.get_verse(
                    ref.book_id, ref.chapter_num, ref.verse_num
                )
                if verse:
                    verses.append(verse)
            
            # Additional verses
            for verse_range in ref.additional_verses:
                chapter = verse_range.chapter_num or ref.chapter_num
                
                if verse_range.end_verse:
                    # It's a range
                    all_verses = bible_repository.get_verses(ref.book_id, chapter)
                    verses.extend([
                        v for v in all_verses 
                        if verse_range.start_verse <= v.num <= verse_range.end_verse
                    ])
                else:
                    # Single verse
                    verse = bible_repository.get_verse(
                        ref.book_id, chapter, verse_range.start_verse
                    )
                    if verse:
                        verses.append(verse)
            
            return verses
        
        return []
