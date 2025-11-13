# Amadeus MCP Server

A comprehensive Model Context Protocol (MCP) server providing access to the complete Amadeus travel API suite. This server enables AI assistants to search, book, and manage flights, hotels, tours, transfers, and more through Amadeus's industry-leading travel APIs.

## Features

### Flight APIs (11 tools)
- **Flight Search & Discovery**
  - `search_flights` - Search for flight offers with flexible parameters
  - `confirm_flight_price` - Validate pricing before booking
  - `flight_inspiration_search` - Discover destinations from an origin
  - `flight_cheapest_dates` - Find cheapest dates to travel

- **Flight Analytics & Predictions**
  - `analyze_flight_price` - AI-powered price analysis
  - `predict_flight_delay` - Forecast flight delays
  - `get_flight_status` - Real-time flight tracking

### Hotel APIs (4 tools)
- `search_hotels_by_city` - Find hotels in a city
- `search_hotels_by_location` - Find hotels near coordinates
- `get_hotel_offers` - Search availability and rates
- `get_hotel_ratings` - Sentiment-based hotel ratings

### Tours & Activities (2 tools)
- `search_activities` - Find tours and activities by location
- `get_activity_details` - Get detailed activity information

### Transfers (1 tool)
- `search_transfers` - Search airport transfers and ground transportation (valid types: PRIVATE, TAXI, HOURLY, SHUTTLE, SHARED)
  - Supports airport-to-airport transfers with automatic location formatting
  - Includes database of 20+ major airports with complete address and coordinate information
  - Automatically adds required location details (city, country code, coordinates) for API compatibility

### Reference Data (6 tools)
- `search_airports` - Find airports by keyword
- `search_cities` - Find cities by name
- `get_nearest_airports` - Find airports near coordinates
- `get_airline_info` - Get airline information
- `get_airline_routes` - Get airline route networks
- `get_airport_routes` - Get airport destinations

### Market Insights (2 tools)
- `get_travel_insights` - Most traveled destinations
- `get_booking_insights` - Most booked destinations

**Total: 26 MCP Tools** - Focused on practical search and discovery features

### Disabled Tools
The following tools are disabled but remain in the codebase for reference:
- ❌ **Booking tools** (5): `book_flight`, `book_hotel`, `book_transfer`, `get_flight_order`, `cancel_flight_order`
  - Reason: Test environment doesn't create real bookings; users prefer booking on airline/hotel websites directly
- ❌ **predict_trip_purpose**: AI prediction of business vs leisure travel
  - Reason: Users already know their trip purpose; minimal practical value

## Installation

### 1. Get Amadeus API Credentials

Sign up for a free Amadeus developer account:
1. Visit https://developers.amadeus.com
2. Create an account
3. Create a new app in the dashboard
4. Copy your **API Key** (Client ID) and **API Secret** (Client Secret)

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

Or install the package directly:

```bash
pip install -e .
```

### 3. Configure Environment Variables

Set your Amadeus credentials as environment variables:

```bash
export AMADEUS_CLIENT_ID="your_api_key_here"
export AMADEUS_CLIENT_SECRET="your_api_secret_here"
export AMADEUS_ENV="test"  # Use "production" for live bookings
```

For persistent configuration, add to your `~/.bashrc` or `~/.zshrc`:

```bash
# Amadeus API Configuration
export AMADEUS_CLIENT_ID="your_api_key_here"
export AMADEUS_CLIENT_SECRET="your_api_secret_here"
export AMADEUS_ENV="test"
```

## Usage

### Running the Server

Start the Amadeus MCP server:

```bash
mcp-server-amadeus
```

Or run directly:

```bash
python -m mcp_server_amadeus
```

### Using with Claude Desktop

Add to your Claude Desktop configuration (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "amadeus": {
      "command": "mcp-server-amadeus",
      "env": {
        "AMADEUS_CLIENT_ID": "your_api_key_here",
        "AMADEUS_CLIENT_SECRET": "your_api_secret_here",
        "AMADEUS_ENV": "test"
      }
    }
  }
}
```

### Example Queries

Once connected, you can ask Claude:

**Flight Search:**
- "Search for flights from NYC to Paris departing December 15th"
- "Find the cheapest business class flights from London to Tokyo next month"
- "Where can I fly from Los Angeles for under $300?"

**Hotel Search:**
- "Find hotels in Paris for December 20-25 for 2 adults"
- "Search for hotels near the Eiffel Tower coordinates"
- "Show me hotel ratings for the Marriott in New York"

**Activities:**
- "What tours and activities are available near the Louvre Museum?"
- "Find things to do in Rome city center"

**Transfers:**
- "Search for transfers from CDG airport to ORY airport"
- "Find a private car from JFK to Manhattan"
- "What taxi options are available from Heathrow to central London?"

**Travel Insights:**
- "What are the most popular destinations from San Francisco?"
- "Predict if this trip is for business or leisure: NYC to Chicago, Monday-Friday"
- "Is this a good price for a flight from LAX to JFK?"

**Reference Data:**
- "Find airports near coordinates 40.7128, -74.0060"
- "What routes does American Airlines operate?"
- "Search for airports in Japan"

## API Environments

### Test Environment (Default)
- **Base URL:** `https://test.api.amadeus.com`
- **Purpose:** Development and testing
- **Features:**
  - Free tier available
  - No real bookings created
  - Limited rate limits
  - Test data may not reflect real-time availability

### Production Environment
- **Base URL:** `https://api.amadeus.com`
- **Purpose:** Live bookings and real data
- **Features:**
  - Real-time data
  - Actual bookings and charges
  - Higher rate limits
  - Requires production API credentials

