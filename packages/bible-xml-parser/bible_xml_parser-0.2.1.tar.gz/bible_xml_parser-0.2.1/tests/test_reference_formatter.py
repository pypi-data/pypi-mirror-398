"""Tests for Bible reference formatter."""

import pytest
from bible_parser import (
    BibleReferenceFormatter,
    BibleReference,
    VerseRange,
    ReferenceFormatError,
    BibleRepository,
)


@pytest.fixture
def bible_repo(tmp_path):
    """Create a test Bible repository with sample data."""
    # Create a minimal test Bible XML file
    test_xml = """<usfx>
<book id="gen"><id id="GEN"/><h>Genesis</h>
<c id="1"/><v id="1">In the beginning God created the heaven and the earth.</v>
<v id="2">And the earth was without form, and void.</v>
<v id="3">And God said, Let there be light: and there was light.</v>
<c id="2"/><v id="1">Thus the heavens and the earth were finished.</v>
<v id="2">And on the seventh day God ended his work.</v>
<v id="3">And God blessed the seventh day.</v>
</book>
<book id="jhn"><id id="JHN"/><h>John</h>
<c id="3"/><v id="16">For God so loved the world.</v>
<v id="17">For God sent not his Son into the world.</v>
<v id="18">He that believeth on him is not condemned.</v>
<v id="19">And this is the condemnation.</v>
<v id="20">For every one that doeth evil hateth the light.</v>
<v id="21">But he that doeth truth cometh to the light.</v>
<v id="22">After these things came Jesus.</v>
</book>
<book id="psa"><id id="PSA"/><h>Psalms</h>
<c id="23"/><v id="1">The LORD is my shepherd; I shall not want.</v>
<v id="2">He maketh me to lie down in green pastures.</v>
<v id="3">He restoreth my soul.</v>
</book>
<book id="rut"><id id="RUT"/><h>Ruth</h>
<c id="1"/><v id="1">Now it came to pass in the days.</v>
<c id="2"/><v id="1">And Naomi had a kinsman.</v>
<c id="3"/><v id="1">Then Naomi her mother in law said unto her.</v>
<c id="4"/><v id="1">Then went Boaz up to the gate.</v>
</book>
<book id="1sa"><id id="1SA"/><h>1 Samuel</h>
<c id="17"/><v id="1">Now the Philistines gathered together their armies.</v>
<v id="58">And Saul said to him, Whose son art thou.</v>
</book>
<book id="2co"><id id="2CO"/><h>2 Corinthians</h>
<c id="5"/><v id="17">Therefore if any man be in Christ, he is a new creature.</v>
</book>
<book id="1jn"><id id="1JN"/><h>1 John</h>
<c id="4"/><v id="8">He that loveth not knoweth not God; for God is love.</v>
</book>
</usfx>"""
    
    # Write to a temporary file to avoid the "filename too long" issue
    test_file = tmp_path / "test_bible.xml"
    test_file.write_text(test_xml)
    
    repo = BibleRepository(xml_path=str(test_file), format='USFX')
    repo.initialize(':memory:')  # Use in-memory database for tests
    yield repo
    repo.close()


class TestBookValidation:
    """Tests for book name validation."""
    
    def test_valid_book_names(self):
        """Test that valid book names are recognized."""
        valid_books = [
            'Genesis', 'genesis', 'GENESIS',
            'John', 'john',
            '1 Samuel', '1 samuel',
            '2 Corinthians', '2 corinthians',
            'Psalm', 'Psalms',
        ]
        for book in valid_books:
            assert BibleReferenceFormatter.is_valid_book(book), f"{book} should be valid"
    
    def test_invalid_book_names(self):
        """Test that invalid book names are rejected."""
        invalid_books = ['Foo', 'Bar', '4 Kings', 'Revelations']
        for book in invalid_books:
            assert not BibleReferenceFormatter.is_valid_book(book), f"{book} should be invalid"
    
    def test_book_name_variants(self):
        """Test that book name variants are recognized."""
        # Psalm/Psalms should both work
        assert BibleReferenceFormatter.is_valid_book('Psalm')
        assert BibleReferenceFormatter.is_valid_book('Psalms')
        
        # Song of Solomon variants
        assert BibleReferenceFormatter.is_valid_book('Song of Solomon')
        assert BibleReferenceFormatter.is_valid_book('Song of Songs')


