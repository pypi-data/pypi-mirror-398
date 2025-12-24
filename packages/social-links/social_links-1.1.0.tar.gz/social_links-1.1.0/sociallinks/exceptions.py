"""
Custom exceptions for social-links library.
"""


class SocialLinksError(Exception):
    """Base exception for all social-links errors."""
    pass


class PlatformNotFoundError(SocialLinksError):
    """Raised when a platform is not found."""
    pass


class PlatformAlreadyExistsError(SocialLinksError):
    """Raised when attempting to create a platform that already exists."""
    pass


class InvalidPlatformError(SocialLinksError):
    """Raised when a platform has invalid configuration (missing patterns, templates, etc.)."""
    pass


class PlatformIDExtractionError(SocialLinksError):
    """Raised when a platform ID cannot be extracted from a URL."""
    pass


class URLMismatchError(SocialLinksError):
    """Raised when a URL does not match the expected platform pattern."""
    pass

