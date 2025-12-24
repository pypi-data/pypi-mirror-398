"""Custom exceptions for internacia SDK."""


class InternaciaError(Exception):
    """Base exception for internacia SDK."""
    pass


class DatabaseError(InternaciaError):
    """Database-related errors."""
    pass


class NotFoundError(InternaciaError):
    """Resource not found errors."""
    pass


class ValidationError(InternaciaError):
    """Input validation errors."""
    pass


class DownloadError(InternaciaError):
    """Database download-related errors."""
    pass


class VersionError(InternaciaError):
    """Version-related errors."""
    pass
