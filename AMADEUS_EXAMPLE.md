# Amadeus MCP Server - Usage Examples

This document provides practical examples of using the Amadeus MCP server.

## Configuration Example

### Environment Variables Setup

```bash
# ~/.bashrc or ~/.zshrc
export AMADEUS_CLIENT_ID="YourAPIKeyHere"
export AMADEUS_CLIENT_SECRET="YourAPISecretHere"
export AMADEUS_ENV="test"  # or "production"
```

### Claude Desktop Configuration

```json
{
  "mcpServers": {
    "amadeus": {
      "command": "mcp-server-amadeus",
      "env": {
        "AMADEUS_CLIENT_ID": "your_api_key",
        "AMADEUS_CLIENT_SECRET": "your_api_secret",
        "AMADEUS_ENV": "test"
      }
    }
  }
}
```

## Example Conversations

### Flight Search Example

**User:** "I need to fly from New York to London on December 15th, returning December 22nd. Find me business class options."

**Claude will use:**
```python
search_flights(
    origin="NYC",
    destination="LON",
    departure_date="2024-12-15",
    return_date="2024-12-22",
    adults=1,
    travel_class="BUSINESS",
    max_results=10,
    currency_code="USD"
)
```

**Response includes:**
- Multiple flight options with prices
- Airline information
- Departure/arrival times
- Connection details
- Duration information

---

### Multi-Step Booking Flow

**1. Search for flights**

**User:** "Find flights from San Francisco to Paris on January 10th"

```python
search_flights(
    origin="SFO",
    destination="PAR",
    departure_date="2025-01-10",
    adults=2
)
```

**2. Confirm pricing**

**User:** "Check the current price for offer #3"

```python
confirm_flight_price(
    flight_offer_data='{"id": "offer-123", ...}'
)
```

**3. Book the flight**

**User:** "Book this flight for John Doe and Jane Smith"

```python
book_flight(
    flight_offer_data='{"id": "offer-123", ...}',
    travelers='[
        {
            "id": "1",
            "dateOfBirth": "1985-05-15",
            "name": {"firstName": "John", "lastName": "Doe"},
            "gender": "MALE",
            "contact": {
                "emailAddress": "john@example.com",
                "phones": [{
                    "deviceType": "MOBILE",
                    "countryCallingCode": "1",
                    "number": "5551234567"
                }]
            }
        },
        {
            "id": "2",
            "dateOfBirth": "1987-08-20",
            "name": {"firstName": "Jane", "lastName": "Smith"},
            "gender": "FEMALE",
            "contact": {
                "emailAddress": "jane@example.com",
                "phones": [{
                    "deviceType": "MOBILE",
                    "countryCallingCode": "1",
                    "number": "5559876543"
                }]
            }
        }
    ]'
)
```

---

### Hotel Search & Booking

**User:** "Find hotels in central Paris for 2 adults, checking in Dec 20 and out Dec 25"

**Step 1: Get hotel IDs**
```python
search_hotels_by_city(
    city_code="PAR",
    radius=5,
    radius_unit="KM"
)
```

**Step 2: Get offers for specific hotels**
```python
get_hotel_offers(
    hotel_ids="HOTEL1,HOTEL2,HOTEL3",
    check_in_date="2024-12-20",
    check_out_date="2024-12-25",
    adults=2,
    room_quantity=1,
    currency="EUR"
)
```

**Step 3: Check ratings**
```python
get_hotel_ratings(
    hotel_ids="HOTEL1,HOTEL2,HOTEL3"
)
```

**Step 4: Book**
```python
book_hotel(
    offer_id="OFFER_123",
    guests='[{
        "name": {"firstName": "John", "lastName": "Doe"},
        "contact": {
            "email": "john@example.com",
            "phone": "+15551234567"
        }
    }]',
    payment='{
        "method": "CREDIT_CARD",
        "vendorCode": "VI",
        "cardNumber": "4111111111111111",
        "expiryDate": "2025-12"
    }'
)
```

---

### Inspiration & Discovery

**User:** "I have a week off in February and $1000 budget. Where can I go from Boston?"

```python
flight_inspiration_search(
    origin="BOS",
    max_results=20
)
```

**User:** "When is the cheapest time to fly from LA to Tokyo?"

```python
flight_cheapest_dates(
    origin="LAX",
    destination="TYO",
    one_way=False
)
```

---

### Price Analysis

**User:** "Is $450 a good price for a round-trip from Chicago to Miami on March 1st?"

```python
analyze_flight_price(
    origin="ORD",
    destination="MIA",
    departure_date="2025-03-01",
    currency_code="USD"
)
```

Response tells you if the price is above/below average based on historical data.

---

### Flight Status & Predictions

**User:** "What's the status of American Airlines flight 123 departing today?"

```python
get_flight_status(
    carrier_code="AA",
    flight_number="123",
    scheduled_departure_date="2024-11-13"
)
```