class TestGetFirstVerse:
    """Tests for get_first_verse_in_reference method."""
    
    def test_simple_verse(self):
        """Test extracting first verse from simple reference."""
        result = BibleReferenceFormatter.get_first_verse_in_reference("John 3:16")
        assert result == "John 3:16"
    
    def test_verse_range_same_chapter(self):
        """Test extracting first verse from same-chapter range."""
        result = BibleReferenceFormatter.get_first_verse_in_reference("John 3:16-18")
        assert result == "John 3:16"
    
    def test_multi_chapter_range(self):
        """Test extracting first verse from multi-chapter range."""
        result = BibleReferenceFormatter.get_first_verse_in_reference("Genesis 1:1-2:3")
        assert result == "Genesis 1:1"
    
    def test_complex_comma_pattern(self):
        """Test extracting first verse from comma-separated pattern."""
        result = BibleReferenceFormatter.get_first_verse_in_reference("John 3:16,18,20-22")
        assert result == "John 3:16"
    
    def test_chapter_only(self):
        """Test extracting first verse from chapter-only reference."""
        result = BibleReferenceFormatter.get_first_verse_in_reference("Psalm 23")
        assert result == "Psalm 23:1"
    
    def test_multi_chapter_no_verses(self):
        """Test extracting first verse from multi-chapter without verses."""
        result = BibleReferenceFormatter.get_first_verse_in_reference("Ruth 1-4")
        assert result == "Ruth 1:1"
    
    def test_semicolon_separated(self):
        """Test extracting first verse from semicolon-separated reference."""
        result = BibleReferenceFormatter.get_first_verse_in_reference("Genesis 1:1-3;2:3-4")
        assert result == "Genesis 1:1"
    
    def test_with_parenthetical_description(self):
        """Test extracting first verse with parenthetical description."""
        result = BibleReferenceFormatter.get_first_verse_in_reference(
            "1 Samuel 17:1-58 (David and Goliath)"
        )
        assert result == "1 Samuel 17:1"
    
    def test_numbered_books(self):
        """Test extracting first verse from numbered books."""
        result = BibleReferenceFormatter.get_first_verse_in_reference("1 Corinthians 13:1")
        assert result == "1 Corinthians 13:1"
        
        result = BibleReferenceFormatter.get_first_verse_in_reference("2 Timothy 3:16-17")
        assert result == "2 Timothy 3:16"
    
    def test_empty_reference(self):
        """Test that empty reference raises error."""
        with pytest.raises(ReferenceFormatError, match="cannot be empty"):
            BibleReferenceFormatter.get_first_verse_in_reference("")
    
    def test_too_long_reference(self):
        """Test that overly long reference raises error."""
        long_ref = "John " + "1:1," * 200  # Very long reference
        with pytest.raises(ReferenceFormatError, match="too long"):
            BibleReferenceFormatter.get_first_verse_in_reference(long_ref)


