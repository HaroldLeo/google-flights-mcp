
#!/usr/bin/env python
import asyncio
import json
import datetime
import sys
import os
from typing import Any, Optional, Dict, List

# Import fast_flights from pip package
try:
    from fast_flights import FlightQuery, Passengers, get_flights, create_query
except ImportError as e:
    print(f"Error importing fast_flights: {e}", file=sys.stderr)
    print(f"Please install fast_flights: pip install fast-flights", file=sys.stderr)
    sys.exit(1)

# Import SerpApi for fallback (optional)
try:
    from serpapi import GoogleSearch
    SERPAPI_AVAILABLE = True
except ImportError:
    SERPAPI_AVAILABLE = False
    print("SerpApi not available. Install with: pip install google-search-results", file=sys.stderr)

from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("google-flights-comprehensive")

# --- SerpApi Configuration ---
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")
SERPAPI_ENABLED = SERPAPI_AVAILABLE and SERPAPI_API_KEY is not None

if SERPAPI_ENABLED:
    print(f"[SerpApi] Fallback enabled with API key", file=sys.stderr)
else:
    if not SERPAPI_AVAILABLE:
        print(f"[SerpApi] Not available - install google-search-results", file=sys.stderr)
    elif not SERPAPI_API_KEY:
        print(f"[SerpApi] API key not configured - set SERPAPI_API_KEY env var for fallback support", file=sys.stderr)

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

def log_info(tool_name: str, message: str):
    """Structured info logging for MCP tools."""
    print(f"[{tool_name}] {message}", file=sys.stderr)

def log_error(tool_name: str, error_type: str, message: str):
    """Structured error logging for MCP tools."""
    print(f"[{tool_name}] ERROR ({error_type}): {message}", file=sys.stderr)

def log_debug(tool_name: str, key: str, value: Any):
    """Structured debug logging for MCP tools."""
    print(f"[{tool_name}] DEBUG: {key} = {value}", file=sys.stderr)

def format_datetime(simple_datetime):
    """Convert SimpleDatetime object to ISO format string.

    Args:
        simple_datetime: SimpleDatetime object with date tuple (year, month, day) and time tuple (hour, minute)

    Returns:
        ISO formatted datetime string (YYYY-MM-DD HH:MM) or (YYYY-MM-DD) if time is missing
    """
    if not simple_datetime:
        return None
    try:
        year, month, day = simple_datetime.date
        # Handle cases where time might be missing or None
        time_attr = getattr(simple_datetime, 'time', None)
        if time_attr is not None and len(time_attr) >= 2:
            hour, minute = time_attr[0], time_attr[1]
            return f"{year:04d}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}"
        else:
            # Return date only if time is missing
            return f"{year:04d}-{month:02d}-{day:02d}"
    except (AttributeError, ValueError, TypeError) as e:
        # Last resort fallback - try to extract just the date
        try:
            if hasattr(simple_datetime, 'date'):
                year, month, day = simple_datetime.date
                return f"{year:04d}-{month:02d}-{day:02d}"
        except:
            pass
        return None

def format_duration(minutes):
    """Convert duration in minutes to human-readable format.

    Args:
        minutes: Duration in minutes (int)

    Returns:
        Formatted duration string (e.g., "2h 30m")
    """
    if not isinstance(minutes, int):
        return str(minutes)
    hours = minutes // 60
    mins = minutes % 60
    if hours > 0 and mins > 0:
        return f"{hours}h {mins}m"
    elif hours > 0:
        return f"{hours}h"
    else:
        return f"{mins}m"

def flight_to_dict(flight, compact=False, origin=None, destination=None):
    """Converts a Flight/Flights object to a dictionary with detailed flight information.

    Supports both fast-flights v2.2 and v3.0rc0 structures.

    Args:
        flight: Flight object (v2.2) or Flights object (v3.0rc0)
        compact: If True, return only essential fields (saves ~40% tokens)
        origin: Optional origin airport code for round-trip leg detection
        destination: Optional destination airport code for round-trip leg detection

    v2.2 Flight structure (simpler):
        - is_best: bool - If this is a recommended flight
        - name: str - Airline name
        - departure: time - Departure time
        - arrival: time - Arrival time
        - duration: int - Duration
        - stops: int - Number of stops
        - price: int - Price

    v3.0rc0 Flights structure (detailed):
        - type: str - Type of flight
        - price: int - Total price
        - airlines: list[str] - List of airline names
        - flights: list[SingleFlight] - List of flight segments
        - carbon: CarbonEmission - Carbon emission data
    """
    try:
        # Detect version by checking for 'flights' attribute (v3.0rc0) vs its absence (v2.2)
        has_segments = hasattr(flight, 'flights') and getattr(flight, 'flights', None)

        if has_segments:
            # v3.0rc0 structure - detailed segments
            return _flight_to_dict_v3(flight, compact, origin, destination)
        else:
            # v2.2 structure - simpler format
            return _flight_to_dict_v2(flight, compact)

    except Exception as e:
        # Fallback: return whatever we can extract
        log_error("flight_to_dict", type(e).__name__, f"Error converting flight: {str(e)}")
        return {
            "error": f"Failed to parse flight data: {str(e)}",
            "raw_data": str(flight)
        }


def _flight_to_dict_v2(flight, compact=False):
    """Handle fast-flights v2.2 Flight objects (simpler structure)."""
    try:
        price = getattr(flight, 'price', None)
        airline_name = getattr(flight, 'name', None)
        is_best = getattr(flight, 'is_best', False)
        departure = getattr(flight, 'departure', None)
        arrival = getattr(flight, 'arrival', None)
        duration = getattr(flight, 'duration', None)
        stops = getattr(flight, 'stops', None)

        # Format duration if it's a number
        if isinstance(duration, (int, float)):
            formatted_duration = format_duration(int(duration))
        else:
            formatted_duration = str(duration) if duration else None

        if compact:
            return {
                "price": price,
                "airlines": airline_name,
                "departure_time": str(departure) if departure else None,
                "arrival_time": str(arrival) if arrival else None,
                "duration": formatted_duration,
                "stops": stops,
                "is_best": is_best,
            }
        else:
            return {
                "price": price,
                "airlines": airline_name,
                "is_best": is_best,
                "departure_time": str(departure) if departure else None,
                "arrival_time": str(arrival) if arrival else None,
                "total_duration": formatted_duration,
                "stops": stops,
                "flight_type": "Unknown",  # v2.2 doesn't expose this
                "segments": [],  # v2.2 doesn't expose detailed segments
                "note": "Detailed segment information not available in fast-flights v2.2. Upgrade to v3.x for detailed segments."
            }
    except Exception as e:
        log_error("_flight_to_dict_v2", type(e).__name__, str(e))
        return {"error": f"Failed to parse v2.2 flight: {str(e)}"}


def _flight_to_dict_v3(flight, compact=False, origin=None, destination=None):
    """Handle fast-flights v3.0rc0 Flights objects (detailed structure)."""
    try:
        # Extract basic info
        price = getattr(flight, 'price', None)
        airlines = getattr(flight, 'airlines', [])
        airline_names = ', '.join(airlines) if airlines else None
        flight_segments = getattr(flight, 'flights', [])
        flight_type = getattr(flight, 'type', None)
        is_round_trip = flight_type and 'round' in flight_type.lower()

        # Calculate stops (number of segments - 1)
        num_stops = len(flight_segments) - 1 if flight_segments else 0

        # Get overall departure and arrival from first and last segments
        overall_departure = None
        overall_arrival = None
        total_duration_minutes = 0

        if flight_segments:
            first_segment = flight_segments[0]
            last_segment = flight_segments[-1]

            overall_departure = format_datetime(getattr(first_segment, 'departure', None))
            overall_arrival = format_datetime(getattr(last_segment, 'arrival', None))

            # Sum up all segment durations
            for segment in flight_segments:
                duration = getattr(segment, 'duration', 0)
                if isinstance(duration, int):
                    total_duration_minutes += duration

        total_duration = format_duration(total_duration_minutes) if total_duration_minutes > 0 else None

        # Get carbon emission data
        carbon_data = getattr(flight, 'carbon', None)
        carbon_emission = None
        if carbon_data:
            emission = getattr(carbon_data, 'emission', None)
            typical = getattr(carbon_data, 'typical_on_route', None)
            if emission is not None:
                carbon_emission = {
                    "emission_grams": emission,
                    "typical_on_route_grams": typical
                }

        if compact:
            # Compact mode: only essential fields
            return {
                "price": price,
                "airlines": airline_names,
                "departure_time": overall_departure,
                "arrival_time": overall_arrival,
                "duration": total_duration,
                "stops": num_stops,
            }
        else:
            # Full mode: detailed information
            # Build detailed segment information
            segments = []

            # For round-trips, detect the "turn-around" point to label outbound vs return
            turn_around_index = None
            if is_round_trip and len(flight_segments) >= 2 and destination:
                # Find where we reach the destination and start heading back
                for i, segment in enumerate(flight_segments):
                    to_airport = getattr(segment, 'to_airport', None)
                    to_code = getattr(to_airport, 'code', None) if to_airport else None

                    # Check if this segment arrives at the destination
                    if to_code and to_code.upper() == destination.upper():
                        turn_around_index = i + 1  # Next segment starts the return
                        break

            for i, segment in enumerate(flight_segments):
                from_airport = getattr(segment, 'from_airport', None)
                to_airport = getattr(segment, 'to_airport', None)

                # Determine leg type for round-trips
                leg_type = None
                if is_round_trip and turn_around_index is not None:
                    leg_type = "outbound" if i < turn_around_index else "return"

                segment_info = {
                    "segment_number": i + 1,
                    "from": {
                        "airport_code": getattr(from_airport, 'code', None),
                        "airport_name": getattr(from_airport, 'name', None),
                    } if from_airport else None,
                    "to": {
                        "airport_code": getattr(to_airport, 'code', None),
                        "airport_name": getattr(to_airport, 'name', None),
                    } if to_airport else None,
                    "departure": format_datetime(getattr(segment, 'departure', None)),
                    "arrival": format_datetime(getattr(segment, 'arrival', None)),
                    "duration": format_duration(getattr(segment, 'duration', 0)),
                    "plane_type": getattr(segment, 'plane_type', None),
                }

                # Add leg_type for round-trips
                if leg_type:
                    segment_info["leg"] = leg_type

                segments.append(segment_info)

            return {
                "price": price,
                "airlines": airline_names,
                "flight_type": flight_type,
                "departure_time": overall_departure,
                "arrival_time": overall_arrival,
                "total_duration": total_duration,
                "stops": num_stops,
                "segments": segments,
                "carbon_emissions": carbon_emission,
            }

    except Exception as e:
        # Fallback: return whatever we can extract
        log_error("flight_to_dict", type(e).__name__, f"Error converting flight: {str(e)}")
        return {
            "error": f"Failed to parse flight data: {str(e)}",
            "raw_data": str(flight)
        }

def parse_price(price):
    """Extracts integer price from a price value.

    Args:
        price: Price value (can be int, string like '$268', or None)

    Returns:
        Integer price or float('inf') if invalid
    """
    if price is None:
        return float('inf')
    if isinstance(price, int):
        return price
    if isinstance(price, str):
        try:
            return int(price.replace('$', '').replace(',', ''))
        except ValueError:
            return float('inf')
    return float('inf')

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


# --- SerpApi Integration Functions ---

def convert_seat_type_to_serpapi(seat_type: str) -> int:
    """Convert our seat_type string to SerpApi travel_class number.

    Args:
        seat_type: One of "economy", "premium_economy", "business", "first"

    Returns:
        SerpApi class number: 1=Economy, 2=Premium, 3=Business, 4=First
    """
    mapping = {
        "economy": 1,
        "premium_economy": 2,
        "business": 3,
        "first": 4
    }
    return mapping.get(seat_type.lower(), 1)


