"""Example usage of BibleReferenceFormatter.

This example demonstrates how to use the BibleReferenceFormatter to parse
Bible references and retrieve verses from a BibleRepository.
"""

from bible_parser import (
    BibleReferenceFormatter,
    BibleRepository,
    ReferenceFormatError,
)


def main(bible_path: str = None, bible_format: str = None):
    """Main example function.
    
    Args:
        bible_path: Path to your Bible XML file (OSIS, USFX, or Zefania format)
        bible_format: Format of the Bible file ('OSIS', 'USFX', or 'ZEFANIA')
    """
    # Use provided path or prompt user
    if not bible_path:
        print("Please provide a Bible XML file path.")
        print("Example usage:")
        print("  python reference_formatter_example.py")
        print("  # Then edit the main() call at the bottom with your file path")
        print()
        print("Supported formats: OSIS, USFX, Zefania")
        print("Example files:")
        print("  - OSIS: eng-kjv.osis.xml")
        print("  - USFX: eng-web.usfx.xml")
        print("  - Zefania: eng-asv.xml")
        return
    
    with BibleRepository(xml_path=bible_path, format=bible_format) as repo:
        repo.initialize(':memory:')  # Use in-memory database for this example
        
        print("=" * 70)
        print("Bible Reference Formatter Examples")
        print("=" * 70)
        
        # Example 1: Parse a simple verse reference
        print("\n1. Simple Verse Reference")
        print("-" * 70)
        try:
            ref = BibleReferenceFormatter.parse("John 3:16", repo)
            print(f"Reference: John 3:16")
            print(f"  Book ID: {ref.book_id}")
            print(f"  Chapter: {ref.chapter_num}")
            print(f"  Verse: {ref.verse_num}")
            
            # Get the actual verse text
            verses = BibleReferenceFormatter.get_verses_from_reference("John 3:16", repo)
            if verses:
                print(f"  Text: {verses[0].text}")
        except ReferenceFormatError as e:
            print(f"  Error: {e}")
        
        # Example 2: Parse a verse range
        print("\n2. Verse Range (Same Chapter)")
        print("-" * 70)
        try:
            ref = BibleReferenceFormatter.parse("John 3:16-18", repo)
            print(f"Reference: John 3:16-18")
            print(f"  Book ID: {ref.book_id}")
            print(f"  Chapter: {ref.chapter_num}")
            print(f"  Start Verse: {ref.verse_num}")
            print(f"  End Verse: {ref.end_verse_num}")
            
            # Get all verses in the range
            verses = BibleReferenceFormatter.get_verses_from_reference("John 3:16-18", repo)
            print(f"  Retrieved {len(verses)} verses:")
            for verse in verses:
                print(f"    {verse.chapter_num}:{verse.num} - {verse.text[:50]}...")
        except ReferenceFormatError as e:
            print(f"  Error: {e}")
        
        # Example 3: Parse a multi-chapter range
        print("\n3. Multi-Chapter Range")
        print("-" * 70)
        try:
            ref = BibleReferenceFormatter.parse("Genesis 1:1-2:3", repo)
            print(f"Reference: Genesis 1:1-2:3")
            print(f"  Book ID: {ref.book_id}")
            print(f"  Start: Chapter {ref.chapter_num}, Verse {ref.verse_num}")
            print(f"  End: Chapter {ref.end_chapter_num}, Verse {ref.end_verse_num}")
            
            verses = BibleReferenceFormatter.get_verses_from_reference("Genesis 1:1-2:3", repo)
            print(f"  Retrieved {len(verses)} verses across chapters")
        except ReferenceFormatError as e:
            print(f"  Error: {e}")
        
        # Example 4: Parse a chapter-only reference
        print("\n4. Chapter-Only Reference")
        print("-" * 70)
        try:
            ref = BibleReferenceFormatter.parse("Psalm 23", repo)
            print(f"Reference: Psalm 23")
            print(f"  Book ID: {ref.book_id}")
            print(f"  Chapter: {ref.chapter_num}")
            print(f"  Is Chapter Only: {ref.is_chapter_only}")
            
            verses = BibleReferenceFormatter.get_verses_from_reference("Psalm 23", repo)
            print(f"  Retrieved {len(verses)} verses from the chapter")
        except ReferenceFormatError as e:
            print(f"  Error: {e}")
        
        # Example 5: Parse complex comma-separated verses
        print("\n5. Complex Comma-Separated Pattern")
        print("-" * 70)
        try:
            ref = BibleReferenceFormatter.parse("John 3:16,18,20-22", repo)
            print(f"Reference: John 3:16,18,20-22")
            print(f"  Book ID: {ref.book_id}")
            print(f"  Chapter: {ref.chapter_num}")
            print(f"  Primary Verse: {ref.verse_num}")
            print(f"  Additional Verses: {len(ref.additional_verses)}")
            for vr in ref.additional_verses:
                if vr.end_verse:
                    print(f"    - Verses {vr.start_verse}-{vr.end_verse}")
                else:
                    print(f"    - Verse {vr.start_verse}")
            
            verses = BibleReferenceFormatter.get_verses_from_reference("John 3:16,18,20-22", repo)
            print(f"  Retrieved {len(verses)} total verses")
        except ReferenceFormatError as e:
            print(f"  Error: {e}")
        
        # Example 6: Parse semicolon-separated references
        print("\n6. Semicolon-Separated References")
        print("-" * 70)
        try:
            ref = BibleReferenceFormatter.parse("Genesis 1:1-3;2:3-4", repo)
            print(f"Reference: Genesis 1:1-3;2:3-4")
            print(f"  Book ID: {ref.book_id}")
            print(f"  Primary: Chapter {ref.chapter_num}, Verses {ref.verse_num}-{ref.end_verse_num}")
            print(f"  Additional Parts: {len(ref.additional_verses)}")
            
            verses = BibleReferenceFormatter.get_verses_from_reference("Genesis 1:1-3;2:3-4", repo)
            print(f"  Retrieved {len(verses)} total verses")
        except ReferenceFormatError as e:
            print(f"  Error: {e}")
        
        # Example 7: Parse reference with parenthetical description
        print("\n7. Reference with Description")
        print("-" * 70)
        try:
            ref = BibleReferenceFormatter.parse("1 Samuel 17:1-58 (David and Goliath)", repo)
            print(f"Reference: 1 Samuel 17:1-58 (David and Goliath)")
            print(f"  Book ID: {ref.book_id}")
            print(f"  Chapter: {ref.chapter_num}")
            print(f"  Verses: {ref.verse_num}-{ref.end_verse_num}")
            print("  Note: Parenthetical description is automatically removed")
        except ReferenceFormatError as e:
            print(f"  Error: {e}")
        
        # Example 8: Get first verse from complex reference
        print("\n8. Extract First Verse from Complex Reference")
        print("-" * 70)
        complex_refs = [
            "John 3:16,18,20-22",
            "Genesis 1:1-2:3",
            "Ruth 1-4",
            "Psalm 23",
        ]
        for ref_str in complex_refs:
            try:
                first = BibleReferenceFormatter.get_first_verse_in_reference(ref_str)
                print(f"  {ref_str:30} → {first}")
            except ReferenceFormatError as e:
                print(f"  {ref_str:30} → Error: {e}")
        
        # Example 9: Validate book names
        print("\n9. Book Name Validation")
        print("-" * 70)
        test_books = ["John", "Genesis", "Foo", "Revelations", "1 Corinthians"]
        for book in test_books:
            is_valid = BibleReferenceFormatter.is_valid_book(book)
            status = "✓ Valid" if is_valid else "✗ Invalid"
            print(f"  {book:20} {status}")
        
        # Example 10: Error handling
        print("\n10. Error Handling")
        print("-" * 70)
        invalid_refs = [
            "",  # Empty reference
            "Foo 1:1",  # Unknown book
            "John 3::16",  # Invalid format
            "John " + "1:1," * 60,  # Too many verses
        ]
        for ref_str in invalid_refs:
            try:
                BibleReferenceFormatter.parse(ref_str, repo)
                print(f"  {ref_str[:40]:40} → Parsed successfully")
            except ReferenceFormatError as e:
                print(f"  {ref_str[:40]:40} → Error: {str(e)[:30]}...")
        
        # Example 11: Working with numbered books
        print("\n11. Numbered Books")
        print("-" * 70)
        numbered_refs = [
            "1 Samuel 17:1",
            "2 Corinthians 5:17",
            "1 John 4:8",
            "2 Timothy 3:16",
        ]
        for ref_str in numbered_refs:
            try:
                ref = BibleReferenceFormatter.parse(ref_str, repo)
                print(f"  {ref_str:25} → Book ID: {ref.book_id}")
            except ReferenceFormatError as e:
                print(f"  {ref_str:25} → Error: {e}")
        
        print("\n" + "=" * 70)
        print("Examples Complete!")
        print("=" * 70)


def display_reference_with_text(reference: str, repo):
    """Helper function to display a reference with its verse text.
    
    Args:
        reference: Bible reference string.
        repo: BibleRepository instance.
    """
    try:
        # Parse the reference
        ref = BibleReferenceFormatter.parse(reference, repo)
        
        # Get verses
        verses = BibleReferenceFormatter.get_verses_from_reference(reference, repo)
        
        # Display
        print(f"\n{reference}")
        print("=" * 70)
        print(f"Parsed: {ref}")
        print(f"Found {len(verses)} verse(s):")
        for verse in verses:
            print(f"  {verse.book_id} {verse.chapter_num}:{verse.num}")
            print(f"    {verse.text}")
        
    except ReferenceFormatError as e:
        print(f"\nError parsing '{reference}': {e}")


if __name__ == "__main__":
    # Example: Uncomment and modify the line below with your Bible file path
    # main('path/to/your/bible.xml', 'OSIS')  # or 'USFX' or 'ZEFANIA'
    
    # If no path provided, show usage instructions
    main()