class TestParseSimpleReferences:
    """Tests for parsing simple reference formats."""
    
    def test_parse_single_verse(self, bible_repo):
        """Test parsing a single verse reference."""
        ref = BibleReferenceFormatter.parse("Genesis 1:1", bible_repo)
        
        assert ref.book_id == 'gen'
        assert ref.chapter_num == 1
        assert ref.verse_num == 1
        assert ref.end_verse_num is None
        assert ref.end_chapter_num is None
        assert not ref.is_chapter_only
        assert len(ref.additional_verses) == 0
    
    def test_parse_verse_range_same_chapter(self, bible_repo):
        """Test parsing verse range in same chapter."""
        ref = BibleReferenceFormatter.parse("John 3:16-18", bible_repo)
        
        assert ref.book_id == 'jhn'
        assert ref.chapter_num == 3
        assert ref.verse_num == 16
        assert ref.end_verse_num == 18
        assert ref.end_chapter_num is None
    
    def test_parse_chapter_only(self, bible_repo):
        """Test parsing chapter-only reference."""
        ref = BibleReferenceFormatter.parse("Psalm 23", bible_repo)
        
        assert ref.book_id == 'psa'
        assert ref.chapter_num == 23
        assert ref.verse_num is None
        assert ref.is_chapter_only is True
    
    def test_parse_multi_chapter_range(self, bible_repo):
        """Test parsing multi-chapter range."""
        ref = BibleReferenceFormatter.parse("Genesis 1:1-2:3", bible_repo)
        
        assert ref.book_id == 'gen'
        assert ref.chapter_num == 1
        assert ref.verse_num == 1
        assert ref.end_chapter_num == 2
        assert ref.end_verse_num == 3
    
    def test_parse_multi_chapter_no_verses(self, bible_repo):
        """Test parsing multi-chapter without verse numbers."""
        ref = BibleReferenceFormatter.parse("Ruth 1-4", bible_repo)
        
        assert ref.book_id == 'rut'
        assert ref.chapter_num == 1
        assert ref.end_chapter_num == 4
        assert ref.is_chapter_only is True
    
    def test_parse_with_parenthetical(self, bible_repo):
        """Test parsing reference with parenthetical description."""
        ref = BibleReferenceFormatter.parse(
            "1 Samuel 17:1-58 (David and Goliath)", bible_repo
        )
        
        assert ref.book_id == '1sa'
        assert ref.chapter_num == 17
        assert ref.verse_num == 1
        assert ref.end_verse_num == 58


class TestParseComplexReferences:
    """Tests for parsing complex reference formats."""
    
    def test_parse_comma_separated_verses(self, bible_repo):
        """Test parsing comma-separated verses."""
        ref = BibleReferenceFormatter.parse("John 3:16,18,20", bible_repo)
        
        assert ref.book_id == 'jhn'
        assert ref.chapter_num == 3
        assert ref.verse_num == 16
        assert len(ref.additional_verses) == 2
        assert ref.additional_verses[0].start_verse == 18
        assert ref.additional_verses[1].start_verse == 20
    
    def test_parse_comma_with_ranges(self, bible_repo):
        """Test parsing comma-separated with ranges."""
        ref = BibleReferenceFormatter.parse("John 3:16,18,20-22", bible_repo)
        
        assert ref.book_id == 'jhn'
        assert ref.chapter_num == 3
        assert ref.verse_num == 16
        assert len(ref.additional_verses) == 2
        assert ref.additional_verses[0].start_verse == 18
        assert ref.additional_verses[1].start_verse == 20
        assert ref.additional_verses[1].end_verse == 22
    
    def test_parse_semicolon_separated(self, bible_repo):
        """Test parsing semicolon-separated references."""
        ref = BibleReferenceFormatter.parse("Genesis 1:1-3;2:3-4", bible_repo)
        
        assert ref.book_id == 'gen'
        assert ref.chapter_num == 1
        assert ref.verse_num == 1
        assert ref.end_verse_num == 3
        assert len(ref.additional_verses) == 1
        assert ref.additional_verses[0].chapter_num == 2
        assert ref.additional_verses[0].start_verse == 3
        assert ref.additional_verses[0].end_verse == 4


