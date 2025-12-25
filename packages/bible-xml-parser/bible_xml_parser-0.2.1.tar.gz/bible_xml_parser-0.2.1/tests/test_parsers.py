"""Tests for Bible parsers."""

import pytest
from bible_parser.parsers import UsfxParser, OsisParser, ZefaniaParser
from bible_parser.errors import ParseError


# Test constants matching Flutter test file
SAMPLE_OSIS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<osis xmlns="http://www.bibletechnologies.net/2003/OSIS/namespace">
  <osisText osisIDWork="KJV">
    <div type="book" osisID="Gen">
      <chapter osisID="Gen.1">
        <verse osisID="Gen.1.1">In the beginning God created the heaven and the earth.</verse>
        <verse osisID="Gen.1.2">And the earth was without form, and void; and darkness was upon the face of the deep.</verse>
      </chapter>
    </div>
  </osisText>
</osis>
"""

SAMPLE_OSIS_XML_ALTERNATIVE = """<?xml version="1.0" encoding="UTF-8"?>
<osis xmlns="http://www.bibletechnologies.net/2003/OSIS/namespace">
  <osisText osisIDWork="KJV">
    <div type="book" osisID="Gen">
      <chapter osisRef="Gen.1" sID="Gen.1.seID.00001" n="1" />
      <verse osisID="Gen.1.1" sID="Gen.1.1.seID.00002" n="1" />In the beginning God created the heaven and the earth.
      <verse eID="Gen.1.1.seID.00002" />
      <verse osisID="Gen.1.2" sID="Gen.1.2.seID.00003" n="2" />And the earth was without form, and void; and darkness was upon the face of the deep.
      <verse eID="Gen.1.2.seID.00003" />
      <chapter eID="Gen.1.seID.00001" />
    </div>
  </osisText>
</osis>
"""

SAMPLE_USFX_XML = """<?xml version="1.0" encoding="UTF-8"?>
<usfx>
  <book id="GEN">
    <c id="1">
      <v id="1">In the beginning God created the heaven and the earth.</v>
      <v id="2">And the earth was without form, and void; and darkness was upon the face of the deep.</v>
    </c>
  </book>
</usfx>
"""

SAMPLE_USFX_XML_ALTERNATIVE = """<?xml version="1.0" encoding="UTF-8"?>
<usfx>
  <book id="GEN">
    <c id="1"/>
    <v id="1"/>In the beginning God created the heaven and the earth.
    <ve/>
    <v id="2"/>And the earth was without form, and void; and darkness was upon the face of the deep.
    <ve/>
  </book>
</usfx>
"""

SAMPLE_ZEFANIA_XML = """<?xml version="1.0" encoding="UTF-8"?>
<XMLBIBLE>
  <BIBLEBOOK bsname="GEN">
    <CHAPTER cnumber="1">
      <VERS vnumber="1">In the beginning God created the heaven and the earth.</VERS>
      <VERS vnumber="2">And the earth was without form, and void; and darkness was upon the face of the deep.</VERS>
    </CHAPTER>
  </BIBLEBOOK>
