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
- Filter by passengers, cabin class, and preferences

Built on the powerful `fast-flights` library, this server provides 10 specialized tools, 2 resource endpoints, and 10 smart prompts for comprehensive travel planning.

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

### Flight Search Tools (10 Total)

#### Core Search Tools

| Tool | Description | Best For |
|------|-------------|----------|
| `search_one_way_flights` | One-way flights for a specific date | Simple one-way trips |
| `search_round_trip_flights` | Round-trip flights with fixed dates | Standard vacation planning |
| `search_round_trips_in_date_range` | Flexible date range search | Finding the best deal within a window |
| `get_multi_city_flights` | Multi-stop itineraries | Complex trips with multiple destinations |

#### Specialized Search Tools

| Tool | Description | Best For |
|------|-------------|----------|
| `search_direct_flights` | Direct flights only (no stops) | Time-sensitive travel, families with kids |
| `search_flights_by_airline` | Filter by airline or alliance | Loyalty programs, airline preferences |
| `search_flights_with_max_stops` | Control maximum number of stops | Balancing price and convenience |

#### Utility Tools

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
- **`reliable_search_strategy`** - 🆕 Guide for choosing fetch modes and troubleshooting

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
- **SerpApi Fallback**: 🆕 Automatic fallback to SerpApi when scraping fails (optional, requires API key)
- **Price context indicators**: 🆕 Know if prices are "low", "typical", or "high"
- **Native airline filtering**: 🆕 Powered by fast-flights 3.0rc0 for reliable results
- **Multiple fetch modes**: 🆕 Choose reliability vs speed (common/fallback/force-fallback/local/bright-data)
- **Token-efficient modes**: 🆕 Compact mode (save ~40% tokens)
- **Result limiting**: 🆕 `max_results` parameter prevents token overload
- **Pagination support**: 🆕 `offset`/`limit` for progressive data loading
- **Error handling**: Robust error recovery with helpful suggestions

---

## Quick Start

### Prerequisites

- Python 3.10 or higher
- An MCP-compatible client (Claude Desktop, Cline, etc.)

### Installation

#### Option 1: Install from PyPI (Recommended)

The easiest way to use this MCP server is via `uvx` (recommended) or `pip`:

```bash
# Using uvx (no installation needed, runs in isolated environment)
uvx mcp-server-google-flights

# Or install globally with pip
pip install mcp-server-google-flights

# Or install with pipx for isolated global installation
pipx install mcp-server-google-flights
```

After installation, you'll need to install Playwright browsers:
```bash
playwright install
```

#### Option 2: Install from Source

```bash
# Clone the repository
git clone https://github.com/HaroldLeo/google-flights-mcp.git
cd google-flights-mcp

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install in development mode
pip install -e .

# Install Playwright browsers (required)
playwright install
```

### Test the Server

```bash
# If installed from PyPI
mcp-server-google-flights

# If running from source
python src/mcp_server_google_flights/server.py
```

The server uses STDIO transport and will wait for MCP client connections.

---

## Configuration

### Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

#### If installed via PyPI (uvx/pip):

```json
{
  "mcpServers": {
    "google-flights": {
      "command": "uvx",
      "args": ["mcp-server-google-flights"]
    }
  }
}
```

#### If running from source:

```json
{
  "mcpServers": {
    "google-flights": {
      "command": "/absolute/path/to/.venv/bin/python",
      "args": ["/absolute/path/to/google-flights-mcp/src/mcp_server_google_flights/server.py"]
    }
  }
}
```

### Cline (VSCode Extension)

Add to `.cline/cline_mcp_settings.json`:

#### If installed via PyPI (uvx/pip):

