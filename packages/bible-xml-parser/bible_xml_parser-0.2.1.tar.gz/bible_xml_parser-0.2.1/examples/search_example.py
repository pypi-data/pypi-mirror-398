"""Example of full-text search functionality."""

from bible_parser import BibleRepository


def main() -> None:
    """Demonstrate full-text search capabilities."""
    
    xml_file = "bible_small_usfx.xml"
    database_file = "my_bible.db"
    
    print("=" * 60)
    print("Bible Parser - Full-Text Search Example")
    print("=" * 60)
    
    with BibleRepository(xml_path=xml_file) as repo:
        repo.initialize(database_file)
        
        # Example 1: Simple search
        print("\n" + "=" * 60)
        print("Example 1: Search for 'God'")
        print("=" * 60)
        
        results = repo.search_verses('God', limit=5)
        print(f"\nFound {len(results)} verses:\n")
        
        for verse in results:
            print(f"{verse.book_id.upper()} {verse.chapter_num}:{verse.num}")
            print(f"  {verse.text}\n")
        
        # Example 2: Multi-word search
        print("=" * 60)
        print("Example 2: Search for 'heaven and earth'")
        print("=" * 60)
        
        results = repo.search_verses('heaven earth', limit=5)
        print(f"\nFound {len(results)} verses:\n")
        
        for verse in results:
            print(f"{verse.book_id.upper()} {verse.chapter_num}:{verse.num}")
            print(f"  {verse.text}\n")
        
        # Example 3: Search in specific book
        print("=" * 60)
        print("Example 3: Count verses with 'Lord' in Psalms")
        print("=" * 60)
        
        # Get all Psalms verses
        psalm_chapters = repo.get_chapter_count('psa')
        lord_count = 0
        
        for chapter in range(1, psalm_chapters + 1):
            verses = repo.get_verses('psa', chapter)
            for verse in verses:
                if 'Lord' in verse.text or 'LORD' in verse.text:
                    lord_count += 1
        
        print(f"\nFound 'Lord' in {lord_count} verses in Psalms")
        
        # Example 4: Search statistics
        print("\n" + "=" * 60)
        print("Example 4: Search Statistics")
        print("=" * 60)
        
        search_terms = ['God', 'light', 'earth', 'day', 'blessed']
        
        print("\nWord frequency in the sample:\n")
        for term in search_terms:
            results = repo.search_verses(term, limit=1000)
            print(f"  {term:10s}: {len(results):4d} verses")


if __name__ == "__main__":
    main()
