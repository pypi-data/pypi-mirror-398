
import pytest
from pyleadfinder.models import Company, SessionConfig, OutputMode

class TestCompany:
    def test_company_init(self):
        c = Company(
            name="Test Corp",
            place_id="123",
            address="123 Main St",
            state="OR",
            zip_code="97204"
        )
        assert c.name == "Test Corp"
        assert c.latitude == 0.0

    def test_post_init_email_normalization(self):
        c = Company(
            name="Test",
            place_id="123",
            address="Addr",
            state="OR",
            zip_code="12345",
            email="b@example.com, a@example.com, b@example.com"
        )
        # Should be sorted and unique
        assert c.email == "a@example.com, b@example.com"

    def test_has_contact_info(self):
        c = Company(name="T", place_id="1", address="A", state="S", zip_code="Z")
        assert not c.has_contact_info()
        
        c.phone = "555-1234"
        assert c.has_contact_info()
        
        c = Company(name="T", place_id="1", address="A", state="S", zip_code="Z", website="http://test.com")
        assert c.has_contact_info()

    def test_to_dict(self):
        c = Company(
            name="Test",
            place_id="123",
            address="Addr",
            state="OR",
            zip_code="12345",
            email="a@example.com"
        )
        d = c.to_dict()
        assert d['name'] == "Test"
        assert d['emails'] == ["a@example.com"]


class TestSessionConfig:
    def test_defaults(self):
        config = SessionConfig(
            places_api_key="key",
            queries=["q"],
            map_name="map"
        )
        assert config.search_radius == 30
        assert config.radius_unit == "miles"
        assert config.output_mode == OutputMode.API
        assert config.search_radius_miles == 30.0

    def test_radius_conversion(self):
        # Miles
        c1 = SessionConfig(places_api_key="k", queries=["q"], map_name="m", search_radius=10, radius_unit="miles")
        assert c1.search_radius_miles == 10.0

        # KM
        c2 = SessionConfig(places_api_key="k", queries=["q"], map_name="m", search_radius=10, radius_unit="km")
        assert abs(c2.search_radius_miles - 6.21371) < 0.001

        # Meters
        c3 = SessionConfig(places_api_key="k", queries=["q"], map_name="m", search_radius=1000, radius_unit="meters")
        assert abs(c3.search_radius_miles - 0.621371) < 0.001

    def test_validation(self):
        with pytest.raises(ValueError, match="radius_unit must be"):
            SessionConfig(places_api_key="k", queries=["q"], map_name="m", radius_unit="invalid")
