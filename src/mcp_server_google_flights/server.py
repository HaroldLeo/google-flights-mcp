
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

**Result:** I'll find flights on your preferred airline/alliance, show you the best mileage-earning options, and provide strategies to maximize your loyalty benefits."""


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
async def search_one_way_flights(
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
    except RuntimeError as e:
        error_msg = str(e)
        print(f"MCP Tool RuntimeError in search_one_way_flights: {error_msg}", file=sys.stderr)

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
                "note": "One-way searches may not return results via scraping. Click the URL below to view flights in your browser."
            }
            if google_flights_url:
                response_data["google_flights_url"] = google_flights_url
            return json.dumps(response_data)

        return json.dumps({"error": {"message": error_msg, "type": "RuntimeError"}})
    except Exception as e:
        error_msg = str(e)
        print(f"MCP Tool Error in search_one_way_flights: {error_msg}", file=sys.stderr)

        # Try to extract URL from any exception
        google_flights_url = None
        if "https://www.google.com/travel/flights" in error_msg:
            import re
            url_match = re.search(r'(https://www\.google\.com/travel/flights[^\s]+)', error_msg)
            if url_match:
                google_flights_url = url_match.group(1)

        response_data = {"error": {"message": error_msg, "type": type(e).__name__}}
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
    return_cheapest_only: bool = False
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
            max_stops=max_stops
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
                    "max_stops": max_stops,
                    "return_cheapest_only": return_cheapest_only
                },
                result_key: processed_flights
            }
            return json.dumps(output_data, indent=2)
        else:
             return json.dumps({
                "message": f"No round trip flights found for {origin} <-> {destination} from {departure_date} to {return_date} with max {max_stops} stops.",
                 "search_parameters": { "origin": origin, "destination": destination, "departure_date": departure_date, "return_date": return_date, "adults": adults, "seat_type": seat_type, "max_stops": max_stops }
            })

    except ValueError as e:
         # Return structured error
         error_payload = {"error": {"message": f"Invalid date format provided. Use YYYY-MM-DD.", "type": "ValueError"}}
         return json.dumps(error_payload)
    except RuntimeError as e:
        error_msg = str(e)
        print(f"MCP Tool RuntimeError in search_round_trip_flights: {error_msg}", file=sys.stderr)

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
                "note": f"Round-trip searches with max {max_stops} stops may not return results via scraping. Try max_stops=0 or 1 for better reliability, or click the URL below to view flights in your browser."
            }
            if google_flights_url:
                response_data["google_flights_url"] = google_flights_url
            return json.dumps(response_data)

        return json.dumps({"error": {"message": error_msg, "type": "RuntimeError"}})
    except Exception as e:
        error_msg = str(e)
        print(f"MCP Tool Error in search_round_trip_flights: {error_msg}", file=sys.stderr)

        # Try to extract URL from any exception
        google_flights_url = None
        if "https://www.google.com/travel/flights" in error_msg:
            import re
            url_match = re.search(r'(https://www\.google\.com/travel/flights[^\s]+)', error_msg)
            if url_match:
                google_flights_url = url_match.group(1)

        response_data = {"error": {"message": error_msg, "type": type(e).__name__}}
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
    return_cheapest_only: bool = False
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
        return_cheapest_only: If True, returns only the cheapest flight for each date pair (default: False).

    Example Args:
        {"origin": "JFK", "destination": "MIA", "start_date_str": "2025-09-10", "end_date_str": "2025-09-20", "min_stay_days": 5}
        {"origin": "JFK", "destination": "MIA", "start_date_str": "2025-09-10", "end_date_str": "2025-09-20", "min_stay_days": 5, "return_cheapest_only": true}
    """
    # Rate limit protection
    MAX_DATE_COMBINATIONS = 30
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

    # Enforce rate limit protection
    if total_combinations > MAX_DATE_COMBINATIONS:
        return json.dumps({
            "error": {
                "message": f"Too many date combinations ({total_combinations} requested, maximum {MAX_DATE_COMBINATIONS} allowed). "
                          f"This would make {total_combinations} scraping requests and hit rate limits. "
                          f"Please narrow your date range or add min_stay_days/max_stay_days filters.",
                "type": "RateLimitError",
                "requested_combinations": total_combinations,
                "maximum_allowed": MAX_DATE_COMBINATIONS,
                "suggestion": "Try: (1) Shorter date range, (2) Add min_stay_days/max_stay_days, (3) Split into multiple smaller searches"
            }
        })

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
    except RuntimeError as e:
        error_msg = str(e)
        print(f"MCP Tool RuntimeError in get_multi_city_flights: {error_msg}", file=sys.stderr)

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
                "note": "Multi-city searches may not return results via scraping. Click the URL below to view flights in your browser."
            }
            if google_flights_url:
                response_data["google_flights_url"] = google_flights_url
            return json.dumps(response_data)

        return json.dumps({"error": {"message": error_msg, "type": "RuntimeError"}})
    except Exception as e:
        error_msg = str(e)
        print(f"MCP Tool Error in get_multi_city_flights: {error_msg}", file=sys.stderr)

        # Try to extract URL from any exception
        google_flights_url = None
        if "https://www.google.com/travel/flights" in error_msg:
            import re
            url_match = re.search(r'(https://www\.google\.com/travel/flights[^\s]+)', error_msg)
            if url_match:
                google_flights_url = url_match.group(1)

        response_data = {"error": {"message": error_msg, "type": type(e).__name__}}
        if google_flights_url:
            response_data["google_flights_url"] = google_flights_url
        return json.dumps(response_data)


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

    ⚠️ RATE LIMIT WARNING: This function makes multiple Google Flights scraping requests.
    Each origin-destination combination = 1 request. LIMITED to MAXIMUM of 12 requests
    (e.g., 3 origins × 4 destinations, or 2 origins × 6 destinations).

    Example request counts:
    - 2 origins × 2 destinations: 4 requests (Safe)
    - 3 origins × 3 destinations: 9 requests (Safe)
    - 4 origins × 4 destinations: 16 requests (WILL BE REJECTED)
    - 5 origins × 5 destinations: 25 requests (WILL BE REJECTED)

    💡 TIP: Limit to 2-3 airports per list for best results.

    Args:
        origin_airports: Origin airport code(s). Can be either:
                        - Single airport: "SFO"
                        - Multiple airports: ["SFO", "OAK", "SJC"] (JSON array)
        destination_airports: Destination airport code(s). Can be either:
                             - Single airport: "JFK"
                             - Multiple airports: ["JFK", "EWR", "LGA"] (JSON array)
        date: The specific date to search (YYYY-MM-DD format).
        adults: Number of adult passengers (default: 1).
        seat_type: Fare class (default: "economy").

    Example Args:
        {"origin_airports": "SFO", "destination_airports": "JFK", "date": "2025-07-20"}
        {"origin_airports": '["SFO", "OAK"]', "destination_airports": '["JFK", "EWR"]', "date": "2025-07-20"}
    """
    # Rate limit protection
    MAX_AIRPORT_COMBINATIONS = 12
    print(f"MCP Tool: Comparing flights across multiple airports for {date}...", file=sys.stderr)
    try:
        # Parse airport arrays - accept both plain strings or JSON arrays
        # Parse origins
        try:
            origins = json.loads(origin_airports)
            if not isinstance(origins, list):
                origins = [origins]
        except json.JSONDecodeError:
            # Treat as plain string
            origins = [origin_airports]

        # Parse destinations
        try:
            destinations = json.loads(destination_airports)
            if not isinstance(destinations, list):
                destinations = [destinations]
        except json.JSONDecodeError:
            # Treat as plain string
            destinations = [destination_airports]

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

        # Enforce rate limit protection
        if total_combinations > MAX_AIRPORT_COMBINATIONS:
            return json.dumps({
                "error": {
                    "message": f"Too many airport combinations ({total_combinations} requested, maximum {MAX_AIRPORT_COMBINATIONS} allowed). "
                              f"This would make {total_combinations} scraping requests and hit rate limits. "
                              f"Please reduce the number of airports in your lists.",
                    "type": "RateLimitError",
                    "requested_combinations": total_combinations,
                    "maximum_allowed": MAX_AIRPORT_COMBINATIONS,
                    "origins_count": len(origins),
                    "destinations_count": len(destinations),
                    "suggestion": "Try: (1) Limit to 2-3 airports per list, (2) Split into multiple smaller searches"
                }
            })

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
    return_cheapest_only: bool = False
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
    print(f"MCP Tool: Searching direct flights {origin}->{destination} for {date}...", file=sys.stderr)
    try:
        # Validate date format
        datetime.datetime.strptime(date, '%Y-%m-%d')

        if is_round_trip:
            if not return_date:
                return json.dumps({"error": {"message": "return_date is required when is_round_trip=True", "type": "ValueError"}})
            datetime.datetime.strptime(return_date, '%Y-%m-%d')

            flight_data = [
                FlightData(date=date, from_airport=origin, to_airport=destination),
                FlightData(date=return_date, from_airport=destination, to_airport=origin),
            ]
            trip_type = "round-trip"
        else:
            flight_data = [
                FlightData(date=date, from_airport=origin, to_airport=destination),
            ]
            trip_type = "one-way"

        passengers_info = Passengers(
            adults=adults,
            children=children,
            infants_in_seat=infants_in_seat,
            infants_on_lap=infants_on_lap
        )

        result = get_flights(
            flight_data=flight_data,
            trip=trip_type,
            seat=seat_type,
            passengers=passengers_info,
            max_stops=0  # Direct flights only
        )

        if result and result.flights:
            if return_cheapest_only:
                cheapest_flight = min(result.flights, key=lambda f: parse_price(f.price))
                processed_flights = [flight_to_dict(cheapest_flight)]
                result_key = "cheapest_direct_flight"
            else:
                processed_flights = [flight_to_dict(f) for f in result.flights]
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
                result_key: processed_flights
            }
            return json.dumps(output_data, indent=2)
        else:
            return json.dumps({
                "message": f"No direct flights found for {origin} -> {destination} on {date}.",
                "search_parameters": {"origin": origin, "destination": destination, "date": date, "max_stops": 0}
            })

    except ValueError as e:
        return json.dumps({"error": {"message": f"Invalid date format. Use YYYY-MM-DD.", "type": "ValueError"}})
    except RuntimeError as e:
        error_msg = str(e)
        print(f"MCP Tool RuntimeError in search_direct_flights: {error_msg}", file=sys.stderr)

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
        error_msg = str(e)
        print(f"MCP Tool Error in search_direct_flights: {error_msg}", file=sys.stderr)

        # Try to extract URL from any exception
        google_flights_url = None
        if "https://www.google.com/travel/flights" in error_msg:
            import re
            url_match = re.search(r'(https://www\.google\.com/travel/flights[^\s]+)', error_msg)
            if url_match:
                google_flights_url = url_match.group(1)

        response_data = {"error": {"message": error_msg, "type": type(e).__name__}}
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
    return_cheapest_only: bool = False
) -> str:
    """
    Search flights filtered by specific airlines or alliances.

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
        return_cheapest_only: If True, returns only the cheapest flight (default: False).

    Example Args:
        {"origin": "SFO", "destination": "TYO", "date": "2026-02-20", "airlines": "UA"}
        {"origin": "SFO", "destination": "JFK", "date": "2025-07-20", "airlines": "[\"UA\", \"AA\"]"}
        {"origin": "SFO", "destination": "JFK", "date": "2025-07-20", "airlines": "STAR_ALLIANCE"}
    """
    print(f"MCP Tool: Searching flights by airline {origin}->{destination}...", file=sys.stderr)
    try:
        # Parse airlines - accept both plain string "UA" or JSON array "[\"UA\"]"
        airlines_list = None
        try:
            # First try parsing as JSON array
            airlines_list = json.loads(airlines)
            if not isinstance(airlines_list, list):
                # If it parsed but isn't a list, wrap it
                airlines_list = [airlines_list]
        except json.JSONDecodeError:
            # If JSON parsing fails, treat it as a plain string and wrap it in a list
            airlines_list = [airlines]

        if not airlines_list:
            return json.dumps({"error": {"message": "airlines parameter cannot be empty", "type": "ValueError"}})

        # Debug logging
        print(f"MCP Tool Debug: airlines_list = {airlines_list}", file=sys.stderr)

        # Validate dates
        datetime.datetime.strptime(date, '%Y-%m-%d')

        if is_round_trip:
            if not return_date:
                return json.dumps({"error": {"message": "return_date is required when is_round_trip=True", "type": "ValueError"}})
            datetime.datetime.strptime(return_date, '%Y-%m-%d')

            flight_data = [
                FlightData(date=date, from_airport=origin, to_airport=destination, airlines=airlines_list),
                FlightData(date=return_date, from_airport=destination, to_airport=origin, airlines=airlines_list),
            ]
            trip_type = "round-trip"
        else:
            flight_data = [
                FlightData(date=date, from_airport=origin, to_airport=destination, airlines=airlines_list),
            ]
            trip_type = "one-way"

        passengers_info = Passengers(adults=adults)

        result = get_flights(
            flight_data=flight_data,
            trip=trip_type,
            seat=seat_type,
            passengers=passengers_info,
        )

        if result and result.flights:
            if return_cheapest_only:
                cheapest_flight = min(result.flights, key=lambda f: parse_price(f.price))
                processed_flights = [flight_to_dict(cheapest_flight)]
                result_key = "cheapest_flight_by_airline"
            else:
                processed_flights = [flight_to_dict(f) for f in result.flights]
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
                    "return_cheapest_only": return_cheapest_only
                },
                result_key: processed_flights
            }
            return json.dumps(output_data, indent=2)
        else:
            return json.dumps({
                "message": f"No flights found for specified airlines on {date}.",
                "search_parameters": {"origin": origin, "destination": destination, "date": date, "airlines": airlines_list}
            })

    except ValueError as e:
        return json.dumps({"error": {"message": f"Invalid date format. Use YYYY-MM-DD.", "type": "ValueError"}})
    except RuntimeError as e:
        error_msg = str(e)
        print(f"MCP Tool RuntimeError in search_flights_by_airline: {error_msg}", file=sys.stderr)

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
                    "return_date": return_date if is_round_trip else None
                },
                "note": "Airline-filtered searches may not return results via scraping. Click the URL below to view flights in your browser."
            }
            if google_flights_url:
                response_data["google_flights_url"] = google_flights_url
            return json.dumps(response_data)

        return json.dumps({"error": {"message": error_msg, "type": "RuntimeError"}})
    except Exception as e:
        import traceback
        error_msg = str(e)
        error_trace = traceback.format_exc()
        print(f"MCP Tool Error in search_flights_by_airline: {type(e).__name__}: {error_msg}", file=sys.stderr)
        print(f"Full traceback:\n{error_trace}", file=sys.stderr)

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
    return_cheapest_only: bool = False
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
    print(f"MCP Tool: Searching flights with max {max_stops} stops {origin}->{destination}...", file=sys.stderr)
    try:
        # Validate max_stops
        if max_stops not in [0, 1, 2]:
            return json.dumps({"error": {"message": "max_stops must be 0, 1, or 2", "type": "ValueError"}})

        # Validate dates
        datetime.datetime.strptime(date, '%Y-%m-%d')

        if is_round_trip:
            if not return_date:
                return json.dumps({"error": {"message": "return_date is required when is_round_trip=True", "type": "ValueError"}})
            datetime.datetime.strptime(return_date, '%Y-%m-%d')

            flight_data = [
                FlightData(date=date, from_airport=origin, to_airport=destination),
                FlightData(date=return_date, from_airport=destination, to_airport=origin),
            ]
            trip_type = "round-trip"
        else:
            flight_data = [
                FlightData(date=date, from_airport=origin, to_airport=destination),
            ]
            trip_type = "one-way"

        passengers_info = Passengers(adults=adults)

        result = get_flights(
            flight_data=flight_data,
            trip=trip_type,
            seat=seat_type,
            passengers=passengers_info,
            max_stops=max_stops
        )

        if result and result.flights:
            if return_cheapest_only:
                cheapest_flight = min(result.flights, key=lambda f: parse_price(f.price))
                processed_flights = [flight_to_dict(cheapest_flight)]
                result_key = "cheapest_flight_with_max_stops"
            else:
                processed_flights = [flight_to_dict(f) for f in result.flights]
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
                result_key: processed_flights
            }
            return json.dumps(output_data, indent=2)
        else:
            return json.dumps({
                "message": f"No flights found with max {max_stops} stops on {date}.",
                "search_parameters": {"origin": origin, "destination": destination, "date": date, "max_stops": max_stops}
            })

    except ValueError as e:
        return json.dumps({"error": {"message": f"Invalid date format. Use YYYY-MM-DD.", "type": "ValueError"}})
    except RuntimeError as e:
        error_msg = str(e)
        print(f"MCP Tool RuntimeError in search_flights_with_max_stops: {error_msg}", file=sys.stderr)

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
        error_msg = str(e)
        print(f"MCP Tool Error in search_flights_with_max_stops: {error_msg}", file=sys.stderr)

        # Try to extract URL from any exception
        google_flights_url = None
        if "https://www.google.com/travel/flights" in error_msg:
            import re
            url_match = re.search(r'(https://www\.google\.com/travel/flights[^\s]+)', error_msg)
            if url_match:
                google_flights_url = url_match.group(1)

        response_data = {"error": {"message": error_msg, "type": type(e).__name__}}
        if google_flights_url:
            response_data["google_flights_url"] = google_flights_url
        return json.dumps(response_data)