</XMLBIBLE>
"""


class TestOsisParser:
    """Tests for OSIS parser."""

    def test_check_format(self) -> None:
        """Test OSIS format detection."""
        parser = OsisParser("")
        
        assert parser.check_format("<osis><osisText></osisText></osis>")
        assert parser.check_format("<OSIS><osisText></osisText></OSIS>")
        assert not parser.check_format("<usfx></usfx>")

    def test_parse_osis_id(self) -> None:
        """Test OSIS ID parsing."""
        parser = OsisParser("")
        
        book_id, chapter, verse = parser._parse_osis_id("Gen.1.1")
        assert book_id == "gen"
        assert chapter == 1
        assert verse == 1
        
        book_id, chapter, verse = parser._parse_osis_id("Matt.5.3")
        assert book_id == "matt"
        assert chapter == 5
        assert verse == 3

    def test_parse_sample_osis_xml(self) -> None:
        """Test parsing sample OSIS XML."""
        parser = OsisParser(SAMPLE_OSIS_XML)
        
        # Test format detection
        assert parser.check_format(SAMPLE_OSIS_XML)
        
        # Test book parsing
        books = list(parser.parse_books())
        assert len(books) > 0
        assert books[0].id == "gen"
        assert books[0].title.lower() == "gen"  # Title defaults to ID in OSIS parser
        
        # Test verse parsing
        verses = list(parser.parse_verses())
        assert len(verses) == 2
        assert verses[0].num == 1
        assert verses[0].chapter_num == 1
        assert verses[0].book_id == "gen"
        assert "In the beginning" in verses[0].text

    def test_parse_sample_osis_xml_alternative(self) -> None:
        """Test parsing sample OSIS XML with alternative version."""
        parser = OsisParser(SAMPLE_OSIS_XML_ALTERNATIVE)
        
        # Test format detection
        assert parser.check_format(SAMPLE_OSIS_XML_ALTERNATIVE)
        
        # Test book parsing
        books = list(parser.parse_books())
        assert len(books) > 0
        assert books[0].id == "gen"
        
        # Test verse parsing
        verses = list(parser.parse_verses())
        assert len(verses) == 2
        assert verses[0].num == 1
        assert verses[0].chapter_num == 1
        assert verses[0].book_id == "gen"
        assert "In the beginning" in verses[0].text


class TestUsfxParser:
    """Tests for USFX parser."""

    def test_check_format(self) -> None:
        """Test USFX format detection."""
        parser = UsfxParser("")
        
        assert parser.check_format("<usfx><book id='gen'></book></usfx>")
        assert parser.check_format("<USFX><book id='gen'></book></USFX>")
        assert not parser.check_format("<osis></osis>")

    def test_get_book_name(self) -> None:
        """Test book name mapping."""
        parser = UsfxParser("")
        
        assert parser._get_book_name("GEN") == "Genesis"
        assert parser._get_book_name("MAT") == "Matthew"
        assert parser._get_book_name("REV") == "Revelation"

    def test_get_book_num(self) -> None:
        """Test book number mapping."""
        parser = UsfxParser("")
        
        assert parser._get_book_num("GEN") == 1
        assert parser._get_book_num("MAT") == 40
        assert parser._get_book_num("REV") == 66

    def test_parse_sample_usfx_xml(self) -> None:
        """Test parsing sample USFX XML."""
        parser = UsfxParser(SAMPLE_USFX_XML)
        
        # Test format detection
        assert parser.check_format(SAMPLE_USFX_XML)
        
        # Test book parsing
        books = list(parser.parse_books())
        assert len(books) > 0
        assert books[0].id == "gen"
        
        # Test verse parsing
        verses = list(parser.parse_verses())
        assert len(verses) == 2
        assert verses[0].num == 1
        assert verses[0].chapter_num == 1
        assert verses[0].book_id == "gen"
        assert "In the beginning" in verses[0].text

    def test_parse_sample_usfx_xml_alternative(self) -> None:
        """Test parsing sample USFX XML with alternative version."""
        parser = UsfxParser(SAMPLE_USFX_XML_ALTERNATIVE)
        
        # Test format detection
        assert parser.check_format(SAMPLE_USFX_XML_ALTERNATIVE)
        
        # Test book parsing
        books = list(parser.parse_books())
        assert len(books) > 0
        assert books[0].id == "gen"
        
        # Test verse parsing
        verses = list(parser.parse_verses())
        assert len(verses) == 2
        assert verses[0].num == 1
        assert verses[0].chapter_num == 1
        assert verses[0].book_id == "gen"
        assert "In the beginning" in verses[0].text


class TestZefaniaParser:
    """Tests for Zefania parser."""

    def test_check_format(self) -> None:
        """Test Zefania format detection."""
        parser = ZefaniaParser("")
        
        assert parser.check_format("<xmlbible><BIBLEBOOK></BIBLEBOOK></xmlbible>")
        assert parser.check_format("<XMLBIBLE><BIBLEBOOK></BIBLEBOOK></XMLBIBLE>")
        assert not parser.check_format("<usfx></usfx>")

    def test_parse_sample_zefania_xml(self) -> None:
        """Test parsing sample Zefania XML."""
        parser = ZefaniaParser(SAMPLE_ZEFANIA_XML)
        
        # Test format detection
        assert parser.check_format(SAMPLE_ZEFANIA_XML)
        
        # Test book parsing
        books = list(parser.parse_books())
        assert len(books) > 0
        assert books[0].id.lower() == "gen"
        
        # Test verse parsing
        verses = list(parser.parse_verses())
        assert len(verses) == 2
        assert verses[0].num == 1
        assert verses[0].chapter_num == 1
        assert verses[0].book_id.lower() == "gen"
        assert "In the beginning" in verses[0].text
