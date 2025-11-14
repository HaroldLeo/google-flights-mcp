# Test Suite for Google Flights MCP Server

This directory contains comprehensive tests for the Google Flights MCP Server.

## Test Files

### `conftest.py`
Contains pytest fixtures and mock objects for testing, including:
- Mock flight responses
- Mock airport objects
- Common test data (dates, passengers, etc.)

## Running Tests

### Run All Tests
```bash
pytest tests/
```

### Run with Coverage
```bash
pytest tests/ --cov=mcp_server_google_flights --cov-report=html
```

## Installing Test Dependencies

```bash
pip install -e ".[dev]"
```

Or install directly:
```bash
pip install pytest pytest-asyncio pytest-mock
```

## Implementation Details

The Google Flights MCP Server uses fast-flights v2.2 API, which provides:
- Real Google Flights search results
- Correct combined round-trip pricing
- Playwright fallback for improved reliability
- Support for one-way, round-trip, multi-city, and direct flight searches

## Continuous Integration

These tests should be run:
- Before committing changes
- In CI/CD pipelines
- After updating fast-flights dependency
- When modifying search functions

## Contributing

When adding new search functions:
1. Ensure they use `FlightData` from fast-flights v2.2
2. Use `fetch_mode="fallback"` for Playwright support
3. Call `get_flights()` directly with appropriate parameters
4. Add corresponding tests to verify functionality
