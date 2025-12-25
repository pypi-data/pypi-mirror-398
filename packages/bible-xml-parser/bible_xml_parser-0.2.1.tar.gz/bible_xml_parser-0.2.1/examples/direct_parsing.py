"""Example of direct parsing approach."""

from bible_parser import BibleParser


def main() -> None:
    """Demonstrate direct parsing of a Bible XML file."""
    
    # Use the sample Bible XML file
    xml_file = "bible_small_usfx.xml"
    
    print("=" * 60)
    print("Bible Parser - Direct Parsing Example")
    print("=" * 60)
    
    # Create parser (format will be auto-detected)
    parser = BibleParser(xml_file)
    print(f"\nDetected format: {parser.format}")
    
    # Example 1: Iterate over books
    print("\n" + "=" * 60)
    print("Example 1: List all books")
    print("=" * 60)
    
    for book in parser.books:
        print(f"{book.num:2d}. {book.title:20s} ({book.id:5s}) - "
              f"{len(book.chapters):3d} chapters, {len(book.verses):4d} verses")
    
    # Example 2: Get verses from a specific book
    print("\n" + "=" * 60)
    print("Example 2: First 5 verses of Genesis")
    print("=" * 60)
    
    parser2 = BibleParser(xml_file)  # Create new parser instance
    verse_count = 0
    
    for verse in parser2.verses:
        if verse.book_id == "gen" and verse.chapter_num == 1 and verse_count < 5:
            print(f"\nGenesis 1:{verse.num}")
            print(f"  {verse.text}")
            verse_count += 1
        elif verse_count >= 5:
            break
    
    # Example 3: Parse from string
    print("\n" + "=" * 60)
    print("Example 3: Parse from XML string")
    print("=" * 60)
    
    xml_content = """
    <usfx>
        <book id="gen">
            <c id="1"/>
            <v id="1">In the beginning God created the heaven and the earth.</v>
            <v id="2">And the earth was without form, and void.</v>
        </book>
    </usfx>
    """
    
    parser3 = BibleParser.from_string(xml_content, format="USFX")
    
    for book in parser3.books:
        print(f"\nBook: {book.title}")
        for verse in book.verses:
            print(f"  {verse.chapter_num}:{verse.num} - {verse.text}")


if __name__ == "__main__":
    main()
