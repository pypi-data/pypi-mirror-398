from datetime import datetime


class APIClientError(Exception):
    """Base class for all Breezeway client errors."""
    pass

class AuthenticationError(APIClientError): pass

class MultipleCompaniesError(APIClientError): pass

class NoCompaniesError(APIClientError): pass

class NotFoundError(APIClientError): pass

class RateLimitExceeded(APIClientError):
    def __init__(self, response: dict | None = None):
        if not response or 'details' not in response or 'message' not in response['details'] or 'retry_after' not in response['details']:
            raise ValueError("Invalid response format for RateLimitExceeded")
        super().__init__(response['details']['message'])
        self.retry_after: datetime = datetime.fromisoformat(response['details']['retry_after'])

    @property
    def is_expired(self) -> bool:
        """Check if the rate limit is expired."""
        return datetime.now() > self.retry_after

class UnauthorizedError(APIClientError): pass