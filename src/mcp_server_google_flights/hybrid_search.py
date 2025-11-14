"""
Hybrid flight search that uses SerpAPI as primary source with fast-flights fallback.

SerpAPI provides richer data (250 free searches/month):
- Flight numbers
- Layover details
- Carbon emissions
- Price insights
- Multi-seller booking options

Fast-flights is used as fallback when:
- SerpAPI quota exhausted
- SerpAPI key not configured
- SerpAPI request fails
"""

import logging
from typing import List, Dict, Any, Optional
from .serpapi_client import SerpAPIClient, is_serpapi_available
from fast_flights import FlightData, Passengers, get_flights

logger = logging.getLogger(__name__)


async def hybrid_flight_search(
    origin: str,
    destination: str,
    outbound_date: str,
    return_date: Optional[str] = None,
    adults: int = 1,
    seat_type: str = "economy",
    max_stops: Optional[int] = None,
    compact_mode: bool = False,
) -> Dict[str, Any]:
    """
    Search for flights using SerpAPI with fast-flights fallback.

    Args:
        origin: Origin airport code
        destination: Destination airport code
        outbound_date: Departure date (YYYY-MM-DD)
        return_date: Return date for round-trip (YYYY-MM-DD)
        adults: Number of passengers
        seat_type: Cabin class
        max_stops: Maximum stops (None for any, 0 for direct)
        compact_mode: Return compact results

    Returns:
        Dictionary with flights and metadata
    """
    # Try SerpAPI first
    if is_serpapi_available():
        try:
            logger.info("Using SerpAPI for flight search")
            client = SerpAPIClient()

            results = client.search_flights(
                departure_id=origin,
                arrival_id=destination,
                outbound_date=outbound_date,
                return_date=return_date,
                adults=adults,
                travel_class=seat_type,
                max_stops=max_stops,
            )

            # Parse flights
            flights = client.parse_flight_results(results)
            price_insights = client.get_price_insights(results)

            response = {
                "source": "serpapi",
                "flights": flights,
                "search_metadata": results.get("search_metadata", {}),
            }

            if price_insights:
                response["price_insights"] = price_insights

            # Add booking URL from SerpAPI
            if "search_metadata" in results and "google_flights_url" in results["search_metadata"]:
                response["booking_url"] = results["search_metadata"]["google_flights_url"]

            logger.info(f"SerpAPI returned {len(flights)} flights")
            return response

        except Exception as e:
            logger.warning(f"SerpAPI search failed, falling back to fast-flights: {e}")
            # Fall through to fast-flights

    # Fallback to fast-flights
    logger.info("Using fast-flights for flight search")
    return await fastflights_search(
        origin=origin,
        destination=destination,
        outbound_date=outbound_date,
        return_date=return_date,
        adults=adults,
        seat_type=seat_type,
        max_stops=max_stops,
        compact_mode=compact_mode,
    )


async def fastflights_search(
    origin: str,
    destination: str,
    outbound_date: str,
    return_date: Optional[str] = None,
    adults: int = 1,
    seat_type: str = "economy",
    max_stops: Optional[int] = None,
    compact_mode: bool = False,
) -> Dict[str, Any]:
    """
    Search flights using fast-flights library (fallback).

    Args:
        origin: Origin airport code
        destination: Destination airport code
        outbound_date: Departure date (YYYY-MM-DD)
        return_date: Return date for round-trip
        adults: Number of passengers
        seat_type: Cabin class
        max_stops: Maximum stops
        compact_mode: Return compact results

    Returns:
        Dictionary with flights and metadata
    """
    from .server import flight_to_dict, create_booking_url

    # Create flight data
    flight_data = [FlightData(date=outbound_date, from_airport=origin, to_airport=destination)]

    if return_date:
        flight_data.append(FlightData(date=return_date, from_airport=destination, to_airport=origin))

    # Create passengers
    passengers = Passengers(adults=adults)

    # Determine trip type
    trip_type = "round-trip" if return_date else "one-way"

    # Search flights
    try:
        kwargs = {
            "flight_data": flight_data,
            "trip": trip_type,
            "seat": seat_type,
            "passengers": passengers,
            "fetch_mode": "fallback",
        }

        if max_stops is not None:
            kwargs["max_stops"] = max_stops

        results = get_flights(**kwargs)

        # Parse results
        flights = []
        for flight in results:
            parsed = flight_to_dict(flight, compact=compact_mode, origin=origin, destination=destination)
            flights.append(parsed)

        # Create booking URL
        booking_url = create_booking_url(
            origin=origin,
            destination=destination,
            outbound_date=outbound_date,
            return_date=return_date,
            seat_type=seat_type,
            adults=adults,
        )

        return {
            "source": "fast-flights",
            "flights": flights,
            "booking_url": booking_url,
            "note": "Using fast-flights v2.2. For richer data (flight numbers, layovers, price insights), configure SERPAPI_API_KEY environment variable.",
        }

    except Exception as e:
        logger.error(f"fast-flights search failed: {e}")
        raise


def create_booking_url(origin: str, destination: str, outbound_date: str, return_date: Optional[str] = None, seat_type: str = "economy", adults: int = 1) -> str:
    """
    Create Google Flights booking URL.

    Args:
        origin: Origin airport code
        destination: Destination airport code
        outbound_date: Departure date
        return_date: Return date (optional)
        seat_type: Cabin class
        adults: Number of passengers

    Returns:
        Google Flights URL
    """
    base_url = "https://www.google.com/travel/flights"

    # Build query params
    params = []

    # Add origin and destination
    params.append(f"f=0.{origin}.{destination}.{outbound_date}")

    if return_date:
        params.append(f"*{destination}.{origin}.{return_date}")

    # Add passengers
    params.append(f"1.{adults}.0.0.0")

    # Add class
    class_map = {"economy": "y", "premium_economy": "w", "business": "c", "first": "f"}
    class_code = class_map.get(seat_type.lower(), "y")
    params.append(class_code)

    query = ".".join(params)

    return f"{base_url}?tfs={query}"
