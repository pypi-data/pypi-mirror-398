"""Custom exception hierarchy for planecompose.

All planecompose exceptions inherit from PlaneComposeError for easy catching.
"""


class PlaneComposeError(Exception):
    """Base exception for all planecompose errors."""
    
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class APIError(PlaneComposeError):
    """Raised when API calls fail.
    
    Attributes:
        status_code: HTTP status code
        retry_after: Seconds to wait before retrying (for 429 errors)
        endpoint: API endpoint that failed
    """
    
    def __init__(
        self,
        message: str,
        status_code: int,
        endpoint: str | None = None,
        retry_after: int | None = None,
        details: dict | None = None,
    ):
        super().__init__(message, details)
        self.status_code = status_code
        self.endpoint = endpoint
        self.retry_after = retry_after
    
    def is_client_error(self) -> bool:
        """Check if error is 4xx (client error)."""
        return 400 <= self.status_code < 500
    
    def is_server_error(self) -> bool:
        """Check if error is 5xx (server error)."""
        return 500 <= self.status_code < 600
    
    def is_rate_limit_error(self) -> bool:
        """Check if error is 429 (rate limit)."""
        return self.status_code == 429


class RateLimitError(APIError):
    """Raised when API rate limit is exceeded (HTTP 429).
    
    Attributes:
        retry_after: Seconds to wait before retrying
    """
    
    def __init__(self, retry_after: int | None = None, details: dict | None = None):
        message = "Rate limit exceeded"
        if retry_after:
            message += f". Retry after {retry_after} seconds"
        
        super().__init__(
            message=message,
            status_code=429,
            retry_after=retry_after,
            details=details,
        )


class AuthenticationError(APIError):
    """Raised when authentication fails (HTTP 401)."""
    
    def __init__(self, details: dict | None = None):
        super().__init__(
            message="Authentication failed. Check your API key.",
            status_code=401,
            details=details,
        )


class PermissionError(APIError):
    """Raised when user lacks permission (HTTP 403)."""
    
    def __init__(self, resource: str | None = None, details: dict | None = None):
        message = "Permission denied"
        if resource:
            message += f" for {resource}"
        
        super().__init__(
            message=message,
            status_code=403,
            details=details,
        )


class NotFoundError(APIError):
    """Raised when resource is not found (HTTP 404)."""
    
    def __init__(self, resource: str, details: dict | None = None):
        super().__init__(
            message=f"{resource} not found",
            status_code=404,
            details=details,
        )


class ConfigError(PlaneComposeError):
    """Raised when configuration is invalid or missing.
    
    Examples:
        - Missing plane.yaml
        - Invalid YAML syntax
        - Required fields missing
    """
    pass


class ValidationError(PlaneComposeError):
    """Raised when input validation fails.
    
    Examples:
        - Invalid work item data
        - Schema validation errors
        - Type mismatches
    """
    
    def __init__(self, message: str, field: str | None = None, details: dict | None = None):
        super().__init__(message, details)
        self.field = field


class StateError(PlaneComposeError):
    """Raised when state operations fail.
    
    Examples:
        - Corrupted state.json
        - State version mismatch
        - Sync conflicts
    """
    pass


class NetworkError(PlaneComposeError):
    """Raised when network operations fail.
    
    Examples:
        - Connection timeout
        - DNS resolution failed
        - Network unreachable
    """
    
    def __init__(self, message: str, original_error: Exception | None = None, details: dict | None = None):
        super().__init__(message, details)
        self.original_error = original_error


class ParserError(PlaneComposeError):
    """Raised when YAML parsing fails.
    
    Examples:
        - Invalid YAML syntax
        - Unexpected data structure
        - Missing required fields
    """
    
    def __init__(self, message: str, file_path: str | None = None, line: int | None = None, details: dict | None = None):
        super().__init__(message, details)
        self.file_path = file_path
        self.line = line