def get_flights_from_serpapi(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: Optional[str] = None,
    adults: int = 1,
    children: int = 0,
    infants_in_seat: int = 0,
    infants_on_lap: int = 0,
    seat_type: str = "economy",
    max_stops: Optional[int] = None,
    airlines: Optional[List[str]] = None
) -> Optional[Dict]:
    """Fetch flights from SerpApi Google Flights API.

    Args:
        origin: Origin airport code
        destination: Destination airport code
        departure_date: Departure date (YYYY-MM-DD)
        return_date: Optional return date for round-trips (YYYY-MM-DD)
        adults: Number of adults
        children: Number of children (2-11 years)
        infants_in_seat: Number of infants with seat (<2 years)
        infants_on_lap: Number of lap infants (<2 years)
        seat_type: Cabin class
        max_stops: Maximum number of stops (0, 1, or 2)
        airlines: List of airline codes to filter by

    Returns:
        SerpApi response dict or None if error
    """
    if not SERPAPI_ENABLED:
        return None

    try:
        # Build search parameters
        params = {
            "engine": "google_flights",
            "api_key": SERPAPI_API_KEY,
            "departure_id": origin,
            "arrival_id": destination,
            "outbound_date": departure_date,
            "currency": "USD",
            "hl": "en",
        }

        # Flight type
        if return_date:
            params["type"] = 1  # Round trip
            params["return_date"] = return_date
        else:
            params["type"] = 2  # One way

        # Travel class
        params["travel_class"] = convert_seat_type_to_serpapi(seat_type)

        # Passengers
        if adults > 1:
            params["adults"] = adults
        if children > 0:
            params["children"] = children
        if infants_in_seat > 0:
            params["infants_in_seat"] = infants_in_seat
        if infants_on_lap > 0:
            params["infants_on_lap"] = infants_on_lap

        # Filters
        if max_stops is not None:
            params["stops"] = max_stops

        if airlines and len(airlines) > 0:
            # SerpApi uses comma-separated airline codes
            params["include_airlines"] = ",".join(airlines)

        # Execute search
        search = GoogleSearch(params)
        results = search.get_dict()

        return results

    except Exception as e:
        log_error("SerpApi", type(e).__name__, str(e))
        return None


def normalize_serpapi_flight(flight_data: Dict, is_best: bool = False) -> Dict:
    """Convert SerpApi flight format to our standard format.

    Args:
        flight_data: Flight object from SerpApi response
        is_best: Whether this is from best_flights (vs other_flights)

    Returns:
        Normalized flight dict matching our flight_to_dict format
    """
    try:
        # Extract flights array (segments)
        segments = []
        raw_flights = flight_data.get("flights", [])

        for i, segment in enumerate(raw_flights):
            segment_info = {
                "segment_number": i + 1,
                "from": {
                    "airport_code": segment.get("departure_airport", {}).get("id"),
                    "airport_name": segment.get("departure_airport", {}).get("name"),
                },
                "to": {
                    "airport_code": segment.get("arrival_airport", {}).get("id"),
                    "airport_name": segment.get("arrival_airport", {}).get("name"),
                },
                "departure": segment.get("departure_airport", {}).get("time"),
                "arrival": segment.get("arrival_airport", {}).get("time"),
                "duration": f"{segment.get('duration', 0)}m",
                "plane_type": segment.get("airplane"),
                "airline": segment.get("airline"),
                "flight_number": segment.get("flight_number"),
            }
            segments.append(segment_info)

        # Calculate stops
        num_stops = len(segments) - 1 if segments else 0

        # Get overall times from first/last segment
        overall_departure = None
        overall_arrival = None
        if segments:
            overall_departure = segments[0]["departure"]
            overall_arrival = segments[-1]["arrival"]

        # Extract price
        price = flight_data.get("price")

        # Extract total duration
        total_duration_min = flight_data.get("total_duration", 0)
        total_duration = format_duration(total_duration_min) if total_duration_min else None

        # Extract airline(s)
        airline_names = ", ".join([s.get("airline", "") for s in raw_flights if s.get("airline")])

        # Extract carbon emissions if available
        carbon_emission = None
        carbon_data = flight_data.get("carbon_emissions")
        if carbon_data:
            carbon_emission = {
                "emission_grams": carbon_data.get("this_flight"),
                "typical_on_route_grams": carbon_data.get("typical_for_this_route"),
                "difference_percent": carbon_data.get("difference_percent"),
            }

        # Build result
        return {
            "price": price,
            "airlines": airline_names or None,
            "flight_type": flight_data.get("type"),
            "departure_time": overall_departure,
            "arrival_time": overall_arrival,
            "total_duration": total_duration,
            "stops": num_stops,
            "segments": segments,
            "carbon_emissions": carbon_emission,
            "layovers": flight_data.get("layovers", []),
            "source": "SerpApi",
            "is_best_flight": is_best,
        }

    except Exception as e:
        log_error("normalize_serpapi_flight", type(e).__name__, str(e))
        return {
            "error": f"Failed to normalize SerpApi flight: {str(e)}",
            "raw_data": str(flight_data)
        }


def convert_serpapi_response(serpapi_result: Dict) -> List[Dict]:
    """Convert full SerpApi response to list of normalized flights.

    Args:
        serpapi_result: Full response from SerpApi

    Returns:
        List of normalized flight dicts
    """
    flights = []

    # Process best_flights first
    best_flights = serpapi_result.get("best_flights", [])
    for flight in best_flights:
        normalized = normalize_serpapi_flight(flight, is_best=True)
        flights.append(normalized)

    # Then process other_flights
    other_flights = serpapi_result.get("other_flights", [])
    for flight in other_flights:
        normalized = normalize_serpapi_flight(flight, is_best=False)
        flights.append(normalized)

    return flights


def try_serpapi_fallback(
    tool_name: str,
    origin: str,
    destination: str,
    departure_date: str,
    return_date: Optional[str] = None,
    adults: int = 1,
    children: int = 0,
    infants_in_seat: int = 0,
    infants_on_lap: int = 0,
    seat_type: str = "economy",
    max_stops: Optional[int] = None,
    airlines: Optional[List[str]] = None,
    return_cheapest_only: bool = False,
    max_results: int = 10
) -> Optional[str]:
    """Try to fetch flights using SerpApi as a fallback.

    Returns JSON string if successful, None if failed.
    """
    if not SERPAPI_ENABLED:
        return None

    log_info(tool_name, "Attempting SerpApi fallback...")
    try:
        serpapi_result = get_flights_from_serpapi(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            return_date=return_date,
            adults=adults,
            children=children,
            infants_in_seat=infants_in_seat,
            infants_on_lap=infants_on_lap,
            seat_type=seat_type,
            max_stops=max_stops,
            airlines=airlines
        )

        if serpapi_result:
            flights = convert_serpapi_response(serpapi_result)
            if flights:
                log_info(tool_name, f"SerpApi fallback successful: {len(flights)} flights")

                # Process based on return_cheapest_only
                if return_cheapest_only and len(flights) > 0:
                    cheapest_flight = min(flights, key=lambda f: parse_price(f.get("price")))
                    processed_flights = [cheapest_flight]
                    result_key = "cheapest_flight"
                else:
                    flights_to_process = flights[:max_results] if max_results > 0 else flights
                    processed_flights = flights_to_process
                    result_key = "flights"

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
                    result_key: processed_flights,
                    "data_source": "SerpApi (fallback)",
                    "note": "Results from SerpApi due to fast-flights error"
                }

                # Add warning for round-trip searches
                if return_date:
                    output_data["round_trip_note"] = (
                        "⚠️  SerpApi fallback currently shows outbound flights only. "
                        "For complete round-trip options with both outbound and return flights, "
                        "the primary fast-flights method is recommended. "
                        "Alternatively, search two separate one-way flights for full control."
                    )

                if not return_cheapest_only and max_results > 0:
                    output_data["result_metadata"] = {
                        "total_found": len(flights),
                        "returned": len(processed_flights),
                        "truncated": len(flights) > max_results
                    }

                return json.dumps(output_data, indent=2)
    except Exception as fallback_error:
        log_error(tool_name, "SerpApi fallback", str(fallback_error))

    return None


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
        result["note"] = f"Showing first 100 of {len(airports)} airports."

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
        "error": f"Airport code '{code}' not found"
    })


# --- MCP Prompts ---

@mcp.prompt()
def find_best_deal() -> str:
    """Comprehensive search strategy to find the absolute cheapest flights."""
    return """I'll help you find the absolute best flight deal using a comprehensive search strategy.

**Search Strategy:**
1. Use `search_round_trips_in_date_range` to search all dates within your flexible window
   - Set `return_cheapest_only=true` for faster results
   - Try different stay durations (e.g., 3-7 days, 7-14 days)
2. If you have nearby airports, use `compare_nearby_airports` to check all combinations
   - Example: NYC has JFK, LGA, EWR; SF Bay has SFO, OAK, SJC
3. Compare results and identify the cheapest option
4. Use `generate_google_flights_url` to create a direct booking link

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
5. Find the cheapest weekend option with `search_round_trip_flights`

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
2. Search specific dates with `search_one_way_flights` or `search_round_trip_flights`
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
1. Focus on flight times that maximize productivity:
   - Early morning departures (6-8 AM) to arrive for business hours
   - Evening returns (6-9 PM) to maximize on-site time
   - Avoid red-eyes unless specifically requested
2. Prioritize direct flights using `search_one_way_flights` or `search_round_trip_flights`
   - Set `return_cheapest_only=false` to see multiple options by time
3. If dates are flexible, use `search_round_trips_in_date_range` with short windows (2-3 days)
4. For premium cabins, search with `seat_type="business"` or `seat_type="first"`
5. Compare nearby airports for better schedules, not just price
6. Generate booking link with `generate_google_flights_url`

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


@mcp.prompt()
def family_vacation() -> str:
    """Plan family-friendly flights with kids."""
    return """I'll help you find the perfect family-friendly flights for your vacation!

**Family Travel Search Strategy:**
1. Prioritize `search_direct_flights` to avoid complications with connections and kids
   - Direct flights are especially important with children to minimize travel stress
2. Filter for reasonable departure times using `filter_by_departure_time`
   - Avoid very early morning (before 8 AM) or late night departures
   - Morning or afternoon flights work best with kids' schedules
3. Use `search_round_trip_flights` or `search_round_trips_in_date_range` for family dates
   - School breaks, holidays, and summer vacations
4. Consider `compare_nearby_airports` if you have multiple options
   - Sometimes a slightly farther airport has better direct flight options
5. Account for all passengers: adults + children with proper age groups

**Family-Friendly Flight Priorities:**
- Direct flights preferred (avoids connection stress with kids)
- Reasonable departure times (not too early or too late)
- Adequate time for check-in and security (families need extra time)
- Aisle seats for easy bathroom access (mention in results)
- Consider flight duration - shorter is better with kids
- Book early for better seat selection

**What I need from you:**
- Origin and destination cities
- Travel dates or date flexibility (school breaks, etc.)
- Number of adults and children (with ages if relevant)
- Seat class preference
- Any specific needs (infant seats, lap infants, etc.)

**Result:** I'll find the most family-friendly flights with direct options prioritized, reasonable times, and booking links."""


