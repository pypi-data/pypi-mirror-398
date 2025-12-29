"""
Custom exceptions for FAR Search Tool
"""


class FARSearchError(Exception):
    """Base exception for FAR Search Tool"""
    pass


class FARAPIError(FARSearchError):
    """Raised when the FAR RAG API returns an error"""
    
    def __init__(self, message: str, status_code: int = None):
        self.status_code = status_code
        super().__init__(message)


class FARRateLimitError(FARSearchError):
    """Raised when rate limit is exceeded"""
    
    def __init__(self, message: str = "Rate limit exceeded. Please try again later or upgrade your plan."):
        super().__init__(message)

