"""Tests for main BibleParser class."""

import pytest
from bible_parser import BibleParser
from bible_parser.errors import FormatDetectionError, ParserUnavailableError


class TestBibleParser:
    """Tests for BibleParser class."""

    def test_format_detection_usfx(self) -> None:
        """Test USFX format detection."""
        xml = "<usfx><book id='gen'></book></usfx>"
        parser = BibleParser.from_string(xml)
        
        assert parser.format == "USFX"

    def test_format_detection_osis(self) -> None:
        """Test OSIS format detection."""
        xml = "<osis><osisText></osisText></osis>"
        parser = BibleParser.from_string(xml)
        
        assert parser.format == "OSIS"

    def test_format_detection_zefania(self) -> None:
        """Test Zefania format detection."""
        xml = "<XMLBIBLE><BIBLEBOOK></BIBLEBOOK></XMLBIBLE>"
        parser = BibleParser.from_string(xml)
        
        assert parser.format == "ZEFANIA"

    def test_explicit_format(self) -> None:
        """Test explicit format specification."""
        xml = "<test></test>"
        parser = BibleParser.from_string(xml, format="USFX")
        
        assert parser.format == "USFX"

    def test_invalid_format(self) -> None:
        """Test invalid format raises error."""
        xml = "<test></test>"
        
        with pytest.raises(ParserUnavailableError):
            BibleParser.from_string(xml, format="INVALID")

    def test_parse_books(self) -> None:
        """Test parsing books."""
        xml = """
        <usfx>
            <book id="gen">
                <c id="1"/>
                <v id="1">Test verse</v>
            </book>
        </usfx>
        """
        
        parser = BibleParser.from_string(xml)
        books = list(parser.books)
        
        assert len(books) == 1
        assert books[0].id == "gen"

    def test_parse_verses(self) -> None:
        """Test parsing verses directly."""
        xml = """
        <usfx>
            <book id="gen">
                <c id="1"/>
                <v id="1">Verse 1</v>
                <v id="2">Verse 2</v>
            </book>
        </usfx>
        """
        
        parser = BibleParser.from_string(xml)
        verses = list(parser.verses)
        
        assert len(verses) == 2
        assert verses[0].text == "Verse 1"
        assert verses[1].text == "Verse 2"
