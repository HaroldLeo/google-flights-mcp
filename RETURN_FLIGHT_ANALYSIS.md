# Return Flight Options Issue - Analysis and Solution

## Problem Statement

The tools don't return return flight options for round-trip searches.

## Investigation Findings

### How Google Flights Works (Web UI)

1. User searches for round-trip flights
2. Google shows **list of outbound flight options**
3. User selects an outbound flight
4. Google shows **list of return flight options** for that outbound choice
5. User selects a return flight
6. Google shows combined price

### How fast-flights Library Works (Primary Method)

**Round-trip query structure:**
```python
flights = [
    FlightQuery(date=departure_date, from_airport=origin, to_airport=destination),
    FlightQuery(date=return_date, from_airport=destination, to_airport=origin),
]
query = create_query(flights=flights, trip="round-trip", ...)
result = get_flights(query)
```

**Result structure (fast-flights 3.0rc0):**
- Returns a list of `Flights` objects
- Each `Flights` object represents a **complete round-trip package**
- The `flights` attribute contains **all segments** (both outbound AND return legs)
- Price is the **total round-trip price**

```
result[0] (Flights object)
  ├── price: 450  (total round-trip price)
  ├── airlines: ["United", "Delta"]
  ├── type: "Round trip"
  ├── flights: [  (all segments including return)
  │   ├── Segment 1: SFO → ORD (outbound, leg 1)
  │   ├── Segment 2: ORD → JFK (outbound, leg 2)
  │   ├── Segment 3: JFK → DEN (return, leg 1)
  │   └── Segment 4: DEN → SFO (return, leg 2)
  │   ]
  └── carbon: {...}
```

**Limitation**: Users cannot mix-and-match outbound/return flights. They get pre-combined packages.

### How SerpApi Works (Fallback Method)

**Current Implementation:** ❌ INCOMPLETE

The current `get_flights_from_serpapi()` function:
```python
params = {
    "type": 1,  # Round trip
    "outbound_date": departure_date,
    "return_date": return_date,
    ...
}
results = search.get_dict()
```

**Problem**: This returns **only outbound flight options**!

**SerpApi's Actual Flow:**

1. **Step 1**: Search with round-trip parameters → Returns outbound flights
   - Each outbound flight has a `departure_token`

2. **Step 2**: Make a second API call with `departure_token` → Returns return flights for that outbound choice
   ```python
   params = {
       "engine": "google_flights",
       "departure_token": "<token-from-step-1>",
       ...
   }
   ```

3. **Step 3**: User selects both outbound and return → Get combined booking

**Current Code Behavior**:
- ✅ Makes Step 1 (gets outbound flights)
- ❌ Skips Step 2 (never fetches return flights)
- ❌ Returns only outbound flights as if they were complete round-trips

## Root Cause

**SerpApi fallback does not implement the `departure_token` flow to fetch return flight options.**

The `get_flights_from_serpapi()` function only makes a single API call and returns outbound flights. It never:
1. Extracts `departure_token` from results
2. Makes a second call to get return flights
3. Combines or presents both options

## Solution Options

### Option 1: Implement Proper SerpApi Round-Trip Flow (Complex)

**Pros:**
- Matches Google Flights UI behavior
- Users can select from multiple outbound and return combinations
- More flexibility

**Cons:**
- Requires significant code changes
- Needs to restructure response format
- More API calls (higher costs for SerpApi users)
- Different response format than fast-flights

**Implementation:**
```python
# Step 1: Get outbound flights
outbound_results = get_outbound_flights(...)
outbound_flights = outbound_results.get("best_flights", [])

# Step 2: For each outbound option, get return flights
round_trip_combinations = []
for outbound in outbound_flights[:max_outbound]:
    departure_token = outbound.get("departure_token")
    return_flights = get_return_flights(departure_token, ...)

    for return_flight in return_flights:
        combination = {
            "outbound": outbound,
            "return": return_flight,
            "total_price": outbound["price"] + return_flight["price"],
            ...
        }
        round_trip_combinations.append(combination)

return round_trip_combinations
```

### Option 2: Match fast-flights Behavior (Simpler)

**Pros:**
- Consistent response format between primary and fallback
- Simpler implementation
- Fewer API calls (lower costs)
- Easier for users to understand

**Cons:**
- Users can't see all outbound/return combinations
- Only shows best combinations (as determined by SerpApi)

**Implementation:**
```python
# Get round-trip results (SerpApi returns best combinations)
results = get_flights(...)

# SerpApi already combines flights into round-trip packages
# Just need to ensure we're extracting both outbound AND return segments

for flight in results["best_flights"]:
    flights_array = flight.get("flights", [])
    # flights_array should contain both outbound and return segments
    # Normalize and return as complete round-trips
```

### Option 3: Add Configuration Parameter

Let users choose behavior:

```python
async def search_round_trip_flights(
    ...,
    separate_legs: bool = False  # New parameter
):
    """
    separate_legs: If True, return separate outbound/return options.
                   If False (default), return combined round-trip packages.
    """
```

## Recommended Solution

**Option 2** (Match fast-flights behavior) for v1, with **Option 3** (configuration) as future enhancement.

**Reasoning:**
1. Consistency: Same behavior whether using fast-flights or SerpApi
2. Simplicity: Less code, fewer API calls, lower costs
3. User experience: Consistent response format
4. Practicality: Most users want "show me cheap round-trips", not "let me mix and match every combination"

## Implementation Plan

1. **Verify current SerpApi behavior**
   - Test that SerpApi round-trip results include both outbound AND return segments
   - Confirm `flights` array contains all legs

2. **Fix `normalize_serpapi_flight()` if needed**
   - Ensure it correctly extracts all segments (outbound + return)
   - Verify total_duration includes full round-trip
   - Check that price is total round-trip price

3. **Update documentation**
   - Clarify that round-trip searches return complete packages
   - Explain that mix-and-match requires separate one-way searches
   - Add note about SerpApi departure_token for future enhancement

4. **Add tests**
   - Test round-trip with SerpApi fallback
   - Verify both outbound and return segments are present
   - Confirm prices are total round-trip prices

## Future Enhancements

If users request the full "select outbound, then select return" flow:

1. Add `separate_legs` parameter
2. Implement departure_token flow for SerpApi
3. Create new response format for separate leg selection
4. Update documentation with examples

## Notes

- Google Flights website shows separate selection because it's interactive
- API/scraping tools typically return pre-combined packages for simplicity
- Most flight search APIs (Skyscanner, Kayak, etc.) work this way
- Users wanting maximum flexibility should use two one-way searches
