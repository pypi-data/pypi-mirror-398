"""
Exception classes for Truslyo SDK
"""

class TrusyloError(Exception):
    """Base exception for Truslyo SDK"""
    pass


class FraudDetectedError(TrusyloError):
    """Raised when fraud is detected"""
    def __init__(self, message, result=None):
        super().__init__(message)
        self.result = result


class InvalidTokenError(TrusyloError):
    """Raised when token is invalid or expired"""
    pass


class APIError(TrusyloError):
    """Raised when API request fails"""
    pass


class RateLimitError(TrusyloError):
    """Raised when rate limit is exceeded"""
    pass