class DocuOcrError(Exception):
    """Base exception for the engine."""


class InvalidDocumentError(DocuOcrError):
    """Raised when the provided document cannot be processed."""


class OcrEngineError(DocuOcrError):
    """Raised when the OCR engine fails."""
