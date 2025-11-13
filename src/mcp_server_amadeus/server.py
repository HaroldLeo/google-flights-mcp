#!/usr/bin/env python
"""
Amadeus MCP Server - Comprehensive travel API integration

This MCP server provides access to the full Amadeus API suite including:
- Flight search, booking, and analytics
- Hotel search, booking, and ratings
- Tours and activities
- Airport transfers
- Reference data (airports, airlines, cities)
- Market insights and predictions
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode
import aiohttp

from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("amadeus-travel-api")

# --- Configuration ---
AMADEUS_CLIENT_ID = os.getenv("AMADEUS_CLIENT_ID")
AMADEUS_CLIENT_SECRET = os.getenv("AMADEUS_CLIENT_SECRET")
AMADEUS_ENV = os.getenv("AMADEUS_ENV", "test")  # "test" or "production"

# Base URLs
BASE_URLS = {
    "test": "https://test.api.amadeus.com",
    "production": "https://api.amadeus.com"
}
BASE_URL = BASE_URLS.get(AMADEUS_ENV, BASE_URLS["test"])

# Token management
_access_token: Optional[str] = None
_token_expiry: Optional[datetime] = None


# --- Helper Functions ---

def log_info(tool_name: str, message: str):
    """Structured info logging for MCP tools."""
    print(f"[Amadeus:{tool_name}] {message}", file=sys.stderr)


def log_error(tool_name: str, error_type: str, message: str):
    """Structured error logging for MCP tools."""
    print(f"[Amadeus:{tool_name}] ERROR ({error_type}): {message}", file=sys.stderr)


async def get_access_token() -> str:
    """
    Get a valid OAuth2 access token, refreshing if necessary.

    Returns:
        str: Valid access token

    Raises:
        ValueError: If credentials are not configured
        RuntimeError: If token request fails
    """
    global _access_token, _token_expiry

    # Check if we have a valid token
    if _access_token and _token_expiry and datetime.now() < _token_expiry:
        return _access_token

    # Validate credentials
    if not AMADEUS_CLIENT_ID or not AMADEUS_CLIENT_SECRET:
        raise ValueError(
            "Amadeus credentials not configured. "
            "Set AMADEUS_CLIENT_ID and AMADEUS_CLIENT_SECRET environment variables."
        )

    # Request new token
    url = f"{BASE_URL}/v1/security/oauth2/token"
    data = {
        "grant_type": "client_credentials",
        "client_id": AMADEUS_CLIENT_ID,
        "client_secret": AMADEUS_CLIENT_SECRET
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise RuntimeError(f"Token request failed ({response.status}): {error_text}")

                result = await response.json()
                _access_token = result["access_token"]
                expires_in = result.get("expires_in", 1799)  # Default ~30 min
                _token_expiry = datetime.now() + timedelta(seconds=expires_in - 60)  # 1 min buffer

                log_info("Auth", f"Access token obtained, expires in {expires_in}s")
                return _access_token

    except Exception as e:
        log_error("Auth", "TokenError", str(e))
        raise RuntimeError(f"Failed to obtain access token: {e}")


async def amadeus_request(
    method: str,
    endpoint: str,
    params: Optional[Dict[str, Any]] = None,
    data: Optional[Dict[str, Any]] = None,
    tool_name: str = "API"
) -> Dict[str, Any]:
    """
    Make an authenticated request to the Amadeus API.

    Args:
        method: HTTP method (GET, POST, DELETE)
        endpoint: API endpoint path (e.g., "/v2/shopping/flight-offers")
        params: Query parameters
        data: JSON body data
        tool_name: Tool name for logging

    Returns:
        Dict containing API response data

    Raises:
        RuntimeError: If request fails
    """
    token = await get_access_token()
    url = f"{BASE_URL}{endpoint}"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    try:
        async with aiohttp.ClientSession() as session:
            request_kwargs = {
                "headers": headers,
                "params": params
            }

            if data:
                request_kwargs["json"] = data

            log_info(tool_name, f"{method} {endpoint}")

            async with session.request(method, url, **request_kwargs) as response:
                response_text = await response.text()

                if response.status >= 400:
                    log_error(tool_name, f"HTTP{response.status}", response_text[:500])
                    raise RuntimeError(
                        f"API request failed ({response.status}): {response_text[:500]}"
                    )

                # Parse JSON response
                if response_text:
                    return json.loads(response_text)
                return {}

    except aiohttp.ClientError as e:
        log_error(tool_name, "NetworkError", str(e))
        raise RuntimeError(f"Network error: {e}")
    except json.JSONDecodeError as e:
        log_error(tool_name, "ParseError", str(e))
        raise RuntimeError(f"Failed to parse response: {e}")


# ============================================================================
# FLIGHT TOOLS
# ============================================================================

@mcp.tool()
async def search_flights(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: Optional[str] = None,
    adults: int = 1,
    children: int = 0,
    infants: int = 0,
    travel_class: Optional[str] = None,
    max_results: int = 10,
    currency_code: str = "USD",
    nonstop_only: bool = False,
    included_airline_codes: Optional[str] = None
) -> str:
    """
    Search for flight offers between two locations.

    Args:
        origin: Origin airport/city IATA code (e.g., "NYC", "JFK")
        destination: Destination airport/city IATA code (e.g., "LAX", "PAR")
        departure_date: Departure date in YYYY-MM-DD format
        return_date: Return date for round-trip in YYYY-MM-DD format (optional)
        adults: Number of adult passengers (age 12+), default 1
        children: Number of child passengers (age 2-11), default 0
        infants: Number of infant passengers (under 2), default 0
        travel_class: Cabin class - ECONOMY, PREMIUM_ECONOMY, BUSINESS, FIRST (optional)
        max_results: Maximum number of flight offers to return (1-250), default 10
        currency_code: Currency for prices (3-letter code), default USD
        nonstop_only: Only return non-stop flights, default False
        included_airline_codes: Comma-separated airline IATA codes to filter (e.g., "AA,UA,DL")

    Returns:
        JSON string with flight offers including prices, airlines, and itineraries.
        The response includes:
        - 'offers': Simplified summary format for easy reading
        - 'raw_offers': Complete flight offer data from Amadeus API for use with confirm_flight_price
    """
    try:
        params = {
            "originLocationCode": origin.upper(),
            "destinationLocationCode": destination.upper(),
            "departureDate": departure_date,
            "adults": adults,
            "currencyCode": currency_code.upper(),
            "max": min(max_results, 250)
        }

        if return_date:
            params["returnDate"] = return_date
        if children > 0:
            params["children"] = children
        if infants > 0:
            params["infants"] = infants
        if travel_class:
            params["travelClass"] = travel_class.upper()
        if nonstop_only:
            params["nonStop"] = "true"
        if included_airline_codes:
            params["includedAirlineCodes"] = included_airline_codes.upper()

        result = await amadeus_request(
            "GET",
            "/v2/shopping/flight-offers",
            params=params,
            tool_name="SearchFlights"
        )

        # Format the response
        offers = result.get("data", [])
        meta = result.get("meta", {})

        summary = {
            "search_params": {
                "origin": origin.upper(),
                "destination": destination.upper(),
                "departure_date": departure_date,
                "return_date": return_date,
                "passengers": {
                    "adults": adults,
                    "children": children,
                    "infants": infants
                }
            },
            "results_count": len(offers),
            "currency": currency_code.upper(),
            "offers": [],
            "raw_offers": offers[:max_results]  # Include complete raw offers for use with confirm_flight_price
        }

        # Extract key information from each offer
        for idx, offer in enumerate(offers[:max_results], 1):
            itineraries = offer.get("itineraries", [])
            price = offer.get("price", {})

            offer_summary = {
                "rank": idx,
                "id": offer.get("id"),
                "price": {
                    "total": price.get("total"),
                    "currency": price.get("currency"),
                    "base": price.get("base"),
                    "fees": price.get("fees", [])
                },
                "itineraries": []
            }

            for itin in itineraries:
                segments = itin.get("segments", [])
                itin_summary = {
                    "duration": itin.get("duration"),
                    "segments": []
                }

                for seg in segments:
                    seg_summary = {
                        "departure": {
                            "airport": seg.get("departure", {}).get("iataCode"),
                            "time": seg.get("departure", {}).get("at"),
                            "terminal": seg.get("departure", {}).get("terminal")
                        },
                        "arrival": {
                            "airport": seg.get("arrival", {}).get("iataCode"),
                            "time": seg.get("arrival", {}).get("at"),
                            "terminal": seg.get("arrival", {}).get("terminal")
                        },
                        "carrier": seg.get("carrierCode"),
                        "flight_number": seg.get("number"),
                        "aircraft": seg.get("aircraft", {}).get("code"),
                        "duration": seg.get("duration"),
                        "cabin_class": seg.get("cabin")
                    }
                    itin_summary["segments"].append(seg_summary)

                offer_summary["itineraries"].append(itin_summary)

            summary["offers"].append(offer_summary)

        log_info("SearchFlights", f"Found {len(offers)} flight offers")
        return json.dumps(summary, indent=2)

    except Exception as e:
        log_error("SearchFlights", type(e).__name__, str(e))
        return json.dumps({"error": str(e)}, indent=2)


def sanitize_flight_offer_for_pricing(offer: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize flight offer data for the pricing API.

    The pricing API is more strict than the search API and frequently rejects
    aircraft codes that are returned by the search API. Since aircraft codes are
    optional for pricing confirmation, we remove them entirely to avoid errors.

    Common error: 400/477 - "Invalid data format at aircraft field"

    Args:
        offer: Flight offer dictionary from search results

    Returns:
        Sanitized flight offer dictionary with aircraft fields removed
    """
    # Create a deep copy to avoid modifying the original
    import copy
    sanitized = copy.deepcopy(offer)

    # Remove ALL aircraft fields from segments
    # The pricing API often rejects aircraft codes even when they look valid (e.g., "32Q")
    # Since aircraft is optional for pricing, safer to remove it entirely
    if "itineraries" in sanitized:
        for itinerary in sanitized["itineraries"]:
            if "segments" in itinerary:
                for segment in itinerary["segments"]:
                    # Remove aircraft field entirely to avoid validation errors
                    if "aircraft" in segment:
                        # Handle both formats: aircraft as string (from search summary) or dict (from raw API)
                        aircraft = segment.get("aircraft")
                        if isinstance(aircraft, dict):
                            aircraft_code = aircraft.get("code", "unknown")
                        elif isinstance(aircraft, str):
                            aircraft_code = aircraft
                        else:
                            aircraft_code = "unknown"
                        log_info("ConfirmPrice", f"Removing aircraft field (code: {aircraft_code}) to prevent API validation errors")
                        segment.pop("aircraft", None)

    return sanitized


