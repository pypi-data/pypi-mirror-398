"""Test OSIS parser title extraction from <title> elements."""

import pytest
from bible_parser.parsers import OsisParser


class TestOsisTitleExtraction:
    """Tests for OSIS parser title extraction."""

    def test_extract_title_from_title_element(self) -> None:
        """Test that parser extracts full book names from <title> elements."""
        osis_xml = """<?xml version="1.0" encoding="UTF-8"?>
<osis xmlns="http://www.bibletechnologies.net/2003/OSIS/namespace">
  <osisText osisIDWork="KJV">
    <div type="book" osisID="Jas">
      <title type="main">James</title>
      <chapter osisID="Jas.1">
        <verse osisID="Jas.1.19">Wherefore, my beloved brethren, let every man be swift to hear, slow to speak, slow to wrath:</verse>
      </chapter>
    </div>
    <div type="book" osisID="Gen">
      <title type="main">Genesis</title>
      <chapter osisID="Gen.1">
        <verse osisID="Gen.1.1">In the beginning God created the heaven and the earth.</verse>
      </chapter>
    </div>
    <div type="book" osisID="Rev">
      <title type="main">Revelation</title>
      <chapter osisID="Rev.1">
        <verse osisID="Rev.1.1">The Revelation of Jesus Christ, which God gave unto him.</verse>
      </chapter>
    </div>
  </osisText>
</osis>
"""
        parser = OsisParser(osis_xml)
        books = list(parser.parse_books())

        assert len(books) == 3

        james = next((b for b in books if b.id == "jas"), None)
        assert james is not None
        assert james.title == "James", f"Expected 'James', got '{james.title}'"

        genesis = next((b for b in books if b.id == "gen"), None)
        assert genesis is not None
        assert genesis.title == "Genesis", f"Expected 'Genesis', got '{genesis.title}'"

        revelation = next((b for b in books if b.id == "rev"), None)
        assert revelation is not None
        assert revelation.title == "Revelation", f"Expected 'Revelation', got '{revelation.title}'"

    def test_fallback_to_capitalized_id_without_title(self) -> None:
        """Test that parser falls back to capitalized ID when no <title> element exists."""
        osis_xml = """<?xml version="1.0" encoding="UTF-8"?>
<osis xmlns="http://www.bibletechnologies.net/2003/OSIS/namespace">
  <osisText osisIDWork="KJV">
    <div type="book" osisID="Jas">
      <chapter osisID="Jas.1">
        <verse osisID="Jas.1.19">Test verse</verse>
      </chapter>
    </div>
  </osisText>
</osis>
"""
        parser = OsisParser(osis_xml)
        books = list(parser.parse_books())

        assert len(books) == 1
        assert books[0].id == "jas"
        assert books[0].title == "Jas", f"Expected fallback 'Jas', got '{books[0].title}'"