@mcp.tool()
async def filter_by_departure_time(
    flights_json: str,
    time_of_day: str
) -> str:
    """
    Filter flight results by departure time of day.
    Takes existing flight search results and filters by time preference.

    Args:
        flights_json: JSON string of flight results from another search tool.
        time_of_day: Time preference - "morning" (6am-12pm), "afternoon" (12pm-6pm),
                     "evening" (6pm-12am), or "red-eye" (12am-6am).

    Returns:
        Filtered flight results matching the time preference.

    Example Args:
        {"flights_json": "[{...}]", "time_of_day": "morning"}
    """
    print(f"MCP Tool: Filtering flights by {time_of_day} departure...", file=sys.stderr)
    try:
        # Parse flights JSON
        try:
            flights_list = json.loads(flights_json)
        except json.JSONDecodeError as e:
            return json.dumps({"error": {"message": f"Invalid JSON in flights_json: {str(e)}", "type": "JSONDecodeError"}})

        if not isinstance(flights_list, list):
            return json.dumps({"error": {"message": "flights_json must be a JSON array", "type": "ValueError"}})

        # Define time ranges
        time_ranges = {
            "morning": (6, 12),
            "afternoon": (12, 18),
            "evening": (18, 24),
            "red-eye": (0, 6)
        }

        if time_of_day not in time_ranges:
            return json.dumps({"error": {"message": f"time_of_day must be one of: {', '.join(time_ranges.keys())}", "type": "ValueError"}})

        start_hour, end_hour = time_ranges[time_of_day]

        # Filter flights by departure time
        filtered_flights = []
        for flight in flights_list:
            departure_time = flight.get('departure')
            if not departure_time:
                continue

            # Try to parse time from various formats
            # Common formats: "6:00 AM", "06:00", "6:00 am", etc.
            try:
                # Remove extra spaces and convert to uppercase for AM/PM
                time_str = departure_time.strip().upper()

                # Handle AM/PM format
                if 'AM' in time_str or 'PM' in time_str:
                    # Parse time like "6:00 AM" or "6:00 PM"
                    time_part = time_str.replace('AM', '').replace('PM', '').strip()
                    hour = int(time_part.split(':')[0])

                    if 'PM' in time_str and hour != 12:
                        hour += 12
                    elif 'AM' in time_str and hour == 12:
                        hour = 0
                else:
                    # Handle 24-hour format like "18:00"
                    hour = int(time_str.split(':')[0])

                # Check if hour falls within the desired range
                if start_hour <= hour < end_hour:
                    filtered_flights.append(flight)

            except (ValueError, IndexError):
                # If we can't parse the time, skip this flight
                continue

        output_data = {
            "filter_applied": {
                "time_of_day": time_of_day,
                "hour_range": f"{start_hour}:00 - {end_hour}:00"
            },
            "total_flights_checked": len(flights_list),
            "flights_matching_time": len(filtered_flights),
            "filtered_flights": filtered_flights
        }

        return json.dumps(output_data, indent=2)

    except Exception as e:
        print(f"MCP Tool Error in filter_by_departure_time: {e}", file=sys.stderr)
        return json.dumps({"error": {"message": f"An unexpected error occurred.", "type": type(e).__name__}})