Set environment with: `export AMADEUS_ENV="production"`

## Tool Reference

### Flight Search Parameters

The `search_flights` tool accepts:

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `origin` | string | Origin airport/city code | "NYC", "JFK" |
| `destination` | string | Destination code | "LAX", "PAR" |
| `departure_date` | string | Departure date | "2024-12-15" |
| `return_date` | string | Return date (optional) | "2024-12-20" |
| `adults` | int | Number of adults | 1 |
| `children` | int | Number of children | 0 |
| `travel_class` | string | Cabin class | "ECONOMY", "BUSINESS" |
| `max_results` | int | Max offers to return | 10 |
| `currency_code` | string | Price currency | "USD", "EUR" |
| `nonstop_only` | bool | Only direct flights | false |
| `included_airline_codes` | string | Filter by airlines | "AA,UA,DL" |

### Hotel Search Parameters

The `get_hotel_offers` tool accepts:

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `hotel_ids` | string | Hotel IDs (comma-separated) | "MCLONGHM,ADNYCCTB" |
| `check_in_date` | string | Check-in date | "2024-12-15" |
| `check_out_date` | string | Check-out date | "2024-12-20" |
| `adults` | int | Adults per room | 2 |
| `room_quantity` | int | Number of rooms | 1 |
| `currency` | string | Price currency | "USD" |

## Authentication

The server automatically handles OAuth2 authentication:

1. **Initial Request:** When first tool is called, server requests access token
2. **Token Caching:** Token is cached and reused for subsequent requests
3. **Auto-Refresh:** Token automatically refreshes before expiration
4. **Error Handling:** Authentication errors are logged clearly

You don't need to manage tokens manually - just set your credentials and the server handles the rest.

## Rate Limits

Amadeus API rate limits vary by environment:

- **Test:** ~10 requests per second
- **Production:** Higher limits based on your plan

The server includes error handling for rate limit responses.

## Error Handling

All tools return JSON with either:

**Success Response:**
```json
{
  "data": [...],
  "meta": {...}
}
```

**Error Response:**
```json
{
  "error": "Detailed error message"
}
```

Errors are also logged to stderr for debugging.

## Supported IATA Codes

### Airport Codes
Use standard 3-letter IATA codes:
- `JFK` - John F. Kennedy International Airport
- `LAX` - Los Angeles International Airport
- `LHR` - London Heathrow
- `CDG` - Paris Charles de Gaulle
- `NRT` - Tokyo Narita

### City Codes
Many cities have their own codes:
- `NYC` - New York City (all airports)
- `LON` - London (all airports)
- `PAR` - Paris (all airports)
- `TYO` - Tokyo (all airports)

### Airline Codes
Standard 2-letter IATA codes:
- `AA` - American Airlines
- `UA` - United Airlines
- `DL` - Delta Air Lines
- `BA` - British Airways
- `LH` - Lufthansa

## Development

### Project Structure

```
src/mcp_server_amadeus/
├── __init__.py          # Package initialization
└── server.py            # Main MCP server with all tools
```

### Adding New Tools

To add a new Amadeus API endpoint:

1. Add the tool function with `@mcp.tool()` decorator
2. Implement the API request using `amadeus_request()`
3. Add proper error handling and logging
4. Update this README with the new tool

### Testing

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/
```

## Troubleshooting

### "Credentials not configured" error
- Ensure `AMADEUS_CLIENT_ID` and `AMADEUS_CLIENT_SECRET` are set
- Check that environment variables are exported in current shell
- Verify credentials are correct in Amadeus developer dashboard

### "Token request failed" error
- Check your internet connection
- Verify credentials are valid
- Ensure you're not hitting rate limits

### "API request failed (401)" error
- Your access token may have expired (should auto-refresh)
- Check if credentials are still valid
- Try regenerating credentials in Amadeus dashboard

### "No results found" errors
- Verify IATA codes are correct (must be uppercase)
- Check dates are in correct format (YYYY-MM-DD)
- Ensure dates are in the future
- Try expanding search parameters (remove filters)

### Rate limit errors
- Wait a few seconds between requests
- Reduce `max_results` parameter
- Consider upgrading to production API with higher limits

## Resources

- **Amadeus for Developers:** https://developers.amadeus.com
- **API Documentation:** https://developers.amadeus.com/self-service
- **API Reference:** https://developers.amadeus.com/self-service/apis-docs
- **Support Forum:** https://developers.amadeus.com/support
- **Discord Community:** https://discord.gg/cVrFBqx

## License

MIT License - See LICENSE file for details

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## Credits

Built with:
- [Model Context Protocol (MCP)](https://modelcontextprotocol.io)
- [Amadeus for Developers API](https://developers.amadeus.com)
- [FastMCP](https://github.com/jlowin/fastmcp)

## Changelog

### Version 0.2.0 (Simplified & Focused)
- **Simplified to 26 MCP tools** - Removed 6 low-value tools
- **Disabled booking tools** (book_flight, book_hotel, book_transfer, get_flight_order, cancel_flight_order)
  - Test environment limitations
  - Users prefer booking on provider websites directly
- **Removed predict_trip_purpose** - Users already know their trip purpose
- **Enhanced tools:**
  - Transfer API with 20+ airport location database
  - Flight price confirmation with auto-sanitization
  - Hotel ratings with better error handling
- **Focus:** Search & discovery (not booking)

### Version 0.1.0 (Initial Release)
- 32 MCP tools covering full Amadeus API
- Automatic OAuth2 authentication
- Flight search, booking, and analytics
- Hotel search and booking
- Tours and activities
- Airport transfers
- Reference data tools
- Market insights and predictions
