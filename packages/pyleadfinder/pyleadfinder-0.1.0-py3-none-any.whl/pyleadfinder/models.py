"""Data models for PyLeadFinder."""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class OutputMode(Enum):
    """Output modes for leadfinder."""
    KML = "kml"  # Output KML file only
    CSV = "csv"  # Output CSV file only
    API = "api"  # Return data only (no file output)


@dataclass
class Company:
    """Represents a company/lead with all enriched data."""

    # Core identification
    name: str
    place_id: str

    # Location data
    address: str
    state: str
    zip_code: str
    latitude: float = 0.0
    longitude: float = 0.0

    # Contact information
    phone: str = ""
    website: str = ""
    email: str = ""


    def __post_init__(self):
        """Validate and normalize data."""
        if self.email:
            # Ensure emails are comma-separated and unique
            emails = [e.strip() for e in self.email.split(',')]
            self.email = ', '.join(sorted(set(emails)))

    def has_contact_info(self, min_fields: int = 1) -> bool:
        """Check if company has sufficient contact information."""
        contact_fields = [self.phone, self.website, self.email]
        return sum(bool(field) for field in contact_fields) >= min_fields

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        emails = []
        if self.email:
            emails = [e.strip() for e in self.email.split(',')]

        return {
            'name': self.name,
            'place_id': self.place_id,
            'address': self.address,
            'state': self.state,
            'zip_code': self.zip_code,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'phone': self.phone,
            'website': self.website,
            'emails': emails 
        }


@dataclass
class SessionConfig:
    """Configuration for a LeadFinderSession."""

    places_api_key: str
    queries: list[str]
    map_name: str
    locations: Optional[list] = None  # List of ZipCode objects with lat/lng
    search_radius: int = 30
    radius_unit: str = "miles"
    num_workers: int = 10
    max_google_rpm: int = 1000
    excluded_keywords: list[str] = field(default_factory=lambda: [])
    min_contact_fields: int = 1
    output_mode: OutputMode = OutputMode.API
    timeout: Optional[int] = None  # Total operation timeout in seconds (None = no timeout)
    scrape_emails: bool = False  # Whether to scrape websites for email addresses

    def __post_init__(self):
        if not self.places_api_key:
            raise ValueError("places_api_key required")
        if not self.queries:
            raise ValueError("queries required")
        if not self.map_name:
            raise ValueError("map_name required")
        if self.radius_unit not in ["miles", "km", "meters", "yards"]:
            raise ValueError("radius_unit must be miles, km, meters, or yards")

    @property
    def search_radius_miles(self) -> float:
        """Convert search radius to miles."""
        conversions = {
            "miles": 1.0,
            "km": 0.621371,
            "meters": 0.000621371,
            "yards": 0.000568182
        }
        return self.search_radius * conversions[self.radius_unit]
