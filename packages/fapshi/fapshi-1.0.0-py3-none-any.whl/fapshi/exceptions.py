"""Custom exceptions for the Fapshi SDK."""


class FapshiException(Exception):
    """Base exception for all Fapshi SDK errors."""
    
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class FapshiAPIError(FapshiException):
    """Exception raised for API errors (4XX responses)."""
    
    def __init__(self, message: str, status_code: int = None, response_data: dict = None):
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(message)


class FapshiValidationError(FapshiException):
    """Exception raised for input validation errors."""
    pass


class FapshiAuthenticationError(FapshiException):
    """Exception raised for authentication failures."""
    pass

