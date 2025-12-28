"""Custom exceptions for EShopBox"""


class EShopBoxException(Exception):
    """Base exception for EShopBox"""
    pass


class AuthenticationError(EShopBoxException):
    """Raised when authentication fails"""
    pass


class APIError(EShopBoxException):
    """Raised when API returns an error"""
    
    def __init__(self, message, status_code=None, response=None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class ValidationError(EShopBoxException):
    """Raised when input validation fails"""
    pass


class RateLimitError(EShopBoxException):
    """Raised when rate limit is exceeded"""
    pass


class NotFoundError(EShopBoxException):
    """Raised when resource is not found"""
    pass