class TestParseNumberedBooks:
    """Tests for parsing references with numbered books."""
    
    def test_parse_1_samuel(self, bible_repo):
        """Test parsing 1 Samuel reference."""
        ref = BibleReferenceFormatter.parse("1 Samuel 17:1", bible_repo)
        assert ref.book_id == '1sa'
        assert ref.chapter_num == 17
        assert ref.verse_num == 1
    
    def test_parse_2_corinthians(self, bible_repo):
        """Test parsing 2 Corinthians reference."""
        ref = BibleReferenceFormatter.parse("2 Corinthians 5:17", bible_repo)
        assert ref.book_id == '2co'
        assert ref.chapter_num == 5
        assert ref.verse_num == 17
    
    def test_parse_1_john(self, bible_repo):
        """Test parsing 1 John reference."""
        ref = BibleReferenceFormatter.parse("1 John 4:8", bible_repo)
        assert ref.book_id == '1jn'
        assert ref.chapter_num == 4
        assert ref.verse_num == 8


class TestErrorHandling:
    """Tests for error handling."""
    
    def test_empty_reference(self, bible_repo):
        """Test that empty reference raises error."""
        with pytest.raises(ReferenceFormatError, match="cannot be empty"):
            BibleReferenceFormatter.parse("", bible_repo)
    
    def test_whitespace_only_reference(self, bible_repo):
        """Test that whitespace-only reference raises error."""
        with pytest.raises(ReferenceFormatError, match="cannot be empty"):
            BibleReferenceFormatter.parse("   ", bible_repo)
    
    def test_unknown_book(self, bible_repo):
        """Test that unknown book raises error."""
        with pytest.raises(ReferenceFormatError, match="Unknown book"):
            BibleReferenceFormatter.parse("Foo 1:1", bible_repo)
    
    def test_invalid_chapter_verse_format(self, bible_repo):
        """Test that invalid format raises error."""
        with pytest.raises(ReferenceFormatError, match="Invalid"):
            BibleReferenceFormatter.parse("John 3::16", bible_repo)
    
    def test_too_long_reference(self, bible_repo):
        """Test that overly long reference raises error."""
        long_ref = "John " + "1:1," * 200
        with pytest.raises(ReferenceFormatError, match="too long"):
            BibleReferenceFormatter.parse(long_ref, bible_repo)
    
    def test_too_many_comma_separated(self, bible_repo):
        """Test that too many comma-separated verses raises error."""
        many_verses = "John 3:" + ",".join(str(i) for i in range(1, 60))
        with pytest.raises(ReferenceFormatError, match="Too many"):
            BibleReferenceFormatter.parse(many_verses, bible_repo)
    
    def test_too_many_semicolon_separated(self, bible_repo):
        """Test that too many semicolon-separated parts raises error."""
        many_parts = "Genesis " + ";".join(f"{i}:1" for i in range(1, 25))
        with pytest.raises(ReferenceFormatError, match="Too many"):
            BibleReferenceFormatter.parse(many_parts, bible_repo)
    
    def test_invalid_number(self, bible_repo):
        """Test that invalid numbers raise error."""
        with pytest.raises(ReferenceFormatError):
            BibleReferenceFormatter.parse("John abc:16", bible_repo)


