# Bible XML Parser

![PyPI](https://img.shields.io/pypi/v/bible-xml-parser)
![Python Versions](https://img.shields.io/pypi/pyversions/bible-xml-parser)
![License](https://img.shields.io/pypi/l/bible-xml-parser)
![Downloads](https://img.shields.io/pypi/dm/bible-xml-parser)

A Python package for parsing Bible texts in various XML formats (USFX, OSIS, ZEFANIA). This package provides both direct parsing and database-backed approaches for handling Bible data in your Python applications.

## Features

- 📖 Parse Bible texts in multiple formats (USFX, OSIS, ZEFANIA)
- 🔍 Automatic format detection
- 🚀 Memory-efficient streaming XML parsing using defusedxml
- 🗄️ SQLite database caching for improved performance
- 🔎 Full-text search functionality (FTS5)
- 📝 **Bible reference parsing** - Parse references like "John 3:16-18" or "Genesis 1:1-2:3"
- 🔒 Secure XML parsing (protected against XXE attacks)
- 📝 Type hints throughout for better IDE support
- 🐍 Python 3.8+ support

## Installation

```bash
pip install bible-xml-parser
```

### Development Installation

```bash
git clone https://github.com/Omarzintan/bible_parser_python.git
cd bible_parser_python
pip install -e ".[dev]"
```

## Quick Start

### Direct Parsing Approach

Parse a Bible file directly without database caching:

```python
from bible_parser import BibleParser

# Parse from file (format auto-detected)
parser = BibleParser('path/to/bible.xml')

# Or parse from string with explicit format
xml_content = open('bible.xml').read()
parser = BibleParser.from_string(xml_content, format='USFX')

# Iterate over books
for book in parser.books:
    print(f"{book.title} ({book.id})")
    print(f"  Chapters: {len(book.chapters)}")
    print(f"  Verses: {len(book.verses)}")

# Or iterate over verses directly
for verse in parser.verses:
    print(f"{verse.book_id} {verse.chapter_num}:{verse.num} - {verse.text}")
```

### Database Approach (Recommended for Production)

For better performance, use the database approach:

```python
from bible_parser import BibleRepository

# Create repository
repo = BibleRepository(xml_path='path/to/bible.xml', format='USFX')

# Initialize database (only needed once)
repo.initialize('my_bible.db')

# Get all books
books = repo.get_books()
for book in books:
    print(f"{book.title} ({book.id})")

# Get verses from a specific chapter
verses = repo.get_verses('gen', 1)  # Genesis chapter 1
for verse in verses:
    print(f"{verse.num}. {verse.text}")

# Get a specific verse
verse = repo.get_verse('jhn', 3, 16)  # John 3:16
if verse:
    print(verse.text)

# Search for verses containing specific text
results = repo.search_verses('love')
print(f"Found {len(results)} verses containing 'love'")

# Don't forget to close
repo.close()
```

### Using Context Manager

```python
from bible_parser import BibleRepository

with BibleRepository(xml_path='bible.xml') as repo:
    repo.initialize('my_bible.db')
    
    # Use the repository
    verses = repo.get_verses('mat', 5)  # Matthew chapter 5
    for verse in verses:
        print(f"{verse.num}. {verse.text}")
    
    # Search
    results = repo.search_verses('faith hope love')
    for verse in results:
        print(f"{verse.book_id} {verse.chapter_num}:{verse.num}")

# Database automatically closed
```

### Bible Reference Parsing

Parse Bible references in various formats and retrieve verses:

```python
from bible_parser import BibleReferenceFormatter, BibleRepository

with BibleRepository(xml_path='bible.xml') as repo:
    repo.initialize('bible.db')
    
    # Parse a simple verse reference
    ref = BibleReferenceFormatter.parse("John 3:16", repo)
    print(f"Book: {ref.book_id}, Chapter: {ref.chapter_num}, Verse: {ref.verse_num}")
    
    # Get verses directly (convenience method)
    verses = BibleReferenceFormatter.get_verses_from_reference("John 3:16-18", repo)
    for verse in verses:
        print(f"{verse.chapter_num}:{verse.num} - {verse.text}")
    
    # Extract first verse from complex references
    first = BibleReferenceFormatter.get_first_verse_in_reference("Genesis 1:1-2:3")
    print(first)  # "Genesis 1:1"
    
    # Validate book names
    is_valid = BibleReferenceFormatter.is_valid_book("John")  # True
```

**Supported Reference Formats:**
- Single verse: `"John 3:16"`
- Verse range: `"John 3:16-18"`
- Multi-chapter: `"Genesis 1:1-2:3"`
- Chapter only: `"Psalm 23"`
- Multi-chapter range: `"Ruth 1-4"`
- Complex patterns: `"John 3:16,18,20-22"`
- Semicolon-separated: `"Genesis 1:1-3;2:3-4"`
- With descriptions: `"1 Samuel 17:1-58 (David and Goliath)"`

## Supported Formats

### USFX (Unified Standard Format XML)
```xml
<usfx>
  <book id="gen">
    <c id="1"/>
    <v id="1">In the beginning...</v>
  </book>
</usfx>
```

### OSIS (Open Scripture Information Standard)
```xml
<osis>
  <osisText>
    <div type="book" osisID="Gen">
      <verse osisID="Gen.1.1">In the beginning...</verse>
    </div>
  </osisText>
</osis>
```

### Zefania XML
```xml
<XMLBIBLE>
  <BIBLEBOOK bnumber="1" bname="Genesis">
    <CHAPTER cnumber="1">
      <VERS vnumber="1">In the beginning...</VERS>
    </CHAPTER>
  </BIBLEBOOK>
</XMLBIBLE>
```

## API Reference

### BibleParser

Main parser class with automatic format detection.

**Methods:**
- `__init__(source, format=None)` - Initialize parser
- `from_string(xml_content, format=None)` - Create from XML string
- `books` - Property that yields Book objects
- `verses` - Property that yields Verse objects

### BibleRepository

Database-backed repository for efficient Bible data access.

**Methods:**
- `__init__(xml_path=None, xml_string=None, format=None)` - Initialize repository
- `initialize(database_name)` - Create/open database
- `get_books()` - Get all books
- `get_verses(book_id, chapter_num)` - Get verses from a chapter
- `get_verse(book_id, chapter_num, verse_num)` - Get a specific verse
- `get_chapter_count(book_id)` - Get number of chapters in a book
- `search_verses(query, limit=100)` - Full-text search
- `close()` - Close database connection

### BibleReferenceFormatter

Utility class for parsing Bible references.

**Methods:**
- `parse(reference, bible_repository)` - Parse a reference string into a BibleReference object
- `get_verses_from_reference(reference, bible_repository)` - Parse and retrieve verses in one call
- `get_first_verse_in_reference(reference)` - Extract the first verse from a complex reference
- `is_valid_book(book_name)` - Check if a book name is valid

### Data Models

**Verse:**
- `num` (int) - Verse number
- `chapter_num` (int) - Chapter number
- `text` (str) - Verse text
- `book_id` (str) - Book identifier

**Chapter:**
- `num` (int) - Chapter number
- `verses` (List[Verse]) - List of verses

**Book:**
- `id` (str) - Book identifier (e.g., 'gen', 'mat')
- `num` (int) - Book number
- `title` (str) - Book title (e.g., 'Genesis', 'Matthew')
- `chapters` (List[Chapter]) - List of chapters
- `verses` (List[Verse]) - Flat list of all verses

**BibleReference:**
- `book_id` (str) - Book identifier
- `chapter_num` (int) - Starting chapter number
- `verse_num` (int) - Starting verse number (None for chapter-only)
- `end_chapter_num` (int) - Ending chapter for multi-chapter ranges
- `end_verse_num` (int) - Ending verse for verse ranges
- `is_chapter_only` (bool) - True if reference is chapter-only
- `additional_verses` (List[VerseRange]) - Additional verses for complex patterns

**VerseRange:**
- `chapter_num` (int) - Chapter number (optional)
- `start_verse` (int) - Starting verse number
- `end_verse` (int) - Ending verse number (None for single verse)

## Performance Considerations

### Direct Parsing
**Pros:**
- Simple implementation
- No database setup required
- Always uses the latest source files

**Cons:**
- CPU and memory intensive
- Slower for repeated access
- Repeated parsing on each run

### Database Approach
**Pros:**
- Much faster access once data is loaded
- Lower memory usage during queries
- Efficient full-text search with FTS5
- Works offline without re-parsing

**Cons:**
- Initial setup time
- Requires disk space
- Additional complexity

## Security

This package uses `defusedxml` for secure XML parsing, protecting against:
- **XXE (XML External Entity) attacks** - Prevents reading local files or making network requests
- **Billion Laughs attack** - Prevents exponential entity expansion
- **Quadratic blowup** - Prevents memory exhaustion

All database queries use parameterized statements to prevent SQL injection.

## Examples

See the `examples/` directory for complete working examples:
- `direct_parsing.py` - Direct parsing example
- `database_approach.py` - Database caching example
- `search_example.py` - Full-text search example

## Testing

Run tests with pytest:

```bash
pytest
```

With coverage:

```bash
pytest --cov=bible_parser --cov-report=term-missing
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Inspired by the Ruby [bible_parser](https://github.com/seven1m/bible_parser) library
- Flutter [bible_parser_flutter](https://github.com/Omarzintan/bible_parser_flutter) implementation
- Bible XML files from the [open-bibles](https://github.com/seven1m/open-bibles) repository

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.

## Support

- 📫 Issues: [GitHub Issues](https://github.com/Omarzintan/bible_parser_python/issues)
- 📖 Documentation: [GitHub Wiki](https://github.com/Omarzintan/bible_parser_python/wiki)
