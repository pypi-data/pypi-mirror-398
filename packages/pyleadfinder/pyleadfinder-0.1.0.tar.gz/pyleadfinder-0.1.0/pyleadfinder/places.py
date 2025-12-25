"""Google Places API integration."""

import requests
from typing import List, Optional
from .models import Company
from .rate_limiter import RateLimiter
from .errors import (
    PlacesAPIError,
    InvalidAPIKeyError,
    QuotaExceededError,
    RateLimitError,
    NetworkError
)


class PlacesClient:

    def __init__(self, api_key: str, rate_limiter: RateLimiter, search_radius_miles: int = 30, timeout: Optional[int] = None):
        self.api_key = api_key
        self.rate_limiter = rate_limiter
        self.search_radius_meters = int(search_radius_miles * 1609.34)  # Convert miles to meters
        self.timeout = timeout if timeout else 30  # Default to 30 if None

    def search_places(
        self,
        query: str,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None
    ) -> List[Company]:
        """
        Search for places using Google Places (New) Text Search API.

        Args:
            query: Search query (e.g., "liquor stores")
            latitude: Latitude for location-based search
            longitude: Longitude for location-based search

        Returns:
            List of Company objects with all information from a single API call
        """
        all_companies = []
        next_page_token = None

        while True:
            self.rate_limiter.wait_if_needed()

            url = "https://places.googleapis.com/v1/places:searchText"

            # Build request body
            body = {
                "textQuery": query,
                "maxResultCount": 20  # Maximum allowed per request
            }

            # Add location bias if coordinates provided
            if latitude is not None and longitude is not None:
                body["locationBias"] = {
                    "circle": {
                        "center": {
                            "latitude": latitude,
                            "longitude": longitude
                        },
                        "radius": self.search_radius_meters
                    }
                }

            # Add page token if this is a subsequent page
            if next_page_token:
                body["pageToken"] = next_page_token

            headers = {
                'Content-Type': 'application/json',
                'X-Goog-Api-Key': self.api_key,
                'X-Goog-FieldMask': 'places.id,places.displayName,places.formattedAddress,places.location,places.nationalPhoneNumber,places.websiteUri,places.addressComponents,nextPageToken'
            }

            try:
                response = requests.post(url, json=body, headers=headers, timeout=self.timeout)

                # Handle specific HTTP status codes
                if response.status_code == 401 or response.status_code == 403:
                    raise InvalidAPIKeyError(
                        f"Invalid or unauthorized API key (status {response.status_code})",
                        status_code=response.status_code
                    )
                elif response.status_code == 429:
                    raise RateLimitError(
                        "Rate limit exceeded. Please wait before making more requests.",
                        status_code=response.status_code
                    )
                elif response.status_code == 400:
                    error_data = response.json() if response.content else {}
                    error_message = error_data.get('error', {}).get('message', 'Bad request')

                    # Check if it's a quota error
                    if 'quota' in error_message.lower() or 'RESOURCE_EXHAUSTED' in str(error_data):
                        raise QuotaExceededError(
                            f"API quota exceeded: {error_message}",
                            status_code=response.status_code,
                            response_data=error_data
                        )
                    else:
                        raise PlacesAPIError(
                            f"Bad request: {error_message}",
                            status_code=response.status_code,
                            response_data=error_data
                        )

                response.raise_for_status()
                data = response.json()

                # Process results from this page
                for place in data.get('places', []):
                    place_id = place.get('id')
                    if not place_id:
                        continue

                    # Extract location data
                    location = place.get('location', {})

                    # Extract state and ZIP from address components
                    state = ''
                    zip_code = ''
                    for component in place.get('addressComponents', []):
                        types = component.get('types', [])
                        if 'administrative_area_level_1' in types:
                            state = component.get('shortText', '')
                        elif 'postal_code' in types:
                            zip_code = component.get('shortText', '')

                    # Get display name
                    display_name = place.get('displayName', {})
                    name = display_name.get('text', '') if isinstance(display_name, dict) else str(display_name)

                    company = Company(
                        name=name,
                        place_id=place_id,
                        address=place.get('formattedAddress', ''),
                        state=state,
                        zip_code=zip_code,
                        latitude=location.get('latitude', 0.0),
                        longitude=location.get('longitude', 0.0),
                        phone=place.get('nationalPhoneNumber', ''),
                        website=place.get('websiteUri', '')
                    )

                    # Basic validation
                    if self._is_valid_company(company):
                        all_companies.append(company)

                # Check for next page
                next_page_token = data.get('nextPageToken')

                # If no more pages, break
                if not next_page_token:
                    break

            except (InvalidAPIKeyError, QuotaExceededError, RateLimitError, PlacesAPIError):
                # Re-raise API errors so they can be handled at a higher level
                raise
            except requests.exceptions.Timeout:
                raise NetworkError(f"Request timed out after {self.timeout} seconds")
            except requests.exceptions.ConnectionError as e:
                raise NetworkError(f"Network connection error: {e}")
            except requests.exceptions.RequestException as e:
                location_str = f"({latitude}, {longitude})" if latitude and longitude else "unknown location"
                raise PlacesAPIError(
                    f'Search failed for "{query}" near {location_str}: {e}',
                    status_code=getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
                )
            except Exception as e:
                location_str = f"({latitude}, {longitude})" if latitude and longitude else "unknown location"
                print(f'  [ERROR] Unexpected error for "{query}" near {location_str}: {e}')
                break

        return all_companies

    def _is_valid_company(self, company: Company) -> bool:
        """Validate company data."""
        # Must have state and ZIP
        if not company.state or not company.zip_code:
            return False

        # Validate state format
        if len(company.state) != 2 or not company.state.isupper():
            return False

        # Validate ZIP format
        if not (company.zip_code.isdigit() and len(company.zip_code) == 5):
            return False

        # Must have valid coordinates
        if company.latitude == 0.0 and company.longitude == 0.0:
            return False

        return True