```json
{
  "mcpServers": {
    "google-flights": {
      "command": "uvx",
      "args": ["mcp-server-google-flights"],
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

#### If running from source:

```json
{
  "mcpServers": {
    "google-flights": {
      "command": "/absolute/path/to/.venv/bin/python",
      "args": ["/absolute/path/to/google-flights-mcp/src/mcp_server_google_flights/server.py"],
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

**Important:** When running from source, use absolute paths for both the Python executable and server script.

### Optional: SerpApi Fallback Configuration

This server includes automatic fallback to [SerpApi](https://serpapi.com) when the primary scraping method fails. This significantly improves reliability and success rates for flight searches.

#### Benefits of SerpApi Fallback

- **Higher Success Rate**: API-based access is more reliable than web scraping
- **Better Rate Limiting**: Avoids Google's anti-scraping restrictions
- **Automatic Activation**: Only used when fast-flights fails
- **Transparent**: Results clearly indicate when fallback was used

#### Setup Instructions

1. **Get a SerpApi API Key**
   - Sign up at [https://serpapi.com](https://serpapi.com)
   - Free tier: 250 searches/month
   - Paid plans available for higher volume

2. **Configure the API Key in MCP**

   Add the `env` parameter to your MCP configuration:

   **Claude Desktop** (`claude_desktop_config.json`):
   ```json
   {
     "mcpServers": {
       "google-flights": {
         "command": "uvx",
         "args": ["mcp-server-google-flights"],
         "env": {
           "SERPAPI_API_KEY": "your_serpapi_key_here"
         }
       }
     }
   }
   ```

   **Cline** (`.cline/cline_mcp_settings.json`):
   ```json
   {
     "mcpServers": {
       "google-flights": {
         "command": "uvx",
         "args": ["mcp-server-google-flights"],
         "disabled": false,
         "autoApprove": [],
         "env": {
           "SERPAPI_API_KEY": "your_serpapi_key_here"
         }
       }
     }
   }
   ```

3. **Restart your MCP client** to apply the changes

#### How It Works

- The server always tries `fast-flights` (free scraping) first
- If scraping fails or returns an error, it automatically tries SerpApi
- Results from SerpApi include `"data_source": "SerpApi (fallback)"` in the response
- If no API key is configured, fallback is disabled and errors are returned normally

#### Verifying SerpApi is Enabled

Check the server logs when it starts. You should see:
```
[SerpApi] Fallback enabled with API key
```

If the API key is not configured, you'll see:
```
[SerpApi] API key not configured - set SERPAPI_API_KEY env var for fallback support
```

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

### Example 4: Direct Flights Only

```
You: "Find direct flights from Chicago to Seattle on March 15, 2026."
```

The AI will use `search_direct_flights` to filter out any flights with connections.

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

### Utility Tools

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
- Invalid airport codes
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

#### Slow Search Performance & Rate Limits

**Problem:** Searches take a long time or are rejected with rate limit errors.

**Explanation:** The server scrapes Google Flights in real-time. Some functions make multiple scraping requests and have hard limits to prevent rate limiting and IP blocking:

**Rate-Limited Functions:**
- `search_round_trips_in_date_range` - **Maximum 30 date combinations**
  - Example: 7-day range with 5-7 day stays = ~10-15 requests (OK)
  - Example: 14-day range with no filters = ~105 requests (REJECTED)

**Solutions:**
- **For date range searches:**
  - Narrow date ranges (keep under 7-10 days)
  - Use `min_stay_days` and `max_stay_days` filters
  - Use `return_cheapest_only=true` for faster results
  - Split large searches into multiple smaller ones

**Why these limits exist:** Without them, searches with 100+ requests would take 30+ minutes and get your IP blocked by Google.

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

### Publishing to PyPI

This package is published to PyPI for easy installation. To publish a new version:

```bash
# Install build tools
pip install build twine

# Update version in pyproject.toml and src/mcp_server_google_flights/__init__.py

# Build the package
python -m build

# Upload to TestPyPI (for testing)
python -m twine upload --repository testpypi dist/*

# Upload to PyPI (production)
python -m twine upload dist/*
```

**Note:** You need PyPI credentials to publish. Contact the maintainer for access.

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