@mcp.tool()
async def confirm_flight_price(flight_offer_data: str) -> str:
    """
    Confirm the pricing of a flight offer before booking.

    This validates that the price is still available and provides detailed tax breakdown.

    IMPORTANT:
    - Use the COMPLETE raw flight offer from 'raw_offers' field in search_flights results
    - Do NOT use the simplified 'offers' summary - it's missing required fields
    - This function automatically removes aircraft codes to prevent API validation errors
    - The pricing API requires: travelerPricings, source, and segment id fields

    Example usage:
        search_result = search_flights("JFK", "LAX", "2024-12-15")
        parsed = json.loads(search_result)
        first_raw_offer = parsed["raw_offers"][0]  # Use raw_offers, not offers
        confirm_flight_price(json.dumps(first_raw_offer))

    Args:
        flight_offer_data: JSON string containing the COMPLETE raw flight offer from
                          the 'raw_offers' field of search_flights results

    Returns:
        JSON string with confirmed pricing and detailed tax information
    """
    try:
        offer = json.loads(flight_offer_data)

        # Validate that this is complete raw offer data, not simplified summary
        missing_fields = []
        if "travelerPricings" not in offer:
            missing_fields.append("travelerPricings")
        if "source" not in offer:
            missing_fields.append("source")

        # Check if segments have IDs
        if "itineraries" in offer:
            for itin_idx, itin in enumerate(offer["itineraries"]):
                if "segments" in itin:
                    for seg_idx, seg in enumerate(itin["segments"]):
                        if "id" not in seg:
                            missing_fields.append(f"itineraries[{itin_idx}].segments[{seg_idx}].id")
                            break
                    if missing_fields:
                        break

        if missing_fields:
            return json.dumps({
                "error": "Invalid flight offer format - missing required fields for pricing API",
                "missing_fields": missing_fields,
                "details": "You are likely passing the simplified 'offers' summary instead of the complete 'raw_offers' data",
                "solution": "Use the 'raw_offers' field from search_flights results, not the 'offers' field",
                "example": {
                    "wrong": "search_result['offers'][0]  # Missing required fields",
                    "correct": "search_result['raw_offers'][0]  # Complete data with all required fields"
                }
            }, indent=2)

        # Sanitize the offer data to remove potentially problematic fields
        sanitized_offer = sanitize_flight_offer_for_pricing(offer)

        payload = {
            "data": {
                "type": "flight-offers-pricing",
                "flightOffers": [sanitized_offer]
            }
        }

        result = await amadeus_request(
            "POST",
            "/v1/shopping/flight-offers/pricing",
            data=payload,
            tool_name="ConfirmPrice"
        )

        log_info("ConfirmPrice", "Price confirmed successfully")
        return json.dumps(result, indent=2)

    except json.JSONDecodeError as e:
        error_msg = f"Invalid flight offer JSON: {e}"
        log_error("ConfirmPrice", "InvalidInput", error_msg)
        return json.dumps({"error": error_msg}, indent=2)
    except Exception as e:
        log_error("ConfirmPrice", type(e).__name__, str(e))
        return json.dumps({"error": str(e)}, indent=2)


