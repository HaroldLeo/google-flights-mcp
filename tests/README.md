# Test Suite for Google Flights MCP Server

This directory contains comprehensive tests for the Google Flights MCP Server, with a focus on verifying the successful migration from fast-flights v3.0rc0 to v2.2 API.

## Test Files

### `test_api_migration.py`
**Purpose**: Verify the complete migration from fast-flights v3.0rc0 to v2.2 API

This test suite ensures that:
1. ✅ All functions use `FlightData` (not `FlightQuery`)
2. ✅ All functions use `get_flights()` directly (not `create_query()`)
3. ✅ All functions use `fetch_mode="fallback"` for Playwright support
4. ✅ The `search_direct_flights` function no longer creates artificial flight combinations
5. ✅ No v3.0rc0 API remnants remain in the codebase

**Test Classes**:
- `TestAPIImports` - Verifies correct API imports
- `TestFlightDataUsage` - Ensures FlightData objects are used correctly
- `TestFetchModeFallback` - Confirms Playwright fallback is enabled
- `TestCorrectTripTypes` - Validates trip type parameters
- `TestDirectFlightsFix` - Verifies the critical bug fix in direct flights
- `TestNoCreateQuery` - Ensures v3.0rc0 API is completely removed

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

### Run Specific Test File
```bash
pytest tests/test_api_migration.py -v
```

### Run Specific Test Class
```bash
pytest tests/test_api_migration.py::TestAPIImports -v
```

### Run Specific Test
```bash
pytest tests/test_api_migration.py::TestDirectFlightsFix::test_direct_round_trip_uses_max_stops_zero -v
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

## What Was Fixed

### The Critical Bug: Missing Return Flights

**Problem**: When using fast-flights v3.0rc0 with `max_stops=0` (direct flights only), round-trip searches only returned outbound flights. Return flight segments were missing.

**Previous Workaround**: Created artificial combinations by:
1. Searching outbound direct flights separately
2. Searching return direct flights separately
3. Creating all possible combinations (e.g., 10×10 = 100 fake packages)
4. Summing individual prices (incorrect!)

**Issues with Workaround**:
- Created "fake" flight packages Google never showed
- Incorrect pricing (sum of individual legs ≠ actual round-trip price)
- Up to 130+ lines of complex code
- Misleading results for users

**Solution**: Migrated to fast-flights v2.2:
- Returns **real** Google Flights round-trip packages
- Correct combined round-trip pricing
- Simpler, cleaner code (removed 130+ line workaround)
- Playwright fallback for improved reliability

### Test Coverage

The test suite verifies:

✅ **API Correctness**: All 7 search functions use v2.2 API
✅ **FlightData Usage**: Proper FlightData object construction
✅ **Playwright Fallback**: All functions use `fetch_mode="fallback"`
✅ **Trip Types**: Correct trip type parameters (one-way, round-trip, multi-city)
✅ **Direct Flights Fix**: No more artificial combinations
✅ **Clean Migration**: No v3.0rc0 remnants in codebase

## Test Results

All 18 tests pass ✅

```
tests/test_api_migration.py::TestAPIImports::test_imports_flight_data_not_flight_query PASSED
tests/test_api_migration.py::TestAPIImports::test_imports_get_flights PASSED
tests/test_api_migration.py::TestAPIImports::test_does_not_import_create_query PASSED
tests/test_api_migration.py::TestFlightDataUsage::test_one_way_uses_flight_data PASSED
tests/test_api_migration.py::TestFlightDataUsage::test_round_trip_uses_flight_data PASSED
tests/test_api_migration.py::TestFlightDataUsage::test_direct_flights_uses_flight_data PASSED
tests/test_api_migration.py::TestFetchModeFallback::test_one_way_uses_fallback PASSED
tests/test_api_migration.py::TestFetchModeFallback::test_round_trip_uses_fallback PASSED
tests/test_api_migration.py::TestFetchModeFallback::test_direct_flights_uses_fallback PASSED
tests/test_api_migration.py::TestFetchModeFallback::test_multi_city_uses_fallback PASSED
tests/test_api_migration.py::TestCorrectTripTypes::test_one_way_trip_type PASSED
tests/test_api_migration.py::TestCorrectTripTypes::test_round_trip_trip_type PASSED
tests/test_api_migration.py::TestCorrectTripTypes::test_multi_city_trip_type PASSED
tests/test_api_migration.py::TestDirectFlightsFix::test_direct_round_trip_uses_max_stops_zero PASSED
tests/test_api_migration.py::TestDirectFlightsFix::test_direct_one_way_uses_max_stops_zero PASSED
tests/test_api_migration.py::TestNoCreateQuery::test_create_query_not_in_module PASSED
tests/test_api_migration.py::TestNoCreateQuery::test_no_create_query_in_source PASSED
tests/test_api_migration.py::TestNoCreateQuery::test_no_flight_query_in_source PASSED
```

## Continuous Integration

These tests should be run:
- Before committing changes
- In CI/CD pipelines
- After updating fast-flights dependency
- When modifying search functions

## Contributing

When adding new search functions:
1. Ensure they use FlightData (not FlightQuery)
2. Use `fetch_mode="fallback"` for Playwright support
3. Call get_flights() directly (not create_query())
4. Add corresponding tests to `test_api_migration.py`
