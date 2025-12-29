"""
InvoiceAI SDK Exceptions
"""


class InvoiceAIError(Exception):
    """Base exception for InvoiceAI SDK errors."""
    
    def __init__(self, message: str, status: int = 500, code: str = "UNKNOWN_ERROR"):
        self.message = message
        self.status = status
        self.code = code
        super().__init__(self.message)
    
    def __str__(self) -> str:
        return f"InvoiceAIError({self.status}): {self.message}"
    
    def __repr__(self) -> str:
        return f"InvoiceAIError(message={self.message!r}, status={self.status}, code={self.code!r})"


class AuthenticationError(InvoiceAIError):
    """Raised when authentication fails."""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status=401, code="AUTHENTICATION_ERROR")


class NotFoundError(InvoiceAIError):
    """Raised when a resource is not found."""
    
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status=404, code="NOT_FOUND")


class ValidationError(InvoiceAIError):
    """Raised when request validation fails."""
    
    def __init__(self, message: str = "Validation failed"):
        super().__init__(message, status=400, code="VALIDATION_ERROR")


class RateLimitError(InvoiceAIError):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, status=429, code="RATE_LIMIT_EXCEEDED")


class TimeoutError(InvoiceAIError):
    """Raised when a request times out."""
    
    def __init__(self, message: str = "Request timeout"):
        super().__init__(message, status=408, code="TIMEOUT")