# ============================================================================
# BOOKING TOOLS - DISABLED
# ============================================================================
# These tools are disabled because they have limited utility in test environment:
# - Test environment does not create real bookings
# - Requires extensive traveler data (passport, contact info, etc.)
# - Most users prefer to book directly on airline/OTA websites
# - Adds complexity without practical value for an MCP tool
#
# To re-enable, uncomment the @mcp.tool() decorators below
# ============================================================================

# @mcp.tool()
async def book_flight(
    flight_offer_data: str,
    travelers: str
) -> str:
    """
    [DISABLED] Book a flight and create a flight order.

    This tool is disabled in the current version. Use confirm_flight_price
    to get detailed pricing, then book directly on the airline website.
    """
    return json.dumps({
        "error": "Booking tools are disabled in this version. Use confirm_flight_price for pricing, then book on the airline website.",
        "reason": "Test environment does not create real bookings"
    }, indent=2)


# @mcp.tool()
async def get_flight_order(order_id: str) -> str:
    """
    [DISABLED] Retrieve details of a flight order.
    """
    return json.dumps({
        "error": "Booking tools are disabled in this version.",
        "reason": "Test environment does not create real bookings"
    }, indent=2)


# @mcp.tool()
async def cancel_flight_order(order_id: str) -> str:
    """
    [DISABLED] Cancel a flight order.
    """
    return json.dumps({
        "error": "Booking tools are disabled in this version.",
        "reason": "Test environment does not create real bookings"
    }, indent=2)


