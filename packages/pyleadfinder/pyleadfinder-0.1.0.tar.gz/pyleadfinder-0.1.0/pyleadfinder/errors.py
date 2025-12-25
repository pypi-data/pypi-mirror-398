
class PyLeadFinderError(Exception):
    """Base exception for all PyLeadFinder errors."""
    pass


class OperationTimeoutError(PyLeadFinderError):
    """Raised when the entire operation exceeds the timeout."""
    pass


class APIError(PyLeadFinderError):
    """Base exception for API-related errors."""
    pass


class PlacesAPIError(APIError):
    """Raised when Google Places API returns an error."""

    def __init__(self, message: str, status_code: int = None, response_data: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class InvalidAPIKeyError(PlacesAPIError):
    """Raised when the Google Places API key is invalid or unauthorized."""
    pass


class QuotaExceededError(PlacesAPIError):
    """Raised when Google Places API quota has been exceeded."""
    pass


class RateLimitError(PlacesAPIError):
    """Raised when rate limit is exceeded."""
    pass


class NetworkError(PyLeadFinderError):
    """Raised when network connectivity issues occur."""
    pass


class ValidationError(PyLeadFinderError):
    """Raised when input validation fails."""
    pass


class InvalidBoundsError(ValidationError):
    """Raised when geographic bounds are invalid."""
    pass


class InvalidOutputModeError(ValidationError):
    """Raised when an invalid output mode is specified."""
    pass


class ScraperError(PyLeadFinderError):
    """Raised when web scraping fails."""
    pass


class ZipCodeOptimizationError(PyLeadFinderError):
    """Raised when ZIP code optimization fails."""
    pass
