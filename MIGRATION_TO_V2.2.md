# Migration Guide: fast-flights 3.0rc0 → 2.2

## Why Migrate?

Version 3.0rc0 is incomplete and missing critical features:
- ❌ No Playwright fallback (less reliable)
- ❌ No fetch_mode parameter
- ❌ Direct round-trip bug

Version 2.2 is stable with:
- ✅ Playwright fallback for reliability
- ✅ `fetch_mode` parameter
- ✅ `is_best` flag
- ✅ Proven in production

## Changes Needed

### 1. Dependency Update

**pyproject.toml:**
```diff
- "fast-flights==3.0rc0",
+ "fast-flights==2.2",
```

### 2. Data Structure Differences

#### v3.0rc0 (Old) - Complex Structure
```python
flight.type              # "Round trip" | "One way"
flight.price             # Total price
flight.airlines          # List[str]
flight.flights           # List[SingleFlight] segments
flight.carbon            # CarbonEmission data

# Segments:
segment.from_airport     # Airport(code, name)
segment.to_airport       # Airport(code, name)
segment.departure        # SimpleDatetime
segment.arrival          # SimpleDatetime
segment.duration         # int (minutes)
segment.plane_type       # str
```

#### v2.2 (New) - Simple Structure
```python
flight.is_best           # Boolean - recommended flight
flight.name              # Airline name
flight.departure         # Departure time
flight.arrival           # Arrival time
flight.arrival_time_ahead # Time zone offset
flight.duration          # Duration
flight.stops             # Number of stops
flight.delay             # Delay info (optional)
flight.price             # Price
```

### 3. API Compatibility

**Good news:** The query API is the same!
```python
# Same in both versions
from fast_flights import FlightQuery, Passengers, get_flights, create_query

flights = [FlightQuery(date="2025-12-15", from_airport="SFO", to_airport="LAX")]
passengers = Passengers(adults=1)
query = create_query(flights=flights, trip="one-way", seat="economy", passengers=passengers)
result = get_flights(query)
```

**What changes:** The structure of objects returned by `get_flights()`

### 4. Code Changes Required

The `flight_to_dict()` function needs to handle both structures for compatibility.

**Detection strategy:**
- If object has `.flights` attribute → v3.0rc0 structure
- Otherwise → v2.2 structure

### 5. Features Gained

✅ **`is_best` flag** - Identify Google's recommended flights
✅ **Playwright fallback** - Better reliability when scraped
✅ **`fetch_mode` options** - common/fallback/force-fallback/local/bright-data
✅ **Stable release** - Production-ready

### 6. Features Lost

❌ **Detailed segments** - v2.2 doesn't expose individual flight segments
❌ **Carbon emissions** - No environmental data
❌ **Airline list** - Only airline name, not list
❌ **Airport details** - Simpler airport info

### 7. Workarounds Impact

**Direct round-trip fix:** Still needed! v2.2 may have same limitation
**SerpApi fallback:** Still useful but less needed with Playwright

### 8. Migration Steps

1. **Update dependency:**
   ```bash
   pip uninstall fast-flights
   pip install fast-flights==2.2
   # Or update pyproject.toml and run:
   pip install -e .
   ```

2. **Install Playwright browsers:**
   ```bash
   playwright install
   ```

3. **Test basic search:**
   ```python
   from fast_flights import FlightQuery, Passengers, get_flights, create_query

   flights = [FlightQuery(date="2025-12-15", from_airport="SFO", to_airport="LAX")]
   query = create_query(flights=flights, trip="one-way", seat="economy", passengers=Passengers(adults=1))
   result = get_flights(query)

   print(f"Found {len(result)} flights")
   if result:
       first = result[0]
       print(f"Price: {first.price}")
       print(f"Airline: {first.name}")
       print(f"Is best: {first.is_best}")
   ```

4. **Test round-trip search:**
   ```python
   flights = [
       FlightQuery(date="2025-12-15", from_airport="SFO", to_airport="LAX"),
       FlightQuery(date="2025-12-20", from_airport="LAX", to_airport="SFO"),
   ]
   query = create_query(flights=flights, trip="round-trip", seat="economy", passengers=Passengers(adults=1))
   result = get_flights(query)

   # Check if it returns complete round-trip packages
   print(f"Results: {len(result)}")
   for i, flight in enumerate(result[:3]):
       print(f"{i+1}. ${flight.price} - {flight.name} - Stops: {flight.stops}")
   ```

5. **Test Playwright fallback:**
   ```python
   query = create_query(..., fetch_mode="fallback")
   result = get_flights(query)
   ```

### 9. Rollback Plan

If issues arise:
```bash
pip install fast-flights==3.0rc0
git checkout <previous-commit>
```

## Expected Results

### Before (v3.0rc0)
- Occasional scraping failures (403 errors)
- No is_best indicators
- Complex segment data (when it works)
- Direct round-trip bug

### After (v2.2)
- More reliable scraping with Playwright fallback
- is_best flags on recommended flights
- Simpler data structure
- Direct round-trip: **needs testing**

## Testing Checklist

- [ ] One-way search works
- [ ] Round-trip search works
- [ ] Direct flights search works
- [ ] Multi-city search works
- [ ] is_best flag appears in results
- [ ] Playwright fallback works
- [ ] SerpApi fallback still works
- [ ] Performance is acceptable
- [ ] No regressions in existing features

## Timeline

- **Day 1:** Install v2.2, run basic tests
- **Day 2:** Test all search functions
- **Day 3:** Update code for compatibility
- **Day 4:** Integration testing
- **Day 5:** Deploy to production

## Support

If issues arise:
1. Check Playwright installation: `playwright install`
2. Test with fetch_mode="local" for local browser
3. Fallback to SerpApi if needed
4. Report issues to fast-flights maintainer