@mcp.prompt()
def budget_backpacker() -> str:
    """Ultra-budget flight search with maximum flexibility."""
    return """I'll help you find the absolute cheapest flights for budget travel!

**Budget Travel Search Strategy:**
1. Use `search_round_trips_in_date_range` with wide date windows
   - Set `return_cheapest_only=true` for fastest results
   - Be flexible on dates - even a day can save significant money
2. Use `compare_nearby_airports` to check all area airports
   - Budget airlines often use secondary airports
   - Includes checking all NYC (JFK/LGA/EWR) or SF Bay (SFO/OAK/SJC) options
3. Use `search_flights_with_max_stops` with `max_stops=2`
   - Multiple stops are acceptable for budget travel
   - Can save 30-50% compared to direct flights
4. Filter by `filter_by_departure_time` for "red-eye" flights
   - Overnight flights are often cheaper
   - Saves a night of accommodation
5. Consider `compare_one_way_vs_roundtrip`
   - Mix and match airlines for best prices

**Budget Travel Priorities:**
- Price is the #1 priority
- Willing to accept multiple stops
- Flexible on departure times (including red-eyes)
- Flexible on dates (within a general window)
- Will consider longer travel times
- Secondary airports acceptable
- Economy class only

**Money-Saving Tips:**
- Fly mid-week (Tue/Wed/Thu) instead of weekends
- Book far in advance for international, 3-8 weeks for domestic
- Red-eye flights save money + accommodation
- One-way tickets sometimes cheaper than round-trip
- Clear browser cookies before booking (avoid price increases)

**What I need from you:**
- General origin and destination (I'll check all nearby airports)
- Approximate travel timeframe (month or season)
- Approximate trip length or date flexibility
- Absolute maximum budget if you have one

**Result:** I'll find the rock-bottom cheapest flights, even if it means red-eyes, multiple stops, and creative routing."""


@mcp.prompt()
def loyalty_program_optimizer() -> str:
    """Optimize flights for airline loyalty programs and miles."""
    return """I'll help you find flights that maximize your airline loyalty benefits!

**Loyalty Program Search Strategy:**
1. Use `search_flights_by_airline` with your preferred airlines or alliance
   - Star Alliance: `["STAR_ALLIANCE"]` - United, Lufthansa, Air Canada, etc.
   - SkyTeam: `["SKYTEAM"]` - Delta, Air France, KLM, etc.
   - Oneworld: `["ONEWORLD"]` - American, British Airways, Qantas, etc.
   - Specific airlines: `["UA", "AA", "DL"]` for United, American, Delta
2. Compare alliance options using multiple searches if you have status with multiple programs
3. Use `search_direct_flights` on your airline for maximum miles/points
   - Direct flights on your airline = full mileage credit
4. Check `search_round_trip_flights` for award availability patterns
5. Consider `compare_nearby_airports` to find airline hub airports
   - Example: United hub at EWR/IAD/ORD/DEN/SFO

**Loyalty Program Priorities:**
- Fly your preferred airline or alliance for miles/points
- Earn status-qualifying miles/segments
- Use airline lounges (priority with status)
- Better upgrade chances on your airline
- Alliance benefits (lounge access, priority boarding)
- Direct flights for full mileage credit
- Positioning flights to hubs for better availability

**Elite Status Optimization:**
- Book higher fare classes for bonus miles (Y, B, M vs. economy saver)
- Target specific airlines for status runs
- Connect through your airline's hubs for better upgrade chances
- Consider paid upgrades for status-qualifying dollars

**What I need from you:**
- Origin and destination
- Your airline loyalty programs (United Mileage Plus, AA AAdvantage, etc.)
- Your current elite status level if any
- Travel dates or flexibility
- Whether you're trying to earn status or maintain it
- Seat class preference (or using points/miles)

**Result:** I'll find flights on your preferred airline/alliance, show you the best mileage-earning options, and provide strategies to maximize your loyalty benefits.

NOTE: Now with fast-flights 3.0, airline filtering is native and more reliable. All searches show price context (low/typical/high) to help you decide if it's a good time to book!"""


@mcp.prompt()
def holiday_peak_travel() -> str:
    """Strategic flight search for peak holiday travel periods."""
    return """I'll help you navigate peak holiday travel and find the best options during busy seasons!

**Peak Travel Search Strategy:**
1. Use `get_travel_dates` to calculate exact holiday dates
2. Use `search_round_trips_in_date_range` to find the best days around holidays
   - Flying on the holiday itself is often cheaper
   - Check +/- 3 days around peak dates
3. Use `compare_nearby_airports` - secondary airports may have better availability
4. Use `search_direct_flights` if available (connections get more risky during holidays)
5. Book EARLY - peak travel sells out fast

**Peak Holiday Periods:**
- Thanksgiving: Wednesday before through Sunday after
- Christmas/New Year: Dec 20-Jan 3
- Spring Break: March-April (varies by region)
- Summer Travel: June-August
- Major US holidays: Memorial Day, July 4th, Labor Day

**Peak Travel Strategies:**
- **Book Early:** 2-3 months minimum for domestic, 4-6 months for international
- **Fly on the Holiday:** Dec 25, Thanksgiving Day, Jan 1 are cheaper
- **Red-Eyes Work:** Overnight flights on holidays have better availability
- **Avoid Peak Days:** Don't fly Wednesday before Thanksgiving or Sunday after
- **Secondary Airports:** More availability, fewer crowds
- **Direct Flights:** Worth the premium during holidays (weather delays common)
- **Travel Insurance:** Consider for expensive peak-season tickets

**What I need from you:**
- Which holiday or peak period you're traveling
- Origin and destination
- Your date flexibility (can you fly on the holiday itself?)
- Number of travelers
- Your budget tolerance (peak pricing is 2-3x normal)

**Result:** I'll find the best available flights during peak season, show you the cheapest days to fly, and provide booking strategies to avoid holiday travel stress."""


@mcp.prompt()
def long_haul_international() -> str:
    """Optimized search for long-haul international flights."""
    return """I'll help you find the best long-haul international flights prioritizing comfort and value!

**Long-Haul International Search Strategy:**
1. Use `search_round_trip_flights` or `search_round_trips_in_date_range` for your dates
2. Consider `search_flights_by_airline` for your preferred airlines
   - International carriers often have better long-haul comfort
3. Use `search_direct_flights` for routes over 6+ hours
   - Direct is worth the premium for very long flights
   - Reduces jet lag and travel time
4. Compare `seat_type="business"` or `seat_type="premium_economy"` for flights over 8 hours
   - Lie-flat business class for ultra long-haul (10+ hours)
5. Consider `compare_one_way_vs_roundtrip` for open-jaw itineraries
   - Fly into one city, out from another

**Long-Haul Flight Priorities:**
- **Comfort over price** for flights 8+ hours
- Direct flights strongly preferred (6+ hours)
- Premium economy or business class consideration
- Better airlines with good service reputation
- Convenient departure times (avoid late night arrivals)
- Good connection times if multi-stop (2-3 hours minimum)
- Consider lie-flat seats for overnight flights

**International Travel Tips:**
- **Gateway Airports:** Major hubs often have better direct international routes
  - US: JFK, LAX, SFO, ORD, IAD, ATL, EWR
  - Europe: LHR, CDG, AMS, FRA
  - Asia: NRT, HKG, SIN, ICN
- **Overnight Flights:** Book late evening departure, arrive morning destination time
- **Premium Cabins:** Consider for flights 8+ hours - worth the comfort
- **Airline Alliances:** Book through alliance partners for better pricing
- **Book Early:** International flights - book 2-6 months ahead
- **Shoulder Season:** Travel just before/after peak season for savings

**What I need from you:**
- Origin and destination countries/cities
- Travel dates or approximate timeframe
- Trip length
- Seat class preference (economy/premium economy/business/first)
- Number of travelers
- Any airline preferences or alliances

**Result:** I'll find the best international flights balancing price and comfort, with priority on direct flights for long-haul routes and premium cabin suggestions where appropriate."""


@mcp.prompt()
def stopover_explorer() -> str:
    """Find flights with interesting layover cities for mini-adventures."""
    return """I'll help you find flights with stopovers that turn layovers into adventures!

**Stopover Explorer Search Strategy:**
1. Use `get_multi_city_flights` to explicitly plan multi-city routes
   - Visit 2-3 cities in one trip
   - Example: NYC → Iceland (3 days) → London → NYC
2. Use `search_flights_with_max_stops` with `max_stops=1` or `max_stops=2`
   - Review layover cities in the results
3. Look for airlines offering free stopover programs:
   - **Iceland air:** Free Iceland stopover (KEF)
   - **TAP Portugal:** Free Lisbon/Porto stopover (LIS/OPO)
   - **Turkish Airlines:** Free Istanbul stopover (IST)
   - **Emirates:** Dubai stopover program (DXB)
   - **Singapore Airlines:** Singapore stopover (SIN)
4. Use `compare_nearby_airports` to find the best gateway for your desired stopover
5. Manually search specific routing if you know you want a stopover

**Popular Stopover Cities:**
- **Reykjavik, Iceland (KEF):** Perfect for EU-bound flights from US East Coast
- **Lisbon, Portugal (LIS):** TAP allows multi-day stopovers
- **Dubai, UAE (DXB):** Luxury stopover between Europe/US and Asia
- **Istanbul, Turkey (IST):** Bridge between Europe and Asia
- **Singapore (SIN):** Perfect stopover en route to Australia/Southeast Asia
- **Tokyo, Japan (NRT/HND):** Asia-Pacific gateway
- **Doha, Qatar (DOH):** Qatar Airways stopover program

**Stopover Strategy:**
- **Free Stopovers:** Some airlines allow extended stopovers at no extra cost
- **Visit Times:** 2-4 days is perfect for a city stopover
- **Hotel Packages:** Many airlines offer discounted hotel packages
- **Visa Requirements:** Check visa needs for stopover country
- **Luggage:** Confirm baggage policies for multi-day stopovers

**What I need from you:**
- Final origin and destination
- Desired stopover city (or I can suggest based on route)
- How long you want in stopover city (1-7 days)
- Total trip timeline
- Your interests (culture, food, nature, city life)

**Result:** I'll find flights with interesting stopover opportunities, show you multi-city routing options, and help you turn a connection into a mini-vacation!"""


@mcp.prompt()
def reliable_search_strategy() -> str:
    """Guide users on choosing the right fetch mode for reliability and handling scraping issues."""
    return """I'll help you choose the best flight search method for your needs and troubleshoot any issues!

## 🎯 Choose Your Fetch Mode

NOTE: The fast-flights 3.0 API has been simplified and no longer requires fetch_mode configuration.
## 🔧 Troubleshooting Guide

### Problem: "No flights found" or Empty Results
**Try:** `fetch_mode="force-fallback"` or `fetch_mode="local"`
**Why:** Standard scraping may have missed JavaScript-loaded data

### Problem: HTTP 401 Errors or Rate Limiting
**Try:** `fetch_mode="local"` or reduce search frequency
**Why:** Serverless Playwright has usage limits

### Problem: Searches Timing Out
**Try:** `fetch_mode="common"` for faster results, or reduce date ranges
**Why:** Complex searches take longer

### Problem: Intermittent Failures
**Try:** `fetch_mode="fallback"` (default) - it auto-retries
**Why:** Network issues or temporary Google Flights changes

## 💡 Pro Tips

1. **Start with default (fallback)** - it handles most cases
2. **Use "local" for batch searching** - install Playwright locally
3. **Add `return_cheapest_only=true`** - faster results, less data
4. **Reduce max_stops** - fewer options = faster searches
5. **Check price_tier in results** - know if it's a good deal!

## 📊 New Features (v3.0)

- **Price Context**: Every search now shows if prices are "low", "typical", or "high"
- **Native Airline Filtering**: Built into fast-flights 3.0, more reliable than before
- **Better Error Messages**: More helpful guidance when searches fail

**What's your issue? Let me help you find the best solution!**"""


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
    TOOL = "get_travel_dates"
    log_info(TOOL, f"Calculating dates: +{days_from_now} days, {trip_length} day trip")

    try:
        today = datetime.date.today()
        departure_date = today + datetime.timedelta(days=days_from_now)
        return_date = departure_date + datetime.timedelta(days=trip_length)

        log_info(TOOL, f"Suggested: {departure_date.strftime('%Y-%m-%d')} to {return_date.strftime('%Y-%m-%d')}")

        return json.dumps({
            "today": today.strftime('%Y-%m-%d'),
            "departure_date": departure_date.strftime('%Y-%m-%d'),
            "return_date": return_date.strftime('%Y-%m-%d'),
            "trip_length_days": trip_length,
            "days_until_departure": days_from_now
        }, indent=2)
    except Exception as e:
        log_error(TOOL, type(e).__name__, str(e))
        return json.dumps({"error": {"message": str(e), "type": type(e).__name__}})


