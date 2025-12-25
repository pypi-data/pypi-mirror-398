"""Main session management for PyLeadFinder."""

import threading
import time
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

from .models import Company, SessionConfig, OutputMode
from .places import PlacesClient
from .scraper import WebScraper
from .maps import MapsClient
from .rate_limiter import RateLimiter
from .errors import (
    OperationTimeoutError,
    InvalidBoundsError,
    InvalidOutputModeError
)


class LeadFinderSession:
    """Main session class for PyLeadFinder."""

    def __init__(self, config: SessionConfig):
        self.config = config
        self.google_limiter = RateLimiter(config.max_google_rpm)
        self.places_client = PlacesClient(
            config.places_api_key,
            self.google_limiter,
            config.search_radius_miles,
            config.timeout
        )
        self.maps_client = MapsClient(config.places_api_key)
        self.scraper = WebScraper(config.excluded_keywords)
        self.companies: List[Company] = []
        self.companies_by_place_id: Dict[str, Company] = {}
        self.lock = threading.Lock()
        self.silent = config.output_mode == OutputMode.API
        self.start_time: Optional[float] = None
        self.timed_out = False

    def _print(self, *args, **kwargs):
        """Print only if not in silent mode."""
        if not self.silent:
            print(*args, **kwargs)

    def _check_timeout(self):
        """Check if the operation has exceeded the timeout."""
        if self.start_time and self.config.timeout and self.config.timeout > 0:
            elapsed = time.time() - self.start_time
            if elapsed > self.config.timeout:
                self.timed_out = True
                raise OperationTimeoutError(f"Operation exceeded timeout of {self.config.timeout} seconds (elapsed: {elapsed:.1f}s)")

    def run(self) -> Dict:
        """Run the complete lead generation pipeline."""
        self.start_time = time.time()

        self._print(f"PyLeadFinder: {self.config.map_name}")
        self._print(f"Search radius: {self.config.search_radius} {self.config.radius_unit}")
        self._print()

        self._search_all_places()
        self._check_timeout()

        if self.config.scrape_emails:
            self._enrich_emails()
            self._check_timeout()

        self._print(f"\nComplete: {len(self.companies)} companies")
        self._print(f"  With emails: {sum(1 for c in self.companies if c.email)}")
        self._print(f"  With phone: {sum(1 for c in self.companies if c.phone)}")
        self._print(f"  With website: {sum(1 for c in self.companies if c.website)}")

        map_data = self.maps_client.create_custom_map(
            self.config.map_name,
            self.companies,
            f"{len(self.companies)} companies"
        )

        return {
            'companies': self.companies,
            'map_data': map_data,
            'stats': {
                'total_companies': len(self.companies),
                'with_email': sum(1 for c in self.companies if c.email),
                'with_phone': sum(1 for c in self.companies if c.phone),
                'with_website': sum(1 for c in self.companies if c.website),
            }
        }

    def _search_all_places(self):
        """Search Google Places for all queries and locations."""
        tasks = []

        if self.config.locations:
            for query in self.config.queries:
                for location in self.config.locations:
                    tasks.append((query, location.latitude, location.longitude))
        else:
            for query in self.config.queries:
                tasks.append((query, None, None))

        self._print(f"Searching {len(tasks)} locations...")

        with ThreadPoolExecutor(max_workers=self.config.num_workers) as executor:
            futures = {
                executor.submit(
                    self.places_client.search_places,
                    query,
                    latitude,
                    longitude
                ): (query, latitude, longitude)
                for query, latitude, longitude in tasks
            }

            with tqdm(total=len(tasks), desc="Progress", disable=self.silent) as pbar:
                for future in as_completed(futures):
                    self._check_timeout()

                    try:
                        companies = future.result()

                        with self.lock:
                            for company in companies:
                                if self._is_excluded(company):
                                    continue

                                if not company.has_contact_info(self.config.min_contact_fields):
                                    continue

                                if company.place_id not in self.companies_by_place_id:
                                    self.companies_by_place_id[company.place_id] = company
                                    self.companies.append(company)

                    except:
                        pass

                    pbar.update(1)

        self._print(f"Found {len(self.companies)} companies")

    def _enrich_emails(self):
        """Enrich companies with email addresses from websites."""
        companies_with_websites = [c for c in self.companies if c.website]

        if not companies_with_websites:
            return

        self._print(f"\nScraping {len(companies_with_websites)} websites...")

        with ThreadPoolExecutor(max_workers=self.config.num_workers) as executor:
            futures = {
                executor.submit(self.scraper.extract_emails_from_company, company): company
                for company in companies_with_websites
            }

            with tqdm(total=len(futures), desc="Progress", disable=self.silent) as pbar:
                for future in as_completed(futures):
                    self._check_timeout()

                    company = futures[future]
                    try:
                        emails = future.result()
                        if emails:
                            with self.lock:
                                if company.email:
                                    all_emails = set(company.email.split(', '))
                                    all_emails.update(emails.split(', '))
                                    company.email = ', '.join(sorted(all_emails))
                                else:
                                    company.email = emails
                    except:
                        pass

                    pbar.update(1)

    def _is_excluded(self, company: Company) -> bool:
        """Check if company should be excluded based on keywords."""
        # Check company name and website
        text_to_check = f"{company.name} {company.website}".lower()
        return any(keyword in text_to_check for keyword in self.config.excluded_keywords)