@mcp.tool()
async def flight_inspiration_search(
    origin: str,
    departure_date: Optional[str] = None,
    max_results: int = 10
) -> str:
    """
    Discover flight destinations from an origin with cheapest prices.

    Perfect for "Where can I fly from NYC?" type queries.

    IMPORTANT: This API works best with major airport codes (not city codes) and
    WITHOUT a specific departure date in the test environment.

    Args:
        origin: Origin AIRPORT IATA code (e.g., "JFK", "LAX", "CDG") - use airport code, not city code
        departure_date: Optional departure date in YYYY-MM-DD format (leave empty for best results in test environment)
        max_results: Maximum destinations to return, default 10

    Returns:
        JSON string with destinations and their cheapest prices
    """
    try:
        # Note: API parameter is "origin" not "originLocationCode"
        params = {"origin": origin.upper()}

        # Only add departure date if provided (test environment works better without it)
        if departure_date:
            params["departureDate"] = departure_date
            log_info("FlightInspiration", f"Searching with specific date: {departure_date} (may have limited results in test environment)")

        result = await amadeus_request(
            "GET",
            "/v1/shopping/flight-destinations",
            params=params,
            tool_name="FlightInspiration"
        )

        destinations = result.get("data", [])

        # Check if we got results
        if not destinations:
            # Provide helpful error message for test environment
            error_response = {
                "error": "No flight destinations found for this query",
                "origin": origin.upper(),
                "possible_reasons": [
                    "Test environment has limited data for this origin airport",
                    "Try using a major airport code (JFK, LAX, CDG, LHR, etc.) instead of city codes",
                    "Remove the departure_date parameter for broader results",
                    "This route may not have data in the test environment"
                ],
                "suggestions": [
                    "Try a major hub airport: JFK, LAX, LHR, CDG, FRA, DXB, SIN, HKG",
                    "Use search_flights instead for specific route searches",
                    "Switch to production environment for complete data coverage"
                ]
            }
            log_error("FlightInspiration", "NoResults", f"No destinations found for origin {origin}")
            return json.dumps(error_response, indent=2)

        destinations = destinations[:max_results]

        summary = {
            "origin": origin.upper(),
            "departure_date": departure_date or "flexible",
            "results_count": len(destinations),
            "destinations": []
        }

        for dest in destinations:
            summary["destinations"].append({
                "destination": dest.get("destination"),
                "price": dest.get("price", {}).get("total"),
                "currency": dest.get("price", {}).get("currency"),
                "departure_date": dest.get("departureDate"),
                "return_date": dest.get("returnDate")
            })

        log_info("FlightInspiration", f"Found {len(destinations)} destinations")
        return json.dumps(summary, indent=2)

    except RuntimeError as e:
        error_msg = str(e)
        # Check for specific Amadeus API errors
        if "1797" in error_msg or "404" in error_msg:
            return json.dumps({
                "error": "No flight destinations found for this query (Amadeus Error 1797)",
                "origin": origin.upper(),
                "details": "The test environment has limited destination data available",
                "suggestions": [
                    "Try a major hub airport: JFK, LAX, LHR, CDG, FRA, DXB, SIN, HKG",
                    "Remove the departure_date parameter for broader results",
                    "Use search_flights for specific destination searches",
                    "Switch to production environment for complete coverage"
                ]
            }, indent=2)
        elif "38189" in error_msg or "500" in error_msg:
            return json.dumps({
                "error": "Internal server error from Amadeus API (Error 38189)",
                "origin": origin.upper(),
                "details": "This often occurs when using a departure date in test environment",
                "suggestions": [
                    "Try removing the departure_date parameter",
                    "Use a major airport code instead of city code",
                    "Use search_flights for date-specific searches"
                ]
            }, indent=2)
        log_error("FlightInspiration", "APIError", error_msg)
        return json.dumps({"error": error_msg}, indent=2)
    except Exception as e:
        log_error("FlightInspiration", type(e).__name__, str(e))
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
async def flight_cheapest_dates(
    origin: str,
    destination: str,
    departure_date: Optional[str] = None,
    one_way: bool = False
) -> str:
    """
    Find the cheapest dates to fly to a destination.

    IMPORTANT: This API has LIMITED data in test environment. Works best with:
    - Major airport codes (not city codes): JFK, LAX, LHR, CDG, etc.
    - Popular international routes
    - Without specific departure dates (for broader results)

    Args:
        origin: Origin AIRPORT IATA code (e.g., "JFK", "LAX") - use airport code, not city code
        destination: Destination AIRPORT IATA code (e.g., "LHR", "CDG")
        departure_date: Optional specific departure date (YYYY-MM-DD) or leave empty for flexible search
        one_way: True for one-way flights, False for round-trip, default False

    Returns:
        JSON string with cheapest flight dates and prices
    """
    try:
        params = {
            "origin": origin.upper(),
            "destination": destination.upper()
        }

        if departure_date:
            params["departureDate"] = departure_date
            log_info("CheapestDates", f"Searching with specific date: {departure_date}")
        if one_way:
            params["oneWay"] = "true"

        result = await amadeus_request(
            "GET",
            "/v1/shopping/flight-dates",
            params=params,
            tool_name="CheapestDates"
        )

        # Check if we got results
        data = result.get("data", [])
        if not data:
            error_response = {
                "error": "No cheapest dates found for this route",
                "route": f"{origin.upper()} → {destination.upper()}",
                "possible_reasons": [
                    "Test environment has very limited data for this route",
                    "This route may not be available in the test database",
                    "Domestic routes often have limited data in test environment"
                ],
                "suggestions": [
                    "Try a major international route: JFK→LHR, LAX→NRT, SFO→CDG",
                    "Use search_flights for specific date searches (more reliable)",
                    "Remove the departure_date parameter for broader results",
                    "Switch to production environment for complete data coverage"
                ]
            }
            log_error("CheapestDates", "NoResults", f"No dates found for {origin}→{destination}")
            return json.dumps(error_response, indent=2)

        log_info("CheapestDates", f"Retrieved {len(data)} cheapest date options")
        return json.dumps(result, indent=2)

    except RuntimeError as e:
        error_msg = str(e)
        # Check for specific Amadeus API errors
        if "1797" in error_msg or "404" in error_msg:
            return json.dumps({
                "error": "No flight dates found for this route (Amadeus Error 1797)",
                "route": f"{origin.upper()} → {destination.upper()}",
                "details": "The test environment has very limited route data available",
                "suggestions": [
                    "Try a major international route: JFK→LHR, LAX→NRT, SFO→CDG, JFK→CDG",
                    "Use search_flights instead - it has much better data coverage",
                    "Remove the departure_date parameter",
                    "Switch to production environment for complete coverage"
                ],
                "note": "search_flights is more reliable for finding actual flight availability"
            }, indent=2)
        elif "38189" in error_msg or "500" in error_msg:
            return json.dumps({
                "error": "Internal server error from Amadeus API (Error 38189)",
                "route": f"{origin.upper()} → {destination.upper()}",
                "details": "This often occurs with limited data availability in test environment",
                "suggestions": [
                    "Use search_flights instead - it's more reliable",
                    "Try a different major international route",
                    "Remove the departure_date parameter"
                ]
            }, indent=2)
        log_error("CheapestDates", "APIError", error_msg)
        return json.dumps({"error": error_msg}, indent=2)
    except Exception as e:
        log_error("CheapestDates", type(e).__name__, str(e))
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
async def analyze_flight_price(
    origin: str,
    destination: str,
    departure_date: str,
    currency_code: str = "USD"
) -> str:
    """
    Analyze if a flight price is a good deal using AI.

    Uses historical booking data to determine if current prices are above or below average.

    Args:
        origin: Origin airport IATA code
        destination: Destination airport IATA code
        departure_date: Departure date in YYYY-MM-DD format
        currency_code: Currency for pricing, default USD

    Returns:
        JSON string with price analysis and recommendations
    """
    try:
        params = {
            "originIataCode": origin.upper(),
            "destinationIataCode": destination.upper(),
            "departureDate": departure_date,
            "currencyCode": currency_code.upper()
        }

        result = await amadeus_request(
            "GET",
            "/v1/analytics/itinerary-price-metrics",
            params=params,
            tool_name="AnalyzePrice"
        )

        log_info("AnalyzePrice", "Price analysis completed")
        return json.dumps(result, indent=2)

    except Exception as e:
        log_error("AnalyzePrice", type(e).__name__, str(e))
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
async def predict_flight_delay(
    origin: str,
    destination: str,
    departure_date: str,
    departure_time: str,
    arrival_date: str,
    arrival_time: str,
    carrier_code: str,
    flight_number: str,
    aircraft_code: str,
    duration: str
) -> str:
    """
    Predict the probability of a flight being delayed.

    Args:
        origin: Origin airport IATA code
        destination: Destination airport IATA code
        departure_date: Departure date in YYYY-MM-DD format
        departure_time: Departure time in HH:MM:SS format
        arrival_date: Arrival date in YYYY-MM-DD format
        arrival_time: Arrival time in HH:MM:SS format
        carrier_code: Airline IATA code (e.g., "AA")
        flight_number: Flight number (e.g., "123")
        aircraft_code: Aircraft type code (e.g., "738")
        duration: Flight duration in ISO 8601 format (e.g., "PT5H30M")

    Returns:
        JSON string with delay prediction probability
    """
    try:
        params = {
            "originLocationCode": origin.upper(),
            "destinationLocationCode": destination.upper(),
            "departureDate": departure_date,
            "departureTime": departure_time,
            "arrivalDate": arrival_date,
            "arrivalTime": arrival_time,
            "aircraftCode": aircraft_code,
            "carrierCode": carrier_code.upper(),
            "flightNumber": flight_number,
            "duration": duration
        }

        result = await amadeus_request(
            "GET",
            "/v1/travel/predictions/flight-delay",
            params=params,
            tool_name="PredictDelay"
        )

        log_info("PredictDelay", "Delay prediction completed")
        return json.dumps(result, indent=2)

    except Exception as e:
        log_error("PredictDelay", type(e).__name__, str(e))
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
async def get_flight_status(
    carrier_code: str,
    flight_number: str,
    scheduled_departure_date: str
) -> str:
    """
    Get real-time flight status information.

    Args:
        carrier_code: Airline IATA code (e.g., "AA")
        flight_number: Flight number (e.g., "123")
        scheduled_departure_date: Scheduled departure date in YYYY-MM-DD format

    Returns:
        JSON string with real-time flight status including gates, delays, etc.
    """
    try:
        params = {
            "carrierCode": carrier_code.upper(),
            "flightNumber": flight_number,
            "scheduledDepartureDate": scheduled_departure_date
        }

        result = await amadeus_request(
            "GET",
            "/v2/schedule/flights",
            params=params,
            tool_name="FlightStatus"
        )

        log_info("FlightStatus", f"Retrieved status for {carrier_code}{flight_number}")
        return json.dumps(result, indent=2)

    except Exception as e:
        log_error("FlightStatus", type(e).__name__, str(e))
        return json.dumps({"error": str(e)}, indent=2)


# ============================================================================
# HOTEL TOOLS
# ============================================================================

