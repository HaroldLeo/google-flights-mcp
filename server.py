
#!/usr/bin/env python
import asyncio
import json
import datetime
import sys
import os
from typing import Any, Optional, Dict

# Import fast_flights from pip package
try:
    from fast_flights import FlightData, Passengers, get_flights
    from fast_flights.search import search_airport
except ImportError as e:
    print(f"Error importing fast_flights: {e}", file=sys.stderr)
    print(f"Please install fast_flights: pip install fast-flights", file=sys.stderr)
    sys.exit(1)

from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("google-flights-comprehensive")

# --- Airport data cache ---
_airports_cache = None

def get_all_airports():
    """Get all available airports from fast_flights."""
    global _airports_cache
    if _airports_cache is None:
        try:
            from fast_flights.search import Airports
            _airports_cache = list(Airports)
        except Exception as e:
            print(f"Warning: Could not load airports: {e}", file=sys.stderr)
            _airports_cache = []
    return _airports_cache

# --- Helper functions ---

def flight_to_dict(flight):
    """Converts a flight object to a dictionary, handling potential missing attributes."""
    return {
        "is_best": getattr(flight, 'is_best', None),
        "name": getattr(flight, 'name', None),
        "departure": getattr(flight, 'departure', None),
        "arrival": getattr(flight, 'arrival', None),
        "arrival_time_ahead": getattr(flight, 'arrival_time_ahead', None),
        "duration": getattr(flight, 'duration', None),
        "stops": getattr(flight, 'stops', None),
        "delay": getattr(flight, 'delay', None),
        "price": getattr(flight, 'price', None),
    }

def parse_price(price_str):
    """Extracts integer price from a string like '$268'."""
    if not price_str or not isinstance(price_str, str):
        return float('inf') # Return infinity if price is missing or invalid
    try:
        return int(price_str.replace('$', '').replace(',', ''))
    except ValueError:
        return float('inf') # Return infinity if conversion fails

def get_date_range(year, month):
    """Generates all dates within a given month."""
    try:
        start_date = datetime.date(year, month, 1)
        # Find the first day of the next month, then subtract one day
        if month == 12:
            end_date = datetime.date(year + 1, 1, 1) - datetime.timedelta(days=1)
        else:
            end_date = datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)
    except ValueError: # Handle invalid year/month
        return []

    current_date = start_date
    while current_date <= end_date:
        yield current_date
        current_date += datetime.timedelta(days=1)

# --- MCP Resources ---

@mcp.resource("airports://all")
def list_all_airports() -> str:
    """List all available airports (first 100 for readability)."""
    airports = get_all_airports()
    airport_list = []
    for airport in airports[:100]:
        airport_list.append({
            "code": airport.value,
            "name": airport.name
        })

    result = {
        "total_airports": len(airports),
        "showing": len(airport_list),
        "airports": airport_list
    }
    if len(airports) > 100:
        result["note"] = f"Showing first 100 of {len(airports)} airports. Use search_airports tool for specific lookups."

    return json.dumps(result, indent=2)


@mcp.resource("airports://{code}")
def get_airport_by_code(code: str) -> str:
    """Get information about a specific airport by its code."""
    airports = get_all_airports()
    code_upper = code.upper()

    for airport in airports:
        if airport.value.upper() == code_upper:
            return json.dumps({
                "code": airport.value,
                "name": airport.name
            }, indent=2)

    return json.dumps({
        "error": f"Airport code '{code}' not found",
        "suggestion": "Use search_airports tool to find available airports"
    })


# --- MCP Prompts ---

@mcp.prompt()
def find_best_deal() -> str:
    """Comprehensive search strategy to find the absolute cheapest flights."""
    return """I'll help you find the absolute best flight deal using a comprehensive search strategy.

**Search Strategy:**
1. First, use `search_airports` to verify origin and destination airport codes
2. Use `find_all_flights_in_range` to search all dates within your flexible window
   - Set `return_cheapest_only=true` for faster results
   - Try different stay durations (e.g., 3-7 days, 7-14 days)
3. If you have nearby airports, use `compare_nearby_airports` to check all combinations
   - Example: NYC has JFK, LGA, EWR; SF Bay has SFO, OAK, SJC
4. Use `get_flexible_dates_grid` to visualize price patterns across entire months
5. Compare results and identify the cheapest option
6. Use `generate_google_flights_url` to create a direct booking link

**What I need from you:**
- Origin city/airport (I'll find nearby alternatives)
- Destination city/airport (I'll find nearby alternatives)
- Approximate travel timeframe (e.g., "sometime in March", "late summer")
- Flexible stay duration or specific length
- Number of travelers and seat class preference

**Result:** I'll present the top 5 cheapest options with dates, prices, and booking links."""


