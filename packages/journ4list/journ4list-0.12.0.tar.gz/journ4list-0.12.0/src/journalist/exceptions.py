from typing import Optional


class journalistError(Exception):
    """Base exception for all journalist-specific errors."""
    pass


class ValidationError(journalistError):
    """Raised when input validation fails."""
    pass


class NetworkError(journalistError):
    """Raised when network operations fail."""
    
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class ExtractionError(journalistError):
    """Raised when content extraction fails."""
    
    def __init__(self, message: str, url: Optional[str] = None):
        super().__init__(message)
        self.url = url