# --- MCP Tool Implementations ---

@mcp.tool()
async def search_one_way_flights(
    origin: str,
    destination: str,
    date: str,
    adults: int = 1,
    children: int = 0,
    infants_in_seat: int = 0,
    infants_on_lap: int = 0,
    seat_type: str = "economy",
    return_cheapest_only: bool = False,
    max_results: int = 10,
    compact_mode: bool = False
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
    TOOL = "search_one_way_flights"
    log_info(TOOL, f"Searching {origin}→{destination} on {date} ({adults} adult(s), {seat_type})")

    try:
        # Validate date format
        datetime.datetime.strptime(date, '%Y-%m-%d')

        flights = [
            FlightQuery(date=date, from_airport=origin, to_airport=destination),
        ]
        passengers_info = Passengers(
            adults=adults,
            children=children,
            infants_in_seat=infants_in_seat,
            infants_on_lap=infants_on_lap
        )

        log_info(TOOL, "Fetching flights from Google Flights...")
        query = create_query(
            flights=flights,
            trip="one-way",
            seat=seat_type,
            passengers=passengers_info
        )

        # Generate booking URL for successful responses
        google_flights_url = f"https://www.google.com/travel/flights?tfs={query}&hl=&curr="

        result = get_flights(query)

        if result:
            log_info(TOOL, f"Found {len(result)} flight(s)")

            # Process flights based on the new parameter
            if return_cheapest_only:
                cheapest_flight = min(result, key=lambda f: parse_price(f.price))
                processed_flights = [flight_to_dict(cheapest_flight, compact=compact_mode)]
                result_key = "cheapest_flight" # Use a specific key for single result
            else:
                flights_to_process = result[:max_results] if max_results > 0 else result
                processed_flights = [flight_to_dict(f, compact=compact_mode) for f in flights_to_process]
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
                result_key: processed_flights,
                "booking_url": google_flights_url
            }
            # Add result metadata for transparency
            if not return_cheapest_only and max_results > 0:
                output_data["result_metadata"] = {
                    "total_found": len(result),
                    "returned": len(processed_flights),
                    "truncated": len(result) > max_results
                }

            return json.dumps(output_data, indent=2)
        else:
            return json.dumps({
                "message": f"No flights found for {origin} -> {destination} on {date}.",
                "search_parameters": { "origin": origin, "destination": destination, "date": date, "adults": adults, "seat_type": seat_type }
             })

    except ValueError as e:
         log_error(TOOL, "ValueError", f"Invalid date format: '{date}'. Use YYYY-MM-DD")
         error_payload = {"error": {"message": f"Invalid date format: '{date}'. Please use YYYY-MM-DD.", "type": "ValueError"}}
         return json.dumps(error_payload)
    except RuntimeError as e:
        error_msg = str(e)
        log_error(TOOL, "RuntimeError", error_msg)

        # Try SerpApi fallback
        fallback_result = try_serpapi_fallback(
            tool_name=TOOL,
            origin=origin,
            destination=destination,
            departure_date=date,
            return_date=None,
            adults=adults,
            children=children,
            infants_in_seat=infants_in_seat,
            infants_on_lap=infants_on_lap,
            seat_type=seat_type,
            return_cheapest_only=return_cheapest_only,
            max_results=max_results
        )
        if fallback_result:
            return fallback_result

        # Try to extract the Google Flights URL from the error
        google_flights_url = None
        if "https://www.google.com/travel/flights" in error_msg:
            import re
            url_match = re.search(r'(https://www\.google\.com/travel/flights[^\s]+)', error_msg)
            if url_match:
                google_flights_url = url_match.group(1)

        # Check if it's a "No flights found" error from fast-flights
        if "No flights found" in error_msg:
            response_data = {
                "message": "The scraper couldn't find flights, but you can view results directly on Google Flights.",
                "search_parameters": {
                    "origin": origin,
                    "destination": destination,
                    "date": date,
                    "adults": adults,
                    "children": children,
                    "infants_in_seat": infants_in_seat,
                    "infants_on_lap": infants_on_lap,
                    "seat_type": seat_type
                },
                "note": "One-way searches may not return results via scraping. Click the URL below to view flights in your browser.",
                "serpapi_note": "Configure SERPAPI_API_KEY to enable automatic fallback to SerpApi." if not SERPAPI_ENABLED else None
            }
            if google_flights_url:
                response_data["google_flights_url"] = google_flights_url
            return json.dumps(response_data)

        return json.dumps({"error": {"message": error_msg, "type": "RuntimeError"}})
    except Exception as e:
        import traceback
        error_msg = str(e)
        log_error(TOOL, type(e).__name__, error_msg)
        log_debug(TOOL, "traceback", traceback.format_exc())

        # Try SerpApi fallback
        fallback_result = try_serpapi_fallback(
            tool_name=TOOL,
            origin=origin,
            destination=destination,
            departure_date=date,
            return_date=None,
            adults=adults,
            children=children,
            infants_in_seat=infants_in_seat,
            infants_on_lap=infants_on_lap,
            seat_type=seat_type,
            return_cheapest_only=return_cheapest_only,
            max_results=max_results
        )
        if fallback_result:
            return fallback_result

        # Try to extract URL from any exception
        google_flights_url = None
        if "https://www.google.com/travel/flights" in error_msg:
            import re
            url_match = re.search(r'(https://www\.google\.com/travel/flights[^\s]+)', error_msg)
            if url_match:
                google_flights_url = url_match.group(1)

        response_data = {
            "error": {"message": error_msg, "type": type(e).__name__},
            "suggestion": "If you encounter issues, try searching with different parameters or check the Google Flights website directly.",
            "serpapi_note": "Configure SERPAPI_API_KEY to enable automatic fallback to SerpApi." if not SERPAPI_ENABLED else None
        }
        if google_flights_url:
            response_data["google_flights_url"] = google_flights_url
        return json.dumps(response_data)


@mcp.tool()
async def search_round_trip_flights(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: str,
    adults: int = 1,
    children: int = 0,
    infants_in_seat: int = 0,
    infants_on_lap: int = 0,
    seat_type: str = "economy",
    max_stops: int = 2,
    return_cheapest_only: bool = False,
    max_results: int = 10,
    compact_mode: bool = False
) -> str:
    """
    Fetches available round-trip flights for specific departure and return dates.
    Can optionally return only the cheapest flight found.

    💡 TIP: Default max_stops=2 provides more reliable scraping. For direct flights only,
    use search_direct_flights() with is_round_trip=True instead.

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
        max_stops: Maximum number of stops (0=direct, 1=one stop, 2=two stops, default: 2).
                   Lower values = more reliable scraping. Set higher if needed, but may reduce reliability.
        return_cheapest_only: If True, returns only the cheapest flight (default: False).

    Example Args:
        {"origin": "DEN", "destination": "LAX", "departure_date": "2025-08-01", "return_date": "2025-08-08"}
        {"origin": "DEN", "destination": "LAX", "departure_date": "2025-08-01", "return_date": "2025-08-08", "adults": 2, "children": 2}
        {"origin": "DEN", "destination": "LAX", "departure_date": "2025-08-01", "return_date": "2025-08-08", "max_stops": 0}
    """
    TOOL = "search_round_trip_flights"
    log_info(TOOL, f"Round-trip {origin}↔{destination} ({departure_date} to {return_date})")
    log_debug(TOOL, "passengers", f"{adults} adult(s), {children} child(ren)")
    log_debug(TOOL, "constraints", f"max_stops={max_stops}, seat={seat_type}")

    try:
        # Validate date formats
        datetime.datetime.strptime(departure_date, '%Y-%m-%d')
        datetime.datetime.strptime(return_date, '%Y-%m-%d')

        flights = [
            FlightQuery(date=departure_date, from_airport=origin, to_airport=destination),
            FlightQuery(date=return_date, from_airport=destination, to_airport=origin),
        ]
        passengers_info = Passengers(
            adults=adults,
            children=children,
            infants_in_seat=infants_in_seat,
            infants_on_lap=infants_on_lap
        )

        log_info(TOOL, "Fetching flights from Google Flights...")
        query = create_query(
            flights=flights,
            trip="round-trip",
            seat=seat_type,
            passengers=passengers_info,
            max_stops=max_stops
        )

        # Generate booking URL for successful responses
        google_flights_url = f"https://www.google.com/travel/flights?tfs={query}&hl=&curr="

        result = get_flights(query)

        if result:
            log_info(TOOL, f"Found {len(result)} round-trip option(s)")
            # Process flights based on the new parameter
            if return_cheapest_only:
                cheapest_flight = min(result, key=lambda f: parse_price(f.price))
                processed_flights = [flight_to_dict(cheapest_flight, compact=compact_mode, origin=origin, destination=destination)]
                result_key = "cheapest_round_trip_option" # Use a specific key for single result
            else:
                flights_to_process = result[:max_results] if max_results > 0 else result
                processed_flights = [flight_to_dict(f, compact=compact_mode, origin=origin, destination=destination) for f in flights_to_process]
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
                    "max_stops": max_stops,
                    "return_cheapest_only": return_cheapest_only
                },
                result_key: processed_flights,
                "booking_url": google_flights_url
            }
            return json.dumps(output_data, indent=2)
        else:
             return json.dumps({
                "message": f"No round trip flights found for {origin} <-> {destination} from {departure_date} to {return_date} with max {max_stops} stops.",
                 "search_parameters": { "origin": origin, "destination": destination, "departure_date": departure_date, "return_date": return_date, "adults": adults, "seat_type": seat_type, "max_stops": max_stops }
            })

    except ValueError as e:
         log_error(TOOL, "ValueError", "Invalid date format provided. Use YYYY-MM-DD")
         error_payload = {"error": {"message": f"Invalid date format provided. Use YYYY-MM-DD.", "type": "ValueError"}}
         return json.dumps(error_payload)
    except RuntimeError as e:
        error_msg = str(e)
        log_error(TOOL, "RuntimeError", error_msg)

        # Try SerpApi fallback
        fallback_result = try_serpapi_fallback(
            tool_name=TOOL,
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            return_date=return_date,
            adults=adults,
            children=children,
            infants_in_seat=infants_in_seat,
            infants_on_lap=infants_on_lap,
            seat_type=seat_type,
            max_stops=max_stops,
            return_cheapest_only=return_cheapest_only,
            max_results=max_results
        )
        if fallback_result:
            return fallback_result

        # Try to extract the Google Flights URL from the error
        # The fast-flights library often includes the URL in the error trace
        google_flights_url = None
        if "https://www.google.com/travel/flights" in error_msg:
            # Extract the URL from the error message
            import re
            url_match = re.search(r'(https://www\.google\.com/travel/flights[^\s]+)', error_msg)
            if url_match:
                google_flights_url = url_match.group(1)

        # Check if it's a "No flights found" error from fast-flights
        if "No flights found" in error_msg:
            response_data = {
                "message": "The scraper couldn't find flights, but you can view results directly on Google Flights.",
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
                    "max_stops": max_stops
                },
                "note": f"Round-trip searches with max {max_stops} stops may not return results via scraping. Try max_stops=0 or 1 for better reliability, or click the URL below to view flights in your browser.",
                "serpapi_note": "Configure SERPAPI_API_KEY to enable automatic fallback to SerpApi." if not SERPAPI_ENABLED else None
            }
            if google_flights_url:
                response_data["google_flights_url"] = google_flights_url
            return json.dumps(response_data)

        return json.dumps({"error": {"message": error_msg, "type": "RuntimeError"}})
    except Exception as e:
        import traceback
        error_msg = str(e)
        log_error(TOOL, type(e).__name__, error_msg)
        log_debug(TOOL, "traceback", traceback.format_exc())

        # Try SerpApi fallback
        fallback_result = try_serpapi_fallback(
            tool_name=TOOL,
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            return_date=return_date,
            adults=adults,
            children=children,
            infants_in_seat=infants_in_seat,
            infants_on_lap=infants_on_lap,
            seat_type=seat_type,
            max_stops=max_stops,
            return_cheapest_only=return_cheapest_only,
            max_results=max_results
        )
        if fallback_result:
            return fallback_result

        # Try to extract URL from any exception
        google_flights_url = None
        if "https://www.google.com/travel/flights" in error_msg:
            import re
            url_match = re.search(r'(https://www\.google\.com/travel/flights[^\s]+)', error_msg)
            if url_match:
                google_flights_url = url_match.group(1)

        response_data = {
            "error": {"message": error_msg, "type": type(e).__name__},
            "suggestion": "If you encounter issues, try searching with different parameters or check the Google Flights website directly.",
            "serpapi_note": "Configure SERPAPI_API_KEY to enable automatic fallback to SerpApi." if not SERPAPI_ENABLED else None
        }
        if google_flights_url:
            response_data["google_flights_url"] = google_flights_url
        return json.dumps(response_data)