@mcp.tool()
async def filter_by_max_duration(
    flights_json: str,
    max_hours: int
) -> str:
    """
    Filter flight results by maximum total travel duration.
    Takes existing flight search results and filters by duration limit.

    Args:
        flights_json: JSON string of flight results from another search tool.
        max_hours: Maximum acceptable flight duration in hours.

    Returns:
        Filtered flight results within the duration limit.

    Example Args:
        {"flights_json": "[{...}]", "max_hours": 8}
    """
    print(f"MCP Tool: Filtering flights by max {max_hours}h duration...", file=sys.stderr)
    try:
        # Parse flights JSON
        try:
            flights_list = json.loads(flights_json)
        except json.JSONDecodeError as e:
            return json.dumps({"error": {"message": f"Invalid JSON in flights_json: {str(e)}", "type": "JSONDecodeError"}})

        if not isinstance(flights_list, list):
            return json.dumps({"error": {"message": "flights_json must be a JSON array", "type": "ValueError"}})

        if max_hours <= 0:
            return json.dumps({"error": {"message": "max_hours must be a positive number", "type": "ValueError"}})

        max_minutes = max_hours * 60

        # Filter flights by duration
        filtered_flights = []
        for flight in flights_list:
            duration_str = flight.get('duration')
            if not duration_str:
                continue

            try:
                # Parse duration strings like "2h 30m", "5h", "45m", "1 hr 15 min", etc.
                total_minutes = 0

                # Remove extra spaces
                duration_str = duration_str.lower().strip()

                # Extract hours
                if 'h' in duration_str or 'hr' in duration_str:
                    # Split by 'h' or 'hr'
                    if 'hr' in duration_str:
                        hours_part = duration_str.split('hr')[0].strip()
                    else:
                        hours_part = duration_str.split('h')[0].strip()

                    # Extract the number
                    hours = int(''.join(filter(str.isdigit, hours_part)))
                    total_minutes += hours * 60

                # Extract minutes
                if 'm' in duration_str or 'min' in duration_str:
                    # Find the minutes part
                    if 'min' in duration_str:
                        # Handle "15 min" or "1hr 15 min"
                        parts = duration_str.split()
                        for i, part in enumerate(parts):
                            if 'min' in part and i > 0:
                                minutes = int(''.join(filter(str.isdigit, parts[i-1])))
                                total_minutes += minutes
                                break
                    else:
                        # Handle "30m" or "2h 30m"
                        # Get text between last digit before 'm' and 'm'
                        m_index = duration_str.rfind('m')
                        # Find the number before 'm'
                        num_str = ''
                        for i in range(m_index - 1, -1, -1):
                            if duration_str[i].isdigit():
                                num_str = duration_str[i] + num_str
                            elif num_str:
                                break
                        if num_str:
                            minutes = int(num_str)
                            total_minutes += minutes

                # Check if within max duration
                if total_minutes > 0 and total_minutes <= max_minutes:
                    flight['parsed_duration_minutes'] = total_minutes
                    filtered_flights.append(flight)

            except (ValueError, IndexError):
                # If we can't parse the duration, skip this flight
                continue

        output_data = {
            "filter_applied": {
                "max_hours": max_hours,
                "max_minutes": max_minutes
            },
            "total_flights_checked": len(flights_list),
            "flights_within_duration": len(filtered_flights),
            "filtered_flights": filtered_flights
        }

        return json.dumps(output_data, indent=2)

    except Exception as e:
        print(f"MCP Tool Error in filter_by_max_duration: {e}", file=sys.stderr)
        return json.dumps({"error": {"message": f"An unexpected error occurred.", "type": type(e).__name__}})


