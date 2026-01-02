"""
Custom exceptions for kxy-open-id-client
"""


class OpenIdClientError(Exception):
    """Base exception for all client errors"""
    pass


class OpenIdAPIError(OpenIdClientError):
    """Exception raised when API returns an error response"""

    def __init__(self, code: int, msg: str, trace_id: str = None):
        self.code = code
        self.msg = msg
        self.trace_id = trace_id
        super().__init__(f"API Error {code}: {msg}")


class OpenIdConnectionError(OpenIdClientError):
    """Exception raised when connection to API fails"""
    pass


class OpenIdTimeoutError(OpenIdClientError):
    """Exception raised when request times out"""
    pass
