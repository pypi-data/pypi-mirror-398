"""Google Maps API integration for custom map creation."""


from typing import List
from .models import Company


class MapsClient:
    """Client for Google Maps API operations."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://www.googleapis.com/mapsengine/v1"

    def create_custom_map(
        self,
        map_name: str,
        companies: List[Company],
        description: str = ""
    ) -> dict:
        """
        Create a custom Google My Map with company data.

        Args:
            map_name: Name for the custom map
            companies: List of Company objects to add as markers
            description: Optional map description

        Returns:
            Dictionary with map data and export formats
        """
        # Filter companies with valid coordinates
        valid_companies = [
            c for c in companies
            if c.latitude != 0.0 or c.longitude != 0.0
        ]

        if not valid_companies:
            raise ValueError("No companies with valid coordinates to map")

        # Generate KML (for Google My Maps import)
        kml = self._generate_kml(map_name, valid_companies, description)

        return {
            'map_name': map_name,
            'total_markers': len(valid_companies),
            'kml': kml,
            'import_instructions': (
                "To import this map to Google My Maps:\n"
                "1. Go to https://www.google.com/mymaps\n"
                "2. Click 'Create a new map'\n"
                "3. Click 'Import' in the left panel\n"
                "4. Upload the saved KML file\n"
                "5. Select latitude/longitude as location columns\n"
                "6. Choose a column for marker names (e.g., 'name')"
            )
        }

    def _generate_kml(
        self,
        map_name: str,
        companies: List[Company],
        description: str
    ) -> str:
        """Generate KML format for Google My Maps import."""
        kml_header = f'''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>{self._escape_xml(map_name)}</name>
    <description>{self._escape_xml(description)}</description>
'''

        kml_footer = '''  </Document>
</kml>'''

        placemarks = []
        for company in companies:
            # Build description with all available data
            desc_parts = []
            if company.address:
                desc_parts.append(f"Address: {company.address}")
            if company.phone:
                desc_parts.append(f"Phone: {company.phone}")
            if company.website:
                desc_parts.append(f"Website: {company.website}")
            if company.email:
                desc_parts.append(f"Email: {company.email}")

            description = "\n".join(desc_parts)

            placemark = f'''    <Placemark>
      <name>{self._escape_xml(company.name)}</name>
      <description>{self._escape_xml(description)}</description>
      <Point>
        <coordinates>{company.longitude},{company.latitude},0</coordinates>
      </Point>
      <ExtendedData>
        <Data name="place_id">
          <value>{self._escape_xml(company.place_id)}</value>
        </Data>
        <Data name="state">
          <value>{self._escape_xml(company.state)}</value>
        </Data>
        <Data name="zip">
          <value>{self._escape_xml(company.zip_code)}</value>
        </Data>
      </ExtendedData>
    </Placemark>
'''
            placemarks.append(placemark)

        return kml_header + ''.join(placemarks) + kml_footer

    def _escape_xml(self, text: str) -> str:
        """Escape XML special characters."""
        if not text:
            return ''
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&apos;'))

    def save_kml(self, kml_content: str, filename: str):
        """Save KML content to file."""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(kml_content)