@mcp.tool()
async def search_hotels_by_city(city_code: str, radius: int = 5, radius_unit: str = "KM") -> str:
    """
    Get list of hotels in a city.

    Args:
        city_code: City IATA code (e.g., "PAR" for Paris, "NYC" for New York)
        radius: Search radius, default 5
        radius_unit: Unit for radius - KM or MILE, default KM

    Returns:
        JSON string with hotel listings including IDs for booking
    """
    try:
        params = {
            "cityCode": city_code.upper(),
            "radius": radius,
            "radiusUnit": radius_unit.upper()
        }

        result = await amadeus_request(
            "GET",
            "/v1/reference-data/locations/hotels/by-city",
            params=params,
            tool_name="SearchHotelsByCity"
        )

        hotels = result.get("data", [])
        log_info("SearchHotelsByCity", f"Found {len(hotels)} hotels in {city_code}")
        return json.dumps(result, indent=2)

    except Exception as e:
        log_error("SearchHotelsByCity", type(e).__name__, str(e))
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
async def search_hotels_by_location(
    latitude: float,
    longitude: float,
    radius: int = 5,
    radius_unit: str = "KM"
) -> str:
    """
    Find hotels near a specific geographic location.

    Args:
        latitude: Latitude coordinate (e.g., 40.7128)
        longitude: Longitude coordinate (e.g., -74.0060)
        radius: Search radius, default 5
        radius_unit: Unit for radius - KM or MILE, default KM

    Returns:
        JSON string with nearby hotels
    """
    try:
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "radius": radius,
            "radiusUnit": radius_unit.upper()
        }

        result = await amadeus_request(
            "GET",
            "/v1/reference-data/locations/hotels/by-geocode",
            params=params,
            tool_name="SearchHotelsByLocation"
        )

        hotels = result.get("data", [])
        log_info("SearchHotelsByLocation", f"Found {len(hotels)} hotels")
        return json.dumps(result, indent=2)

    except Exception as e:
        log_error("SearchHotelsByLocation", type(e).__name__, str(e))
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
async def get_hotel_offers(
    hotel_ids: str,
    check_in_date: str,
    check_out_date: str,
    adults: int = 1,
    children: Optional[str] = None,
    room_quantity: int = 1,
    currency: str = "USD"
) -> str:
    """
    Search for hotel offers and availability.

    Args:
        hotel_ids: Comma-separated hotel IDs from hotel search (e.g., "MCLONGHM,ADNYCCTB")
        check_in_date: Check-in date in YYYY-MM-DD format
        check_out_date: Check-out date in YYYY-MM-DD format
        adults: Number of adult guests per room, default 1
        children: Comma-separated ages of children (e.g., "5,7" for two children), optional
        room_quantity: Number of rooms needed, default 1
        currency: Currency for prices, default USD

    Returns:
        JSON string with available hotel offers and rates
    """
    try:
        params = {
            "hotelIds": hotel_ids.upper(),
            "checkInDate": check_in_date,
            "checkOutDate": check_out_date,
            "adults": adults,
            "roomQuantity": room_quantity,
            "currency": currency.upper()
        }

        if children:
            params["childAges"] = children

        result = await amadeus_request(
            "GET",
            "/v3/shopping/hotel-offers",
            params=params,
            tool_name="GetHotelOffers"
        )

        offers = result.get("data", [])
        log_info("GetHotelOffers", f"Found offers for {len(offers)} hotels")
        return json.dumps(result, indent=2)

    except Exception as e:
        log_error("GetHotelOffers", type(e).__name__, str(e))
        return json.dumps({"error": str(e)}, indent=2)


# @mcp.tool()
async def book_hotel(
    offer_id: str,
    guests: str,
    payment: str
) -> str:
    """
    [DISABLED] Book a hotel room.

    This tool is disabled. Use get_hotel_offers to find hotels,
    then book directly on hotel/OTA websites.
    """
    return json.dumps({
        "error": "Booking tools are disabled in this version. Use get_hotel_offers for pricing, then book on hotel websites.",
        "reason": "Test environment does not create real bookings; requires payment information"
    }, indent=2)


@mcp.tool()
async def get_hotel_ratings(hotel_ids: str) -> str:
    """
    Get hotel ratings based on sentiment analysis of reviews.

    IMPORTANT: The sentiment database has VERY LIMITED coverage in test environment.
    Most hotel IDs will return "not in database" errors. This is a limitation of
    the Amadeus test environment, not a bug.

    For best results:
    - Query 1-3 hotels at a time (maximum 10)
    - Use hotel IDs from search_hotels_by_city or search_hotels_by_location
    - Be prepared for "not in database" responses - this is normal in test environment
    - Production environment has much better coverage

    Args:
        hotel_ids: Comma-separated hotel IDs (e.g., "MCLONGHM,ADNYCCTB")
                   Maximum: 10 hotels per request
                   Recommended: 1-3 hotels per request

    Returns:
        JSON string with hotel sentiment scores and ratings
    """
    try:
        # Split and validate hotel IDs
        ids_list = [id.strip().upper() for id in hotel_ids.split(",") if id.strip()]

        if not ids_list:
            return json.dumps({
                "error": "No hotel IDs provided. Please provide comma-separated hotel IDs."
            }, indent=2)

        # Warn if too many hotels
        if len(ids_list) > 10:
            return json.dumps({
                "error": f"Too many hotel IDs ({len(ids_list)})",
                "details": "The API has a maximum limit of hotels that can be queried at once",
                "provided_count": len(ids_list),
                "maximum_allowed": 10,
                "suggestion": "Split your request into multiple calls with 10 or fewer hotels each"
            }, indent=2)

        if len(ids_list) > 3:
            log_info("GetHotelRatings", f"Warning: Querying {len(ids_list)} hotels. Many may not be in the sentiment database (test environment limitation).")

        # Format hotel IDs for the API
        formatted_ids = ",".join(ids_list)
        params = {"hotelIds": formatted_ids}

        result = await amadeus_request(
            "GET",
            "/v2/e-reputation/hotel-sentiments",
            params=params,
            tool_name="GetHotelRatings"
        )

        # Check if any hotels were found
        data = result.get("data", [])
        if not data:
            return json.dumps({
                "error": "No sentiment ratings found for any of the provided hotel IDs",
                "requested_ids": ids_list,
                "requested_count": len(ids_list),
                "found_count": 0,
                "common_reasons": [
                    "MOST COMMON: Test environment has very limited sentiment database coverage",
                    "Hotel IDs may not have review data in the database",
                    "Hotel IDs may be incorrect or invalid",
                    "Sentiment analysis data is not available for these specific hotels"
                ],
                "suggestions": [
                    "This is normal in test environment - limited database coverage",
                    "Try hotel IDs from major chains in popular cities",
                    "Use search_hotels_by_city or search_hotels_by_location to find valid hotel IDs",
                    "Production environment has much better sentiment database coverage"
                ],
                "note": "Limited sentiment data in test environment is expected - not a bug"
            }, indent=2)

        # Check if we got partial results
        if len(data) < len(ids_list):
            log_info("GetHotelRatings", f"Partial results: Retrieved ratings for {len(data)} out of {len(ids_list)} hotels (some not in sentiment database)")
            # Add warning to the result
            result["warning"] = {
                "message": f"Only {len(data)} out of {len(ids_list)} hotels found in sentiment database",
                "requested_ids": ids_list,
                "found_count": len(data),
                "missing_count": len(ids_list) - len(data),
                "note": "Limited coverage in test environment is normal"
            }

        log_info("GetHotelRatings", f"Retrieved ratings for {len(data)} hotels")
        return json.dumps(result, indent=2)

    except RuntimeError as e:
        error_msg = str(e)
        # Check for specific API errors
        if "404" in error_msg or "not found" in error_msg.lower():
            return json.dumps({
                "error": "Hotels not found in sentiment database",
                "requested_ids": hotel_ids.split(","),
                "details": "The sentiment database has very limited coverage in test environment",
                "suggestions": [
                    "This is expected in test environment - not a bug",
                    "Try major hotel chains in popular tourist cities",
                    "Production environment has much better coverage"
                ]
            }, indent=2)
        log_error("GetHotelRatings", "APIError", error_msg)
        return json.dumps({"error": error_msg}, indent=2)
    except Exception as e:
        log_error("GetHotelRatings", type(e).__name__, str(e))
        return json.dumps({"error": str(e)}, indent=2)


