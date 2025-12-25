
import pytest
from unittest.mock import MagicMock, patch
from pyleadfinder.session import leadfinder, LeadFinderSession
from pyleadfinder.models import Company, SessionConfig, OutputMode

@pytest.fixture
def mock_places_client():
    with patch('pyleadfinder.session.PlacesClient') as mock:
        client = mock.return_value
        client.search_places.return_value = [
            Company(name="Test Co", place_id="1", address="123 St", state="OR", zip_code="97204", email="test@example.com")
        ]
        yield client

@pytest.fixture
def mock_zip_optimizer():
    # Patch where it is defined, so the import in session.py gets the mock
    with patch('pyleadfinder.zip_optimizer.ZipCodeOptimizer') as mock:
        optimizer_instance = mock.return_value
        # Return dummy locations
        optimizer_instance.optimize_coverage.return_value = [MagicMock(latitude=45.5, longitude=-122.6)]
        yield mock

@pytest.fixture
def mock_maps_client():
    with patch('pyleadfinder.session.MapsClient') as mock:
        client = mock.return_value
        client.create_custom_map.return_value = {'kml': '<xml>'}
        yield client

def test_leadfinder_api_mode_defaults(mock_places_client, mock_zip_optimizer, mock_maps_client):
    """Test leadfinder with default API mode."""
    results = leadfinder(
        places_api_key="key",
        queries=["test"],
        bounds=(0, 1, 0, 1)
    )
    
    # Check returns
    assert results['output_mode'] == 'api'
    assert len(results['companies']) == 1
    assert results['companies'][0]['name'] == "Test Co"
    
    # Check interactions
    # mock_zip_optimizer is the class mock, return_value is the instance
    mock_zip_optimizer.return_value.optimize_coverage.assert_called_once()
    mock_places_client.search_places.assert_called()

def test_leadfinder_csv_mode_radius_unit(mock_places_client, mock_zip_optimizer, mock_maps_client):
    """Test leadfinder in CSV mode with KM radius."""
    with patch('pyleadfinder.session._save_csv') as mock_save:
        leadfinder(
            places_api_key="key",
            queries=["test"],
            bounds=(0, 1, 0, 1),
            output_mode="csv",
            radius=10,
            radius_unit="km"
        )
        
        # Verify ZipOptimizer initialized with converted miles
        # Check assertions on the CLASS mock (mock_zip_optimizer)
        # call_args returns (args, kwargs)
        _, kwargs = mock_zip_optimizer.call_args
        
        # 10 km ~= 6.2137 miles
        assert abs(kwargs['search_radius_miles'] - 6.2137) < 0.001
        
        mock_save.assert_called_once()

def test_leadfinder_kml_mode(mock_places_client, mock_zip_optimizer, mock_maps_client):
    """Test leadfinder in KML mode."""
    with patch('builtins.open', new_callable=MagicMock) as mock_open:
        results = leadfinder(
            places_api_key="key",
            queries=["test"],
            bounds=(0, 1, 0, 1),
            output_mode="kml",
            output_name="test_map"
        )
        
        assert results['output_mode'] == 'kml'
        mock_open.assert_called_with('test_map.kml', 'w', encoding='utf-8')

def test_session_threading_logic(mock_places_client, mock_zip_optimizer, mock_maps_client):
    """Test that session creates correct number of tasks."""
    # Setup multiple locations
    mock_zip_optimizer.return_value.optimize_coverage.return_value = [
        MagicMock(latitude=1, longitude=1),
        MagicMock(latitude=2, longitude=2)
    ]
    
    leadfinder(
        places_api_key="key",
        queries=["q1", "q2"], # 2 queries
        bounds=(0, 1, 0, 1),
        num_workers=2
    )
    
    # 2 locations * 2 queries = 4 searches
    assert mock_places_client.search_places.call_count == 4
