# Google Flights MCP Server - Issue Fixes Summary

## Issues Addressed

This document summarizes the fixes applied to address issues with the Google Flights MCP server.

### 1. ✅ Fixed: SimpleDatetime Formatting Issue

**Problem:** Arrival/departure times were displaying as raw object representations like `"SimpleDatetime(date=[2025, 11, 20]"` instead of formatted datetime strings.

**Root Cause:** The `format_datetime()` function was falling back to `str(simple_datetime)` when encountering SimpleDatetime objects that had missing or None time attributes.

**Solution:** Updated `format_datetime()` function in `server.py` (lines 53-82) to:
- Gracefully handle cases where the `time` attribute is missing or None
- Return date-only format (YYYY-MM-DD) when time is unavailable
- Return full datetime format (YYYY-MM-DD HH:MM) when both date and time are available
- Return None as a last resort instead of an object representation

**Testing:** Verified with `test_simple_datetime.py` - all edge cases now return properly formatted strings.

---

### 2. ✅ Fixed: Missing Booking URL in Responses

**Problem:** The Google Flights booking URL was being logged but not included in successful API responses, making it difficult for AI agents to provide users with booking links.

**Root Cause:** The URL was only being generated and included in error responses, not in successful flight search responses.

**Solution:** Added `booking_url` field to all successful flight search responses across all tools:
- `search_one_way_flights` (line 831, 861)
- `search_round_trips` (line 1011, 1044)
- `search_round_trips_in_date_range` (lines 1258, 1271, 1280) - Added to each date pair result
- `get_multi_city_flights` (line 1415, 1438)
- `search_direct_flights` (line 1591, 1620)
- `search_flights_by_airline` (line 1778, 1807)
- `search_flights_with_max_stops` (line 1949, 1977)

**Format:** `"booking_url": "https://www.google.com/travel/flights?tfs={query}&hl=&curr="`

---

### 3. ⚠️ Limitation: Flight Numbers Not Available

**Problem:** Flight search results don't include specific flight numbers.

**Root Cause:** The `fast-flights` library (version 3.0rc0) does not extract flight numbers from the Google Flights data. The `SingleFlight` model in the library only includes:
- from_airport (code and name)
- to_airport (code and name)
- departure (date and time)
- arrival (date and time)
- duration (minutes)
- plane_type

**Analysis:**
- The raw Google Flights data likely contains flight numbers in unused array indices
- The library's parser (in `/usr/local/lib/python3.11/dist-packages/fast_flights/parser.py`) only extracts specific indices from the data
- Flight numbers would be in one of the unexplored indices like [0], [1], [2], [7], [9], [12-16], [18-19], etc.

**Possible Solutions:**
1. Fork and modify the fast-flights library to extract flight numbers
2. Parse the raw HTML/JSON ourselves bypassing the library
3. Submit a feature request to the fast-flights maintainers
4. Wait for library updates

**Current Status:** NOT FIXED - This would require modifying the underlying fast-flights library.

---

### 4. ⚠️ Limitation: Best Flights Flag Not Available

**Problem:** The `best_flights` parameter is never returned in responses.

**Root Cause:** Similar to flight numbers, the `fast-flights` library does not extract the "best flight" flag from Google Flights data. Google Flights typically marks certain flights as "best" based on a combination of price, duration, and convenience.

**Analysis:**
- The library extracts flight data from `data[3][0]` array in the Google JavaScript data
- There may be additional metadata at the flight level (in array `k`) that contains best flight indicators
- The library currently only extracts: type, price, airlines, flight segments, and carbon emissions

**Possible Solutions:** Same as flight numbers - would require library modification.

**Current Status:** NOT FIXED - This would require modifying the underlying fast-flights library.

---

## Summary of Changes

### Files Modified
1. `src/mcp_server_google_flights/server.py`
   - Updated `format_datetime()` function (lines 53-82)
   - Added booking URLs to 7 flight search tool functions

### Files Created (for testing/documentation)
1. `test_simple_datetime.py` - Test script for SimpleDatetime formatting
2. `investigate_raw_data.py` - Analysis script for library limitations
3. `FIXES_SUMMARY.md` - This file

### Test Results
- SimpleDatetime formatting: ✅ PASSED (all edge cases handled)
- Booking URL inclusion: ✅ IMPLEMENTED (all flight search tools updated)
- Flight numbers: ❌ NOT AVAILABLE (library limitation)
- Best flights flag: ❌ NOT AVAILABLE (library limitation)

---

## Recommendations for AI Agents

When using this MCP server:
1. ✅ You can now provide users with direct booking links using the `booking_url` field
2. ⚠️ Do NOT expect flight numbers in the response - they are not available
3. ⚠️ Do NOT expect a `best_flights` or `is_best` field - this data is not exposed by the library
4. ✅ All datetime fields should now be properly formatted (no more raw object representations)
5. 💡 For multi-city trips, recommend using one-way searches as suggested in issue #14

---

## Playwright Fallback Discovery

**Update**: The package DOES have Playwright fallback support... but not in the PyPI version we're using!

### What Happened
- **PyPI `3.0rc0`** (installed): Only has `integration` parameter with BrightData support
- **GitHub main branch**: Has full Playwright fallback with `fetch_mode` parameter:
  - `"common"` - Standard HTTP (current behavior)
  - `"fallback"` - Try HTTP, then Playwright on failure
  - `"force-fallback"` - Force Playwright
  - `"local"` - Local Playwright

### Why We Don't Have It
The `3.0rc0` on PyPI appears to be an early release candidate. The GitHub repo has been updated (Aug 2025) with Playwright fallback features that haven't been released to PyPI yet.

### Options
1. **Install from GitHub**: `pip install git+https://github.com/AWeirdDev/flights.git`
   - Gets Playwright fallback
   - May be less stable
2. **Stay with 3.0rc0**: Current approach
   - Stable release candidate
   - Works with primp (browser impersonation)
   - Missing Playwright fallback

**Note**: Even with Playwright fallback, flight numbers and best_flights would still be unavailable - those are parser limitations, not fetching issues.

See `PLAYWRIGHT_FALLBACK_ANALYSIS.md` for detailed analysis.

---

## Future Improvements

1. **Flight Numbers & Best Flights**: Consider forking fast-flights or creating a custom parser to extract these fields
2. **Additional Metadata**: Investigate what other useful data is available in the raw Google Flights response
3. **Library Updates**: Monitor fast-flights for official 3.0 release with Playwright support
4. **Playwright Fallback**: Consider upgrading to GitHub version if encountering scraping blocks
5. **Alternative APIs**: Consider using Google's official Flight Search API if more detailed data is needed