def leadfinder(
    places_api_key: str,
    queries: list[str],
    bounds: tuple[float, float, float, float],
    output_name: str = "leads",
    radius: int = 30,
    output_mode: str = "api",
    radius_unit: str = "miles",
    **kwargs
) -> Dict:
    """
    Find and enrich business leads using Google Places API.

    Args:
        places_api_key: Google Places API key
        queries: List of search queries (e.g., ["restaurants", "coffee shops"])
        bounds: Geographic bounds (min_lat, max_lat, min_lng, max_lng)
        output_name: Base name for output files (default: "leads")
        radius: Search radius (default: 30)
        output_mode: Output mode - "api", "csv", or "kml" (default: "api")
            - "api": Return JSON-serializable data only (no file output, no printing)
            - "csv": Output CSV file with all company data
            - "kml": Output KML file for Google My Maps import
        radius_unit: Unit for radius - "miles", "km", "meters", or "yards" (default: "miles")
        **kwargs: Additional SessionConfig options including:
            - num_workers: Number of worker threads (default: 10)
            - excluded_keywords: List of keywords to exclude (default: [])
            - timeout: Total operation timeout in seconds (default: None = no timeout)
                      The timeout applies to the entire operation, not individual requests
            - scrape_emails: Whether to scrape websites for emails (default: False)
                            When enabled, extracts email addresses from company websites

    Returns:
        Dictionary with companies, map_data (if applicable), and stats
        In API mode, all data is JSON-serializable

    Examples:
        # API mode (default)
        results = leadfinder(
            places_api_key="YOUR_KEY",
            queries=["restaurants"],
            bounds=(45.4, 45.6, -122.8, -122.5)
        )
        companies = results['companies']  # List of dicts

        # CSV output mode with kilometers
        leadfinder(
            places_api_key="YOUR_KEY",
            queries=["restaurants"],
            bounds=(45.4, 45.6, -122.8, -122.5),
            output_mode="csv",
            radius=10,
            radius_unit="km"
        )
    
        # KML output mode
        leadfinder(
            places_api_key="YOUR_KEY",
            queries=["restaurants"],
            bounds=(45.4, 45.6, -122.8, -122.5),
            output_mode="kml"
        )

    Raises:
        OperationTimeoutError: If the operation exceeds the specified timeout
        InvalidBoundsError: If the bounds parameter is invalid
        InvalidOutputModeError: If the output_mode is not 'kml', 'csv', or 'api'
        InvalidAPIKeyError: If the Google Places API key is invalid
        QuotaExceededError: If the API quota has been exceeded
        RateLimitError: If the API rate limit is exceeded
        NetworkError: If network connectivity issues occur
        PlacesAPIError: For other Google Places API errors
    """
    # Validate bounds
    if len(bounds) != 4:
        raise InvalidBoundsError("bounds must be (min_lat, max_lat, min_lng, max_lng)")

    # Validate and convert output_mode
    try:
        mode = OutputMode(output_mode.lower())
    except ValueError:
        raise InvalidOutputModeError(f"output_mode must be 'kml', 'csv', or 'api', got '{output_mode}'")

    min_lat, max_lat, min_lng, max_lng = bounds

    # Check if we're in silent mode (API mode)
    silent = mode == OutputMode.API

    # Create config first to handle unit conversions
    config = SessionConfig(
        places_api_key=places_api_key,
        queries=queries,
        map_name=output_name,
        locations=[],  # Will be populated after optimization
        search_radius=radius,
        radius_unit=radius_unit,
        output_mode=mode,
        **kwargs
    )

    # Optimize ZIP codes using converted radius
    from .zip_optimizer import ZipCodeOptimizer
    if not silent:
        print("Optimizing ZIP code coverage...")
    
    # Use search_radius_miles from config which handles the conversion
    optimizer = ZipCodeOptimizer(search_radius_miles=config.search_radius_miles)
    optimizer.load_zip_codes()
    locations = optimizer.optimize_coverage(min_lat, max_lat, min_lng, max_lng)
    
    # Update locations in config
    config.locations = locations
    
    if not silent:
        print(f"Optimized to {len(locations)} locations")

    # Run session
    session = LeadFinderSession(config)
    results = session.run()

    # Handle output based on mode
    output_files = []

    if mode == OutputMode.KML:
        # Save KML file
        kml_file = f"{output_name}.kml"
        with open(kml_file, 'w', encoding='utf-8') as f:
            f.write(results['map_data']['kml'])
        output_files.append(kml_file)
        if not silent:
            print(f"\nSaved {kml_file}")

    elif mode == OutputMode.CSV:
        # Save CSV file
        csv_file = f"{output_name}.csv"
        _save_csv(csv_file, results['companies'])
        output_files.append(csv_file)
        if not silent:
            print(f"\nSaved {csv_file}")

    elif mode == OutputMode.API:
        # No file output - convert to JSON-serializable format
        results['companies'] = [company.to_dict() for company in results['companies']]

    # Add output files to results
    results['output_files'] = output_files
    results['output_mode'] = mode.value

    return results


def _save_csv(filename: str, companies: List[Company]):
    """Save companies to CSV file."""
    import csv

    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'name', 'address', 'city', 'state', 'zip_code',
            'phone', 'website', 'email', 'latitude', 'longitude', 'place_id'
        ])
        writer.writeheader()

        for company in companies:
            # Extract city from address
            city = ''
            if company.address:
                parts = company.address.split(',')
                if len(parts) >= 2:
                    city = parts[-2].strip()

            writer.writerow({
                'name': company.name,
                'address': company.address,
                'city': city,
                'state': company.state,
                'zip_code': company.zip_code,
                'phone': company.phone,
                'website': company.website,
                'email': company.email,
                'latitude': company.latitude,
                'longitude': company.longitude,
                'place_id': company.place_id
            })
