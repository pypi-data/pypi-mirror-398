"""ZIP code optimization for efficient geographic coverage."""

import math
import requests
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class ZipCode:
    """Represents a US ZIP code with location data."""
    zip: str
    city: str
    state: str
    state_abbr: str
    county: str
    country_code: str
    latitude: float
    longitude: float


class ZipCodeOptimizer:
    """
    Optimizes ZIP code selection for geographic coverage.

    Uses geometric algorithms to minimize API calls while ensuring
    complete coverage of a search area.
    """

    # Earth's radius in miles
    EARTH_RADIUS_MILES = 3959.0

    def __init__(self, search_radius_miles: int = 30):
        """Initialize optimizer."""
        self.search_radius = search_radius_miles
        self.coverage_diameter = search_radius_miles * 2
        self.all_zips: List[ZipCode] = []

    def load_zip_codes(self, url: str = "https://gist.githubusercontent.com/Tucker-Eric/6a1a6b164726f21bb699623b06591389/raw/us_zips.csv") -> int:
        """
        Load US ZIP codes from remote source.

        Args:
            url: URL to ZIP code database CSV

        Returns:
            Number of ZIP codes loaded
        """
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            lines = response.text.strip().split('\n')
            # header = lines[0]  # zip,city,state,state_abbr,county,country_code,latitude,longitude

            self.all_zips = []
            for line in lines[1:]:
                parts = line.split(',')
                if len(parts) >= 8:
                    try:
                        zip_code = ZipCode(
                            zip=parts[0].strip(),
                            city=parts[1].strip(),
                            state=parts[2].strip(),
                            state_abbr=parts[3].strip(),
                            county=parts[4].strip(),
                            country_code=parts[5].strip(),
                            latitude=float(parts[6].strip()),
                            longitude=float(parts[7].strip())
                        )
                        self.all_zips.append(zip_code)
                    except (ValueError, IndexError):
                        continue

            return len(self.all_zips)

        except Exception:
            return 0

    def filter_by_bounds(
        self,
        min_lat: float,
        max_lat: float,
        min_lng: float,
        max_lng: float
    ) -> List[ZipCode]:
        """
        Filter ZIP codes within geographic bounds.

        Args:
            min_lat: Minimum latitude
            max_lat: Maximum latitude
            min_lng: Minimum longitude
            max_lng: Maximum longitude

        Returns:
            List of ZIP codes within bounds
        """
        return [
            z for z in self.all_zips
            if min_lat <= z.latitude <= max_lat
            and min_lng <= z.longitude <= max_lng
        ]

    def optimize_coverage(
        self,
        min_lat: float,
        max_lat: float,
        min_lng: float,
        max_lng: float
    ) -> List[ZipCode]:
        """
        Optimize ZIP code selection for complete coverage with minimum queries.

        Uses a hexagonal grid pattern for optimal coverage with minimal overlap.

        Args:
            min_lat: Minimum latitude of search area
            max_lat: Maximum latitude of search area
            min_lng: Minimum longitude of search area
            max_lng: Maximum longitude of search area

        Returns:
            List of optimized ZipCode objects with coordinates
        """
        candidate_zips = self.filter_by_bounds(min_lat, max_lat, min_lng, max_lng)

        if not candidate_zips:
            return []

        lat_spacing = self._miles_to_lat_degrees(self.coverage_diameter * 0.866)
        lng_spacing = self._miles_to_lng_degrees(
            self.coverage_diameter * 0.866,
            (min_lat + max_lat) / 2
        )

        # Create grid points
        grid_points = []
        lat = min_lat
        row = 0
        while lat <= max_lat:
            lng = min_lng
            # Offset every other row for hexagonal packing
            if row % 2 == 1:
                lng += lng_spacing / 2

            while lng <= max_lng:
                grid_points.append((lat, lng))
                lng += lng_spacing

            lat += lat_spacing
            row += 1

        selected_zips = []
        for grid_lat, grid_lng in grid_points:
            nearest_zip = self._find_nearest_zip(
                grid_lat,
                grid_lng,
                candidate_zips
            )
            if nearest_zip and nearest_zip not in selected_zips:
                selected_zips.append(nearest_zip)

        return selected_zips

    def _find_nearest_zip(
        self,
        lat: float,
        lng: float,
        candidates: List[ZipCode]
    ) -> Optional[ZipCode]:
        """Find the nearest ZIP code to a given point."""
        if not candidates:
            return None

        min_distance = float('inf')
        nearest = None

        for zip_code in candidates:
            distance = self._haversine_distance(
                lat, lng,
                zip_code.latitude, zip_code.longitude
            )
            if distance < min_distance:
                min_distance = distance
                nearest = zip_code

        return nearest

    def _haversine_distance(
        self,
        lat1: float, lng1: float,
        lat2: float, lng2: float
    ) -> float:
        """
        Calculate distance between two points using Haversine formula.

        Returns:
            Distance in miles
        """
        # Convert to radians
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        dlat = math.radians(lat2 - lat1)
        dlng = math.radians(lng2 - lng1)

        # Haversine formula
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(dlng / 2) ** 2)
        c = 2 * math.asin(math.sqrt(a))

        return self.EARTH_RADIUS_MILES * c

    def _miles_to_lat_degrees(self, miles: float) -> float:
        """Convert miles to degrees latitude (constant conversion)."""
        return miles / 69.0  # 1 degree latitude ≈ 69 miles

    def _miles_to_lng_degrees(self, miles: float, latitude: float) -> float:
        """Convert miles to degrees longitude (varies by latitude)."""
        # Longitude degrees vary by latitude
        # 1 degree longitude = 69 * cos(latitude) miles
        return miles / (69.0 * math.cos(math.radians(latitude)))