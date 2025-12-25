"""Dolivroo SDK Exceptions"""


class DolivrooError(Exception):
    """Base exception for Dolivroo SDK"""
    
    def __init__(self, message: str, code: str = "UNKNOWN_ERROR", status_code: int = None, data: dict = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.data = data or {}

    def __str__(self):
        return f"{self.code}: {self.message}"


class AuthenticationError(DolivrooError):
    """Raised when API key is invalid or missing"""
    
    def __init__(self, message: str = "Invalid API key"):
        super().__init__(message, "AUTHENTICATION_ERROR", 401)


class ValidationError(DolivrooError):
    """Raised when request validation fails"""
    
    def __init__(self, message: str, errors: dict = None):
        super().__init__(message, "VALIDATION_ERROR", 422, errors)
        self.errors = errors or {}


class RateLimitError(DolivrooError):
    """Raised when rate limit is exceeded"""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = None):
        super().__init__(message, "RATE_LIMIT_ERROR", 429)
        self.retry_after = retry_after


class NotFoundError(DolivrooError):
    """Raised when a resource is not found"""
    
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, "NOT_FOUND", 404)
