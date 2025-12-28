# exceptions.py
"""
Custom exceptions for Tradion API client
"""

class TradionError(Exception):
    """Base exception for all Tradion API errors"""
    pass

class AuthenticationError(TradionError):
    """Raised when authentication fails"""
    def __init__(self, message="Authentication failed"):
        self.message = message
        super().__init__(self.message)

class TradionAPIError(TradionError):
    """Raised when API returns an error"""
    def __init__(self, error_code: str, message: str):
        self.error_code = error_code
        self.message = message
        super().__init__(f"[{error_code}] {message}")

class NetworkError(TradionError):
    """Raised when network request fails"""
    pass

class TimeoutError(TradionError):
    """Raised when request times out"""
    pass

class RateLimitError(TradionError):
    """Raised when rate limit is exceeded"""
    def __init__(self, message="Rate limit exceeded. Please wait before retrying."):
        self.message = message
        super().__init__(self.message)

class WebSocketError(TradionError):
    """Raised when WebSocket connection fails"""
    pass

class OrderError(TradionError):
    """Raised when order operation fails"""
    def __init__(self, error_code: str, message: str):
        self.error_code = error_code
        self.message = message
        super().__init__(f"Order Error [{error_code}]: {message}")

class ValidationError(TradionError):
    """Raised when input validation fails"""
    pass

# Error code mappings (from documentation)
ERROR_CODES = {
    "EC003": "An error occurred. Please try again later.",
    "EC900": "'exchange' cannot be empty or null.",
    "EC902": "'tradingSymbol' cannot be empty or null.",
    "EC903": "'quantity' cannot be empty or null.",
    "EC904": "'quantity' should be a positive number.",
    "EC912": "Failed to place the order.",
    "EC945": "'brokerOrderId' cannot be empty or null.",
    "EC087": "Session Expired",
    "EC088": "Single order slicing limit exceeded",
    # Add more as needed
}

def get_error_message(error_code: str) -> str:
    """Get human-readable error message for error code"""
    return ERROR_CODES.get(error_code, "Unknown error")
