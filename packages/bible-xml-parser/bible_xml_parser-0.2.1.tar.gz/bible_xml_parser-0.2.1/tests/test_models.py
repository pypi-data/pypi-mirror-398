"""Tests for data models."""

import pytest
from bible_parser.models import Verse, Chapter, Book


class TestVerse:
    """Tests for Verse model."""

    def test_verse_creation(self) -> None:
        """Test creating a verse."""
        verse = Verse(
            num=1,
            chapter_num=1,
            text="In the beginning God created the heaven and the earth.",
            book_id="gen",
        )
        
        assert verse.num == 1
        assert verse.chapter_num == 1
        assert verse.book_id == "gen"
        assert "beginning" in verse.text

    def test_verse_to_dict(self) -> None:
        """Test verse serialization to dict."""
        verse = Verse(num=16, chapter_num=3, text="For God so loved the world", book_id="jhn")
        
        data = verse.to_dict()
        
        assert data["verse_num"] == 16
        assert data["chapter_num"] == 3
        assert data["book_id"] == "jhn"
        assert data["text"] == "For God so loved the world"

    def test_verse_from_dict(self) -> None:
        """Test verse deserialization from dict."""
        data = {
            "verse_num": 1,
            "chapter_num": 1,
            "text": "Test verse",
            "book_id": "gen",
        }
        
        verse = Verse.from_dict(data)
        
        assert verse.num == 1
        assert verse.chapter_num == 1
        assert verse.text == "Test verse"
        assert verse.book_id == "gen"

    def test_verse_str(self) -> None:
        """Test verse string representation."""
        verse = Verse(num=1, chapter_num=1, text="Test", book_id="gen")
        
        assert str(verse) == "gen 1:1 - Test"


class TestChapter:
    """Tests for Chapter model."""

    def test_chapter_creation(self) -> None:
        """Test creating a chapter."""
        chapter = Chapter(num=1)
        
        assert chapter.num == 1
        assert len(chapter.verses) == 0

    def test_chapter_with_verses(self) -> None:
        """Test chapter with verses."""
        verses = [
            Verse(num=1, chapter_num=1, text="Verse 1", book_id="gen"),
            Verse(num=2, chapter_num=1, text="Verse 2", book_id="gen"),
        ]
        
        chapter = Chapter(num=1, verses=verses)
        
        assert len(chapter.verses) == 2
        assert chapter.verses[0].num == 1
        assert chapter.verses[1].num == 2


class TestBook:
    """Tests for Book model."""

    def test_book_creation(self) -> None:
        """Test creating a book."""
        book = Book(id="gen", num=1, title="Genesis")
        
        assert book.id == "gen"
        assert book.num == 1
        assert book.title == "Genesis"
        assert len(book.chapters) == 0
        assert len(book.verses) == 0

    def test_book_to_dict(self) -> None:
        """Test book serialization to dict."""
        book = Book(id="gen", num=1, title="Genesis")
        
        data = book.to_dict()
        
        assert data["id"] == "gen"
        assert data["num"] == 1
        assert data["title"] == "Genesis"

    def test_book_from_dict(self) -> None:
        """Test book deserialization from dict."""
        data = {"id": "gen", "num": 1, "title": "Genesis"}
        
        book = Book.from_dict(data)
        
        assert book.id == "gen"
        assert book.num == 1
        assert book.title == "Genesis"
