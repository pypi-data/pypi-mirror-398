from typing import Optional, Dict, Any


class ArizonaAIError(Exception):
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response_data = response_data or {}

    def __str__(self) -> str:
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(message={self.message!r}, status_code={self.status_code})"


class AuthenticationError(ArizonaAIError):
    def __init__(
        self,
        message: str = "Authentication failed. Check your API key.",
        status_code: int = 401,
        response_data: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, status_code, response_data)


class RateLimitError(ArizonaAIError):
    def __init__(
        self,
        message: str = "Rate limit exceeded. Please wait before making more requests.",
        status_code: int = 429,
        response_data: Optional[Dict[str, Any]] = None,
        retry_after: Optional[float] = None
    ):
        super().__init__(message, status_code, response_data)
        self.retry_after = retry_after


class NotFoundError(ArizonaAIError):
    def __init__(
        self,
        message: str = "Resource not found.",
        status_code: int = 404,
        response_data: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, status_code, response_data)


class ValidationError(ArizonaAIError):
    def __init__(
        self,
        message: str = "Invalid request parameters.",
        status_code: int = 400,
        response_data: Optional[Dict[str, Any]] = None,
        field: Optional[str] = None
    ):
        super().__init__(message, status_code, response_data)
        self.field = field


class ServerError(ArizonaAIError):
    def __init__(
        self,
        message: str = "Internal server error.",
        status_code: int = 500,
        response_data: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, status_code, response_data)


class StreamError(ArizonaAIError):
    def __init__(
        self,
        message: str = "Error during streaming response.",
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, status_code, response_data)


class ConnectionError(ArizonaAIError):
    def __init__(
        self,
        message: str = "Failed to connect to ArizonaAI API.",
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, status_code, response_data)


class TimeoutError(ArizonaAIError):
    def __init__(
        self,
        message: str = "Request timed out.",
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, status_code, response_data)
