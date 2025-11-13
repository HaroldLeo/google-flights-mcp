# AMADEUS FOR DEVELOPERS - API ENDPOINTS ANALYSIS

**File**: Amadeus for Developers.postman_collection.json  
**Total Endpoints**: 55  
**Last Updated**: 2024

---

## TABLE OF CONTENTS
1. [Flight APIs (25 endpoints)](#flight-apis)
2. [Hotel APIs (13 endpoints)](#hotel-apis)
3. [Destination Experiences APIs (4 endpoints)](#destination-experiences-apis)
4. [Cars and Transfers APIs (3 endpoints)](#cars-and-transfers-apis)
5. [Market Insights APIs (included in Flights)](#market-insights-apis)
6. [Itinerary Management (1 endpoint)](#itinerary-management)
7. [Authorization & Security (2 endpoints)](#authorization--security)
8. [Reference Data APIs (7 endpoints)](#reference-data-apis)

---

## FLIGHT APIs

### Core Flight Search & Booking Endpoints

#### 1. Flight Offers Search (v2)
- **Methods**: GET, POST
- **Endpoints**:
  - `GET /v2/shopping/flight-offers`
  - `POST /v2/shopping/flight-offers`
- **Key Query Parameters** (GET):
  - `originLocationCode` (required) - Origin city/airport IATA code
  - `destinationLocationCode` (required) - Destination city/airport IATA code
  - `departureDate` (required) - Departure date (YYYY-MM-DD)
  - `returnDate` (optional) - Return date for round trips
  - `adults`, `children`, `infants` - Passenger counts
  - `max` - Maximum number of offers to return
  - `includedAirlineCodes` (optional) - Filter by specific airlines
- **Purpose**: Get cheapest flight recommendations and prices on a given journey. Provides flight recommendations and fares with bag allowance, ancillary prices, and fare details.

#### 2. Flight Offers Price
- **Method**: POST
- **Endpoint**: `POST /v1/shopping/flight-offers/pricing`
- **Body**: JSON payload with flight offer data
- **Purpose**: Confirm the price of a flight and obtain information about taxes and fees to be applied to the entire journey. Validates pricing before booking.

#### 3. Flight Create Orders (Booking)
- **Method**: POST
- **Endpoint**: `POST /v1/booking/flight-orders`
- **Body**: JSON payload with flight offer and traveler information
- **Purpose**: Book flights and ancillary services (additional checked bags, seats with extra legroom, etc.). Returns flight order ID and booking details.

#### 4. Flight Order Management
- **Methods**: GET, DELETE
- **Endpoints**:
  - `GET /v1/booking/flight-orders/{flightOrderId}` - Retrieve order details
  - `DELETE /v1/booking/flight-orders/{flightOrderId}` - Cancel order
- **Purpose**: Manipulate and manage flight orders previously created.

### Flight Enhancements & Ancillaries

#### 5. Seatmap Display
- **Methods**: GET, POST
- **Endpoints**:
  - `GET /v1/shopping/seatmaps?flight-orderId={flightOrderId}`
  - `POST /v1/shopping/seatmaps`
- **Purpose**: Retrieve seat maps of one or several flights. Helps with seat selection during booking.

#### 6. Branded Fares Upsell
- **Method**: POST
- **Endpoint**: `POST /v1/shopping/flight-offers/upselling`
- **Purpose**: Handle branded fares (fare families) that combine products like bags, meals, free cancellation, or miles accrual. Upsell opportunities.

#### 7. Flight Availabilities Search
- **Method**: POST
- **Endpoint**: `POST /v1/shopping/availability/flight-availabilities`
- **Body**: JSON payload with itinerary details
- **Purpose**: Provide list of flights with seats for sale on a given itinerary and quantity of available seats in different fare classes.

### Flight Search & Discovery

#### 8. Flight Inspiration Search
- **Method**: GET
- **Endpoint**: `GET /v1/shopping/flight-destinations?departureDate={date}&origin={code}`
- **Key Query Parameters**:
  - `departureDate` - Departure date
  - `origin` - Origin airport code
- **Purpose**: Get list of destinations from a given origin and the cheapest price for each destination. Helps users discover destinations.

#### 9. Flight Cheapest Date Search
- **Method**: GET
- **Endpoint**: `GET /v1/shopping/flight-dates?origin={code}&destination={code}&departureDate={date}`
- **Purpose**: Find the cheapest dates to a given city or airport. Returns flight-date options with prices.

#### 10. Flight Choice Prediction
- **Method**: POST
- **Endpoint**: `POST /v2/shopping/flight-offers/prediction`
- **Body**: JSON with flight offers data
- **Purpose**: Forecast traveler choices in search and shopping context using machine learning and AI.

### Flight Analytics & Predictions

#### 11. Flight Price Analysis
- **Method**: GET
- **Endpoint**: `GET /v1/analytics/itinerary-price-metrics`
- **Key Query Parameters**:
  - `originIataCode` - Origin IATA code
  - `destinationIataCode` - Destination IATA code
  - `departureDate` - Departure date
  - `currencyCode` - Currency for pricing
  - `oneWay` - One-way or round-trip flag
- **Purpose**: Use AI algorithm to determine if flight price is a good deal based on historical booking data.

#### 12. Flight Delay Prediction
- **Method**: GET
- **Endpoint**: `GET /v1/travel/predictions/flight-delay`
- **Key Query Parameters**:
  - `originLocationCode`, `destinationLocationCode`
  - `departureDate`, `departureTime`
  - `arrivalDate`, `arrivalTime`
  - `aircraftCode`, `carrierCode`, `flightNumber`
  - `duration` - Flight duration
- **Purpose**: Forecast the chances for a flight to be delayed.

#### 13. On Demand Flight Status
- **Method**: GET
- **Endpoint**: `GET /v2/schedule/flights`
- **Key Query Parameters**:
  - `carrierCode` - Airline IATA code
  - `flightNumber` - Flight number
  - `scheduledDepartureDate` - Date
- **Purpose**: Provide real-time flight schedule data including departure/arrival times, terminal/gate info, duration, and delay status.

#### 14. Airport On-Time Performance
- **Method**: GET
- **Endpoint**: `GET /v1/airport/predictions/on-time`
- **Key Query Parameters**:
  - `airportCode` - Airport IATA code
  - `date` - Date
- **Purpose**: Return percentage of on-time flight departures from a given airport.

### Market Insights for Flights

#### 15. Flight Most Traveled Destinations
- **Method**: GET
- **Endpoint**: `GET /v1/travel/analytics/air-traffic/traveled`
- **Key Query Parameters**:
  - `originCityCode` - Origin city code
  - `period` - Period in YYYY-MM format
  - `sort` - Sort parameter
  - `max` - Maximum results
- **Purpose**: List most popular flight destinations from a given origin during a specific period.

#### 16. Flight Most Booked Destinations
- **Method**: GET
- **Endpoint**: `GET /v1/travel/analytics/air-traffic/booked`
- **Key Query Parameters**:
  - `originCityCode` - Origin city code
  - `period` - Period in YYYY-MM format
- **Purpose**: Find most popular flight destinations from an origin during a specific period based on bookings.

#### 17. Flight Busiest Traveling Period
- **Method**: GET
- **Endpoint**: `GET /v1/travel/analytics/air-traffic/busiest-period`
- **Key Query Parameters**:
  - `cityCode` - City code
  - `period` - Period (year or month)
  - `direction` - ARRIVING or DEPARTING
- **Purpose**: Find peak and off-peak travel periods for a given city to determine cheapest times to travel.

#### 18. Travel Recommendations
- **Method**: GET
- **Endpoint**: `GET /v1/reference-data/recommended-locations`
- **Key Query Parameters**:
  - `cityCodes` - City codes
  - `travelerCountryCode` - Traveler's country code
- **Purpose**: Get personalized travel recommendations based on traveler profile.

---

## HOTEL APIs

### Hotel Search & Booking Endpoints

#### 1. Hotel Offers Search (v3)
- **Method**: GET
- **Endpoint**: `GET /v3/shopping/hotel-offers`
- **Key Query Parameters**:
  - `hotelIds` (required) - Comma-separated hotel IDs
  - `adults` (required) - Number of adults
  - `children` (optional) - Number of children
  - `checkInDate` - Check-in date
  - `checkOutDate` - Check-out date
- **Purpose**: Search for hotels and retrieve availability and rates information.

#### 2. Hotel Search Offer Information
- **Method**: GET
- **Endpoint**: `GET /v3/shopping/hotel-offers/{hotelOfferId}`
- **Purpose**: Get detailed room and rate information for a specific hotel offer.

#### 3. Hotel Booking v1
- **Method**: POST
- **Endpoint**: `POST /v1/booking/hotel-bookings`
- **Body**: JSON with guest and offer information
- **Purpose**: Book hotel offers from a wide choice of providers. First version of hotel booking API.

#### 4. Hotel Booking v2
- **Method**: POST
- **Endpoint**: `POST /v2/booking/hotel-orders`
- **Body**: JSON with guest and offer information
- **Purpose**: Book hotel offers from various providers. Newer version with enhanced features.

### Hotel Reference Data

#### 5. Hotel List by City
- **Method**: GET
- **Endpoint**: `GET /v1/reference-data/locations/hotels/by-city`
- **Key Query Parameters**:
  - `cityCode` (required) - City IATA code
- **Purpose**: Get list of hotels in a given city with IDs for search.

#### 6. Hotel List by Hotel IDs
- **Method**: GET
- **Endpoint**: `GET /v1/reference-data/locations/hotels/by-hotels`
- **Key Query Parameters**:
  - `hotelIds` (required) - Comma-separated hotel IDs
- **Purpose**: Retrieve hotel details by specific hotel IDs.

#### 7. Hotel List by Geocode
- **Method**: GET
- **Endpoint**: `GET /v1/reference-data/locations/hotels/by-geocode`
- **Key Query Parameters**:
  - `latitude` (required) - Latitude coordinate
  - `longitude` (required) - Longitude coordinate
  - `radius` (optional) - Search radius in km
- **Purpose**: Find hotels near a specific geographical location.

#### 8. Hotel Name Autocomplete
- **Method**: GET
- **Endpoint**: `GET /v1/reference-data/locations/hotel`
- **Key Query Parameters**:
  - `keyword` (required) - Search keyword
  - `subType` (optional) - HOTEL_LEISURE or HOTEL_CITY
- **Purpose**: Autocomplete hotel search field to help users quickly find desired hotel.

### Hotel Ratings & Reviews

#### 9. Hotel Ratings (Sentiments)
- **Method**: GET
- **Endpoint**: `GET /v2/e-reputation/hotel-sentiments`
- **Key Query Parameters**:
  - `hotelIds` (required) - Comma-separated hotel IDs
- **Purpose**: Get hotel ratings based on automated sentiment analysis of online reviews.

---

## DESTINATION EXPERIENCES APIs

### Tours & Activities

#### 1. Tours and Activities Search by Location
- **Method**: GET
- **Endpoint**: `GET /v1/shopping/activities`
- **Key Query Parameters**:
  - `latitude` (required) - Latitude coordinate
  - `longitude` (required) - Longitude coordinate
  - `radius` (optional) - Search radius in km (default 1)
- **Purpose**: Search and book activities, sightseeing tours, day trips, and museum tickets in over 8,000 destinations.

#### 2. Tours and Activities by ID
- **Method**: GET
- **Endpoint**: `GET /v1/shopping/activities/{activityId}`
- **Purpose**: Get detailed information about a specific tour or activity by ID.

#### 3. Tours and Activities by Geographic Square
- **Method**: GET
- **Endpoint**: `GET /v1/shopping/activities/by-square`
- **Key Query Parameters**:
  - `north` - Northern boundary latitude
  - `west` - Western boundary longitude
  - `south` - Southern boundary latitude
  - `east` - Eastern boundary longitude
- **Purpose**: Search tours and activities within a defined geographic area.

### Destination Reference Data

#### 4. City Search
- **Method**: GET
- **Endpoint**: `GET /v1/reference-data/locations/cities`
- **Key Query Parameters**:
  - `countryCode` - Country code (e.g., FR)
  - `keyword` - City name keyword
  - `max` - Maximum results
  - `include` - Include AIRPORTS, HOTELS, etc.
- **Purpose**: Search for cities and get location information for attractions and activities.

---

## CARS AND TRANSFERS APIs

### Transfer Search & Booking

#### 1. Transfer Search
- **Method**: POST
- **Endpoint**: `POST /v1/shopping/transfer-offers`
- **Body**: JSON with location and date information
- **Purpose**: Search for ground transportation (car rental, shuttle, driver services) at travel destination.

#### 2. Transfer Booking
- **Method**: POST
- **Endpoint**: `POST /v1/ordering/transfer-orders`
- **Key Query Parameters**:
  - `offerId` - Transfer offer ID from search results
- **Body**: JSON with passenger information
- **Purpose**: Book a transfer order from available offers.

#### 3. Transfer Management
- **Method**: POST
- **Endpoint**: `POST /v1/ordering/transfer-orders/{transferOrderId}/transfers/cancellation`
- **Key Query Parameters**:
  - `confirmNbr` - Confirmation number
- **Purpose**: Manage and cancel transfer orders.

---

## ITINERARY MANAGEMENT

#### Trip Purpose Prediction
- **Method**: GET
- **Endpoint**: `GET /v1/travel/predictions/trip-purpose`
- **Key Query Parameters**:
  - `originLocationCode` - Origin airport code
  - `destinationLocationCode` - Destination airport code
  - `departureDate` - Departure date
  - `returnDate` (optional) - Return date for round trips
- **Purpose**: Forecast traveler purpose (Business or Leisure) with probability in context of search and shopping.

---

## AUTHORIZATION & SECURITY

#### 1. Access Granted Client Credentials (OAuth2)
- **Method**: POST
- **Endpoint**: `POST /v1/security/oauth2/token`
- **Body Parameters**:
  - `client_id` - Your API Key
  - `client_secret` - Your API Secret
  - `grant_type` - Set to "client_credentials"
- **Purpose**: Request access token using OAuth2 Client Credentials flow for API authentication.

#### 2. Get Token Information
- **Method**: GET
- **Endpoint**: `GET /v1/security/oauth2/token/{access_token}`
- **Purpose**: Retrieve information about an existing access token (expiration, scope, etc.).

---

## REFERENCE DATA APIs

### Airport & City Reference

#### 1. Airport & City Search by Keyword
- **Method**: GET
- **Endpoint**: `GET /v1/reference-data/locations`
- **Key Query Parameters**:
  - `keyword` (required) - Search keyword
  - `subType` - CITY, AIRPORT, or both
  - `countryCode` (optional) - Filter by country
- **Purpose**: Get full name, IATA code, and geographical info of cities/airports matching keyword.

#### 2. Airport & City Search by ID
- **Method**: GET
- **Endpoint**: `GET /v1/reference-data/locations/{locationId}`
- **Purpose**: Get detailed information about a specific city or airport by ID.

#### 3. Airport Nearest Relevant
- **Method**: GET
- **Endpoint**: `GET /v1/reference-data/locations/airports`
- **Key Query Parameters**:
  - `latitude` (required) - Latitude coordinate
  - `longitude` (required) - Longitude coordinate
  - `radius` (optional) - Search radius (default 500 km)
- **Purpose**: Find relevant airports within a radius of a given point based on estimated yearly flight traffic.

### Route Reference Data

#### 4. Airport Routes
- **Method**: GET
- **Endpoint**: `GET /v1/airport/direct-destinations`
- **Key Query Parameters**:
  - `departureAirportCode` (required) - Airport IATA code
  - `max` (optional) - Maximum results
- **Purpose**: Find all destinations served by a given airport (direct routes).

#### 5. Airline Routes
- **Method**: GET
- **Endpoint**: `GET /v1/airline/destinations`
- **Key Query Parameters**:
  - `airlineCode` (required) - Airline IATA code
  - `max` (optional) - Maximum results
- **Purpose**: Find all destinations served by a given airline.

### Airline & Check-in Reference

#### 6. Airline Code Lookup
- **Method**: GET
- **Endpoint**: `GET /v1/reference-data/airlines`
- **Key Query Parameters**:
  - `airlineCodes` (required) - Comma-separated airline codes
- **Purpose**: Get airline names and codes for given IATA codes.

#### 7. Flight Check-in Links
- **Method**: GET
- **Endpoint**: `GET /v2/reference-data/urls/checkin-links`
- **Key Query Parameters**:
  - `airlineCode` (required) - Airline IATA code
  - `language` (optional) - Language code
- **Purpose**: Get direct links to airline check-in pages to simplify passenger check-in process.

---

## SUMMARY BY CATEGORY

| Category | Count | Key Features |
|----------|-------|--------------|
| **Flight APIs** | 25 | Search, booking, pricing, predictions, analytics, status |
| **Hotel APIs** | 13 | Search, booking, ratings, location reference data |
| **Destination Experiences** | 4 | Tours, activities, attractions, attractions search |
| **Cars & Transfers** | 3 | Transfer search, booking, management |
| **Itinerary Management** | 1 | Trip purpose prediction |
| **Authorization** | 2 | OAuth2 token management |
| **Reference Data** | 7 | Airports, cities, airlines, routes |
| **TOTAL** | **55** | Complete travel ecosystem |

---

## BASE URL

All endpoints use the following base URL:
```
https://test.api.amadeus.com/
```

For production, use:
```
https://api.amadeus.com/
```

---

## AUTHENTICATION

All API endpoints (except the token endpoint itself) require:
- **Header**: `Authorization: Bearer {access_token}`
- Obtain access token via `/v1/security/oauth2/token` endpoint
- Token obtained via OAuth2 Client Credentials flow

---

## KEY PARAMETERS FREQUENTLY USED

| Parameter | Format | Purpose |
|-----------|--------|---------|
| `originLocationCode` | IATA (3 letters) | Origin airport/city code |
| `destinationLocationCode` | IATA (3 letters) | Destination airport/city code |
| `departureDate` | YYYY-MM-DD | Travel departure date |
| `returnDate` | YYYY-MM-DD | Return date (optional, for round trips) |
| `adults` | Integer | Number of adult passengers |
| `children` | Integer | Number of child passengers |
| `infants` | Integer | Number of infant passengers |
| `hotelIds` | Comma-separated | Hotel identifiers |
| `latitude` | Decimal | Geographic latitude |
| `longitude` | Decimal | Geographic longitude |
| `max` | Integer | Maximum results to return |
| `period` | YYYY-MM or YYYY | Time period for analytics |

---

## DOCUMENT METADATA

- **Source File**: Amadeus for Developers.postman_collection.json
- **File Location**: /home/user/google-flights-mcp/
- **Total Endpoints Analyzed**: 55
- **Analysis Date**: 2024
- **API Base URL**: https://test.api.amadeus.com/

