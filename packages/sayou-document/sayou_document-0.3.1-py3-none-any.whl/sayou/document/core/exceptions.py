from sayou.core.exceptions import SayouCoreError


class DocumentError(SayouCoreError):
    """Base exception for all document processing errors."""

    pass


class ParserError(DocumentError):
    """Raised when parsing a document fails (e.g., encrypted PDF)."""

    pass


class OCRError(DocumentError):
    """Raised when OCR processing fails."""

    pass


class ConversionError(DocumentError):
    """Raised when file conversion fails."""

    pass
