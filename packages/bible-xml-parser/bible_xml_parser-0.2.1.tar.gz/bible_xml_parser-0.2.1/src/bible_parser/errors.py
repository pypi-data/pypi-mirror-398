"""Custom exceptions for the bible_parser package."""


class BibleParserException(Exception):
    """Base exception for all bible_parser errors."""

    pass


class ParseError(BibleParserException):
    """Raised when parsing XML content fails."""

    pass


class FormatDetectionError(BibleParserException):
    """Raised when the Bible format cannot be automatically detected."""

    pass


class ParserUnavailableError(BibleParserException):
    """Raised when a parser for the specified format is not available."""

    pass


class ReferenceFormatError(BibleParserException):
    """Raised when a Bible reference format is invalid or cannot be parsed.
    
    This exception is raised when:
    - The reference string is empty or invalid
    - The book name is not recognized
    - The chapter/verse format is malformed
    - The reference exceeds reasonable limits
    
    Examples:
        >>> raise ReferenceFormatError("Unknown book name: Foo")
        >>> raise ReferenceFormatError("Invalid chapter:verse format: 3::16")
        >>> raise ReferenceFormatError("Reference too long (max 500 characters)")
    """

    pass
