"""Pytest configuration and fixtures for Google Flights MCP tests."""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta


class MockAirport:
    """Mock Airport object from fast-flights."""
    def __init__(self, code, name="Test Airport"):
        self.code = code
        self.name = name
        self.id = code


class MockFlight:
    """Mock Flight object returned by fast-flights v2.2."""
    def __init__(
        self,
        price=100,
        name="Test Airline",
        flight_times=None,
        stops=0,
        delay=None,
        duration=120,
        is_best=False,
        departure_airport="SFO",
        arrival_airport="LAX",
        co2_emissions=None,
        from_airport_code="SFO",
        to_airport_code="LAX",
        airline_logo="https://example.com/logo.png"
    ):
        self.price = price
        self.name = name
        self.flight_times = flight_times or ["10:00 AM", "12:00 PM"]
        self.stops = stops
        self.delay = delay
        self.duration = duration
        self.is_best = is_best
        self.departure_airport = departure_airport
        self.arrival_airport = arrival_airport
        self.co2_emissions = co2_emissions
        self.from_airport = MockAirport(from_airport_code)
        self.to_airport = MockAirport(to_airport_code)
        self.airline_logo = airline_logo
        self.airlines = [name]


@pytest.fixture
def mock_one_way_flights():
    """Mock response for one-way flight search."""
    return [
        MockFlight(price=150, name="United", stops=0, is_best=True),
        MockFlight(price=200, name="Delta", stops=1, is_best=False),
        MockFlight(price=175, name="American", stops=0, is_best=False),
    ]


@pytest.fixture
def mock_round_trip_flights():
    """Mock response for round-trip flight search."""
    return [
        MockFlight(
            price=300,
            name="United",
            stops=0,
            is_best=True,
            flight_times=["10:00 AM", "12:00 PM", "3:00 PM", "5:00 PM"]
        ),
        MockFlight(
            price=350,
            name="Delta",
            stops=1,
            is_best=False,
            flight_times=["11:00 AM", "2:00 PM", "4:00 PM", "7:00 PM"]
        ),
    ]


@pytest.fixture
def mock_multi_city_flights():
    """Mock response for multi-city flight search."""
    return [
        MockFlight(price=500, name="United", stops=0, is_best=True),
        MockFlight(price=550, name="Delta", stops=1, is_best=False),
    ]


@pytest.fixture
def mock_direct_flights():
    """Mock response for direct flights only."""
    return [
        MockFlight(price=250, name="United", stops=0, is_best=True),
        MockFlight(price=275, name="American", stops=0, is_best=False),
    ]


@pytest.fixture
def mock_get_flights():
    """Fixture to mock the get_flights function from fast-flights."""
    with patch('mcp_server_google_flights.server.get_flights') as mock:
        yield mock


@pytest.fixture
def sample_passengers():
    """Sample passenger data for tests."""
    return {
        "adults": 1,
        "children": 0,
        "infants_in_seat": 0,
        "infants_on_lap": 0
    }


@pytest.fixture
def future_date():
    """Return a date 30 days in the future."""
    return (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')


@pytest.fixture
def future_return_date():
    """Return a date 35 days in the future."""
    return (datetime.now() + timedelta(days=35)).strftime('%Y-%m-%d')


@pytest.fixture
def date_range():
    """Return a date range for testing."""
    start = datetime.now() + timedelta(days=30)
    end = datetime.now() + timedelta(days=37)
    return {
        "start": start.strftime('%Y-%m-%d'),
        "end": end.strftime('%Y-%m-%d')
    }
