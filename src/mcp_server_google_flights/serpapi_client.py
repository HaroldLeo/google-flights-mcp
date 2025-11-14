"""
SerpAPI client for Google Flights integration.

This module provides a comprehensive interface to SerpAPI's Google Flights API,
offering richer data than fast-flights including:
- Flight numbers
- Layover details (airport, duration, overnight)
- Carbon emissions with comparison to typical
- Price insights (historical data, price level)
- Multi-seller booking options
- Delay history
- Amenities (Wi-Fi, power, entertainment)
"""

import os
import logging
from typing import Optional, Dict, Any, List
from serpapi import GoogleSearch

logger = logging.getLogger(__name__)


class SerpAPIClient:
    """Client for interacting with SerpAPI Google Flights API."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize SerpAPI client.

        Args:
            api_key: SerpAPI API key. If not provided, reads from SERPAPI_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("SERPAPI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "SerpAPI key required. Set SERPAPI_API_KEY environment variable or pass api_key parameter."
            )

    def search_flights(
        self,
        departure_id: str,
        arrival_id: str,
        outbound_date: str,
        return_date: Optional[str] = None,
        adults: int = 1,
        travel_class: str = "economy",
        currency: str = "USD",
        max_stops: Optional[int] = None,
        departure_token: Optional[str] = None,
        booking_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Search for flights using SerpAPI.

        Args:
            departure_id: Origin airport code (e.g., "LAX")
            arrival_id: Destination airport code (e.g., "AUS")
            outbound_date: Departure date (YYYY-MM-DD)
            return_date: Return date for round-trip (YYYY-MM-DD)
            adults: Number of adult passengers
            travel_class: Cabin class (economy, premium_economy, business, first)
            currency: Currency code (USD, EUR, etc.)
            max_stops: Maximum number of stops (0 for direct)
            departure_token: Token to get return flights (from initial search)
            booking_token: Token to get booking options (from flight selection)

        Returns:
            Dictionary containing SerpAPI response with flights data
        """
        params = {
            "engine": "google_flights",
            "api_key": self.api_key,
            "hl": "en",
            "currency": currency,
        }

        # If booking_token provided, get booking options
        if booking_token:
            params["booking_token"] = booking_token
        # If departure_token provided, get return flights
        elif departure_token:
            params["departure_id"] = departure_id
            params["arrival_id"] = arrival_id
            params["outbound_date"] = outbound_date
            if return_date:
                params["return_date"] = return_date
            params["departure_token"] = departure_token
        # Otherwise, initial search
        else:
            params["departure_id"] = departure_id
            params["arrival_id"] = arrival_id
            params["outbound_date"] = outbound_date

            if return_date:
                params["return_date"] = return_date
                params["type"] = 1  # Round-trip
            else:
                params["type"] = 2  # One-way

            if adults > 1:
                params["adults"] = adults

            # Map travel class
            class_mapping = {
                "economy": "1",
                "premium_economy": "2",
                "business": "3",
                "first": "4",
            }
            params["travel_class"] = class_mapping.get(travel_class.lower(), "1")

            if max_stops is not None:
                params["stops"] = max_stops

        try:
            search = GoogleSearch(params)
            results = search.get_dict()
            return results
        except Exception as e:
            logger.error(f"SerpAPI search failed: {e}")
            raise

    def parse_flight_results(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse SerpAPI flight results into standardized format.

        Args:
            results: Raw SerpAPI response

        Returns:
            List of parsed flight dictionaries
        """
        flights = []

        # Get best_flights and other_flights
        best_flights = results.get("best_flights", [])
        other_flights = results.get("other_flights", [])

        all_flights = best_flights + other_flights

        for idx, flight in enumerate(all_flights):
            is_best = idx < len(best_flights)

            parsed_flight = {
                "is_best": is_best,
                "price": flight.get("price"),
                "type": flight.get("type"),
                "total_duration": flight.get("total_duration"),
                "departure_token": flight.get("departure_token"),
                "booking_token": flight.get("booking_token"),
            }

            # Parse carbon emissions
            carbon = flight.get("carbon_emissions", {})
            if carbon:
                parsed_flight["carbon_emissions"] = {
                    "this_flight_grams": carbon.get("this_flight"),
                    "typical_for_route_grams": carbon.get("typical_for_this_route"),
                    "difference_percent": carbon.get("difference_percent"),
                }

            # Parse flight segments
            segments = []
            layovers = flight.get("layovers", [])

            for segment in flight.get("flights", []):
                dep_airport = segment.get("departure_airport", {})
                arr_airport = segment.get("arrival_airport", {})

                parsed_segment = {
                    "flight_number": segment.get("flight_number"),
                    "airline": segment.get("airline"),
                    "airplane": segment.get("airplane"),
                    "departure_airport": {
                        "code": dep_airport.get("id"),
                        "name": dep_airport.get("name"),
                        "time": dep_airport.get("time"),
                    },
                    "arrival_airport": {
                        "code": arr_airport.get("id"),
                        "name": arr_airport.get("name"),
                        "time": arr_airport.get("time"),
                    },
                    "duration": segment.get("duration"),
                    "legroom": segment.get("legroom"),
                    "travel_class": segment.get("travel_class"),
                    "overnight": segment.get("overnight", False),
                    "often_delayed": segment.get("often_delayed_by_over_30_min", False),
                    "extensions": segment.get("extensions", []),
                }
                segments.append(parsed_segment)

            parsed_flight["segments"] = segments

            # Parse layovers
            parsed_layovers = []
            for layover in layovers:
                parsed_layovers.append({
                    "airport_code": layover.get("id"),
                    "airport_name": layover.get("name"),
                    "duration": layover.get("duration"),
                    "overnight": layover.get("overnight", False),
                })
            parsed_flight["layovers"] = parsed_layovers

            # Determine airlines
            airlines = list(set(seg.get("airline") for seg in flight.get("flights", []) if seg.get("airline")))
            parsed_flight["airlines"] = ", ".join(airlines) if airlines else None

            flights.append(parsed_flight)

        return flights

    def get_price_insights(self, results: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract price insights from SerpAPI results.

        Args:
            results: Raw SerpAPI response

        Returns:
            Price insights dictionary or None
        """
        insights = results.get("price_insights")
        if not insights:
            return None

        return {
            "lowest_price": insights.get("lowest_price"),
            "price_level": insights.get("price_level"),
            "typical_price_range": insights.get("typical_price_range"),
            "price_history": insights.get("price_history"),
        }

    def get_booking_options(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract booking options from SerpAPI results.

        Args:
            results: Raw SerpAPI response with booking_token used

        Returns:
            List of booking options with seller comparison
        """
        booking_options = []

        for option in results.get("booking_options", []):
            parsed_option = {
                "separate_tickets": option.get("separate_tickets", False),
            }

            # Parse "together" booking (both legs from same seller)
            if "together" in option:
                together = option["together"]
                parsed_option["together"] = {
                    "book_with": together.get("book_with"),
                    "is_airline": together.get("airline", False),
                    "price": together.get("price"),
                    "marketed_as": together.get("marketed_as", []),
                    "baggage_prices": together.get("baggage_prices", []),
                }

            # Parse separate departing/returning bookings
            if "departing" in option:
                departing = option["departing"]
                parsed_option["departing"] = {
                    "book_with": departing.get("book_with"),
                    "price": departing.get("price"),
                    "baggage_prices": departing.get("baggage_prices", []),
                }

            if "returning" in option:
                returning = option["returning"]
                parsed_option["returning"] = {
                    "book_with": returning.get("book_with"),
                    "price": returning.get("price"),
                    "baggage_prices": returning.get("baggage_prices", []),
                }

            booking_options.append(parsed_option)

        # Also get overall baggage prices
        baggage = results.get("baggage_prices", {})
        if baggage:
            return {
                "options": booking_options,
                "baggage_policies": {
                    "departing": baggage.get("departing", []),
                    "returning": baggage.get("returning", []),
                    "together": baggage.get("together", []),
                }
            }

        return {"options": booking_options}


def is_serpapi_available() -> bool:
    """Check if SerpAPI key is configured."""
    return bool(os.getenv("SERPAPI_API_KEY"))