@mcp.tool()
async def search_round_trips_in_date_range(
    origin: str,
    destination: str,
    start_date_str: str,
    end_date_str: str,
    min_stay_days: Optional[int] = None,
    max_stay_days: Optional[int] = None,
    adults: int = 1,
    seat_type: str = "economy",
    max_stops: int = 2,
    return_cheapest_only: bool = False,
    max_results: int = 10,
    offset: int = 0,
    limit: int = 20
) -> str:
    """
    Finds available round-trip flights within a specified date range.
    Can optionally return only the cheapest flight found for each date pair.

    ⚠️ RATE LIMIT WARNING: This function makes multiple Google Flights scraping requests.
    Each date pair combination = 1 request. The function is LIMITED to a MAXIMUM of 30
    requests to prevent rate limiting and IP blocking.

    Example request counts:
    - 7 day range with 5-7 day stays: ~10-15 requests (Safe)
    - 14 day range with no limits: ~105 requests (WILL BE REJECTED)
    - 30 day range: ~465 requests (WILL BE REJECTED)

    💡 TIP: Use min_stay_days and max_stay_days to reduce combinations.
    Set return_cheapest_only=true for faster results.

    Args:
        origin: Origin airport code (e.g., "DEN").
        destination: Destination airport code (e.g., "LAX").
        start_date_str: Start date of the search range (YYYY-MM-DD format).
        end_date_str: End date of the search range (YYYY-MM-DD format).
        min_stay_days: Minimum number of days for the stay (optional).
        max_stay_days: Maximum number of days for the stay (optional).
        adults: Number of adult passengers (default: 1).
        seat_type: Fare class (e.g., "economy", "business", default: "economy").
        max_stops: Maximum number of stops (0=direct, 1=one stop, 2=two stops, default: 2).
        return_cheapest_only: If True, returns only the cheapest flight for each date pair (default: False).
        max_results: Maximum number of results to return (default: 10). Set to 0 or -1 for unlimited.
        offset: Number of results to skip (for pagination, default: 0).
        compact_mode: If True, return only essential fields (saves ~40% tokens, default: False).
        limit: Maximum number of date pairs to process (for pagination, default: 20).

    Example Args:
        {"origin": "JFK", "destination": "MIA", "start_date_str": "2025-09-10", "end_date_str": "2025-09-20", "min_stay_days": 5}
        {"origin": "JFK", "destination": "MIA", "start_date_str": "2025-09-10", "end_date_str": "2025-09-20", "min_stay_days": 5, "return_cheapest_only": true}
    """
    TOOL = "search_round_trips_in_date_range"
    MAX_DATE_COMBINATIONS = 30

    search_mode = "cheapest per pair" if return_cheapest_only else "all flights"
    log_info(TOOL, f"Date range search {origin}↔{destination} ({start_date_str} to {end_date_str})")
    log_debug(TOOL, "mode", search_mode)
    log_debug(TOOL, "stay_range", f"{min_stay_days or 'any'}-{max_stay_days or 'any'} days")

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

    # Apply pagination to date pairs
    total_date_pairs = len(date_pairs_to_check)
    paginated_pairs = date_pairs_to_check[offset:offset + limit] if limit > 0 else date_pairs_to_check[offset:]

    # Enforce rate limit protection on paginated set
    if len(paginated_pairs) > MAX_DATE_COMBINATIONS:
        return json.dumps({
            "error": {
                "message": f"Too many date combinations ({len(paginated_pairs)} requested after pagination, maximum {MAX_DATE_COMBINATIONS} allowed). "
                          f"This would make {len(paginated_pairs)} scraping requests and hit rate limits. "
                          f"Please use smaller limit parameter or narrow your date range.",
                "type": "RateLimitError",
                "requested_combinations": len(paginated_pairs),
                "maximum_allowed": MAX_DATE_COMBINATIONS,
                "total_combinations_available": total_date_pairs,
                "suggestion": "Try: (1) Use limit=20 or less, (2) Shorter date range, (3) Add min_stay_days/max_stay_days"
            }
        })

    log_info(TOOL, f"Checking {len(paginated_pairs)} date combination(s) (of {total_date_pairs} total, offset={offset}, limit={limit})...")
    count = 0

    # Update date_pairs_to_check to use paginated version
    date_pairs_to_check = paginated_pairs

    for depart_date, return_date in date_pairs_to_check:
        count += 1
        if count % 10 == 0:
            log_info(TOOL, f"Progress: {count}/{total_combinations} - {depart_date.strftime('%Y-%m-%d')}→{return_date.strftime('%Y-%m-%d')}")

        try:
            flights = [
                FlightQuery(date=depart_date.strftime('%Y-%m-%d'), from_airport=origin, to_airport=destination),
                FlightQuery(date=return_date.strftime('%Y-%m-%d'), from_airport=destination, to_airport=origin),
            ]
            passengers_info = Passengers(adults=adults)

            query = create_query(flights=flights, trip="round-trip", seat=seat_type, passengers=passengers_info, max_stops=max_stops)

            # Generate booking URL for this date pair
            date_pair_url = f"https://www.google.com/travel/flights?tfs={query}&hl=&curr="

            result = get_flights(query)

            # Collect results based on mode
            if result:
                if return_cheapest_only:
                    # Find and store only the cheapest for this pair
                    cheapest_flight_for_pair = min(result, key=lambda f: parse_price(f.price))
                    results_data.append({
                        "departure_date": depart_date.strftime('%Y-%m-%d'),
                        "return_date": return_date.strftime('%Y-%m-%d'),
                        "cheapest_flight": flight_to_dict(cheapest_flight_for_pair), # Store single cheapest
                        "booking_url": date_pair_url
                    })
                else:
                    # Store all flights for this pair
                    flights_list = [flight_to_dict(f) for f in result]
                    results_data.append({
                        "departure_date": depart_date.strftime('%Y-%m-%d'),
                        "return_date": return_date.strftime('%Y-%m-%d'),
                        "flights": flights_list, # Store list of all flights
                        "booking_url": date_pair_url
                    })
            # else: # Optional: Log if no flights were found for a specific pair
                # print(f"MCP Tool: No flights found for {depart_date.strftime('%Y-%m-%d')} -> {return_date.strftime('%Y-%m-%d')}", file=sys.stderr)

        except Exception as e:
            date_str = f"{depart_date.strftime('%Y-%m-%d')}→{return_date.strftime('%Y-%m-%d')}"
            log_error(TOOL, type(e).__name__, f"{date_str}: {str(e)[:100]}")
            err_msg = f"Error fetching {date_str}: {type(e).__name__}"
            if err_msg not in error_messages:
                 error_messages.append(err_msg)

    log_info(TOOL, f"Complete: Found {len(results_data)} results, {len(error_messages)} errors")

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
                "max_stops": max_stops,
                "return_cheapest_only": return_cheapest_only # Include parameter in output
            },
            results_key: results_data, # Use dynamic key for results
            "errors_encountered": error_messages if error_messages else None,
            "pagination": {
                "offset": offset,
                "limit": limit,
                "returned": len(results_data),
                "total_date_pairs": total_date_pairs,
                "has_more": offset + limit < total_date_pairs
            }
        }
        return json.dumps(output_data, indent=2)
    else:
        # This case should ideally not be reached if the loop runs and finds nothing,
        # but kept as a fallback.
        return json.dumps({
            "message": f"No flights found and no errors encountered for {origin} -> {destination} in the range {start_date_str} to {end_date_str}.",
            "search_parameters": {
                 "origin": origin, "destination": destination, "start_date": start_date_str, "end_date": end_date_str,
                 "min_stay_days": min_stay_days, "max_stay_days": max_stay_days, "adults": adults, "seat_type": seat_type, "max_stops": max_stops
            },
            "errors_encountered": error_messages if error_messages else None
        })


