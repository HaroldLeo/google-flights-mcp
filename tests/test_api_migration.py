"""
Tests to verify successful migration from fast-flights v3.0rc0 to v2.2 API.

These tests ensure:
1. All functions use FlightData (not FlightQuery)
2. All functions use get_flights() directly (not create_query())
3. All functions use fetch_mode="fallback" for Playwright support
4. The migration is complete and correct
"""

import pytest
from unittest.mock import patch, MagicMock, call
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestAPIImports:
    """Test that we're importing the correct v2.2 API components."""

    def test_imports_flight_data_not_flight_query(self):
        """Verify we import FlightData, not FlightQuery."""
        from mcp_server_google_flights import server

        # Check that FlightData is available
        assert hasattr(server, 'FlightData')

        # Check that FlightQuery is NOT imported
        assert not hasattr(server, 'FlightQuery')

    def test_imports_get_flights(self):
        """Verify we import get_flights."""
        from mcp_server_google_flights import server

        assert hasattr(server, 'get_flights')

    def test_does_not_import_create_query(self):
        """Verify we do NOT import create_query (v3.0rc0 API)."""
        from mcp_server_google_flights import server

        # Should not have create_query
        assert not hasattr(server, 'create_query')


class TestFlightDataUsage:
    """Test that functions create FlightData objects correctly."""

    @patch('mcp_server_google_flights.server.get_flights')
    @pytest.mark.asyncio
    async def test_one_way_uses_flight_data(self, mock_get_flights):
        """Verify search_one_way_flights uses FlightData."""
        from mcp_server_google_flights.server import search_one_way_flights, FlightData

        mock_get_flights.return_value = []

        await search_one_way_flights(
            origin="SFO",
            destination="LAX",
            date="2025-12-10"
        )

        # Verify get_flights was called
        assert mock_get_flights.called

        # Get the call arguments
        call_kwargs = mock_get_flights.call_args[1]

        # Should have flight_data parameter (v2.2)
        assert 'flight_data' in call_kwargs

        # flight_data should be a list of FlightData objects
        flight_data = call_kwargs['flight_data']
        assert isinstance(flight_data, list)
        assert len(flight_data) == 1
        assert isinstance(flight_data[0], FlightData)

    @patch('mcp_server_google_flights.server.get_flights')
    @pytest.mark.asyncio
    async def test_round_trip_uses_flight_data(self, mock_get_flights):
        """Verify search_round_trip_flights uses FlightData."""
        from mcp_server_google_flights.server import search_round_trip_flights, FlightData

        mock_get_flights.return_value = []

        await search_round_trip_flights(
            origin="SFO",
            destination="LAX",
            departure_date="2025-12-10",
            return_date="2025-12-15"
        )

        assert mock_get_flights.called
        call_kwargs = mock_get_flights.call_args[1]

        # Should have flight_data with 2 legs
        assert 'flight_data' in call_kwargs
        flight_data = call_kwargs['flight_data']
        assert isinstance(flight_data, list)
        assert len(flight_data) == 2
        assert all(isinstance(fd, FlightData) for fd in flight_data)

    @patch('mcp_server_google_flights.server.get_flights')
    @pytest.mark.asyncio
    async def test_direct_flights_uses_flight_data(self, mock_get_flights):
        """Verify search_direct_flights uses FlightData (this was the broken function!)."""
        from mcp_server_google_flights.server import search_direct_flights, FlightData

        mock_get_flights.return_value = []

        # Test round-trip direct
        await search_direct_flights(
            origin="SFO",
            destination="LAX",
            date="2025-12-10",
            is_round_trip=True,
            return_date="2025-12-15"
        )

        assert mock_get_flights.called
        call_kwargs = mock_get_flights.call_args[1]

        # Should use flight_data (v2.2) not create artificial combinations
        assert 'flight_data' in call_kwargs
        flight_data = call_kwargs['flight_data']
        assert isinstance(flight_data, list)
        assert len(flight_data) == 2  # Round-trip has 2 legs
        assert all(isinstance(fd, FlightData) for fd in flight_data)

        # Should set max_stops=0 for direct flights
        assert call_kwargs.get('max_stops') == 0


class TestFetchModeFallback:
    """Test that all functions use fetch_mode='fallback' for Playwright support."""

    @patch('mcp_server_google_flights.server.get_flights')
    @pytest.mark.asyncio
    async def test_one_way_uses_fallback(self, mock_get_flights):
        """Verify search_one_way_flights uses fetch_mode='fallback'."""
        from mcp_server_google_flights.server import search_one_way_flights

        mock_get_flights.return_value = []

        await search_one_way_flights(
            origin="SFO",
            destination="LAX",
            date="2025-12-10"
        )

        call_kwargs = mock_get_flights.call_args[1]
        assert call_kwargs.get('fetch_mode') == 'fallback'

    @patch('mcp_server_google_flights.server.get_flights')
    @pytest.mark.asyncio
    async def test_round_trip_uses_fallback(self, mock_get_flights):
        """Verify search_round_trip_flights uses fetch_mode='fallback'."""
        from mcp_server_google_flights.server import search_round_trip_flights

        mock_get_flights.return_value = []

        await search_round_trip_flights(
            origin="SFO",
            destination="LAX",
            departure_date="2025-12-10",
            return_date="2025-12-15"
        )

        call_kwargs = mock_get_flights.call_args[1]
        assert call_kwargs.get('fetch_mode') == 'fallback'

    @patch('mcp_server_google_flights.server.get_flights')
    @pytest.mark.asyncio
    async def test_direct_flights_uses_fallback(self, mock_get_flights):
        """Verify search_direct_flights uses fetch_mode='fallback'."""
        from mcp_server_google_flights.server import search_direct_flights

        mock_get_flights.return_value = []

        await search_direct_flights(
            origin="SFO",
            destination="LAX",
            date="2025-12-10"
        )

        call_kwargs = mock_get_flights.call_args[1]
        assert call_kwargs.get('fetch_mode') == 'fallback'

    @patch('mcp_server_google_flights.server.get_flights')
    @pytest.mark.asyncio
    async def test_multi_city_uses_fallback(self, mock_get_flights):
        """Verify get_multi_city_flights uses fetch_mode='fallback'."""
        from mcp_server_google_flights.server import get_multi_city_flights

        mock_get_flights.return_value = []

        await get_multi_city_flights(
            flight_segments='[{"from": "SFO", "to": "LAX", "date": "2025-12-10"}, {"from": "LAX", "to": "JFK", "date": "2025-12-15"}]'
        )

        call_kwargs = mock_get_flights.call_args[1]
        assert call_kwargs.get('fetch_mode') == 'fallback'