@mcp.prompt()
def weekend_getaway() -> str:
    """Find the best weekend getaway flights (Fri-Sun or Sat-Mon)."""
    return """I'll help you plan the perfect weekend getaway!

**Search Strategy:**
1. Calculate upcoming weekends using `get_travel_dates`
2. Search both Friday-Sunday and Saturday-Monday patterns
3. Check multiple weekend options (next 4-8 weekends)
4. For major metro areas, compare all nearby airports using `compare_nearby_airports`
5. Find the cheapest weekend option with `get_round_trip_flights`

**Weekend Patterns to Check:**
- Friday evening departure → Sunday evening return (2 nights)
- Friday morning departure → Sunday night return (2 nights)
- Saturday morning departure → Monday evening return (2 nights)
- Thursday evening departure → Sunday night return (3 nights, extended weekend)

**What I need from you:**
- Your home city/airport
- Destination city/airport
- How many weekends out to search (e.g., "next 4 weekends", "March weekends")
- Number of travelers and seat class

**Result:** I'll show you the cheapest weekend for your trip with exact dates and prices."""


@mcp.prompt()
def last_minute_travel() -> str:
    """Optimized search for urgent travel needs within the next 2 weeks."""
    return """I'll help you find the best last-minute flights for urgent travel!

**Last-Minute Search Strategy:**
1. Use `get_travel_dates` to get dates for the next 14 days
2. Search specific dates with `get_flights_on_date` or `get_round_trip_flights`
   - Set `return_cheapest_only=true` for quick results
3. For better deals, check if nearby airports have availability using `compare_nearby_airports`
4. If you have flexibility, search a 3-5 day window around your target date
5. Prioritize direct flights for time-sensitive travel
6. Generate immediate booking links with `generate_google_flights_url`

**Last-Minute Tips:**
- Weekday flights (Tue/Wed/Thu) are often cheaper than weekends
- Early morning and late evening flights tend to be less expensive
- Consider nearby airports even if slightly less convenient
- Book immediately once you find a good price - they change quickly

**What I need from you:**
- Origin and destination
- Target travel date (or date range if flexible)
- Round-trip or one-way
- Trip duration if round-trip
- Number of travelers

**Result:** I'll find the fastest and/or cheapest options available now with booking links."""


@mcp.prompt()
def business_trip() -> str:
    """Optimized flight search for business travel with focus on convenience and flexibility."""
    return """I'll help you find the best business travel flights prioritizing convenience and flexibility.

**Business Travel Search Strategy:**
1. Use `search_airports` to identify all nearby airports for maximum flexibility
2. Focus on flight times that maximize productivity:
   - Early morning departures (6-8 AM) to arrive for business hours
   - Evening returns (6-9 PM) to maximize on-site time
   - Avoid red-eyes unless specifically requested
3. Prioritize direct flights using `get_flights_on_date` or `get_round_trip_flights`
   - Set `return_cheapest_only=false` to see multiple options by time
4. If dates are flexible, use `find_all_flights_in_range` with short windows (2-3 days)
5. For premium cabins, search with `seat_type="business"` or `seat_type="first"`
6. Compare nearby airports for better schedules, not just price
7. Generate booking link with `generate_google_flights_url`

**Business Travel Priorities:**
- Schedule convenience over price (within reason)
- Direct flights preferred (less delay risk)
- Departure times that allow morning meetings
- Return times that don't waste a full business day
- Premium cabins for international or long flights (4+ hours)
- Refundable/flexible fares (mention this in results)

**What I need from you:**
- Origin city (I'll check all nearby airports)
- Destination city
- Meeting/event dates or flexibility window
- Preferred departure time windows
- Seat class preference (economy/business/first)
- Trip purpose (helps prioritize schedule vs cost)

**Result:** I'll present 3-5 best options ranked by schedule convenience, with direct flights first, plus booking links."""


# --- MCP Tool: Date Calculator ---