class TestGetVersesFromReference:
    """Tests for get_verses_from_reference convenience method."""
    
    def test_get_single_verse(self, bible_repo):
        """Test getting a single verse."""
        verses = BibleReferenceFormatter.get_verses_from_reference(
            "Genesis 1:1", bible_repo
        )
        
        assert len(verses) == 1
        assert verses[0].book_id == 'gen'
        assert verses[0].chapter_num == 1
        assert verses[0].num == 1
    
    def test_get_verse_range(self, bible_repo):
        """Test getting a verse range."""
        verses = BibleReferenceFormatter.get_verses_from_reference(
            "Genesis 1:1-3", bible_repo
        )
        
        assert len(verses) == 3
        assert all(v.chapter_num == 1 for v in verses)
        assert [v.num for v in verses] == [1, 2, 3]
    
    def test_get_chapter(self, bible_repo):
        """Test getting an entire chapter."""
        verses = BibleReferenceFormatter.get_verses_from_reference(
            "Genesis 1", bible_repo
        )
        
        assert len(verses) > 0
        assert all(v.chapter_num == 1 for v in verses)
    
    def test_get_multi_chapter_range(self, bible_repo):
        """Test getting a multi-chapter range."""
        verses = BibleReferenceFormatter.get_verses_from_reference(
            "Genesis 1:1-2:3", bible_repo
        )
        
        assert len(verses) > 3
        # Should have verses from chapter 1 and chapter 2
        chapters = set(v.chapter_num for v in verses)
        assert 1 in chapters
        assert 2 in chapters
    
    def test_get_nonexistent_verse(self, bible_repo):
        """Test getting a non-existent verse returns empty list."""
        verses = BibleReferenceFormatter.get_verses_from_reference(
            "Genesis 1:9999", bible_repo
        )
        
        assert len(verses) == 0


class TestBibleReferenceModel:
    """Tests for BibleReference model."""
    
    def test_string_representation_simple(self):
        """Test string representation of simple reference."""
        ref = BibleReference(book_id='jhn', chapter_num=3, verse_num=16)
        assert str(ref) == "jhn 3:16"
    
    def test_string_representation_range(self):
        """Test string representation of verse range."""
        ref = BibleReference(
            book_id='jhn', chapter_num=3, verse_num=16, end_verse_num=18
        )
        assert str(ref) == "jhn 3:16-18"
    
    def test_string_representation_multi_chapter(self):
        """Test string representation of multi-chapter range."""
        ref = BibleReference(
            book_id='gen', chapter_num=1, verse_num=1,
            end_chapter_num=2, end_verse_num=3
        )
        assert str(ref) == "gen 1:1-2:3"
    
    def test_string_representation_chapter_only(self):
        """Test string representation of chapter-only reference."""
        ref = BibleReference(book_id='psa', chapter_num=23, is_chapter_only=True)
        assert str(ref) == "psa 23"


class TestVerseRangeModel:
    """Tests for VerseRange model."""
    
    def test_string_representation_simple(self):
        """Test string representation of simple verse range."""
        vr = VerseRange(start_verse=16, end_verse=18)
        assert str(vr) == "16-18"
    
    def test_string_representation_single(self):
        """Test string representation of single verse."""
        vr = VerseRange(start_verse=16)
        assert str(vr) == "16"
    
    def test_string_representation_with_chapter(self):
        """Test string representation with chapter number."""
        vr = VerseRange(chapter_num=2, start_verse=3, end_verse=5)
        assert str(vr) == "2:3-5"


class TestSecurityFeatures:
    """Tests for security features."""
    
    def test_input_length_validation(self, bible_repo):
        """Test that input length is validated."""
        long_input = "John " + "1:1," * 200
        with pytest.raises(ReferenceFormatError, match="too long"):
            BibleReferenceFormatter.parse(long_input, bible_repo)
    
    def test_complexity_limit_comma(self, bible_repo):
        """Test complexity limit for comma-separated verses."""
        complex_ref = "John 3:" + ",".join(str(i) for i in range(1, 60))
        with pytest.raises(ReferenceFormatError, match="Too many"):
            BibleReferenceFormatter.parse(complex_ref, bible_repo)
    
    def test_complexity_limit_semicolon(self, bible_repo):
        """Test complexity limit for semicolon-separated parts."""
        complex_ref = "Genesis " + ";".join(f"{i}:1" for i in range(1, 25))
        with pytest.raises(ReferenceFormatError, match="Too many"):
            BibleReferenceFormatter.parse(complex_ref, bible_repo)
    
    def test_special_characters_handled(self, bible_repo):
        """Test that special characters in parentheses are handled."""
        ref = BibleReferenceFormatter.parse(
            "John 3:16 (For God so loved!@#$%)", bible_repo
        )
        assert ref.verse_num == 16
