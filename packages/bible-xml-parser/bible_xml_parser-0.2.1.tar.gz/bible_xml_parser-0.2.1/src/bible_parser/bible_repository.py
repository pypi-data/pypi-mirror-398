"""Database repository for Bible data with SQLite caching."""

import sqlite3
import sys
from pathlib import Path
from typing import Optional, List, Any, Dict

# Python 3.9+ uses collections.abc, Python 3.8 uses typing
if sys.version_info >= (3, 9):
    pass
else:
    pass

from bible_parser.models import Book, Verse
from bible_parser.bible_parser import BibleParser


class BibleRepository:
    """Repository for accessing Bible data with SQLite database caching.
    
    This class provides efficient access to Bible data by caching parsed content
    in a SQLite database. It supports full-text search using FTS5 and provides
    methods for querying books, chapters, and verses.
    
    Example:
        >>> with BibleRepository(xml_path='bible.xml') as repo:
        ...     repo.initialize('my_bible.db')
        ...     verses = repo.get_verses('gen', 1)
        ...     results = repo.search_verses('love')
    """

    def __init__(
        self,
        xml_path: Optional[str] = None,
        xml_string: Optional[str] = None,
        format: Optional[str] = None,
    ):
        """Initialize the Bible repository.
        
        Args:
            xml_path: Path to XML file (mutually exclusive with xml_string).
            xml_string: XML content as string (mutually exclusive with xml_path).
            format: Optional Bible format specification.
        """
        self.xml_path = xml_path
        self.xml_string = xml_string
        self.format = format
        self._db: Optional[sqlite3.Connection] = None

    def initialize(self, database_name: str) -> bool:
        """Initialize the repository and database.
        
        Creates the database if it doesn't exist, or opens it if it does.
        If the database is empty, it will parse the XML and populate it.
        
        Args:
            database_name: Name of the SQLite database file.
            
        Returns:
            True if initialization was successful.
            
        Raises:
            Exception: If initialization fails.
        """
        try:
            # Close any existing connection
            if self._db is not None:
                self._db.close()
            
            db_path = Path(database_name)
            db_exists = db_path.exists()
            
            # Open database connection
            self._db = sqlite3.connect(str(db_path))
            self._db.row_factory = sqlite3.Row  # Enable column access by name
            
            if not db_exists or not self._is_database_initialized():
                # Create schema and populate
                self._create_schema()
                self._populate_database()
            
            return True
        
        except Exception as e:
            raise Exception(f"Failed to initialize Bible repository: {e}")

    def _is_database_initialized(self) -> bool:
        """Check if the database has been initialized with data.
        
        Returns:
            True if database contains data.
        """
        if self._db is None:
            return False
        
        cursor = self._db.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='books'"
        )
        if cursor.fetchone() is None:
            return False
        
        # Check if books table has data
        cursor.execute("SELECT COUNT(*) as count FROM books")
        result = cursor.fetchone()
        return result["count"] > 0 if result else False

    def _create_schema(self) -> None:
        """Create the database schema."""
        if self._db is None:
            raise Exception("Database not connected")
        
        cursor = self._db.cursor()
        
        # Create books table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS books (
                id TEXT PRIMARY KEY,
                num INTEGER,
                title TEXT
            )
        """)
        
        # Create verses table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS verses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id TEXT,
                chapter_num INTEGER,
                verse_num INTEGER,
                text TEXT,
                FOREIGN KEY (book_id) REFERENCES books (id)
            )
        """)
        
        # Create indexes for fast lookup
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_verses_lookup 
            ON verses (book_id, chapter_num, verse_num)
        """)
        
        # Create FTS5 virtual table for full-text search
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS verses_fts 
            USING fts5(book_id, chapter_num, verse_num, text, content=verses, content_rowid=id)
        """)
        
        # Create triggers to keep FTS table in sync
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS verses_ai AFTER INSERT ON verses BEGIN
                INSERT INTO verses_fts(rowid, book_id, chapter_num, verse_num, text)
                VALUES (new.id, new.book_id, new.chapter_num, new.verse_num, new.text);
            END
        """)
        
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS verses_ad AFTER DELETE ON verses BEGIN
                DELETE FROM verses_fts WHERE rowid = old.id;
            END
        """)
        
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS verses_au AFTER UPDATE ON verses BEGIN
                UPDATE verses_fts SET 
                    book_id = new.book_id,
                    chapter_num = new.chapter_num,
                    verse_num = new.verse_num,
                    text = new.text
                WHERE rowid = new.id;
            END
        """)
        
        self._db.commit()

    def _populate_database(self) -> None:
        """Parse XML and populate the database."""
        if self._db is None:
            raise Exception("Database not connected")
        
        # Create parser
        if self.xml_string is not None:
            parser = BibleParser.from_string(self.xml_string, format=self.format)
        elif self.xml_path is not None:
            parser = BibleParser(self.xml_path, format=self.format)
        else:
            raise Exception("No XML source provided")
        
        cursor = self._db.cursor()
        
        # Use transaction for better performance
        try:
            for book in parser.books:
                # Insert book
                cursor.execute(
                    "INSERT OR IGNORE INTO books (id, num, title) VALUES (?, ?, ?)",
                    (book.id, book.num, book.title),
                )
                
                # Insert verses in batch
                verse_data = [
                    (verse.book_id, verse.chapter_num, verse.num, verse.text)
                    for verse in book.verses
                ]
                
                cursor.executemany(
                    "INSERT INTO verses (book_id, chapter_num, verse_num, text) VALUES (?, ?, ?, ?)",
                    verse_data,
                )
            
            self._db.commit()
        
        except Exception as e:
            self._db.rollback()
            raise Exception(f"Failed to populate database: {e}")

    def get_books(self) -> List[Book]:
        """Get all books in the Bible.
        
        Returns:
            List of Book objects (without chapters/verses).
            
        Raises:
            Exception: If database is not initialized.
        """
        self._ensure_db_initialized()
        
        cursor = self._db.cursor()
        cursor.execute("SELECT id, num, title FROM books ORDER BY num")
        
        books = []
        for row in cursor.fetchall():
            books.append(Book.from_dict(dict(row)))
        
        return books

    def get_chapter_count(self, book_id: str) -> int:
        """Get the number of chapters in a book.
        
        Args:
            book_id: Book identifier (e.g., 'gen', 'mat').
            
        Returns:
            Number of chapters in the book.
        """
        self._ensure_db_initialized()
        
        cursor = self._db.cursor()
        cursor.execute(
            "SELECT COUNT(DISTINCT chapter_num) as count FROM verses WHERE book_id = ?",
            (book_id,),
        )
        
        result = cursor.fetchone()
        return result["count"] if result else 0

    def get_verses(self, book_id: str, chapter_num: int) -> List[Verse]:
        """Get all verses in a specific chapter.
        
        Args:
            book_id: Book identifier.
            chapter_num: Chapter number.
            
        Returns:
            List of Verse objects.
        """
        self._ensure_db_initialized()
        
        cursor = self._db.cursor()
        cursor.execute(
            """
            SELECT book_id, chapter_num, verse_num, text 
            FROM verses 
            WHERE book_id = ? AND chapter_num = ?
            ORDER BY verse_num
            """,
            (book_id, chapter_num),
        )
        
        verses = []
        for row in cursor.fetchall():
            verses.append(Verse.from_dict(dict(row)))
        
        return verses

    def get_verse(self, book_id: str, chapter_num: int, verse_num: int) -> Optional[Verse]:
        """Get a specific verse.
        
        Args:
            book_id: Book identifier.
            chapter_num: Chapter number.
            verse_num: Verse number.
            
        Returns:
            Verse object if found, None otherwise.
        """
        self._ensure_db_initialized()
        
        cursor = self._db.cursor()
        cursor.execute(
            """
            SELECT book_id, chapter_num, verse_num, text 
            FROM verses 
            WHERE book_id = ? AND chapter_num = ? AND verse_num = ?
            """,
            (book_id, chapter_num, verse_num),
        )
        
        row = cursor.fetchone()
        return Verse.from_dict(dict(row)) if row else None

    def search_verses(self, query: str, limit: int = 100) -> List[Verse]:
        """Search for verses containing the query text.
        
        Uses SQLite FTS5 for efficient full-text search.
        
        Args:
            query: Search query string.
            limit: Maximum number of results to return.
            
        Returns:
            List of matching Verse objects.
        """
        self._ensure_db_initialized()
        
        # Sanitize query to prevent FTS injection
        query = query.replace('"', '""')
        
        cursor = self._db.cursor()
        cursor.execute(
            """
            SELECT v.book_id, v.chapter_num, v.verse_num, v.text
            FROM verses v
            INNER JOIN verses_fts fts ON v.id = fts.rowid
            WHERE verses_fts MATCH ?
            LIMIT ?
            """,
            (query, limit),
        )
        
        verses = []
        for row in cursor.fetchall():
            verses.append(Verse.from_dict(dict(row)))
        
        return verses

    def close(self) -> None:
        """Close the database connection."""
        if self._db is not None:
            self._db.close()
            self._db = None

    def _ensure_db_initialized(self) -> None:
        """Ensure database is initialized before use.
        
        Raises:
            Exception: If database is not initialized.
        """
        if self._db is None:
            raise Exception("Database not initialized. Call initialize() first.")

    def __enter__(self) -> "BibleRepository":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit - closes database connection."""
        self.close()
