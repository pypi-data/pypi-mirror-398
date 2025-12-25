"""Custom exceptions for Vision MCP."""


class VisionAPIError(Exception):
    """Base exception for Vision API errors."""
    pass


class VisionAuthError(VisionAPIError):
    """Authentication related errors."""
    pass


class VisionRequestError(VisionAPIError):
    """Request related errors."""
    pass


class VisionTimeoutError(VisionAPIError):
    """Timeout related errors."""
    pass


class VisionValidationError(VisionAPIError):
    """Validation related errors."""
    pass