**User:** "How likely is this flight to be delayed?"

```python
predict_flight_delay(
    origin="JFK",
    destination="LAX",
    departure_date="2024-11-15",
    departure_time="14:30:00",
    arrival_date="2024-11-15",
    arrival_time="17:45:00",
    carrier_code="AA",
    flight_number="123",
    aircraft_code="738",
    duration="PT5H15M"
)
```

---

### Tours & Activities

**User:** "What can I do near the Eiffel Tower?"

```python
# Eiffel Tower coordinates: 48.8584, 2.2945
search_activities(
    latitude=48.8584,
    longitude=2.2945,
    radius=2
)
```

**User:** "Tell me more about activity ABC123"

```python
get_activity_details(
    activity_id="ABC123"
)
```

---

### Airport Transfers

**User:** "I need a transfer from JFK to my hotel in Manhattan on Dec 15 at 3pm"

```python
search_transfers(
    start_location="JFK",
    end_location="Times Square, New York, NY",
    transfer_type="PRIVATE",
    start_date_time="2024-12-15T15:00:00",
    passengers=2
)
```

**Note:** Valid transfer_type values are PRIVATE, TAXI, or HOURLY. Use PRIVATE for airport transfers.

---

### Reference Data Queries

**User:** "Find all airports in Japan"

```python
search_airports(
    keyword="Japan",
    country_code="JP"
)
```

**User:** "What are the closest airports to coordinates 34.0522, -118.2437?"

```python
get_nearest_airports(
    latitude=34.0522,
    longitude=-118.2437,
    radius=100
)
```

**User:** "Show me all destinations United Airlines flies to"

```python
get_airline_routes(
    airline_code="UA"
)
```

**User:** "What direct flights are available from LAX?"

```python
get_airport_routes(
    airport_code="LAX"
)
```

---

### Market Insights

**User:** "What are the most popular destinations from New York right now?"

```python
get_travel_insights(
    origin_city="NYC",
    period="2024-11",
    max_results=10
)
```

**User:** "Where are people booking flights to from London?"

```python
get_booking_insights(
    origin_city="LON",
    period="2024-11",
    max_results=10
)
```

**User:** "Is this trip likely business or leisure?"

```python
predict_trip_purpose(
    origin="SFO",
    destination="NYC",
    departure_date="2024-11-18",
    return_date="2024-11-22"
)
```

---

## Complex Multi-Service Example

**User:** "Plan a complete trip: flights from NYC to Paris Dec 15-22, hotel near Eiffel Tower, airport transfer, and tours"

Claude will orchestrate multiple tools:

1. **Search flights**
```python
search_flights(origin="NYC", destination="PAR",
               departure_date="2024-12-15", return_date="2024-12-22")
```

2. **Find hotels near Eiffel Tower**
```python
search_hotels_by_location(latitude=48.8584, longitude=2.2945, radius=2)
get_hotel_offers(hotel_ids="...", check_in_date="2024-12-15",
                 check_out_date="2024-12-22")
```

3. **Book airport transfer**
```python
search_transfers(start_location="CDG",
                end_location="48.8584,2.2945",
                transfer_type="PRIVATE",
                start_date_time="2024-12-15T10:00:00")
```

4. **Find activities**
```python
search_activities(latitude=48.8584, longitude=2.2945, radius=5)
```

Claude will present all options in an organized format for you to review and book.

---

## Tips for Best Results

### Date Formats
- Always use `YYYY-MM-DD` format
- Example: `2024-12-15` not `12/15/2024`

### Airport Codes
- Use 3-letter IATA codes: `JFK`, `LAX`, `LHR`
- City codes work too: `NYC`, `LON`, `PAR`
- Must be uppercase (server converts automatically)

### Airline Codes
- Use 2-letter IATA codes: `AA`, `UA`, `DL`
- Find codes with `get_airline_info()`

### Currency Codes
- Use 3-letter ISO codes: `USD`, `EUR`, `GBP`
- Consistent currency helps compare prices

### Passenger Counts
- `adults`: Age 12+
- `children`: Age 2-11
- `infants`: Under 2

### Travel Classes
- `ECONOMY` - Standard class
- `PREMIUM_ECONOMY` - Premium economy
- `BUSINESS` - Business class
- `FIRST` - First class

## Error Handling

All tools return errors in a consistent format:

```json
{
  "error": "Detailed error message explaining what went wrong"
}
```

Common errors:
- **Invalid IATA code** - Check airport/airline codes
- **Invalid date format** - Use YYYY-MM-DD
- **No results found** - Expand search criteria
- **Authentication error** - Check credentials
- **Rate limit** - Wait and retry

## Getting Help

- Check the error message first
- Review AMADEUS_README.md for configuration
- Visit Amadeus documentation: https://developers.amadeus.com
- Join Discord: https://discord.gg/cVrFBqx