# ============================================================================
# TOURS & ACTIVITIES
# ============================================================================

@mcp.tool()
async def search_activities(
    latitude: float,
    longitude: float,
    radius: int = 1
) -> str:
    """
    Search for tours and activities near a location.

    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
        radius: Search radius in kilometers, default 1

    Returns:
        JSON string with available activities and tours
    """
    try:
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "radius": radius
        }

        result = await amadeus_request(
            "GET",
            "/v1/shopping/activities",
            params=params,
            tool_name="SearchActivities"
        )

        activities = result.get("data", [])
        log_info("SearchActivities", f"Found {len(activities)} activities")
        return json.dumps(result, indent=2)

    except Exception as e:
        log_error("SearchActivities", type(e).__name__, str(e))
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
async def get_activity_details(activity_id: str) -> str:
    """
    Get detailed information about a specific activity.

    Args:
        activity_id: Activity ID from search results

    Returns:
        JSON string with complete activity details
    """
    try:
        result = await amadeus_request(
            "GET",
            f"/v1/shopping/activities/{activity_id}",
            tool_name="GetActivityDetails"
        )

        log_info("GetActivityDetails", f"Retrieved details for {activity_id}")
        return json.dumps(result, indent=2)

    except Exception as e:
        log_error("GetActivityDetails", type(e).__name__, str(e))
        return json.dumps({"error": str(e)}, indent=2)


# ============================================================================
# TRANSFERS
# ============================================================================

# Airport location database with complete information for transfer API
AIRPORT_LOCATIONS = {
    # Paris Airports
    "CDG": {
        "name": "Paris Charles de Gaulle Airport",
        "cityName": "Paris",
        "countryCode": "FR",
        "geoCode": "49.0097,2.5479",
        "addressLine": "95700 Roissy-en-France"
    },
    "ORY": {
        "name": "Paris Orly Airport",
        "cityName": "Paris",
        "countryCode": "FR",
        "geoCode": "48.7233,2.3794",
        "addressLine": "94390 Orly"
    },
    # New York Airports
    "JFK": {
        "name": "John F. Kennedy International Airport",
        "cityName": "New York",
        "countryCode": "US",
        "geoCode": "40.6413,-73.7781",
        "addressLine": "Queens, NY 11430"
    },
    "LGA": {
        "name": "LaGuardia Airport",
        "cityName": "New York",
        "countryCode": "US",
        "geoCode": "40.7769,-73.8740",
        "addressLine": "Queens, NY 11371"
    },
    "EWR": {
        "name": "Newark Liberty International Airport",
        "cityName": "Newark",
        "countryCode": "US",
        "geoCode": "40.6895,-74.1745",
        "addressLine": "Newark, NJ 07114"
    },
    # London Airports
    "LHR": {
        "name": "London Heathrow Airport",
        "cityName": "London",
        "countryCode": "GB",
        "geoCode": "51.4700,-0.4543",
        "addressLine": "Longford TW6, United Kingdom"
    },
    "LGW": {
        "name": "London Gatwick Airport",
        "cityName": "London",
        "countryCode": "GB",
        "geoCode": "51.1537,-0.1821",
        "addressLine": "Horley RH6 0NP, United Kingdom"
    },
    "STN": {
        "name": "London Stansted Airport",
        "cityName": "London",
        "countryCode": "GB",
        "geoCode": "51.8860,0.2389",
        "addressLine": "Stansted CM24 1QW, United Kingdom"
    },
    # Los Angeles
    "LAX": {
        "name": "Los Angeles International Airport",
        "cityName": "Los Angeles",
        "countryCode": "US",
        "geoCode": "33.9416,-118.4085",
        "addressLine": "1 World Way, Los Angeles, CA 90045"
    },
    # Tokyo Airports
    "NRT": {
        "name": "Narita International Airport",
        "cityName": "Tokyo",
        "countryCode": "JP",
        "geoCode": "35.7720,140.3929",
        "addressLine": "Narita, Chiba 282-0004"
    },
    "HND": {
        "name": "Tokyo Haneda Airport",
        "cityName": "Tokyo",
        "countryCode": "JP",
        "geoCode": "35.5494,139.7798",
        "addressLine": "Ota City, Tokyo 144-0041"
    },
    # Other Major Airports
    "SFO": {
        "name": "San Francisco International Airport",
        "cityName": "San Francisco",
        "countryCode": "US",
        "geoCode": "37.6213,-122.3790",
        "addressLine": "San Francisco, CA 94128"
    },
    "MIA": {
        "name": "Miami International Airport",
        "cityName": "Miami",
        "countryCode": "US",
        "geoCode": "25.7959,-80.2870",
        "addressLine": "Miami, FL 33126"
    },
    "DXB": {
        "name": "Dubai International Airport",
        "cityName": "Dubai",
        "countryCode": "AE",
        "geoCode": "25.2532,55.3657",
        "addressLine": "Dubai, United Arab Emirates"
    },
    "FRA": {
        "name": "Frankfurt Airport",
        "cityName": "Frankfurt",
        "countryCode": "DE",
        "geoCode": "50.0379,8.5622",
        "addressLine": "60547 Frankfurt"
    },
    "AMS": {
        "name": "Amsterdam Schiphol Airport",
        "cityName": "Amsterdam",
        "countryCode": "NL",
        "geoCode": "52.3105,4.7683",
        "addressLine": "1118 Schiphol"
    },
    "MAD": {
        "name": "Madrid-Barajas Airport",
        "cityName": "Madrid",
        "countryCode": "ES",
        "geoCode": "40.4719,-3.5626",
        "addressLine": "28042 Madrid"
    },
    "BCN": {
        "name": "Barcelona-El Prat Airport",
        "cityName": "Barcelona",
        "countryCode": "ES",
        "geoCode": "41.2974,2.0833",
        "addressLine": "08820 El Prat de Llobregat, Barcelona"
    },
    "SIN": {
        "name": "Singapore Changi Airport",
        "cityName": "Singapore",
        "countryCode": "SG",
        "geoCode": "1.3644,103.9915",
        "addressLine": "Airport Boulevard, Singapore"
    },
    "HKG": {
        "name": "Hong Kong International Airport",
        "cityName": "Hong Kong",
        "countryCode": "HK",
        "geoCode": "22.3080,113.9185",
        "addressLine": "Hong Kong"
    },
    "ICN": {
        "name": "Incheon International Airport",
        "cityName": "Seoul",
        "countryCode": "KR",
        "geoCode": "37.4602,126.4407",
        "addressLine": "Jung-gu, Incheon"
    }
}


