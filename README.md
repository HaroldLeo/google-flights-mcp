# Google Flights MCP Server (Comprehensive Edition)

This comprehensive MCP server provides powerful tools, resources, and prompts to interact with Google Flights data using the `fast-flights` library.

## Features

### MCP Tools (9 total)

#### Flight Search Tools
*   **`get_flights_on_date`**: Fetches available one-way flights for a specific date between two airports.
    *   Args: `origin`, `destination`, `date` (YYYY-MM-DD), `adults`, `children`, `infants_in_seat`, `infants_on_lap`, `seat_type` (economy/premium_economy/business/first), `return_cheapest_only`
*   **`get_round_trip_flights`**: Fetches available round-trip flights for specific departure and return dates.
    *   Args: `origin`, `destination`, `departure_date`, `return_date`, `adults`, `children`, `infants_in_seat`, `infants_on_lap`, `seat_type`, `return_cheapest_only`
*   **`find_all_flights_in_range`**: Finds available round-trip flights within a specified date range with flexible stay duration.
    *   Args: `origin`, `destination`, `start_date_str`, `end_date_str`, `min_stay_days`, `max_stay_days`, `adults`, `seat_type`, `return_cheapest_only`
*   **`get_multi_city_flights`**: Fetches multi-city/multi-stop itineraries for complex trip planning.
    *   Args: `flight_segments` (JSON array), `adults`, `seat_type`, `return_cheapest_only`
*   **`get_flexible_dates_grid`**: Get a price grid showing cheapest round-trip flights across different date combinations.
    *   Args: `origin`, `destination`, `departure_month` (YYYY-MM), `return_month`, `adults`, `seat_type`, `max_results`
*   **`compare_nearby_airports`**: Compare flight prices from multiple nearby airports simultaneously.
    *   Args: `origin_airports` (JSON array), `destination_airports` (JSON array), `date`, `adults`, `seat_type`

#### Utility Tools
*   **`search_airports`**: Search for airports by name or code.
    *   Args: `query` (airport name, city, or code)
*   **`get_travel_dates`**: Calculate suggested travel dates based on current date.
    *   Args: `days_from_now`, `trip_length`
*   **`generate_google_flights_url`**: Generate a Google Flights search URL that opens in the browser.
    *   Args: `origin`, `destination`, `departure_date`, `return_date` (optional), `adults`, `children`, `seat_type`

### MCP Resources

*   **`airports://all`**: List all available airports (first 100 for readability)
*   **`airports://{code}`**: Get information about a specific airport by its code (e.g., `airports://JFK`)

### MCP Prompts

*   **`plan_trip`**: Structured travel planning prompt template
*   **`compare_destinations`**: Destination comparison prompt template

## Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/cantsegfault/google-flights-mcp.git
    cd google-flights-mcp
    ```
2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Install Playwright browsers (needed by `fast_flights`):**
    ```bash
    playwright install
    ```

## Running the Server

You can run the server directly using Python:

```bash
python server.py
```

The server uses STDIO transport by default.

## Integrating with MCP Clients (e.g., Cline, Claude Desktop)

Add the server to your MCP client's configuration file. Example for `cline_mcp_settings.json` or `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "google-flights": {
      "command": "/path/to/your/.venv/bin/python", // Use absolute path to venv python
      "args": [
        "/absolute/path/to/flight_mcp_server/server.py" // Use absolute path to server script
      ],
      "env": {},
      "disabled": false,
      "autoApprove": []
    }
    // ... other servers
  }
}
```

**Important:** Replace the paths in `command` and `args` with the absolute paths to your virtual environment's Python executable and the `server.py` script on your system.

## Key Features

### Passenger Support
All flight search tools support:
- **Adults**: Passengers 12+ years old
- **Children**: Ages 2-11 years
- **Infants in Seat**: Under 2 years, with their own seat
- **Infants on Lap**: Under 2 years, seated on adult's lap

### Seat Classes
Choose from multiple cabin classes:
- `economy` - Standard economy class (default)
- `premium_economy` - Premium economy with extra legroom
- `business` - Business class
- `first` - First class

### Flexible Search Options
- **Price optimization**: Use `return_cheapest_only=true` to get only the best deal
- **Date flexibility**: Search entire months or date ranges
- **Multi-airport comparison**: Compare prices across nearby airports
- **Multi-city routing**: Plan complex itineraries with multiple stops

## Notes

*   This server uses the `fast-flights` library (originally from [https://github.com/AWeirdDev/flights](https://github.com/AWeirdDev/flights)) installed via pip for its core flight scraping functionality.
*   Flight scraping can sometimes be unreliable or slow depending on Google Flights changes and network conditions. The tools include comprehensive error handling.
*   The `find_all_flights_in_range` and `get_flexible_dates_grid` tools can be resource-intensive as they check many date combinations.
*   All dates should be in `YYYY-MM-DD` format (e.g., `2025-07-20`).
*   Month parameters should be in `YYYY-MM` format (e.g., `2025-07`).