@mcp.tool()
async def get_multi_city_flights(
    flight_segments: str,
    adults: int = 1,
    seat_type: str = "economy",
    return_cheapest_only: bool = False,
    max_results: int = 10,
    compact_mode: bool = False
) -> str:
    """
    Fetches multi-city/multi-stop itineraries for complex trip planning.

    ⚠️  IMPORTANT: Multi-city flight scraping is not fully supported by the underlying fast-flights
    library. This function will generate a valid Google Flights URL with your search parameters,
    but may not be able to parse the results. If parsing fails, you'll receive a direct link to
    view the flights on Google Flights.

    💡 RECOMMENDATION FOR AI AGENTS: Instead of using this function, consider using the
    get_one_way_flights() function multiple times (once for each leg of the journey) and
    combining the results. This approach is more reliable and provides detailed flight
    information for each segment, which you can then present together as a complete itinerary.

    Args:
        flight_segments: JSON string of flight segments. Each segment should have "date", "from", and "to" fields.
                        Example: '[{"date": "2025-07-01", "from": "SFO", "to": "NYC"}, {"date": "2025-07-05", "from": "NYC", "to": "MIA"}, {"date": "2025-07-10", "from": "MIA", "to": "SFO"}]'
        adults: Number of adult passengers (default: 1).
        seat_type: Fare class (e.g., "economy", "business", default: "economy").
        return_cheapest_only: If True, returns only the cheapest option (default: False).

    Example Args:
        {"flight_segments": '[{"date": "2025-07-01", "from": "SFO", "to": "NYC"}, {"date": "2025-07-05", "from": "NYC", "to": "MIA"}]'}
    """
    TOOL = "get_multi_city_flights"

    try:
        # Parse the flight segments JSON
        segments = json.loads(flight_segments)

        if not segments or not isinstance(segments, list):
            log_error(TOOL, "ValueError", "flight_segments must be a non-empty JSON array")
            return json.dumps({"error": {"message": "flight_segments must be a non-empty JSON array", "type": "ValueError"}})

        if len(segments) < 2:
            log_error(TOOL, "ValueError", f"Multi-city requires ≥2 segments, got {len(segments)}")
            return json.dumps({"error": {"message": "Multi-city trips require at least 2 flight segments", "type": "ValueError"}})

        # Build route description
        route = " → ".join([f"{s['from']}" for s in segments] + [segments[-1]['to']])
        log_info(TOOL, f"Multi-city route: {route} ({len(segments)} segments)")
        log_debug(TOOL, "constraints", f"adults={adults}, seat={seat_type}")

        # Validate and build flight data
        flights = []
        for i, segment in enumerate(segments):
            if not all(k in segment for k in ["date", "from", "to"]):
                log_error(TOOL, "ValueError", f"Segment {i} missing required fields")
                return json.dumps({"error": {"message": f"Segment {i} missing required fields (date, from, to)", "type": "ValueError"}})

            # Validate date format
            try:
                datetime.datetime.strptime(segment["date"], '%Y-%m-%d')
            except ValueError:
                log_error(TOOL, "ValueError", f"Segment {i} invalid date: {segment['date']}")
                return json.dumps({"error": {"message": f"Invalid date format in segment {i}: '{segment['date']}'. Use YYYY-MM-DD.", "type": "ValueError"}})

            flights.append(
                FlightQuery(date=segment["date"], from_airport=segment["from"], to_airport=segment["to"])
            )

        passengers_info = Passengers(adults=adults)

        log_info(TOOL, "Fetching flights from Google Flights...")
        query = create_query(
            flights=flights,
            trip="multi-city",
            seat=seat_type,
            passengers=passengers_info
        )

        # Extract URL for fallback (multi-city parsing often fails in fast-flights)
        google_flights_url = f"https://www.google.com/travel/flights?tfs={query}&hl=&curr="

        result = get_flights(query)

        if result:
            log_info(TOOL, f"Found {len(result)} multi-city option(s)")
            if return_cheapest_only:
                cheapest_flight = min(result, key=lambda f: parse_price(f.price))
                processed_flights = [flight_to_dict(cheapest_flight, compact=compact_mode)]
                result_key = "cheapest_multi_city_option"
            else:
                flights_to_process = result[:max_results] if max_results > 0 else result
                processed_flights = [flight_to_dict(f, compact=compact_mode) for f in flights_to_process]
                result_key = "multi_city_options"

            output_data = {
                "search_parameters": {
                    "segments": segments,
                    "adults": adults,
                    "seat_type": seat_type,
                    "return_cheapest_only": return_cheapest_only
                },
                result_key: processed_flights,
                "booking_url": google_flights_url
            }
            return json.dumps(output_data, indent=2)
        else:
            return json.dumps({
                "message": "No multi-city flights found for the specified route.",
                "search_parameters": {"segments": segments, "adults": adults, "seat_type": seat_type}
            })

    except json.JSONDecodeError as e:
        log_error(TOOL, "JSONDecodeError", f"Invalid JSON in flight_segments: {str(e)}")
        return json.dumps({"error": {"message": f"Invalid JSON in flight_segments: {str(e)}", "type": "JSONDecodeError"}})
    except RuntimeError as e:
        error_msg = str(e)
        log_error(TOOL, "RuntimeError", error_msg)

        # Try to extract the Google Flights URL from the error
        # The fast-flights library often includes the URL in the error trace
        google_flights_url = None
        if "https://www.google.com/travel/flights" in error_msg:
            # Extract the URL from the error message
            import re
            url_match = re.search(r'(https://www\.google\.com/travel/flights[^\s]+)', error_msg)
            if url_match:
                google_flights_url = url_match.group(1)

        # Check if it's a "No flights found" error from fast-flights
        if "No flights found" in error_msg:
            response_data = {
                "message": "The scraper couldn't find flights, but you can view results directly on Google Flights.",
                "search_parameters": {"segments": segments, "adults": adults, "seat_type": seat_type},
                "note": "Multi-city searches may not return results via scraping. Click the URL below to view flights in your browser.",
                "google_flights_url": google_flights_url
            }
            return json.dumps(response_data)

        return json.dumps({"error": {"message": error_msg, "type": "RuntimeError"}, "google_flights_url": google_flights_url})
    except IndexError as e:
        # IndexError occurs when fast-flights can't parse multi-city results
        # This is a known limitation - multi-city is not fully supported by the library
        error_msg = str(e)
        log_error(TOOL, "IndexError", f"Multi-city parsing failed: {error_msg}")
        log_info(TOOL, "Attempting fallback: searching each segment individually")

        # FALLBACK: Try searching each segment as a separate one-way flight
        try:
            segment_results = []
            all_segments_successful = True

            for i, segment in enumerate(segments):
                try:
                    log_info(TOOL, f"Searching segment {i+1}/{len(segments)}: {segment['from']}→{segment['to']} on {segment['date']}")

                    # Create query for this individual segment
                    segment_flight = [FlightQuery(
                        date=segment["date"],
                        from_airport=segment["from"],
                        to_airport=segment["to"]
                    )]
                    passengers_info = Passengers(adults=adults)

                    segment_query = create_query(
                        flights=segment_flight,
                        trip="one-way",
                        seat=seat_type,
                        passengers=passengers_info
                    )

                    segment_url = f"https://www.google.com/travel/flights?tfs={segment_query}&hl=&curr="
                    segment_flights = get_flights(segment_query)

                    if segment_flights:
                        log_info(TOOL, f"Found {len(segment_flights)} flight(s) for segment {i+1}")

                        # Process based on return_cheapest_only
                        if return_cheapest_only:
                            cheapest = min(segment_flights, key=lambda f: parse_price(f.price))
                            processed = [flight_to_dict(cheapest, compact=compact_mode)]
                        else:
                            flights_to_process = segment_flights[:max_results] if max_results > 0 else segment_flights
                            processed = [flight_to_dict(f, compact=compact_mode) for f in flights_to_process]

                        segment_results.append({
                            "segment_number": i + 1,
                            "route": f"{segment['from']} → {segment['to']}",
                            "date": segment["date"],
                            "flights": processed,
                            "booking_url": segment_url
                        })
                    else:
                        log_info(TOOL, f"No flights found for segment {i+1}")
                        segment_results.append({
                            "segment_number": i + 1,
                            "route": f"{segment['from']} → {segment['to']}",
                            "date": segment["date"],
                            "message": "No flights found for this segment",
                            "booking_url": segment_url
                        })
                        all_segments_successful = False

                except Exception as seg_error:
                    log_error(TOOL, type(seg_error).__name__, f"Segment {i+1} search failed: {str(seg_error)}")
                    segment_results.append({
                        "segment_number": i + 1,
                        "route": f"{segment['from']} → {segment['to']}",
                        "date": segment["date"],
                        "error": str(seg_error)
                    })
                    all_segments_successful = False

            # If we got at least some results, return them
            if segment_results:
                log_info(TOOL, f"Fallback successful: retrieved {len(segment_results)} segment(s)")

                response_data = {
                    "message": "Multi-city search was split into individual one-way segments",
                    "note": "Since multi-city parsing is not supported, each leg of your journey was searched separately. You can book these flights individually or use the combined URL below to view all segments together on Google Flights.",
                    "search_parameters": {
                        "segments": segments,
                        "adults": adults,
                        "seat_type": seat_type
                    },
                    "segments": segment_results,
                    "combined_booking_url": google_flights_url
                }

                if not all_segments_successful:
                    response_data["warning"] = "Some segments could not be retrieved. Check individual segment details above."

                return json.dumps(response_data, indent=2)

        except Exception as fallback_error:
            log_error(TOOL, type(fallback_error).__name__, f"Fallback also failed: {str(fallback_error)}")

        # If fallback also failed, return the original error response
        log_info(TOOL, "Multi-city scraping not fully supported by fast-flights library")
        response_data = {
            "message": "Multi-city flight scraping is not fully supported by the underlying library.",
            "google_flights_url": google_flights_url,
            "search_parameters": {
                "segments": segments,
                "adults": adults,
                "seat_type": seat_type
            },
            "note": "Please click the URL above to view multi-city flights directly on Google Flights. The URL has been generated with your search parameters.",
            "technical_details": {
                "error_type": "IndexError",
                "reason": "The fast-flights library can generate multi-city search URLs but cannot parse the results due to differences in page structure."
            }
        }
        return json.dumps(response_data, indent=2)
    except Exception as e:
        import traceback
        error_msg = str(e)
        log_error(TOOL, type(e).__name__, error_msg)
        log_debug(TOOL, "traceback", traceback.format_exc())

        # URL already extracted earlier - use it
        response_data = {
            "error": {"message": error_msg, "type": type(e).__name__},
            "suggestion": "If you encounter issues, try searching with different parameters or check the Google Flights website directly.",
            "google_flights_url": google_flights_url
        }
        return json.dumps(response_data)

