# Google Flights MCP Server

<div align="center">

**A powerful Model Context Protocol (MCP) server for intelligent flight search and travel planning**

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

[Features](#features) • [Quick Start](#quick-start) • [Installation](#installation) • [Usage](#usage-examples) • [Documentation](#api-reference)

</div>

---

## Overview

Transform how you search for flights with AI assistance. This MCP server integrates Google Flights data directly into your AI workflow, enabling natural language flight searches, intelligent price comparisons, and automated travel planning through Claude and other MCP-compatible clients.

**What you can do:**
- Search flights with natural language queries
- Compare prices across multiple airports and dates
- Find the cheapest travel dates automatically
- Plan complex multi-city itineraries
- Get flexible date price grids
- Filter by passengers, cabin class, and preferences

Built on the powerful `fast-flights` library, this server provides 15 specialized tools, 2 resource endpoints, and 10 smart prompts for comprehensive travel planning.

---

## Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage Examples](#usage-examples)
- [API Reference](#api-reference)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## Features

### Flight Search Tools (15 Total)

#### Core Search Tools

| Tool | Description | Best For |
|------|-------------|----------|
| `search_one_way_flights` | One-way flights for a specific date | Simple one-way trips |
| `search_round_trip_flights` | Round-trip flights with fixed dates | Standard vacation planning |
| `search_round_trips_in_date_range` | Flexible date range search | Finding the best deal within a window |
| `get_multi_city_flights` | Multi-stop itineraries | Complex trips with multiple destinations |
| `get_flexible_dates_grid` | Price matrix across date combinations | Visualizing price trends |
| `compare_nearby_airports` | Multi-airport price comparison | Comparing NYC airports (JFK/LGA/EWR) |

#### Specialized Search Tools

| Tool | Description | Best For |
|------|-------------|----------|
| `search_direct_flights` | Direct flights only (no stops) | Time-sensitive travel, families with kids |
| `search_flights_by_airline` | Filter by airline or alliance | Loyalty programs, airline preferences |
| `search_flights_with_max_stops` | Control maximum number of stops | Balancing price and convenience |

#### Filter & Analysis Tools

| Tool | Description | Best For |
|------|-------------|----------|
| `filter_by_departure_time` | Filter by time of day | Morning/afternoon/evening/red-eye preferences |
| `filter_by_max_duration` | Filter by total travel time | Time-sensitive travelers |
| `compare_one_way_vs_roundtrip` | Compare pricing strategies | Finding hidden savings |

#### Utility Tools

- **`search_airports`**: Find airport codes by name or location
- **`get_travel_dates`**: Calculate travel dates relative to today
- **`generate_google_flights_url`**: Create shareable Google Flights search links

### MCP Resources

- **`airports://all`** - Browse all available airports
- **`airports://{code}`** - Get detailed info for specific airports (e.g., `airports://LAX`)

### Smart Prompts

#### General Travel
- **`find_best_deal`** - Comprehensive search strategy to find the absolute cheapest flights
- **`weekend_getaway`** - Find the best weekend getaway flights (Fri-Sun or Sat-Mon patterns)
- **`last_minute_travel`** - Optimized search for urgent travel needs within the next 2 weeks

#### Specialized Travel
- **`business_trip`** - Business travel focused on schedule convenience and direct flights
- **`family_vacation`** - Family-friendly flights with kids (direct flights, reasonable times)
- **`budget_backpacker`** - Ultra-budget travel with maximum flexibility (red-eyes, multiple stops)
- **`loyalty_program_optimizer`** - Maximize airline miles, points, and elite status benefits
- **`holiday_peak_travel`** - Strategic planning for peak holiday seasons (Thanksgiving, Christmas, etc.)
- **`long_haul_international`** - Long-haul international flights prioritizing comfort and value
- **`stopover_explorer`** - Turn layovers into mini-adventures with strategic stopovers

### Key Capabilities

- **Multi-passenger support**: Adults, children, lap infants, seat infants
- **All cabin classes**: Economy, Premium Economy, Business, First
- **Flexible filtering**: Return only cheapest flights or see all options
- **Date intelligence**: Search by date ranges, relative dates, or flexible months
- **Error handling**: Robust error recovery and helpful feedback

---

## ⚡ Performance & Reliability

> **Important:** This server uses web scraping which has inherent performance and reliability limitations.

### Tool Reliability Status

| Status | Tool | Speed | Notes |
|--------|------|-------|-------|
| ✅ **Reliable** | `search_one_way_flights` | Fast (< 30s) | Most reliable tool, works consistently |
| ✅ **Reliable** | `search_airports` | Instant | Local search, always works |
| ✅ **Reliable** | `get_travel_dates` | Instant | Local calculation, always works |
| ✅ **Reliable** | `generate_google_flights_url` | Instant | Generates URLs, always works |
| ⚠️ **May Timeout** | `search_round_trip_flights` | Slow (30-60s) | May exceed MCP timeout limits |
| ⚠️ **May Timeout** | `search_direct_flights` | Slow (30-60s) | Complex queries may timeout |
| ⚠️ **May Timeout** | `search_flights_by_airline` | Slow (30-60s) | Filtered searches take longer |
| ⚠️ **May Timeout** | `search_flights_with_max_stops` | Slow (30-60s) | May timeout on some routes |
| ❌ **Often Timeouts** | `search_round_trips_in_date_range` | Very Slow (60s+) | Multiple searches, high timeout risk |
| ❌ **Often Timeouts** | `get_flexible_dates_grid` | Very Slow (60s+) | Searches entire month grid |
| ❌ **Often Timeouts** | `compare_nearby_airports` | Very Slow (60s+) | Searches all airport combinations |
| ❌ **Often Timeouts** | `get_multi_city_flights` | Very Slow (60s+) | Complex itineraries often fail to scrape |
| ❌ **Often Timeouts** | `compare_one_way_vs_roundtrip` | Very Slow (60s+) | Makes 3 separate searches |
| ⚠️ **Depends on Input** | `filter_by_departure_time` | Fast | Works if given valid flight data |
| ⚠️ **Depends on Input** | `filter_by_max_duration` | Fast | Works if given valid flight data |

### Recommended Usage Pattern

**For Best Results:**
1. **Use `search_one_way_flights`** for reliable flight data
2. **For round-trips:** Search two one-way flights separately instead of using `search_round_trip_flights`
3. **For multi-city:** Use `generate_google_flights_url` to get a clickable link instead of scraping
4. **When tools timeout:** Check the error response for `google_flights_url` field to view results in browser

**Performance Tips:**
- Use `return_cheapest_only=true` to speed up searches
- Narrow date ranges instead of searching entire months
- Search fewer airports at once in comparison tools
- Consider using URL generation for complex searches

### Why Scraping is Slow

This server uses Playwright (headless browser) to scrape Google Flights in real-time:
- Each search launches a browser session
- Pages must fully load and render
- Google may rate-limit or block excessive requests
- MCP has built-in timeout limits (typically 60 seconds)

**Alternative Approach:** For complex searches, use the URL generator tools to create Google Flights links for manual browsing.

---

## Quick Start

### Prerequisites

- Python 3.10 or higher
- An MCP-compatible client (Claude Desktop, Cline, etc.)

### Installation

```bash
# Clone the repository
git clone https://github.com/HaroldLeo/google-flights-mcp.git
cd google-flights-mcp

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers (required)
playwright install
```

### Test the Server

```bash
python server.py
```

The server uses STDIO transport and will wait for MCP client connections.

---

## Configuration

### Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "google-flights": {
      "command": "/absolute/path/to/.venv/bin/python",
      "args": ["/absolute/path/to/google-flights-mcp/server.py"]
    }
  }
}
```

### Cline (VSCode Extension)

Add to `.cline/cline_mcp_settings.json`:

```json
{
  "mcpServers": {
    "google-flights": {
      "command": "/absolute/path/to/.venv/bin/python",
      "args": ["/absolute/path/to/google-flights-mcp/server.py"],
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

**Important:** Use absolute paths for both the Python executable and server script.

### Verify Installation

After restarting your MCP client, verify the server is connected:
- **Claude Desktop**: Look for "google-flights" in the MCP servers list
- **Cline**: Check the MCP status indicator

---

## Usage Examples

### Example 1: Simple Round Trip

```
You: "Find me round-trip flights from New York to London, leaving July 15 and returning July 25, 2026. I need 2 adults in economy."
```

The AI will use `search_round_trip_flights` with:
- Origin: JFK (or search airports if unclear)
- Destination: LHR
- Dates: 2026-07-15 to 2026-07-25
- Passengers: 2 adults
- Seat class: economy

### Example 2: Flexible Date Search

```
You: "I want to visit Tokyo for about a week sometime in March 2026. What are the cheapest dates?"
```

The AI will use `search_round_trips_in_date_range` to search the entire month with 6-8 day stays.

### Example 3: Multi-City Trip

```
You: "Plan a trip: San Francisco -> Paris (3 days) -> Rome (4 days) -> back to SF. Starting June 1, 2026."
```

The AI will use `get_multi_city_flights` with calculated dates for each segment.

### Example 4: Airport Comparison

```
You: "Compare flight prices from all NYC airports to Miami on December 20, 2026."
```

The AI will use `compare_nearby_airports` with JFK, LGA, and EWR.

### Example 5: Flexible Date Grid

```
You: "Show me a price calendar for Los Angeles to Honolulu in April 2026."
```

The AI will use `get_flexible_dates_grid` to show prices across different date combinations.

---

## API Reference

### Flight Search Tools

#### `search_one_way_flights`

Search one-way flights for a specific date.

**Parameters:**
- `origin` (string, required): Departure airport code (e.g., "JFK")
- `destination` (string, required): Arrival airport code (e.g., "LAX")
- `date` (string, required): Travel date in YYYY-MM-DD format
- `adults` (integer, default: 1): Number of adult passengers (12+ years)
- `children` (integer, default: 0): Number of children (2-11 years)
- `infants_in_seat` (integer, default: 0): Infants with own seat (<2 years)
- `infants_on_lap` (integer, default: 0): Lap infants (<2 years)
- `seat_type` (string, default: "economy"): Cabin class (`economy`, `premium_economy`, `business`, `first`)
- `return_cheapest_only` (boolean, default: false): Return only the cheapest flight

**Returns:** List of flight options with prices, times, airlines, and durations.

---

#### `search_round_trip_flights`

Search round-trip flights with specific departure and return dates.

**Parameters:**
- `origin` (string, required): Departure airport code
- `destination` (string, required): Arrival airport code
- `departure_date` (string, required): Outbound date (YYYY-MM-DD)
- `return_date` (string, required): Return date (YYYY-MM-DD)
- `adults` (integer, default: 1): Adult passengers
- `children` (integer, default: 0): Child passengers
- `infants_in_seat` (integer, default: 0): Infants with seat
- `infants_on_lap` (integer, default: 0): Lap infants
- `seat_type` (string, default: "economy"): Cabin class
- `return_cheapest_only` (boolean, default: false): Return only cheapest option

**Returns:** Round-trip flight combinations with total prices.

---

#### `search_round_trips_in_date_range`

Search all possible round-trip combinations within a date range.

**Parameters:**
- `origin` (string, required): Departure airport code
- `destination` (string, required): Arrival airport code
- `start_date_str` (string, required): Range start date (YYYY-MM-DD)
- `end_date_str` (string, required): Range end date (YYYY-MM-DD)
- `min_stay_days` (integer, default: 3): Minimum trip length
- `max_stay_days` (integer, default: 7): Maximum trip length
- `adults` (integer, default: 1): Number of adults
- `seat_type` (string, default: "economy"): Cabin class
- `return_cheapest_only` (boolean, default: true): Return only cheapest per combination

**Returns:** All valid round-trip combinations sorted by price.

**Note:** Can be resource-intensive for large date ranges.

---

#### `get_multi_city_flights`

Search complex multi-city itineraries.

**Parameters:**
- `flight_segments` (JSON array, required): Array of flight segments
  ```json
  [
    {"origin": "SFO", "destination": "CDG", "date": "2026-06-01"},
    {"origin": "CDG", "destination": "FCO", "date": "2026-06-05"},
    {"origin": "FCO", "destination": "SFO", "date": "2026-06-10"}
  ]
  ```
- `adults` (integer, default: 1): Number of adults
- `seat_type` (string, default: "economy"): Cabin class
- `return_cheapest_only` (boolean, default: false): Return only cheapest option

**Returns:** Multi-city itinerary options with total prices.

---

#### `get_flexible_dates_grid`

Get a price grid showing flight costs across different date combinations.

**Parameters:**
- `origin` (string, required): Departure airport code
- `destination` (string, required): Arrival airport code
- `departure_month` (string, required): Outbound month (YYYY-MM)
- `return_month` (string, required): Return month (YYYY-MM)
- `adults` (integer, default: 1): Number of adults
- `seat_type` (string, default: "economy"): Cabin class
- `max_results` (integer, default: 50): Maximum results to return

**Returns:** Grid of prices for different date combinations.

---

#### `compare_nearby_airports`

Compare prices from multiple origin airports to multiple destinations.

**Parameters:**
- `origin_airports` (JSON array, required): List of origin airport codes
  ```json
  ["JFK", "LGA", "EWR"]
  ```
- `destination_airports` (JSON array, required): List of destination codes
  ```json
  ["LAX", "SFO"]
  ```
- `date` (string, required): Travel date (YYYY-MM-DD)
- `adults` (integer, default: 1): Number of adults
- `seat_type` (string, default: "economy"): Cabin class

**Returns:** Price comparison across all airport combinations.

---

#### `search_direct_flights`

Search for direct flights only (no stops) for one-way or round-trip.

**Parameters:**
- `origin` (string, required): Departure airport code
- `destination` (string, required): Arrival airport code
- `date` (string, required): Departure date (YYYY-MM-DD)
- `is_round_trip` (boolean, default: false): Search round-trip if true
- `return_date` (string, optional): Return date (required if is_round_trip=true)
- `adults` (integer, default: 1): Adult passengers
- `children` (integer, default: 0): Child passengers
- `infants_in_seat` (integer, default: 0): Infants with seat
- `infants_on_lap` (integer, default: 0): Lap infants
- `seat_type` (string, default: "economy"): Cabin class
- `return_cheapest_only` (boolean, default: false): Return only cheapest option

**Returns:** Direct flight options only (no connections).

**Example:**
```json
{"origin": "SFO", "destination": "JFK", "date": "2025-07-20"}
```

---

#### `search_flights_by_airline`

Filter flights by specific airlines or alliances.

**Parameters:**
- `origin` (string, required): Departure airport code
- `destination` (string, required): Arrival airport code
- `date` (string, required): Departure date (YYYY-MM-DD)
- `airlines` (JSON array, required): Airline codes or alliance names
  - Airline codes: `["UA", "AA", "DL"]` (2-letter codes)
  - Alliances: `["STAR_ALLIANCE"]`, `["SKYTEAM"]`, or `["ONEWORLD"]`
- `is_round_trip` (boolean, default: false): Search round-trip if true
- `return_date` (string, optional): Return date (required if is_round_trip=true)
- `adults` (integer, default: 1): Number of adults
- `seat_type` (string, default: "economy"): Cabin class
- `return_cheapest_only` (boolean, default: false): Return only cheapest option

**Returns:** Flights filtered by specified airlines/alliances.

**Example:**
```json
{"origin": "SFO", "destination": "JFK", "date": "2025-07-20", "airlines": "[\"UA\", \"AA\"]"}
```

---

#### `search_flights_with_max_stops`

Search flights with a maximum number of stops.

**Parameters:**
- `origin` (string, required): Departure airport code
- `destination` (string, required): Arrival airport code
- `date` (string, required): Departure date (YYYY-MM-DD)
- `max_stops` (integer, required): Maximum number of stops (0, 1, or 2)
- `is_round_trip` (boolean, default: false): Search round-trip if true
- `return_date` (string, optional): Return date (required if is_round_trip=true)
- `adults` (integer, default: 1): Number of adults
- `seat_type` (string, default: "economy"): Cabin class
- `return_cheapest_only` (boolean, default: false): Return only cheapest option

**Returns:** Flights with at most the specified number of stops.

**Example:**
```json
{"origin": "SFO", "destination": "JFK", "date": "2025-07-20", "max_stops": 1}
```

---

#### `filter_by_departure_time`

Filter existing flight results by departure time of day.

**Parameters:**
- `flights_json` (string, required): JSON string of flight results from another search
- `time_of_day` (string, required): Time preference
  - `"morning"` (6am-12pm)
  - `"afternoon"` (12pm-6pm)
  - `"evening"` (6pm-12am)
  - `"red-eye"` (12am-6am)

**Returns:** Filtered flights matching the time preference.

**Example:**
```json
{"flights_json": "[{...}]", "time_of_day": "morning"}
```

---

#### `filter_by_max_duration`

Filter existing flight results by maximum travel duration.

**Parameters:**
- `flights_json` (string, required): JSON string of flight results from another search
- `max_hours` (integer, required): Maximum acceptable flight duration in hours

**Returns:** Flights within the duration limit.

**Example:**
```json
{"flights_json": "[{...}]", "max_hours": 8}
```

---

#### `compare_one_way_vs_roundtrip`

Compare pricing for round-trip ticket vs two one-way tickets.

**Parameters:**
- `origin` (string, required): Departure airport code
- `destination` (string, required): Arrival airport code
- `departure_date` (string, required): Outbound date (YYYY-MM-DD)
- `return_date` (string, required): Return date (YYYY-MM-DD)
- `adults` (integer, default: 1): Number of adults
- `seat_type` (string, default: "economy"): Cabin class

**Returns:** Price comparison with recommendation and potential savings.

**Example:**
```json
{"origin": "SFO", "destination": "JFK", "departure_date": "2025-07-20", "return_date": "2025-07-27"}
```

---

### Utility Tools

#### `search_airports`

Search for airports by name, city, or code.

**Parameters:**
- `query` (string, required): Search term (e.g., "Los Angeles", "LAX", "London")

**Returns:** List of matching airports with codes and names.

---

#### `get_travel_dates`

Calculate travel dates relative to today.

**Parameters:**
- `days_from_now` (integer, default: 30): Days until departure
- `trip_length` (integer, default: 7): Duration of trip

**Returns:** Suggested departure and return dates.

---

#### `generate_google_flights_url`

Create a Google Flights search URL.

**Parameters:**
- `origin` (string, required): Departure airport code
- `destination` (string, required): Arrival airport code
- `departure_date` (string, required): Departure date (YYYY-MM-DD)
- `return_date` (string, optional): Return date for round-trips
- `adults` (integer, default: 1): Number of adults
- `children` (integer, default: 0): Number of children
- `seat_type` (string, default: "economy"): Cabin class

**Returns:** Complete Google Flights URL.

---

### Resources

Access airport data directly:

```
airports://all          # List all airports (first 100)
airports://JFK          # Get info for JFK airport
airports://heathrow     # Search by name
```

---

## Troubleshooting

### Common Issues

#### Server Not Connecting

**Problem:** MCP client doesn't show the google-flights server.

**Solutions:**
1. Verify absolute paths in configuration
2. Check Python executable: `which python` (Unix) or `where python` (Windows)
3. Restart MCP client completely
4. Check logs in client's developer console

---

#### Playwright Browser Error

**Problem:** Error about missing browser binaries.

**Solution:**
```bash
# Activate venv first
source .venv/bin/activate

# Install browsers
playwright install

# If that fails, try with dependencies
playwright install --with-deps
```

---

#### Flight Search Returns No Results

**Possible causes:**
- Invalid airport codes (use `search_airports` tool first)
- Dates in the past
- Invalid date format (must be YYYY-MM-DD)
- No flights available for that route/date
- Google Flights rate limiting

**Solutions:**
1. Verify airport codes exist
2. Check date formatting
3. Try broader date range
4. Wait a few minutes if rate-limited

---

#### Slow Search Performance

**Problem:** Searches take a long time.

**Explanation:** The server scrapes Google Flights in real-time, which can be slow, especially for:
- `search_round_trips_in_date_range` with large date ranges
- `get_flexible_dates_grid` with full months
- `compare_nearby_airports` with many airports

**Solutions:**
- Use `return_cheapest_only=true` for faster results
- Narrow date ranges
- Search fewer airports at once

---

#### Import Errors

**Problem:** `ModuleNotFoundError` when starting server.

**Solution:**
```bash
# Ensure venv is activated
source .venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

---

### Debug Mode

For troubleshooting, run the server with Python logging:

```bash
python -u server.py 2>&1 | tee server.log
```

Check `server.log` for detailed error messages.

---

## Contributing

Contributions are welcome! Here's how you can help:

### Reporting Bugs

Open an issue with:
- Description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Server logs if applicable

### Suggesting Features

Open an issue describing:
- The feature you'd like to see
- Use cases and examples
- Why it would be valuable

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Test thoroughly
5. Commit with clear messages
6. Push to your fork
7. Open a Pull Request

### Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/google-flights-mcp.git
cd google-flights-mcp

# Install dev dependencies
pip install -r requirements.txt
pip install pytest black ruff

# Run tests
pytest

# Format code
black .
ruff check .
```

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- Built with the [Model Context Protocol](https://modelcontextprotocol.io) by Anthropic
- Flight data powered by [fast-flights](https://github.com/AWeirdDev/flights) library
- Inspired by the need for better AI-assisted travel planning
- Special thanks to these projects that helped shape this implementation:
  - [opspawn/Google-Flights-MCP-Server](https://github.com/opspawn/Google-Flights-MCP-Server)
  - [salamentic/google-flights-mcp](https://github.com/salamentic/google-flights-mcp)

---

## Support

- **Issues:** [GitHub Issues](https://github.com/HaroldLeo/google-flights-mcp/issues)
- **MCP Documentation:** [modelcontextprotocol.io](https://modelcontextprotocol.io)
- **Discussions:** [GitHub Discussions](https://github.com/HaroldLeo/google-flights-mcp/discussions)

---

<div align="center">

**Made for the MCP community**

Star this repo if you find it helpful!

</div>
