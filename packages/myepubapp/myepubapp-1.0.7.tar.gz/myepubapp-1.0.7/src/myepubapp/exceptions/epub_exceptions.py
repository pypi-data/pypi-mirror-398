class EPUBError(Exception):
    """Base exception class for EPUB processing"""

    pass


class ChapterError(EPUBError):
    """Exception for chapter processing"""

    pass


class MetadataError(EPUBError):
    """Exception for metadata processing"""

    pass


class TOCError(EPUBError):
    """Exception for table of contents generation"""

    pass


class ContentGenerationError(EPUBError):
    """Exception for content generation"""

    pass


class FileHandlerError(EPUBError):
    """Exception for file handling"""

    pass


class TextProcessingError(EPUBError):
    """Exception for text processing"""

    pass