@mcp.tool()
async def search_direct_flights(
    origin: str,
    destination: str,
    date: str,
    is_round_trip: bool = False,
    return_date: Optional[str] = None,
    adults: int = 1,
    children: int = 0,
    infants_in_seat: int = 0,
    infants_on_lap: int = 0,
    seat_type: str = "economy",
    return_cheapest_only: bool = False,
    max_results: int = 10,
    compact_mode: bool = False
) -> str:
    """
    Search for direct flights only (no stops). Supports both one-way and round-trip.

    Args:
        origin: Origin airport code (e.g., "SFO").
        destination: Destination airport code (e.g., "JFK").
        date: Departure date (YYYY-MM-DD format).
        is_round_trip: If True, search round-trip flights (default: False).
        return_date: Return date for round-trips (YYYY-MM-DD format, required if is_round_trip=True).
        adults: Number of adult passengers (default: 1).
        children: Number of children (2-11 years, default: 0).
        infants_in_seat: Number of infants in seat (under 2 years, default: 0).
        infants_on_lap: Number of infants on lap (under 2 years, default: 0).
        seat_type: Fare class - economy/premium_economy/business/first (default: "economy").
        return_cheapest_only: If True, returns only the cheapest flight (default: False).

    Example Args:
        {"origin": "SFO", "destination": "JFK", "date": "2025-07-20"}
        {"origin": "SFO", "destination": "JFK", "date": "2025-07-20", "is_round_trip": true, "return_date": "2025-07-27"}
    """
    TOOL = "search_direct_flights"

    try:
        # Validate date format
        datetime.datetime.strptime(date, '%Y-%m-%d')

        if is_round_trip:
            if not return_date:
                log_error(TOOL, "ValueError", "return_date required for round-trip")
                return json.dumps({"error": {"message": "return_date is required when is_round_trip=True", "type": "ValueError"}})
            datetime.datetime.strptime(return_date, '%Y-%m-%d')

            log_info(TOOL, f"Direct round-trip {origin}↔{destination} ({date} to {return_date})")

            # Workaround: fast-flights with max_stops=0 doesn't return complete round-trips
            # Search each leg separately and combine results
            log_debug(TOOL, "workaround", "Searching outbound and return legs separately")

            passengers_info = Passengers(
                adults=adults,
                children=children,
                infants_in_seat=infants_in_seat,
                infants_on_lap=infants_on_lap
            )

            # Search outbound direct flights
            log_info(TOOL, "Fetching outbound direct flights...")
            outbound_query = create_query(
                flights=[FlightQuery(date=date, from_airport=origin, to_airport=destination)],
                trip="one-way",
                seat=seat_type,
                passengers=passengers_info,
                max_stops=0
            )
            outbound_flights = get_flights(outbound_query)

            # Search return direct flights
            log_info(TOOL, "Fetching return direct flights...")
            return_query = create_query(
                flights=[FlightQuery(date=return_date, from_airport=destination, to_airport=origin)],
                trip="one-way",
                seat=seat_type,
                passengers=passengers_info,
                max_stops=0
            )
            return_flights = get_flights(return_query)

            if not outbound_flights:
                return json.dumps({
                    "message": f"No direct outbound flights found for {origin} → {destination} on {date}.",
                    "search_parameters": {"origin": origin, "destination": destination, "date": date, "max_stops": 0}
                })

            if not return_flights:
                return json.dumps({
                    "message": f"No direct return flights found for {destination} → {origin} on {return_date}.",
                    "search_parameters": {"origin": destination, "destination": origin, "date": return_date, "max_stops": 0}
                })

            # Generate booking URL for round-trip
            round_trip_query = create_query(
                flights=[
                    FlightQuery(date=date, from_airport=origin, to_airport=destination),
                    FlightQuery(date=return_date, from_airport=destination, to_airport=origin),
                ],
                trip="round-trip",
                seat=seat_type,
                passengers=passengers_info,
                max_stops=0
            )
            google_flights_url = f"https://www.google.com/travel/flights?tfs={round_trip_query}&hl=&curr="

            # Combine outbound and return into complete round-trip packages
            log_info(TOOL, f"Combining {len(outbound_flights)} outbound × {len(return_flights)} return = {len(outbound_flights) * len(return_flights)} combinations")

            result = []
            for outbound in outbound_flights:
                for return_flight in return_flights:
                    # Create combined round-trip package
                    combined = {
                        "outbound": outbound,
                        "return": return_flight,
                        "total_price": parse_price(getattr(outbound, 'price', 0)) + parse_price(getattr(return_flight, 'price', 0)),
                    }
                    result.append(combined)

            # Sort by total price
            result.sort(key=lambda x: x["total_price"])

            # Process combined results
            if return_cheapest_only and result:
                result = [result[0]]
            elif max_results > 0:
                result = result[:max_results]

            # Convert to output format
            processed_flights = []
            for combo in result:
                outbound_dict = flight_to_dict(combo["outbound"], compact=compact_mode, origin=origin, destination=destination)
                return_dict = flight_to_dict(combo["return"], compact=compact_mode, origin=destination, destination=origin)

                # Extract segments from both legs
                outbound_segments = outbound_dict.get("segments", [])
                return_segments = return_dict.get("segments", [])

                # Label segments
                for seg in outbound_segments:
                    seg["leg"] = "outbound"
                for seg in return_segments:
                    seg["leg"] = "return"
                    seg["segment_number"] += len(outbound_segments)  # Renumber return segments

                # Combine into single flight package
                combined_flight = {
                    "price": combo["total_price"],
                    "outbound_airlines": outbound_dict.get("airlines"),
                    "return_airlines": return_dict.get("airlines"),
                    "flight_type": "Round trip",
                    "outbound_departure": outbound_dict.get("departure_time"),
                    "outbound_arrival": outbound_dict.get("arrival_time"),
                    "return_departure": return_dict.get("departure_time"),
                    "return_arrival": return_dict.get("arrival_time"),
                    "total_duration": None,  # Not meaningful for round-trips with days between
                    "stops": 0,  # Direct flights only
                    "segments": outbound_segments + return_segments,
                }

                if not compact_mode:
                    combined_flight["outbound_carbon_emissions"] = outbound_dict.get("carbon_emissions")
                    combined_flight["return_carbon_emissions"] = return_dict.get("carbon_emissions")

                processed_flights.append(combined_flight)

            output_data = {
                "search_parameters": {
                    "origin": origin,
                    "destination": destination,
                    "date": date,
                    "is_round_trip": is_round_trip,
                    "return_date": return_date,
                    "adults": adults,
                    "children": children,
                    "seat_type": seat_type,
                    "max_stops": 0,
                    "return_cheapest_only": return_cheapest_only
                },
                "direct_flights" if not return_cheapest_only else "cheapest_direct_flight": processed_flights,
                "booking_url": google_flights_url,
                "note": "Round-trip results show combined outbound + return direct flight packages."
            }
            return json.dumps(output_data, indent=2)

        else:
            log_info(TOOL, f"Direct one-way {origin}→{destination} on {date}")
            flights = [
                FlightQuery(date=date, from_airport=origin, to_airport=destination),
            ]
            trip_type = "one-way"

            log_debug(TOOL, "constraints", f"max_stops=0 (direct only), seat={seat_type}, adults={adults}")

            passengers_info = Passengers(
                adults=adults,
                children=children,
                infants_in_seat=infants_in_seat,
                infants_on_lap=infants_on_lap
            )

            log_info(TOOL, "Fetching direct flights from Google Flights...")
            query = create_query(
                flights=flights,
                trip=trip_type,
                seat=seat_type,
                passengers=passengers_info,
                max_stops=0  # Direct flights only
            )

            # Generate booking URL for successful responses
            google_flights_url = f"https://www.google.com/travel/flights?tfs={query}&hl=&curr="

            result = get_flights(query)

        if result:
            log_info(TOOL, f"Found {len(result)} direct flight(s)")
            if return_cheapest_only:
                cheapest_flight = min(result, key=lambda f: parse_price(f.price))
                processed_flights = [flight_to_dict(cheapest_flight, compact=compact_mode, origin=origin, destination=destination)]
                result_key = "cheapest_direct_flight"
            else:
                flights_to_process = result[:max_results] if max_results > 0 else result
                processed_flights = [flight_to_dict(f, compact=compact_mode, origin=origin, destination=destination) for f in flights_to_process]
                result_key = "direct_flights"

            output_data = {
                "search_parameters": {
                    "origin": origin,
                    "destination": destination,
                    "date": date,
                    "is_round_trip": is_round_trip,
                    "return_date": return_date if is_round_trip else None,
                    "adults": adults,
                    "children": children,
                    "seat_type": seat_type,
                    "max_stops": 0,
                    "return_cheapest_only": return_cheapest_only
                },
                result_key: processed_flights,
                "booking_url": google_flights_url
            }
            return json.dumps(output_data, indent=2)
        else:
            return json.dumps({
                "message": f"No direct flights found for {origin} -> {destination} on {date}.",
                "search_parameters": {"origin": origin, "destination": destination, "date": date, "max_stops": 0}
            })

    except ValueError as e:
        log_error(TOOL, "ValueError", "Invalid date format. Use YYYY-MM-DD")
        return json.dumps({"error": {"message": f"Invalid date format. Use YYYY-MM-DD.", "type": "ValueError"}})
    except RuntimeError as e:
        error_msg = str(e)
        log_error(TOOL, "RuntimeError", error_msg)

        # Try to extract the Google Flights URL from the error
        google_flights_url = None
        if "https://www.google.com/travel/flights" in error_msg:
            import re
            url_match = re.search(r'(https://www\.google\.com/travel/flights[^\s]+)', error_msg)
            if url_match:
                google_flights_url = url_match.group(1)

        # Check if it's a "No flights found" error from fast-flights
        if "No flights found" in error_msg:
            response_data = {
                "message": "The scraper couldn't find direct flights, but you can view results directly on Google Flights.",
                "search_parameters": {
                    "origin": origin,
                    "destination": destination,
                    "date": date,
                    "is_round_trip": is_round_trip,
                    "return_date": return_date if is_round_trip else None,
                    "max_stops": 0
                },
                "note": "Direct flight searches may not return results via scraping. Click the URL below to view flights in your browser."
            }
            if google_flights_url:
                response_data["google_flights_url"] = google_flights_url
            return json.dumps(response_data)

        return json.dumps({"error": {"message": error_msg, "type": "RuntimeError"}})
    except Exception as e:
        import traceback
        error_msg = str(e)
        log_error(TOOL, type(e).__name__, error_msg)
        log_debug(TOOL, "traceback", traceback.format_exc())

        # Try to extract URL from any exception
        google_flights_url = None
        if "https://www.google.com/travel/flights" in error_msg:
            import re
            url_match = re.search(r'(https://www\.google\.com/travel/flights[^\s]+)', error_msg)
            if url_match:
                google_flights_url = url_match.group(1)

        response_data = {
            "error": {"message": error_msg, "type": type(e).__name__},
            "suggestion": "If you encounter issues, try searching with different parameters or check the Google Flights website directly."
        }
        if google_flights_url:
            response_data["google_flights_url"] = google_flights_url
        return json.dumps(response_data)


