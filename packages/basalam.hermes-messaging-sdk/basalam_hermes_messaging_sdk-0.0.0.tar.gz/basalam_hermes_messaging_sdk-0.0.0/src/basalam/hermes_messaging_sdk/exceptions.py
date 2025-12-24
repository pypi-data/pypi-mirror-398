"""
Custom exceptions for Hermes SDK
"""


class HermesError(Exception):
    """Base exception for all Hermes SDK errors"""
    pass


class HermesAPIError(HermesError):
    """Raised when the API returns an error response"""

    def __init__(self, message: str, status_code: int = None, response_data: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class HermesAuthorizationError(HermesAPIError):
    """Raised when authorization fails (403 Forbidden or 401 Unauthorized)"""

    def __init__(self, message: str = None, status_code: int = None, response_data: dict = None):
        if message is None:
            if status_code == 401:
                message = "Authentication failed: Invalid or expired access token"
            elif status_code == 403:
                message = "Access denied: You don't have permission to access this workflow"
            else:
                message = "Authorization error"
        super().__init__(message, status_code, response_data)


class HermesConnectionError(HermesError):
    """Raised when unable to connect to Hermes API"""
    pass