def format_location_for_transfer(location: str, is_start: bool = True) -> Dict[str, Any]:
    """
    Format a location string into the detailed format required by Amadeus Transfer API.

    Args:
        location: Airport IATA code, "lat,long", or address string
        is_start: True if this is the start location, False for end location

    Returns:
        Dictionary with properly formatted location fields
    """
    location_upper = location.upper().strip()

    # Check if it's an airport code in our database
    if location_upper in AIRPORT_LOCATIONS:
        airport_data = AIRPORT_LOCATIONS[location_upper]
        if is_start:
            # Start location can just use the airport code
            return {"startLocationCode": location_upper}
        else:
            # End location needs full details
            return {
                "endLocationCode": location_upper,
                "endAddressLine": airport_data["addressLine"],
                "endCityName": airport_data["cityName"],
                "endCountryCode": airport_data["countryCode"],
                "endGeoCode": airport_data["geoCode"],
                "endName": airport_data["name"]
            }

    # Check if it's coordinates (lat,long format)
    if "," in location and len(location.split(",")) == 2:
        try:
            lat, lon = location.split(",")
            float(lat.strip())
            float(lon.strip())

            if is_start:
                return {"startGeoCode": location.strip()}
            else:
                return {"endGeoCode": location.strip()}
        except ValueError:
            pass

    # Otherwise treat as address
    if is_start:
        return {"startAddressLine": location}
    else:
        return {"endAddressLine": location}


@mcp.tool()
async def search_transfers(
    start_location: str,
    end_location: str,
    transfer_type: str,
    start_date_time: str,
    passengers: int = 1,
    duration: Optional[str] = None
) -> str:
    """
    Search for airport transfer options.

    Args:
        start_location: Starting location - Airport IATA code (e.g., "CDG", "JFK") or coordinates as "lat,long"
        end_location: Destination - Airport IATA code, coordinates as "lat,long", or address
        transfer_type: Type of transfer service. Valid values are:
            - PRIVATE: Private transfer/car service (recommended for airport transfers)
            - TAXI: Taxi service
            - HOURLY: Hourly rental service (requires duration parameter)
            - SHUTTLE: Shared shuttle service
            - SHARED: Shared transfer service
        start_date_time: Start date and time in ISO 8601 format (e.g., "2024-11-20T10:30:00")
        passengers: Number of passengers, default 1
        duration: Duration for HOURLY transfers in ISO 8601 format (e.g., "PT2H30M" for 2 hours 30 minutes)

    Returns:
        JSON string with available transfer options and prices
    """
    try:
        # Format locations with complete information
        start_fields = format_location_for_transfer(start_location, is_start=True)
        end_fields = format_location_for_transfer(end_location, is_start=False)

        # Build transfer search payload
        payload = {
            **start_fields,
            **end_fields,
            "transferType": transfer_type.upper(),
            "startDateTime": start_date_time,
            "passengers": passengers
        }

        # Add duration for HOURLY transfers
        if transfer_type.upper() == "HOURLY":
            if not duration:
                return json.dumps({
                    "error": "Duration is required for HOURLY transfer type. Use ISO 8601 format like 'PT2H30M' for 2 hours 30 minutes."
                }, indent=2)
            payload["duration"] = duration

        result = await amadeus_request(
            "POST",
            "/v1/shopping/transfer-offers",
            data=payload,
            tool_name="SearchTransfers"
        )

        offers = result.get("data", [])
        log_info("SearchTransfers", f"Found {len(offers)} transfer options")
        return json.dumps(result, indent=2)

    except Exception as e:
        log_error("SearchTransfers", type(e).__name__, str(e))
        return json.dumps({"error": str(e)}, indent=2)


# @mcp.tool()
async def book_transfer(
    offer_id: str,
    passenger_details: str
) -> str:
    """
    [DISABLED] Book an airport transfer.

    This tool is disabled. Use search_transfers to find options,
    then book directly with transfer companies or through travel websites.
    """
    return json.dumps({
        "error": "Booking tools are disabled in this version. Use search_transfers for pricing, then book on transfer websites.",
        "reason": "Test environment does not create real bookings"
    }, indent=2)


# ============================================================================
# REFERENCE DATA & LOCATION TOOLS
# ============================================================================

