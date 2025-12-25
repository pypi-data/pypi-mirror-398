"""Example of database-backed approach."""

from bible_parser import BibleRepository


def main() -> None:
    """Demonstrate database-backed Bible access."""
    
    # Use the sample Bible XML file
    xml_file = "bible_small_usfx.xml"
    database_file = "my_bible.db"
    
    print("=" * 60)
    print("Bible Parser - Database Approach Example")
    print("=" * 60)
    
    # Use context manager for automatic cleanup
    with BibleRepository(xml_path=xml_file) as repo:
        # Initialize database (only needed once)
        print(f"\nInitializing database: {database_file}")
        repo.initialize(database_file)
        print("Database initialized successfully!")
        
        # Example 1: List all books
        print("\n" + "=" * 60)
        print("Example 1: List all books")
        print("=" * 60)
        
        books = repo.get_books()
        for book in books:
            chapter_count = repo.get_chapter_count(book.id)
            print(f"{book.num:2d}. {book.title:20s} ({book.id:5s}) - "
                  f"{chapter_count:3d} chapters")
        
        # Example 2: Get verses from a specific chapter
        print("\n" + "=" * 60)
        print("Example 2: Genesis Chapter 1")
        print("=" * 60)
        
        verses = repo.get_verses('gen', 1)
        print(f"\nFound {len(verses)} verses in Genesis 1\n")
        
        for verse in verses[:5]:  # Show first 5 verses
            print(f"Genesis 1:{verse.num}")
            print(f"  {verse.text}\n")
        
        # Example 3: Get a specific verse
        print("=" * 60)
        print("Example 3: Get Genesis 1:1")
        print("=" * 60)
        
        verse = repo.get_verse('gen', 1, 1)
        if verse:
            print(f"\nGenesis 1:1")
            print(f"  {verse.text}\n")
        else:
            print("\nVerse not found")
        
        # Example 4: Search for verses
        print("=" * 60)
        print("Example 4: Search for 'God'")
        print("=" * 60)
        
        results = repo.search_verses('God', limit=10)
        print(f"\nFound {len(results)} verses (showing first 10):\n")
        
        for verse in results:
            print(f"{verse.book_id.upper()} {verse.chapter_num}:{verse.num}")
            # Show first 100 characters of text
            text = verse.text[:100] + "..." if len(verse.text) > 100 else verse.text
            print(f"  {text}\n")
    
    print("=" * 60)
    print("Database connection closed automatically")
    print("=" * 60)


if __name__ == "__main__":
    main()
