# Bible Parser Examples

This directory contains example scripts demonstrating how to use the bible_parser package.

## Sample Files

- **`bible_small_usfx.xml`** - Small sample Bible in USFX format (Genesis 1-2)
- **`bible_small_osis.xml`** - Small sample Bible in OSIS format (Genesis 1-2)

## Example Scripts

### 1. Direct Parsing (`direct_parsing.py`)

Demonstrates parsing Bible XML files directly without database caching.

**Run:**
```bash
cd examples
python direct_parsing.py
```

**Features:**
- Auto-detect Bible format
- Iterate over books
- Access verses directly
- Parse from string

### 2. Database Approach (`database_approach.py`)

Demonstrates using SQLite database for caching and fast access.

**Run:**
```bash
cd examples
python database_approach.py
```

**Features:**
- Database initialization
- List all books
- Get verses from specific chapters
- Get specific verses
- Full-text search

### 3. Search Example (`search_example.py`)

Demonstrates full-text search capabilities using SQLite FTS5.

**Run:**
```bash
cd examples
python search_example.py
```

**Features:**
- Simple text search
- Multi-word search
- Search in specific books
- Search statistics

### 4. Reference Formatter Example (`reference_formatter_example.py`)

Demonstrates parsing Bible references and retrieving verses.

**Run:**
```bash
cd examples
# Edit the file to add your Bible path, then:
python reference_formatter_example.py
```

**Features:**
- Parse simple verse references (e.g., "John 3:16")
- Parse verse ranges (e.g., "John 3:16-18")
- Parse multi-chapter ranges (e.g., "Genesis 1:1-2:3")
- Parse complex patterns (e.g., "John 3:16,18,20-22")
- Parse chapter-only references (e.g., "Psalm 23")
- Parse semicolon-separated references (e.g., "Genesis 1:1-3;2:3-4")
- Handle parenthetical descriptions (e.g., "1 Samuel 17:1-58 (David and Goliath)")
- Extract first verse from complex references
- Validate book names
- Works with OSIS, USFX, and Zefania formats

**Usage:**
```python
from bible_parser import BibleReferenceFormatter, BibleRepository

with BibleRepository(xml_path='bible.xml', format='OSIS') as repo:
    repo.initialize(':memory:')
    
    # Parse a reference
    ref = BibleReferenceFormatter.parse("John 3:16", repo)
    
    # Get verses directly
    verses = BibleReferenceFormatter.get_verses_from_reference("John 3:16-18", repo)
```

## Using Your Own Bible Files

To use your own Bible XML files, simply change the `xml_file` variable in any example:

```python
# Use your own file
xml_file = "/path/to/your/bible.xml"

# Or use one of the sample files
xml_file = "bible_small_usfx.xml"
xml_file = "bible_small_osis.xml"
```

## Supported Formats

The parser automatically detects these formats:
- **USFX** - Unified Standard Format XML
- **OSIS** - Open Scripture Information Standard
- **ZEFANIA** - Zefania XML Bible Markup Language

## Output

Each example will:
1. Parse the Bible file
2. Display information about books, chapters, and verses
3. Demonstrate specific features
4. Clean up resources automatically

## Database Files

The database examples create a `my_bible.db` file in the examples directory. This file can be reused across runs for faster access. Delete it to re-import from XML.

## Requirements

Make sure the bible_parser package is installed:

```bash
cd ..
pip install -e .
```

## Getting More Bible Files

You can find more Bible XML files at:
- [Open Bibles Repository](https://github.com/seven1m/open-bibles)
- Various Bible translation websites

## Notes

- The sample files contain only Genesis chapters 1-2 for demonstration purposes
- For production use, download complete Bible translations
- The database approach is recommended for applications that need repeated access
- The direct parsing approach is good for one-time processing or when you need the latest data