@mcp.tool()
async def search_flights_by_airline(
    origin: str,
    destination: str,
    date: str,
    airlines: str,
    is_round_trip: bool = False,
    return_date: Optional[str] = None,
    adults: int = 1,
    seat_type: str = "economy",
    max_stops: int = 2,
    return_cheapest_only: bool = False,
    max_results: int = 10,
    compact_mode: bool = False
) -> str:
    """
    Search flights filtered by specific airlines or alliances.

    💡 TIP: Default max_stops=2 provides more reliable scraping for round-trip searches.

    Args:
        origin: Origin airport code (e.g., "SFO").
        destination: Destination airport code (e.g., "JFK").
        date: Departure date (YYYY-MM-DD format).
        airlines: Airline code(s) or alliance name. Can be either:
                 - Single airline: "UA" or "AA" or "DL" (2-letter codes)
                 - Multiple airlines: ["UA", "AA", "DL"] (JSON array)
                 - Alliance: "STAR_ALLIANCE" or "SKYTEAM" or "ONEWORLD"
        is_round_trip: If True, search round-trip flights (default: False).
        return_date: Return date for round-trips (YYYY-MM-DD format).
        adults: Number of adult passengers (default: 1).
        seat_type: Fare class (default: "economy").
        max_stops: Maximum number of stops (0=direct, 1=one stop, 2=two stops, default: 2).
        return_cheapest_only: If True, returns only the cheapest flight (default: False).

    Example Args:
        {"origin": "SFO", "destination": "TYO", "date": "2026-02-20", "airlines": "UA"}
        {"origin": "SFO", "destination": "JFK", "date": "2025-07-20", "airlines": "[\"UA\", \"AA\"]"}
        {"origin": "SFO", "destination": "JFK", "date": "2025-07-20", "airlines": "STAR_ALLIANCE", "max_stops": 0}
    """
    TOOL = "search_flights_by_airline"

    try:
        # Parse airlines - accept both plain string "UA" or JSON array "[\"UA\"]"
        airlines_list = None
        try:
            airlines_list = json.loads(airlines)
            if not isinstance(airlines_list, list):
                airlines_list = [airlines_list]
        except json.JSONDecodeError:
            airlines_list = [airlines]

        if not airlines_list:
            return json.dumps({"error": {"message": "airlines parameter cannot be empty", "type": "ValueError"}})

        trip_desc = f"{'round-trip' if is_round_trip else 'one-way'}"
        log_info(TOOL, f"{trip_desc.capitalize()} {origin}→{destination} on {airlines_list}")
        log_debug(TOOL, "constraints", f"max_stops={max_stops}, seat={seat_type}, adults={adults}")

        # Validate dates
        datetime.datetime.strptime(date, '%Y-%m-%d')

        if is_round_trip:
            if not return_date:
                return json.dumps({"error": {"message": "return_date is required when is_round_trip=True", "type": "ValueError"}})
            datetime.datetime.strptime(return_date, '%Y-%m-%d')
            log_debug(TOOL, "dates", f"{date} to {return_date}")

            flights = [
                FlightQuery(date=date, from_airport=origin, to_airport=destination, airlines=airlines_list),
                FlightQuery(date=return_date, from_airport=destination, to_airport=origin, airlines=airlines_list),
            ]
            trip_type = "round-trip"
        else:
            log_debug(TOOL, "date", date)
            flights = [
                FlightQuery(date=date, from_airport=origin, to_airport=destination, airlines=airlines_list),
            ]
            trip_type = "one-way"

        passengers_info = Passengers(adults=adults)

        log_info(TOOL, "Fetching flights from Google Flights...")
        query = create_query(
            flights=flights,
            trip=trip_type,
            seat=seat_type,
            passengers=passengers_info,
            max_stops=max_stops
        )

        # Generate booking URL for successful responses
        google_flights_url = f"https://www.google.com/travel/flights?tfs={query}&hl=&curr="

        result = get_flights(query)

        if result:
            log_info(TOOL, f"Found {len(result)} flight(s)")
            if return_cheapest_only:
                cheapest_flight = min(result, key=lambda f: parse_price(f.price))
                processed_flights = [flight_to_dict(cheapest_flight, compact=compact_mode)]
                result_key = "cheapest_flight_by_airline"
            else:
                flights_to_process = result[:max_results] if max_results > 0 else result
                processed_flights = [flight_to_dict(f, compact=compact_mode) for f in flights_to_process]
                result_key = "flights_by_airline"

            output_data = {
                "search_parameters": {
                    "origin": origin,
                    "destination": destination,
                    "date": date,
                    "airlines": airlines_list,
                    "is_round_trip": is_round_trip,
                    "return_date": return_date if is_round_trip else None,
                    "adults": adults,
                    "seat_type": seat_type,
                    "max_stops": max_stops,
                    "return_cheapest_only": return_cheapest_only
                },
                result_key: processed_flights,
                "booking_url": google_flights_url
            }
            return json.dumps(output_data, indent=2)
        else:
            return json.dumps({
                "message": f"No flights found for specified airlines on {date} with max {max_stops} stops.",
                "search_parameters": {"origin": origin, "destination": destination, "date": date, "airlines": airlines_list, "max_stops": max_stops}
            })

    except ValueError as e:
        log_error(TOOL, "ValueError", "Invalid date format. Use YYYY-MM-DD")
        return json.dumps({"error": {"message": f"Invalid date format. Use YYYY-MM-DD.", "type": "ValueError"}})
    except RuntimeError as e:
        error_msg = str(e)
        log_error(TOOL, "RuntimeError", error_msg)

        # Try to extract the Google Flights URL from the error
        google_flights_url = None
        if "https://www.google.com/travel/flights" in error_msg:
            import re
            url_match = re.search(r'(https://www\.google\.com/travel/flights[^\s]+)', error_msg)
            if url_match:
                google_flights_url = url_match.group(1)

        # Check if it's a "No flights found" error from fast-flights
        if "No flights found" in error_msg:
            try:
                airlines_list = json.loads(airlines)
            except:
                airlines_list = []
            response_data = {
                "message": "The scraper couldn't find flights for the specified airlines, but you can view results directly on Google Flights.",
                "search_parameters": {
                    "origin": origin,
                    "destination": destination,
                    "date": date,
                    "airlines": airlines_list,
                    "is_round_trip": is_round_trip,
                    "return_date": return_date if is_round_trip else None,
                    "max_stops": max_stops
                },
                "note": f"Airline-filtered searches with max {max_stops} stops may not return results via scraping. Try max_stops=0 or 1 for better reliability, or click the URL below to view flights in your browser."
            }
            if google_flights_url:
                response_data["google_flights_url"] = google_flights_url
            return json.dumps(response_data)

        return json.dumps({"error": {"message": error_msg, "type": "RuntimeError"}})
    except Exception as e:
        import traceback
        error_msg = str(e)
        log_error(TOOL, type(e).__name__, error_msg)
        log_debug(TOOL, "traceback", traceback.format_exc())

        # Try to extract URL from any exception
        google_flights_url = None
        if "https://www.google.com/travel/flights" in error_msg:
            import re
            url_match = re.search(r'(https://www\.google\.com/travel/flights[^\s]+)', error_msg)
            if url_match:
                google_flights_url = url_match.group(1)

        response_data = {"error": {"message": f"{type(e).__name__}: {error_msg}", "type": type(e).__name__}}
        if google_flights_url:
            response_data["google_flights_url"] = google_flights_url
        return json.dumps(response_data)


@mcp.tool()
async def search_flights_with_max_stops(
    origin: str,
    destination: str,
    date: str,
    max_stops: int,
    is_round_trip: bool = False,
    return_date: Optional[str] = None,
    adults: int = 1,
    seat_type: str = "economy",
    return_cheapest_only: bool = False,
    max_results: int = 10,
    compact_mode: bool = False
) -> str:
    """
    Search flights with a maximum number of stops (0=direct, 1=one stop, 2=two stops).

    Args:
        origin: Origin airport code (e.g., "SFO").
        destination: Destination airport code (e.g., "JFK").
        date: Departure date (YYYY-MM-DD format).
        max_stops: Maximum number of stops (0, 1, or 2).
        is_round_trip: If True, search round-trip flights (default: False).
        return_date: Return date for round-trips (YYYY-MM-DD format).
        adults: Number of adult passengers (default: 1).
        seat_type: Fare class (default: "economy").
        return_cheapest_only: If True, returns only the cheapest flight (default: False).

    Example Args:
        {"origin": "SFO", "destination": "JFK", "date": "2025-07-20", "max_stops": 1}
        {"origin": "SFO", "destination": "JFK", "date": "2025-07-20", "max_stops": 0, "is_round_trip": true, "return_date": "2025-07-27"}
    """
    TOOL = "search_flights_with_max_stops"

    try:
        # Validate max_stops
        if max_stops not in [0, 1, 2]:
            log_error(TOOL, "ValueError", f"Invalid max_stops: {max_stops} (must be 0, 1, or 2)")
            return json.dumps({"error": {"message": "max_stops must be 0, 1, or 2", "type": "ValueError"}})

        # Validate dates
        datetime.datetime.strptime(date, '%Y-%m-%d')

        if is_round_trip:
            if not return_date:
                log_error(TOOL, "ValueError", "return_date required for round-trip")
                return json.dumps({"error": {"message": "return_date is required when is_round_trip=True", "type": "ValueError"}})
            datetime.datetime.strptime(return_date, '%Y-%m-%d')

            log_info(TOOL, f"Round-trip {origin}↔{destination} with ≤{max_stops} stops ({date} to {return_date})")
            flights = [
                FlightQuery(date=date, from_airport=origin, to_airport=destination),
                FlightQuery(date=return_date, from_airport=destination, to_airport=origin),
            ]
            trip_type = "round-trip"
        else:
            log_info(TOOL, f"One-way {origin}→{destination} with ≤{max_stops} stops on {date}")
            flights = [
                FlightQuery(date=date, from_airport=origin, to_airport=destination),
            ]
            trip_type = "one-way"

        passengers_info = Passengers(adults=adults)

        log_info(TOOL, "Fetching flights from Google Flights...")
        query = create_query(
            flights=flights,
            trip=trip_type,
            seat=seat_type,
            passengers=passengers_info,
            max_stops=max_stops
        )

        # Generate booking URL for successful responses
        google_flights_url = f"https://www.google.com/travel/flights?tfs={query}&hl=&curr="

        result = get_flights(query)

        if result:
            log_info(TOOL, f"Found {len(result)} flight(s)")
            if return_cheapest_only:
                cheapest_flight = min(result, key=lambda f: parse_price(f.price))
                processed_flights = [flight_to_dict(cheapest_flight, compact=compact_mode)]
                result_key = "cheapest_flight_with_max_stops"
            else:
                flights_to_process = result[:max_results] if max_results > 0 else result
                processed_flights = [flight_to_dict(f, compact=compact_mode) for f in flights_to_process]
                result_key = "flights_with_max_stops"

            output_data = {
                "search_parameters": {
                    "origin": origin,
                    "destination": destination,
                    "date": date,
                    "max_stops": max_stops,
                    "is_round_trip": is_round_trip,
                    "return_date": return_date if is_round_trip else None,
                    "adults": adults,
                    "seat_type": seat_type,
                    "return_cheapest_only": return_cheapest_only
                },
                result_key: processed_flights,
                "booking_url": google_flights_url
            }
            return json.dumps(output_data, indent=2)
        else:
            return json.dumps({
                "message": f"No flights found with max {max_stops} stops on {date}.",
                "search_parameters": {"origin": origin, "destination": destination, "date": date, "max_stops": max_stops}
            })

    except ValueError as e:
        log_error(TOOL, "ValueError", "Invalid date format. Use YYYY-MM-DD")
        return json.dumps({"error": {"message": f"Invalid date format. Use YYYY-MM-DD.", "type": "ValueError"}})
    except RuntimeError as e:
        error_msg = str(e)
        log_error(TOOL, "RuntimeError", error_msg)

        # Try to extract the Google Flights URL from the error
        google_flights_url = None
        if "https://www.google.com/travel/flights" in error_msg:
            import re
            url_match = re.search(r'(https://www\.google\.com/travel/flights[^\s]+)', error_msg)
            if url_match:
                google_flights_url = url_match.group(1)

        # Check if it's a "No flights found" error from fast-flights
        if "No flights found" in error_msg:
            response_data = {
                "message": "The scraper couldn't find flights with the specified stop criteria, but you can view results directly on Google Flights.",
                "search_parameters": {
                    "origin": origin,
                    "destination": destination,
                    "date": date,
                    "max_stops": max_stops,
                    "is_round_trip": is_round_trip,
                    "return_date": return_date if is_round_trip else None
                },
                "note": "Max-stops searches may not return results via scraping. Click the URL below to view flights in your browser."
            }
            if google_flights_url:
                response_data["google_flights_url"] = google_flights_url
            return json.dumps(response_data)

        return json.dumps({"error": {"message": error_msg, "type": "RuntimeError"}})
    except Exception as e:
        import traceback
        error_msg = str(e)
        log_error(TOOL, type(e).__name__, error_msg)
        log_debug(TOOL, "traceback", traceback.format_exc())

        # Try to extract URL from any exception
        google_flights_url = None
        if "https://www.google.com/travel/flights" in error_msg:
            import re
            url_match = re.search(r'(https://www\.google\.com/travel/flights[^\s]+)', error_msg)
            if url_match:
                google_flights_url = url_match.group(1)

        response_data = {
            "error": {"message": error_msg, "type": type(e).__name__},
            "suggestion": "If you encounter issues, try searching with different parameters or check the Google Flights website directly."
        }
        if google_flights_url:
            response_data["google_flights_url"] = google_flights_url
        return json.dumps(response_data)

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
    TOOL = "generate_google_flights_url"

    try:
        trip_type = "round-trip" if return_date else "one-way"
        log_info(TOOL, f"Generating {trip_type} URL: {origin}→{destination}")

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

        log_info(TOOL, f"URL generated successfully")

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
        log_error(TOOL, "ValueError", "Invalid date format. Use YYYY-MM-DD")
        return json.dumps({"error": {"message": f"Invalid date format. Use YYYY-MM-DD.", "type": "ValueError"}})
    except Exception as e:
        import traceback
        log_error(TOOL, type(e).__name__, str(e))
        log_debug(TOOL, "traceback", traceback.format_exc())
        return json.dumps({"error": {"message": str(e), "type": type(e).__name__}})


# --- Run the server ---
def main():
    """Main entry point for the MCP server."""
    mcp.run(transport='stdio')


if __name__ == "__main__":
    main()