@mcp.tool()
async def search_airports(
    keyword: str,
    country_code: Optional[str] = None
) -> str:
    """
    Search for airports by keyword.

    Args:
        keyword: Search keyword (city name, airport name, or code)
        country_code: Optional 2-letter country code to filter results (e.g., "US", "FR")

    Returns:
        JSON string with matching airports including IATA codes and locations
    """
    try:
        params = {
            "keyword": keyword,
            "subType": "AIRPORT"
        }

        if country_code:
            params["countryCode"] = country_code.upper()

        result = await amadeus_request(
            "GET",
            "/v1/reference-data/locations",
            params=params,
            tool_name="SearchAirports"
        )

        locations = result.get("data", [])
        log_info("SearchAirports", f"Found {len(locations)} airports")
        return json.dumps(result, indent=2)

    except Exception as e:
        log_error("SearchAirports", type(e).__name__, str(e))
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
async def search_cities(
    keyword: str,
    country_code: Optional[str] = None
) -> str:
    """
    Search for cities by keyword.

    Args:
        keyword: Search keyword (city name)
        country_code: Optional 2-letter country code to filter (e.g., "US", "FR")

    Returns:
        JSON string with matching cities and their codes
    """
    try:
        params = {
            "keyword": keyword,
            "subType": "CITY"
        }

        if country_code:
            params["countryCode"] = country_code.upper()

        result = await amadeus_request(
            "GET",
            "/v1/reference-data/locations",
            params=params,
            tool_name="SearchCities"
        )

        cities = result.get("data", [])
        log_info("SearchCities", f"Found {len(cities)} cities")
        return json.dumps(result, indent=2)

    except Exception as e:
        log_error("SearchCities", type(e).__name__, str(e))
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
async def get_nearest_airports(
    latitude: float,
    longitude: float,
    radius: int = 500
) -> str:
    """
    Find nearest airports to a geographic location.

    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
        radius: Search radius in kilometers, default 500

    Returns:
        JSON string with nearby airports sorted by relevance
    """
    try:
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "radius": radius
        }

        result = await amadeus_request(
            "GET",
            "/v1/reference-data/locations/airports",
            params=params,
            tool_name="NearestAirports"
        )

        airports = result.get("data", [])
        log_info("NearestAirports", f"Found {len(airports)} airports")
        return json.dumps(result, indent=2)

    except Exception as e:
        log_error("NearestAirports", type(e).__name__, str(e))
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
async def get_airline_info(airline_codes: str) -> str:
    """
    Get airline information by IATA codes.

    Args:
        airline_codes: Comma-separated airline IATA codes (e.g., "AA,UA,DL")

    Returns:
        JSON string with airline names and details
    """
    try:
        params = {"airlineCodes": airline_codes.upper()}

        result = await amadeus_request(
            "GET",
            "/v1/reference-data/airlines",
            params=params,
            tool_name="GetAirlineInfo"
        )

        log_info("GetAirlineInfo", "Retrieved airline information")
        return json.dumps(result, indent=2)

    except Exception as e:
        log_error("GetAirlineInfo", type(e).__name__, str(e))
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
async def get_airline_routes(airline_code: str) -> str:
    """
    Get all destinations served by an airline.

    Args:
        airline_code: Airline IATA code (e.g., "AA")

    Returns:
        JSON string with all routes operated by the airline
    """
    try:
        params = {"airlineCode": airline_code.upper()}

        result = await amadeus_request(
            "GET",
            "/v1/airline/destinations",
            params=params,
            tool_name="GetAirlineRoutes"
        )

        destinations = result.get("data", [])
        log_info("GetAirlineRoutes", f"Found {len(destinations)} destinations")
        return json.dumps(result, indent=2)

    except Exception as e:
        log_error("GetAirlineRoutes", type(e).__name__, str(e))
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
async def get_airport_routes(airport_code: str) -> str:
    """
    Get all direct destinations from an airport.

    Args:
        airport_code: Airport IATA code (e.g., "JFK")

    Returns:
        JSON string with all direct routes from the airport
    """
    try:
        params = {"departureAirportCode": airport_code.upper()}

        result = await amadeus_request(
            "GET",
            "/v1/airport/direct-destinations",
            params=params,
            tool_name="GetAirportRoutes"
        )

        destinations = result.get("data", [])
        log_info("GetAirportRoutes", f"Found {len(destinations)} destinations")
        return json.dumps(result, indent=2)

    except Exception as e:
        log_error("GetAirportRoutes", type(e).__name__, str(e))
        return json.dumps({"error": str(e)}, indent=2)


# ============================================================================
# MARKET INSIGHTS & ANALYTICS
# ============================================================================

@mcp.tool()
async def get_travel_insights(
    origin_city: str,
    period: str,
    max_results: int = 10
) -> str:
    """
    Get most traveled destinations from an origin city.

    Args:
        origin_city: Origin city IATA code (e.g., "NYC")
        period: Period in YYYY-MM format (e.g., "2024-12")
        max_results: Maximum number of destinations to return, default 10

    Returns:
        JSON string with popular destinations and traffic data
    """
    try:
        params = {
            "originCityCode": origin_city.upper(),
            "period": period,
            "max": max_results
        }

        result = await amadeus_request(
            "GET",
            "/v1/travel/analytics/air-traffic/traveled",
            params=params,
            tool_name="TravelInsights"
        )

        log_info("TravelInsights", f"Retrieved insights for {origin_city}")
        return json.dumps(result, indent=2)

    except Exception as e:
        log_error("TravelInsights", type(e).__name__, str(e))
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
async def get_booking_insights(
    origin_city: str,
    period: str,
    max_results: int = 10
) -> str:
    """
    Get most booked destinations from an origin city.

    Args:
        origin_city: Origin city IATA code (e.g., "NYC")
        period: Period in YYYY-MM format (e.g., "2024-12")
        max_results: Maximum number of destinations, default 10

    Returns:
        JSON string with popular booked destinations
    """
    try:
        params = {
            "originCityCode": origin_city.upper(),
            "period": period,
            "max": max_results
        }

        result = await amadeus_request(
            "GET",
            "/v1/travel/analytics/air-traffic/booked",
            params=params,
            tool_name="BookingInsights"
        )

        log_info("BookingInsights", f"Retrieved booking insights for {origin_city}")
        return json.dumps(result, indent=2)

    except Exception as e:
        log_error("BookingInsights", type(e).__name__, str(e))
        return json.dumps({"error": str(e)}, indent=2)


# @mcp.tool()
async def predict_trip_purpose(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: Optional[str] = None
) -> str:
    """
    [DISABLED] Predict if a trip is for business or leisure.

    This tool is disabled because users already know their trip purpose.
    The AI prediction provides minimal practical value.
    """
    return json.dumps({
        "error": "predict_trip_purpose is disabled in this version.",
        "reason": "Users already know their trip purpose; minimal practical value"
    }, indent=2)


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main entry point for the Amadeus MCP server."""

    # Check if credentials are configured
    if not AMADEUS_CLIENT_ID or not AMADEUS_CLIENT_SECRET:
        print("\n" + "="*70, file=sys.stderr)
        print("AMADEUS MCP SERVER - CONFIGURATION REQUIRED", file=sys.stderr)
        print("="*70, file=sys.stderr)
        print("\nPlease set the following environment variables:", file=sys.stderr)
        print("  - AMADEUS_CLIENT_ID: Your Amadeus API key", file=sys.stderr)
        print("  - AMADEUS_CLIENT_SECRET: Your Amadeus API secret", file=sys.stderr)
        print("\nOptional:", file=sys.stderr)
        print("  - AMADEUS_ENV: 'test' (default) or 'production'", file=sys.stderr)
        print("\nGet your credentials at: https://developers.amadeus.com", file=sys.stderr)
        print("="*70 + "\n", file=sys.stderr)
    else:
        print("\n" + "="*70, file=sys.stderr)
        print("AMADEUS MCP SERVER STARTING", file=sys.stderr)
        print("="*70, file=sys.stderr)
        print(f"Environment: {AMADEUS_ENV}", file=sys.stderr)
        print(f"Base URL: {BASE_URL}", file=sys.stderr)
        print(f"Client ID: {AMADEUS_CLIENT_ID[:8]}...", file=sys.stderr)
        print("="*70 + "\n", file=sys.stderr)

    # Run the MCP server
    mcp.run()


if __name__ == "__main__":
    main()
