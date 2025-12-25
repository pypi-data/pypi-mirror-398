class ConnectorError(Exception):
    """Base class for connector-related errors."""
    pass

class RateLimitExceededError(ConnectorError):
    """Raised when the API rate limit is exceeded."""
    def __init__(self, message="API rate limit has been exceeded."):
        super().__init__(message)

class AuthorizationError(ConnectorError):
    """Raised when there is an authorization error (e.g., invalid API key)."""
    def __init__(self, message="Authorization failed. Check your API credentials."):
        super().__init__(message)

class InvalidQueryError(ConnectorError):
    """Raised when the query is invalid."""
    def __init__(self, message="The query provided is invalid."):
        super().__init__(message)

class ConnectorUnavailableError(ConnectorError):
    """Raised when the connector's service is unavailable."""
    def __init__(self, message="The connector service is currently unavailable."):
        super().__init__(message)