"""PyLeadFinder - Lead generation tool using Google Places API."""

__version__ = "0.1.0"

from .session import leadfinder
from .models import OutputMode
from .errors import (
    PyLeadFinderError,
    OperationTimeoutError,
    APIError,
    PlacesAPIError,
    InvalidAPIKeyError,
    QuotaExceededError,
    RateLimitError,
    NetworkError,
    ValidationError,
    InvalidBoundsError,
    InvalidOutputModeError,
    ScraperError,
    ZipCodeOptimizationError
)

__all__ = [
    "leadfinder",
    "OutputMode",
    # Errors
    "PyLeadFinderError",
    "OperationTimeoutError",
    "APIError",
    "PlacesAPIError",
    "InvalidAPIKeyError",
    "QuotaExceededError",
    "RateLimitError",
    "NetworkError",
    "ValidationError",
    "InvalidBoundsError",
    "InvalidOutputModeError",
    "ScraperError",
    "ZipCodeOptimizationError"
]