@mcp.tool()
async def compare_one_way_vs_roundtrip(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: str,
    adults: int = 1,
    seat_type: str = "economy"
) -> str:
    """
    Compare pricing for round-trip vs two one-way tickets.
    Sometimes booking two one-way tickets is cheaper than a round-trip.

    Args:
        origin: Origin airport code (e.g., "SFO").
        destination: Destination airport code (e.g., "JFK").
        departure_date: Outbound date (YYYY-MM-DD format).
        return_date: Return date (YYYY-MM-DD format).
        adults: Number of adult passengers (default: 1).
        seat_type: Fare class (default: "economy").

    Returns:
        Comparison of round-trip vs two one-way prices with recommendation.

    Example Args:
        {"origin": "SFO", "destination": "JFK", "departure_date": "2025-07-20", "return_date": "2025-07-27"}
    """
    print(f"MCP Tool: Comparing round-trip vs one-way prices {origin}<->{destination}...", file=sys.stderr)
    try:
        # Validate dates
        datetime.datetime.strptime(departure_date, '%Y-%m-%d')
        datetime.datetime.strptime(return_date, '%Y-%m-%d')

        passengers_info = Passengers(adults=adults)

        # Get round-trip price
        round_trip_data = [
            FlightData(date=departure_date, from_airport=origin, to_airport=destination),
            FlightData(date=return_date, from_airport=destination, to_airport=origin),
        ]

        round_trip_result = get_flights(
            flight_data=round_trip_data,
            trip="round-trip",
            seat=seat_type,
            passengers=passengers_info,
        )

        # Get outbound one-way price
        outbound_data = [
            FlightData(date=departure_date, from_airport=origin, to_airport=destination),
        ]

        outbound_result = get_flights(
            flight_data=outbound_data,
            trip="one-way",
            seat=seat_type,
            passengers=passengers_info,
        )

        # Get return one-way price
        return_data = [
            FlightData(date=return_date, from_airport=destination, to_airport=origin),
        ]

        return_result = get_flights(
            flight_data=return_data,
            trip="one-way",
            seat=seat_type,
            passengers=passengers_info,
        )

        # Find cheapest options
        cheapest_round_trip = None
        cheapest_round_trip_price = float('inf')

        if round_trip_result and round_trip_result.flights:
            cheapest_round_trip = min(round_trip_result.flights, key=lambda f: parse_price(f.price))
            cheapest_round_trip_price = parse_price(cheapest_round_trip.price)

        cheapest_outbound = None
        cheapest_outbound_price = float('inf')

        if outbound_result and outbound_result.flights:
            cheapest_outbound = min(outbound_result.flights, key=lambda f: parse_price(f.price))
            cheapest_outbound_price = parse_price(cheapest_outbound.price)

        cheapest_return = None
        cheapest_return_price = float('inf')

        if return_result and return_result.flights:
            cheapest_return = min(return_result.flights, key=lambda f: parse_price(f.price))
            cheapest_return_price = parse_price(cheapest_return.price)

        # Calculate total for two one-ways
        two_one_ways_total = cheapest_outbound_price + cheapest_return_price

        # Determine recommendation
        if cheapest_round_trip_price == float('inf') and two_one_ways_total == float('inf'):
            recommendation = "No flights found for this route"
        elif cheapest_round_trip_price == float('inf'):
            recommendation = "Book two one-way tickets (round-trip not available)"
            savings = None
        elif two_one_ways_total == float('inf'):
            recommendation = "Book round-trip ticket (one-way options not available)"
            savings = None
        elif two_one_ways_total < cheapest_round_trip_price:
            savings = cheapest_round_trip_price - two_one_ways_total
            recommendation = f"Book two one-way tickets (save ${savings})"
        elif cheapest_round_trip_price < two_one_ways_total:
            savings = two_one_ways_total - cheapest_round_trip_price
            recommendation = f"Book round-trip ticket (save ${savings})"
        else:
            savings = 0
            recommendation = "Same price - choose based on flexibility preference"

        output_data = {
            "search_parameters": {
                "origin": origin,
                "destination": destination,
                "departure_date": departure_date,
                "return_date": return_date,
                "adults": adults,
                "seat_type": seat_type
            },
            "round_trip_option": {
                "price": f"${cheapest_round_trip_price}" if cheapest_round_trip_price != float('inf') else "Not available",
                "flight_details": flight_to_dict(cheapest_round_trip) if cheapest_round_trip else None
            },
            "two_one_way_option": {
                "total_price": f"${two_one_ways_total}" if two_one_ways_total != float('inf') else "Not available",
                "outbound_price": f"${cheapest_outbound_price}" if cheapest_outbound_price != float('inf') else "Not available",
                "return_price": f"${cheapest_return_price}" if cheapest_return_price != float('inf') else "Not available",
                "outbound_flight": flight_to_dict(cheapest_outbound) if cheapest_outbound else None,
                "return_flight": flight_to_dict(cheapest_return) if cheapest_return else None
            },
            "recommendation": recommendation,
            "potential_savings": f"${savings}" if savings else None
        }

        return json.dumps(output_data, indent=2)

    except ValueError as e:
        return json.dumps({"error": {"message": f"Invalid date format. Use YYYY-MM-DD.", "type": "ValueError"}})
    except RuntimeError as e:
        error_msg = str(e)
        print(f"MCP Tool RuntimeError in compare_one_way_vs_roundtrip: {error_msg}", file=sys.stderr)

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
                "message": "The scraper couldn't complete the comparison, but you can view results directly on Google Flights.",
                "search_parameters": {
                    "origin": origin,
                    "destination": destination,
                    "departure_date": departure_date,
                    "return_date": return_date,
                    "adults": adults,
                    "seat_type": seat_type
                },
                "note": "Comparison searches may not return results via scraping. Click the URL below to view flights in your browser."
            }
            if google_flights_url:
                response_data["google_flights_url"] = google_flights_url
            return json.dumps(response_data)

        return json.dumps({"error": {"message": error_msg, "type": "RuntimeError"}})
    except Exception as e:
        error_msg = str(e)
        print(f"MCP Tool Error in compare_one_way_vs_roundtrip: {error_msg}", file=sys.stderr)

        # Try to extract URL from any exception
        google_flights_url = None
        if "https://www.google.com/travel/flights" in error_msg:
            import re
            url_match = re.search(r'(https://www\.google\.com/travel/flights[^\s]+)', error_msg)
            if url_match:
                google_flights_url = url_match.group(1)

        response_data = {"error": {"message": error_msg, "type": type(e).__name__}}
        if google_flights_url:
            response_data["google_flights_url"] = google_flights_url
        return json.dumps(response_data)


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
def main():
    """Main entry point for the MCP server."""
    mcp.run(transport='stdio')


if __name__ == "__main__":
    main()