@mcp.tool()
async def get_travel_dates(
    days_from_now: int = 30,
    trip_length: int = 7
) -> str:
    """
    Calculate suggested travel dates based on current date.
    Helpful for planning future trips.

    Args:
        days_from_now: Number of days from today for departure (default: 30).
        trip_length: Length of trip in days (default: 7).

    Returns:
        JSON with suggested departure and return dates.

    Example Args:
        {"days_from_now": 45, "trip_length": 10}
    """
    try:
        today = datetime.date.today()
        departure_date = today + datetime.timedelta(days=days_from_now)
        return_date = departure_date + datetime.timedelta(days=trip_length)

        return json.dumps({
            "today": today.strftime('%Y-%m-%d'),
            "departure_date": departure_date.strftime('%Y-%m-%d'),
            "return_date": return_date.strftime('%Y-%m-%d'),
            "trip_length_days": trip_length,
            "days_until_departure": days_from_now
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": {"message": str(e), "type": type(e).__name__}})


# --- MCP Tool Implementations ---

@mcp.tool()
async def get_flights_on_date(
    origin: str,
    destination: str,
    date: str,
    adults: int = 1,
    children: int = 0,
    infants_in_seat: int = 0,
    infants_on_lap: int = 0,
    seat_type: str = "economy",
    return_cheapest_only: bool = False
) -> str:
    """
    Fetches available one-way flights for a specific date between two airports.
    Can optionally return only the cheapest flight found.

    Args:
        origin: Origin airport code (e.g., "DEN").
        destination: Destination airport code (e.g., "LAX").
        date: The specific date to search (YYYY-MM-DD format).
        adults: Number of adult passengers (default: 1).
        children: Number of children (2-11 years, default: 0).
        infants_in_seat: Number of infants in seat (under 2 years, default: 0).
        infants_on_lap: Number of infants on lap (under 2 years, default: 0).
        seat_type: Fare class - economy/premium_economy/business/first (default: "economy").
        return_cheapest_only: If True, returns only the cheapest flight (default: False).

    Example Args:
        {"origin": "SFO", "destination": "JFK", "date": "2025-07-20"}
        {"origin": "SFO", "destination": "JFK", "date": "2025-07-20", "adults": 2, "children": 1}
        {"origin": "SFO", "destination": "JFK", "date": "2025-07-20", "return_cheapest_only": true}
    """
    print(f"MCP Tool: Getting flights {origin}->{destination} for {date}...", file=sys.stderr)
    try:
        # Validate date format
        datetime.datetime.strptime(date, '%Y-%m-%d')

        flight_data = [
            FlightData(date=date, from_airport=origin, to_airport=destination),
        ]
        passengers_info = Passengers(
            adults=adults,
            children=children,
            infants_in_seat=infants_in_seat,
            infants_on_lap=infants_on_lap
        )

        result = get_flights(
            flight_data=flight_data,
            trip="one-way", # Explicitly one-way for this tool
            seat=seat_type,
            passengers=passengers_info,
        )

        if result and result.flights:
            # Process flights based on the new parameter
            if return_cheapest_only:
                cheapest_flight = min(result.flights, key=lambda f: parse_price(f.price))
                processed_flights = [flight_to_dict(cheapest_flight)]
                result_key = "cheapest_flight" # Use a specific key for single result
            else:
                processed_flights = [flight_to_dict(f) for f in result.flights]
                result_key = "flights" # Keep original key for list

            output_data = {
                "search_parameters": {
                    "origin": origin,
                    "destination": destination,
                    "date": date,
                    "adults": adults,
                    "children": children,
                    "infants_in_seat": infants_in_seat,
                    "infants_on_lap": infants_on_lap,
                    "seat_type": seat_type,
                    "return_cheapest_only": return_cheapest_only
                },
                result_key: processed_flights
            }
            return json.dumps(output_data, indent=2)
        else:
            return json.dumps({
                "message": f"No flights found for {origin} -> {destination} on {date}.",
                "search_parameters": { "origin": origin, "destination": destination, "date": date, "adults": adults, "seat_type": seat_type }
             })

    except ValueError as e:
         # Return structured error
         error_payload = {"error": {"message": f"Invalid date format: '{date}'. Please use YYYY-MM-DD.", "type": "ValueError"}}
         return json.dumps(error_payload)
    except Exception as e:
        print(f"MCP Tool Error in get_flights_on_date: {e}", file=sys.stderr)
        # Return structured error
        error_payload = {"error": {"message": f"An unexpected error occurred.", "type": type(e).__name__}}
        return json.dumps(error_payload)


@mcp.tool()
async def get_round_trip_flights(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: str,
    adults: int = 1,
    children: int = 0,
    infants_in_seat: int = 0,
    infants_on_lap: int = 0,
    seat_type: str = "economy",
    return_cheapest_only: bool = False
) -> str:
    """
    Fetches available round-trip flights for specific departure and return dates.
    Can optionally return only the cheapest flight found.

    Args:
        origin: Origin airport code (e.g., "DEN").
        destination: Destination airport code (e.g., "LAX").
        departure_date: The specific departure date (YYYY-MM-DD format).
        return_date: The specific return date (YYYY-MM-DD format).
        adults: Number of adult passengers (default: 1).
        children: Number of children (2-11 years, default: 0).
        infants_in_seat: Number of infants in seat (under 2 years, default: 0).
        infants_on_lap: Number of infants on lap (under 2 years, default: 0).
        seat_type: Fare class - economy/premium_economy/business/first (default: "economy").
        return_cheapest_only: If True, returns only the cheapest flight (default: False).

    Example Args:
        {"origin": "DEN", "destination": "LAX", "departure_date": "2025-08-01", "return_date": "2025-08-08"}
        {"origin": "DEN", "destination": "LAX", "departure_date": "2025-08-01", "return_date": "2025-08-08", "adults": 2, "children": 2}
    """
    print(f"MCP Tool: Getting round trip {origin}<->{destination} for {departure_date} to {return_date}...", file=sys.stderr)
    try:
        # Validate date formats
        datetime.datetime.strptime(departure_date, '%Y-%m-%d')
        datetime.datetime.strptime(return_date, '%Y-%m-%d')

        flight_data = [
            FlightData(date=departure_date, from_airport=origin, to_airport=destination),
            FlightData(date=return_date, from_airport=destination, to_airport=origin),
        ]
        passengers_info = Passengers(
            adults=adults,
            children=children,
            infants_in_seat=infants_in_seat,
            infants_on_lap=infants_on_lap
        )

        result = get_flights(
            flight_data=flight_data,
            trip="round-trip",
            seat=seat_type,
            passengers=passengers_info,
        )

        if result and result.flights:
            # Process flights based on the new parameter
            if return_cheapest_only:
                cheapest_flight = min(result.flights, key=lambda f: parse_price(f.price))
                processed_flights = [flight_to_dict(cheapest_flight)]
                result_key = "cheapest_round_trip_option" # Use a specific key for single result
            else:
                processed_flights = [flight_to_dict(f) for f in result.flights]
                result_key = "round_trip_options" # Keep original key for list

            # Note: The library might return combined round-trip options or separate legs.
            # Assuming it returns combined options based on the original script's handling.
            output_data = {
                "search_parameters": {
                    "origin": origin,
                    "destination": destination,
                    "departure_date": departure_date,
                    "return_date": return_date,
                    "adults": adults,
                    "children": children,
                    "infants_in_seat": infants_in_seat,
                    "infants_on_lap": infants_on_lap,
                    "seat_type": seat_type,
                    "return_cheapest_only": return_cheapest_only
                },
                result_key: processed_flights
            }
            return json.dumps(output_data, indent=2)
        else:
             return json.dumps({
                "message": f"No round trip flights found for {origin} <-> {destination} from {departure_date} to {return_date}.",
                 "search_parameters": { "origin": origin, "destination": destination, "departure_date": departure_date, "return_date": return_date, "adults": adults, "seat_type": seat_type }
            })

    except ValueError as e:
         # Return structured error
         error_payload = {"error": {"message": f"Invalid date format provided. Use YYYY-MM-DD.", "type": "ValueError"}}
         return json.dumps(error_payload)
    except Exception as e:
        print(f"MCP Tool Error in get_round_trip_flights: {e}", file=sys.stderr)
        # Return structured error
        error_payload = {"error": {"message": f"An unexpected error occurred.", "type": type(e).__name__}}
        return json.dumps(error_payload)


@mcp.tool(name="find_all_flights_in_range") # Renamed tool
async def find_all_flights_in_range( # Renamed function
    origin: str,
    destination: str,
    start_date_str: str,
    end_date_str: str,
    min_stay_days: Optional[int] = None,
    max_stay_days: Optional[int] = None,
    adults: int = 1,
    seat_type: str = "economy",
    return_cheapest_only: bool = False # Added parameter
) -> str:
    """
    Finds available round-trip flights within a specified date range.
    Can optionally return only the cheapest flight found for each date pair.

    Args:
        origin: Origin airport code (e.g., "DEN").
        destination: Destination airport code (e.g., "LAX").
        start_date_str: Start date of the search range (YYYY-MM-DD format).
        end_date_str: End date of the search range (YYYY-MM-DD format).
        min_stay_days: Minimum number of days for the stay (optional).
        max_stay_days: Maximum number of days for the stay (optional).
        adults: Number of adult passengers (default: 1).
        seat_type: Fare class (e.g., "economy", "business", default: "economy").
        return_cheapest_only: If True, returns only the cheapest flight for each date pair (default: False).

    Example Args:
        {"origin": "JFK", "destination": "MIA", "start_date_str": "2025-09-10", "end_date_str": "2025-09-20", "min_stay_days": 5}
        {"origin": "JFK", "destination": "MIA", "start_date_str": "2025-09-10", "end_date_str": "2025-09-20", "min_stay_days": 5, "return_cheapest_only": true}
    """
    # Adjust print message based on mode
    search_mode = "cheapest flight per pair" if return_cheapest_only else "all flights"
    print(f"MCP Tool: Finding {search_mode} {origin}<->{destination} between {start_date_str} and {end_date_str}...", file=sys.stderr)

    # Initialize list to store results based on mode
    results_data = []
    error_messages = []

    try:
        start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except ValueError as e:
        # Return structured error
        error_payload = {"error": {"message": f"Invalid date format. Use YYYY-MM-DD.", "type": "ValueError"}}
        return json.dumps(error_payload)

    if start_date > end_date:
        # Return structured error
        error_payload = {"error": {"message": "Start date cannot be after end date.", "type": "ValueError"}}
        return json.dumps(error_payload)

    date_list = []
    current_date = start_date
    while current_date <= end_date:
        date_list.append(current_date)
        current_date += datetime.timedelta(days=1)

    if not date_list:
         return json.dumps({"error": "No valid dates in the specified range."})

    total_combinations = 0
    date_pairs_to_check = []
    for i, depart_date in enumerate(date_list):
        for j, return_date in enumerate(date_list[i:]):
            stay_duration = (return_date - depart_date).days
            valid_stay = True
            if min_stay_days is not None and stay_duration < min_stay_days:
                valid_stay = False
            if max_stay_days is not None and stay_duration > max_stay_days:
                valid_stay = False

            if valid_stay:
                total_combinations += 1
                date_pairs_to_check.append((depart_date, return_date))

    print(f"MCP Tool: Checking {total_combinations} valid date combinations in range...", file=sys.stderr)
    count = 0

    for depart_date, return_date in date_pairs_to_check:
        count += 1
        if count % 10 == 0: # Log progress
            print(f"MCP Tool Progress: Checking {depart_date.strftime('%Y-%m-%d')} -> {return_date.strftime('%Y-%m-%d')} ({count}/{total_combinations})", file=sys.stderr)

        try:
            flight_data = [
                FlightData(date=depart_date.strftime('%Y-%m-%d'), from_airport=origin, to_airport=destination),
                FlightData(date=return_date.strftime('%Y-%m-%d'), from_airport=destination, to_airport=origin),
            ]
            passengers_info = Passengers(adults=adults)

            result = get_flights(
                flight_data=flight_data,
                trip="round-trip",
                seat=seat_type,
                passengers=passengers_info,
            )

            # Collect results based on mode
            if result and result.flights:
                if return_cheapest_only:
                    # Find and store only the cheapest for this pair
                    cheapest_flight_for_pair = min(result.flights, key=lambda f: parse_price(f.price))
                    results_data.append({
                        "departure_date": depart_date.strftime('%Y-%m-%d'),
                        "return_date": return_date.strftime('%Y-%m-%d'),
                        "cheapest_flight": flight_to_dict(cheapest_flight_for_pair) # Store single cheapest
                    })
                else:
                    # Store all flights for this pair
                    flights_list = [flight_to_dict(f) for f in result.flights]
                    results_data.append({
                        "departure_date": depart_date.strftime('%Y-%m-%d'),
                        "return_date": return_date.strftime('%Y-%m-%d'),
                        "flights": flights_list # Store list of all flights
                    })
            # else: # Optional: Log if no flights were found for a specific pair
                # print(f"MCP Tool: No flights found for {depart_date.strftime('%Y-%m-%d')} -> {return_date.strftime('%Y-%m-%d')}", file=sys.stderr)

        except Exception as e:
            # Log the specific error message to stderr for better debugging
            print(f"MCP Tool Error fetching for {depart_date.strftime('%Y-%m-%d')} -> {return_date.strftime('%Y-%m-%d')}: {type(e).__name__} - {str(e)}", file=sys.stderr)
            # Add a slightly more informative message to the results
            err_msg = f"Error fetching flights for {depart_date.strftime('%Y-%m-%d')} -> {return_date.strftime('%Y-%m-%d')}: {type(e).__name__}. Check server logs for details: {str(e)[:100]}..." # Include first 100 chars of error
            if err_msg not in error_messages:
                 error_messages.append(err_msg)

    print("MCP Tool: Range search complete.", file=sys.stderr)

    # Return collected flight data
    if results_data or error_messages: # Return even if only errors were found
        # Determine the key for the results based on the mode
        results_key = "cheapest_option_per_date_pair" if return_cheapest_only else "all_round_trip_options"
        output_data = {
            "search_parameters": {
                "origin": origin,
                "destination": destination,
                "start_date": start_date_str,
                "end_date": end_date_str,
                "min_stay_days": min_stay_days,
                "max_stay_days": max_stay_days,
                "adults": adults,
                "seat_type": seat_type,
                "return_cheapest_only": return_cheapest_only # Include parameter in output
            },
            results_key: results_data, # Use dynamic key for results
            "errors_encountered": error_messages if error_messages else None
        }
        return json.dumps(output_data, indent=2)
    else:
        # This case should ideally not be reached if the loop runs and finds nothing,
        # but kept as a fallback.
        return json.dumps({
            "message": f"No flights found and no errors encountered for {origin} -> {destination} in the range {start_date_str} to {end_date_str}.",
            "search_parameters": {
                 "origin": origin, "destination": destination, "start_date": start_date_str, "end_date": end_date_str,
                 "min_stay_days": min_stay_days, "max_stay_days": max_stay_days, "adults": adults, "seat_type": seat_type
            },
            "errors_encountered": error_messages if error_messages else None
        })


@mcp.tool()
async def get_multi_city_flights(
    flight_segments: str,
    adults: int = 1,
    seat_type: str = "economy",
    return_cheapest_only: bool = False
) -> str:
    """
    Fetches multi-city/multi-stop itineraries for complex trip planning.

    Args:
        flight_segments: JSON string of flight segments. Each segment should have "date", "from", and "to" fields.
                        Example: '[{"date": "2025-07-01", "from": "SFO", "to": "NYC"}, {"date": "2025-07-05", "from": "NYC", "to": "MIA"}, {"date": "2025-07-10", "from": "MIA", "to": "SFO"}]'
        adults: Number of adult passengers (default: 1).
        seat_type: Fare class (e.g., "economy", "business", default: "economy").
        return_cheapest_only: If True, returns only the cheapest option (default: False).

    Example Args:
        {"flight_segments": '[{"date": "2025-07-01", "from": "SFO", "to": "NYC"}, {"date": "2025-07-05", "from": "NYC", "to": "MIA"}]'}
    """
    print(f"MCP Tool: Getting multi-city flights...", file=sys.stderr)
    try:
        # Parse the flight segments JSON
        segments = json.loads(flight_segments)

        if not segments or not isinstance(segments, list):
            return json.dumps({"error": {"message": "flight_segments must be a non-empty JSON array", "type": "ValueError"}})

        if len(segments) < 2:
            return json.dumps({"error": {"message": "Multi-city trips require at least 2 flight segments", "type": "ValueError"}})

        # Validate and build flight data
        flight_data = []
        for i, segment in enumerate(segments):
            if not all(k in segment for k in ["date", "from", "to"]):
                return json.dumps({"error": {"message": f"Segment {i} missing required fields (date, from, to)", "type": "ValueError"}})

            # Validate date format
            try:
                datetime.datetime.strptime(segment["date"], '%Y-%m-%d')
            except ValueError:
                return json.dumps({"error": {"message": f"Invalid date format in segment {i}: '{segment['date']}'. Use YYYY-MM-DD.", "type": "ValueError"}})

            flight_data.append(
                FlightData(date=segment["date"], from_airport=segment["from"], to_airport=segment["to"])
            )

        passengers_info = Passengers(adults=adults)

        result = get_flights(
            flight_data=flight_data,
            trip="multi-city",
            seat=seat_type,
            passengers=passengers_info,
        )

        if result and result.flights:
            if return_cheapest_only:
                cheapest_flight = min(result.flights, key=lambda f: parse_price(f.price))
                processed_flights = [flight_to_dict(cheapest_flight)]
                result_key = "cheapest_multi_city_option"
            else:
                processed_flights = [flight_to_dict(f) for f in result.flights]
                result_key = "multi_city_options"

            output_data = {
                "search_parameters": {
                    "segments": segments,
                    "adults": adults,
                    "seat_type": seat_type,
                    "return_cheapest_only": return_cheapest_only
                },
                result_key: processed_flights
            }
            return json.dumps(output_data, indent=2)
        else:
            return json.dumps({
                "message": "No multi-city flights found for the specified route.",
                "search_parameters": {"segments": segments, "adults": adults, "seat_type": seat_type}
            })

    except json.JSONDecodeError as e:
        return json.dumps({"error": {"message": f"Invalid JSON in flight_segments: {str(e)}", "type": "JSONDecodeError"}})
    except Exception as e:
        print(f"MCP Tool Error in get_multi_city_flights: {e}", file=sys.stderr)
        return json.dumps({"error": {"message": f"An unexpected error occurred.", "type": type(e).__name__}})


@mcp.tool()
async def search_airports(
    query: str
) -> str:
    """
    Search for airports by name or code. Useful for finding airport codes when planning trips.

    Args:
        query: Search term (can be airport name, city, or code). Case-insensitive.
               Examples: "paris", "JFK", "angeles", "heathrow"

    Example Args:
        {"query": "paris"}
        {"query": "JFK"}
        {"query": "angeles"}
    """
    print(f"MCP Tool: Searching airports for '{query}'...", file=sys.stderr)
    try:
        results = search_airport(query)

        if results:
            # Convert Airport enum objects to readable format
            airports_list = []
            for airport in results[:50]:  # Limit to 50 results to avoid overwhelming output
                # Airport enum values are typically in format like "JFK" and names like "JFK_New_York"
                airports_list.append({
                    "code": airport.value,
                    "name": airport.name
                })

            output_data = {
                "query": query,
                "results_count": len(airports_list),
                "total_matches": len(results),
                "airports": airports_list
            }

            if len(results) > 50:
                output_data["note"] = f"Showing first 50 of {len(results)} matches. Refine your search for more specific results."

            return json.dumps(output_data, indent=2)
        else:
            return json.dumps({
                "query": query,
                "results_count": 0,
                "message": f"No airports found matching '{query}'",
                "airports": []
            })

    except Exception as e:
        print(f"MCP Tool Error in search_airports: {e}", file=sys.stderr)
        return json.dumps({"error": {"message": f"An unexpected error occurred.", "type": type(e).__name__}})


@mcp.tool()
async def get_flexible_dates_grid(
    origin: str,
    destination: str,
    departure_month: str,
    return_month: str,
    adults: int = 1,
    seat_type: str = "economy",
    max_results: int = 20
) -> str:
    """
    Get a price grid showing the cheapest round-trip flights across different date combinations.
    Perfect for flexible travelers who want to find the best prices.

    Args:
        origin: Origin airport code (e.g., "SFO").
        destination: Destination airport code (e.g., "JFK").
        departure_month: Month for departure in YYYY-MM format (e.g., "2025-07").
        return_month: Month for return in YYYY-MM format (e.g., "2025-07").
        adults: Number of adult passengers (default: 1).
        seat_type: Fare class (default: "economy").
        max_results: Maximum number of cheapest combinations to return (default: 20).

    Example Args:
        {"origin": "SFO", "destination": "JFK", "departure_month": "2025-07", "return_month": "2025-07"}
    """
    print(f"MCP Tool: Getting flexible dates grid {origin}<->{destination} for {departure_month}/{return_month}...", file=sys.stderr)
    try:
        # Parse month strings
        try:
            dep_year, dep_month = map(int, departure_month.split('-'))
            ret_year, ret_month = map(int, return_month.split('-'))
        except ValueError:
            return json.dumps({"error": {"message": "Invalid month format. Use YYYY-MM (e.g., '2025-07').", "type": "ValueError"}})

        # Generate all dates in the months
        departure_dates = list(get_date_range(dep_year, dep_month))
        return_dates = list(get_date_range(ret_year, ret_month))

        if not departure_dates or not return_dates:
            return json.dumps({"error": {"message": "Invalid month specified.", "type": "ValueError"}})

        # Collect all valid round-trip combinations with prices
        price_grid = []
        total_checks = 0

        for dep_date in departure_dates:
            for ret_date in return_dates:
                # Only check if return is after departure
                if ret_date <= dep_date:
                    continue

                total_checks += 1
                if total_checks % 20 == 0:
                    print(f"MCP Tool Progress: Checked {total_checks} date combinations...", file=sys.stderr)

                try:
                    flight_data = [
                        FlightData(date=dep_date.strftime('%Y-%m-%d'), from_airport=origin, to_airport=destination),
                        FlightData(date=ret_date.strftime('%Y-%m-%d'), from_airport=destination, to_airport=origin),
                    ]
                    passengers_info = Passengers(adults=adults)

                    result = get_flights(
                        flight_data=flight_data,
                        trip="round-trip",
                        seat=seat_type,
                        passengers=passengers_info,
                    )

                    if result and result.flights:
                        # Get the cheapest flight for this date pair
                        cheapest = min(result.flights, key=lambda f: parse_price(f.price))
                        price_int = parse_price(cheapest.price)

                        if price_int != float('inf'):
                            price_grid.append({
                                "departure_date": dep_date.strftime('%Y-%m-%d'),
                                "return_date": ret_date.strftime('%Y-%m-%d'),
                                "duration_days": (ret_date - dep_date).days,
                                "price": cheapest.price,
                                "price_numeric": price_int,
                                "flight_details": flight_to_dict(cheapest)
                            })

                except Exception as e:
                    # Silently continue on individual date pair errors
                    continue

        # Sort by price and limit results
        price_grid.sort(key=lambda x: x["price_numeric"])
        top_results = price_grid[:max_results]

        if top_results:
            output_data = {
                "search_parameters": {
                    "origin": origin,
                    "destination": destination,
                    "departure_month": departure_month,
                    "return_month": return_month,
                    "adults": adults,
                    "seat_type": seat_type
                },
                "total_combinations_checked": total_checks,
                "valid_flights_found": len(price_grid),
                "showing_top": len(top_results),
                "cheapest_options": top_results
            }
            return json.dumps(output_data, indent=2)
        else:
            return json.dumps({
                "message": f"No flights found for {origin} <-> {destination} in the specified months.",
                "search_parameters": {
                    "origin": origin,
                    "destination": destination,
                    "departure_month": departure_month,
                    "return_month": return_month
                },
                "total_combinations_checked": total_checks
            })

    except Exception as e:
        print(f"MCP Tool Error in get_flexible_dates_grid: {e}", file=sys.stderr)
        return json.dumps({"error": {"message": f"An unexpected error occurred: {str(e)}", "type": type(e).__name__}})


@mcp.tool()
async def compare_nearby_airports(
    origin_airports: str,
    destination_airports: str,
    date: str,
    adults: int = 1,
    seat_type: str = "economy"
) -> str:
    """
    Compare flight prices from multiple nearby airports simultaneously.
    Perfect for finding the best deal when you have flexibility in departure/arrival airports.

    Args:
        origin_airports: JSON array of origin airport codes (e.g., '["SFO", "OAK", "SJC"]').
        destination_airports: JSON array of destination airport codes (e.g., '["JFK", "EWR", "LGA"]').
        date: The specific date to search (YYYY-MM-DD format).
        adults: Number of adult passengers (default: 1).
        seat_type: Fare class (default: "economy").

    Example Args:
        {"origin_airports": '["SFO", "OAK", "SJC"]', "destination_airports": '["JFK", "EWR", "LGA"]', "date": "2025-07-20"}
    """
    print(f"MCP Tool: Comparing flights across multiple airports for {date}...", file=sys.stderr)
    try:
        # Parse airport arrays
        try:
            origins = json.loads(origin_airports)
            destinations = json.loads(destination_airports)
        except json.JSONDecodeError as e:
            return json.dumps({"error": {"message": f"Invalid JSON in airport lists: {str(e)}", "type": "JSONDecodeError"}})

        if not isinstance(origins, list) or not isinstance(destinations, list):
            return json.dumps({"error": {"message": "Airport parameters must be JSON arrays", "type": "ValueError"}})

        if not origins or not destinations:
            return json.dumps({"error": {"message": "Airport lists cannot be empty", "type": "ValueError"}})

        # Validate date format
        try:
            datetime.datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            return json.dumps({"error": {"message": f"Invalid date format: '{date}'. Use YYYY-MM-DD.", "type": "ValueError"}})

        # Search all combinations
        comparisons = []
        total_combinations = len(origins) * len(destinations)
        count = 0

        for origin in origins:
            for destination in destinations:
                count += 1
                print(f"MCP Tool Progress: Checking {origin} -> {destination} ({count}/{total_combinations})...", file=sys.stderr)

                try:
                    flight_data = [
                        FlightData(date=date, from_airport=origin, to_airport=destination),
                    ]
                    passengers_info = Passengers(adults=adults)

                    result = get_flights(
                        flight_data=flight_data,
                        trip="one-way",
                        seat=seat_type,
                        passengers=passengers_info,
                    )

                    if result and result.flights:
                        # Get cheapest flight for this route
                        cheapest = min(result.flights, key=lambda f: parse_price(f.price))
                        price_int = parse_price(cheapest.price)

                        comparisons.append({
                            "origin": origin,
                            "destination": destination,
                            "price": cheapest.price,
                            "price_numeric": price_int,
                            "cheapest_flight": flight_to_dict(cheapest),
                            "total_options": len(result.flights)
                        })
                    else:
                        comparisons.append({
                            "origin": origin,
                            "destination": destination,
                            "price": None,
                            "message": "No flights found"
                        })

                except Exception as e:
                    comparisons.append({
                        "origin": origin,
                        "destination": destination,
                        "error": f"{type(e).__name__}: {str(e)[:100]}"
                    })

        # Sort by price (valid prices first)
        valid_comparisons = [c for c in comparisons if c.get("price_numeric") and c["price_numeric"] != float('inf')]
        invalid_comparisons = [c for c in comparisons if not (c.get("price_numeric") and c["price_numeric"] != float('inf'))]

        valid_comparisons.sort(key=lambda x: x["price_numeric"])

        output_data = {
            "search_parameters": {
                "origin_airports": origins,
                "destination_airports": destinations,
                "date": date,
                "adults": adults,
                "seat_type": seat_type
            },
            "total_combinations_checked": total_combinations,
            "valid_routes_found": len(valid_comparisons),
            "comparisons": valid_comparisons + invalid_comparisons
        }

        if valid_comparisons:
            output_data["best_deal"] = valid_comparisons[0]

        return json.dumps(output_data, indent=2)

    except Exception as e:
        print(f"MCP Tool Error in compare_nearby_airports: {e}", file=sys.stderr)
        return json.dumps({"error": {"message": f"An unexpected error occurred: {str(e)}", "type": type(e).__name__}})

# --- URL Generation Tool ---

@mcp.tool()
async def generate_google_flights_url(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: Optional[str] = None,
    adults: int = 1,
    children: int = 0,
    seat_type: str = "economy"
) -> str:
    """
    Generate a Google Flights search URL that opens in the browser.
    Creates search URLs using natural language queries.

    Args:
        origin: Origin airport code (e.g., "SFO").
        destination: Destination airport code (e.g., "JFK").
        departure_date: Departure date (YYYY-MM-DD format).
        return_date: Return date for round-trip (YYYY-MM-DD format, optional).
        adults: Number of adult passengers (default: 1).
        children: Number of children (default: 0).
        seat_type: Fare class - economy/premium_economy/business/first (default: "economy").

    Returns:
        JSON with the Google Flights URL.

    Example Args:
        {"origin": "SFO", "destination": "JFK", "departure_date": "2025-07-20"}
        {"origin": "SFO", "destination": "JFK", "departure_date": "2025-07-20", "return_date": "2025-07-27"}
    """
    try:
        # Validate dates
        datetime.datetime.strptime(departure_date, '%Y-%m-%d')
        if return_date:
            datetime.datetime.strptime(return_date, '%Y-%m-%d')

        # Build passenger info
        passenger_parts = []
        if adults > 0:
            passenger_parts.append(f"{adults} adult{'s' if adults > 1 else ''}")
        if children > 0:
            passenger_parts.append(f"{children} child{'ren' if children > 1 else ''}")
        passengers_str = " ".join(passenger_parts) if passenger_parts else "1 adult"

        # Format seat class for query
        seat_class = seat_type.replace('_', ' ')

        # Build the search query with proper trip type specification
        if return_date:
            # Round trip - use "through" for better compatibility
            query = f"flights from {origin} to {destination} on {departure_date} through {return_date} {passengers_str} {seat_class} class"
            trip_type = "round-trip"
        else:
            # One way - explicitly include "oneway" in query
            query = f"flights from {origin} to {destination} on {departure_date} oneway {passengers_str} {seat_class} class"
            trip_type = "one-way"

        # URL encode the query
        from urllib.parse import quote_plus
        encoded_query = quote_plus(query)

        url = f"https://www.google.com/travel/flights/search?q={encoded_query}"

        output_data = {
            "url": url,
            "search_query": query,
            "trip_details": {
                "type": trip_type,
                "origin": origin,
                "destination": destination,
                "departure_date": departure_date,
                "return_date": return_date if return_date else None,
                "passengers": passengers_str,
                "seat_class": seat_type
            },
            "note": "Open this URL in your browser to search for flights on Google Flights"
        }

        return json.dumps(output_data, indent=2)

    except ValueError as e:
        return json.dumps({"error": {"message": f"Invalid date format. Use YYYY-MM-DD.", "type": "ValueError"}})
    except Exception as e:
        return json.dumps({"error": {"message": str(e), "type": type(e).__name__}})


# --- Run the server ---
if __name__ == "__main__":
    # Run the server using stdio transport
    mcp.run(transport='stdio')