class TestCorrectTripTypes:
    """Test that functions use correct trip types."""

    @patch('mcp_server_google_flights.server.get_flights')
    @pytest.mark.asyncio
    async def test_one_way_trip_type(self, mock_get_flights):
        """Verify one-way uses trip='one-way'."""
        from mcp_server_google_flights.server import search_one_way_flights

        mock_get_flights.return_value = []

        await search_one_way_flights(
            origin="SFO",
            destination="LAX",
            date="2025-12-10"
        )

        call_kwargs = mock_get_flights.call_args[1]
        assert call_kwargs.get('trip') == 'one-way'

    @patch('mcp_server_google_flights.server.get_flights')
    @pytest.mark.asyncio
    async def test_round_trip_trip_type(self, mock_get_flights):
        """Verify round-trip uses trip='round-trip'."""
        from mcp_server_google_flights.server import search_round_trip_flights

        mock_get_flights.return_value = []

        await search_round_trip_flights(
            origin="SFO",
            destination="LAX",
            departure_date="2025-12-10",
            return_date="2025-12-15"
        )

        call_kwargs = mock_get_flights.call_args[1]
        assert call_kwargs.get('trip') == 'round-trip'

    @patch('mcp_server_google_flights.server.get_flights')
    @pytest.mark.asyncio
    async def test_multi_city_trip_type(self, mock_get_flights):
        """Verify multi-city uses trip='multi-city'."""
        from mcp_server_google_flights.server import get_multi_city_flights

        mock_get_flights.return_value = []

        await get_multi_city_flights(
            flight_segments='[{"from": "SFO", "to": "LAX", "date": "2025-12-10"}, {"from": "LAX", "to": "JFK", "date": "2025-12-15"}]'
        )

        call_kwargs = mock_get_flights.call_args[1]
        assert call_kwargs.get('trip') == 'multi-city'


class TestDirectFlightsFix:
    """Test that search_direct_flights properly fixed the bug."""

    @patch('mcp_server_google_flights.server.get_flights')
    @pytest.mark.asyncio
    async def test_direct_round_trip_uses_max_stops_zero(self, mock_get_flights):
        """Verify direct round-trip uses max_stops=0 instead of artificial combinations."""
        from mcp_server_google_flights.server import search_direct_flights

        mock_get_flights.return_value = []

        await search_direct_flights(
            origin="SFO",
            destination="LAX",
            date="2025-12-10",
            is_round_trip=True,
            return_date="2025-12-15"
        )

        call_kwargs = mock_get_flights.call_args[1]

        # Should call with round-trip and max_stops=0
        assert call_kwargs.get('trip') == 'round-trip'
        assert call_kwargs.get('max_stops') == 0

        # Should NOT call get_flights twice (no artificial combinations)
        assert mock_get_flights.call_count == 1

    @patch('mcp_server_google_flights.server.get_flights')
    @pytest.mark.asyncio
    async def test_direct_one_way_uses_max_stops_zero(self, mock_get_flights):
        """Verify direct one-way uses max_stops=0."""
        from mcp_server_google_flights.server import search_direct_flights

        mock_get_flights.return_value = []

        await search_direct_flights(
            origin="SFO",
            destination="LAX",
            date="2025-12-10"
        )

        call_kwargs = mock_get_flights.call_args[1]

        assert call_kwargs.get('trip') == 'one-way'
        assert call_kwargs.get('max_stops') == 0


class TestNoCreateQuery:
    """Verify create_query() is never used (v3.0rc0 API)."""

    def test_create_query_not_in_module(self):
        """Verify create_query is not available in the module."""
        from mcp_server_google_flights import server

        # Should not have create_query function
        assert not hasattr(server, 'create_query')

    def test_no_create_query_in_source(self):
        """Verify create_query() is not called anywhere in source code."""
        import os

        server_path = os.path.join(
            os.path.dirname(__file__),
            '..',
            'src',
            'mcp_server_google_flights',
            'server.py'
        )

        with open(server_path, 'r') as f:
            content = f.read()

        # Should not have any create_query() calls
        assert 'create_query(' not in content
        assert 'create_query ' not in content

    def test_no_flight_query_in_source(self):
        """Verify FlightQuery is not used anywhere in source code."""
        import os

        server_path = os.path.join(
            os.path.dirname(__file__),
            '..',
            'src',
            'mcp_server_google_flights',
            'server.py'
        )

        with open(server_path, 'r') as f:
            content = f.read()

        # Should not have FlightQuery (v3.0rc0)
        assert 'FlightQuery(' not in content


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
