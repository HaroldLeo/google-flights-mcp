# fast-flights Version Comparison: 2.2 vs 3.0rc0 vs GitHub Main

## 🚨 CRITICAL: API Incompatibility Between Versions

**BREAKING CHANGE ALERT:** v2.2 and v3.0rc0 have **completely different APIs** that are NOT compatible!

### v2.2 API
```python
from fast_flights import FlightData, Passengers, get_flights

result = get_flights(
    flight_data=[FlightData(date="2025-12-15", from_airport="SFO", to_airport="LAX")],
    trip="one-way",
    passengers=Passengers(adults=1),
    seat="economy",
    fetch_mode="common",  # Supports: common/fallback/force-fallback/local
    max_stops=None
)
```

### v3.0rc0 API
```python
from fast_flights import FlightQuery, Passengers, create_query, get_flights

flights = [FlightQuery(date="2025-12-15", from_airport="SFO", to_airport="LAX")]
query = create_query(flights=flights, trip="one-way", seat="economy", passengers=Passengers(adults=1))
result = get_flights(query)  # Takes query string, not parameters
```

### Key API Differences

| Component | v2.2 | v3.0rc0 |
|-----------|------|---------|
| **Flight definition** | `FlightData` | `FlightQuery` |
| **Import names** | `FlightData` | `FlightQuery` |
| **Query method** | Direct `get_flights()` call | `create_query()` → `get_flights()` |
| **Query parameter** | Named parameters | Query string |
| **`fetch_mode`** | ✅ Available | ❌ Not available |
| **`create_query()` function** | ❌ Doesn't exist | ✅ Required |

### Migration Impact

**Downgrading to v2.2 requires rewriting ALL search functions:**
- Every `create_query()` call must be replaced
- Every `FlightQuery` → `FlightData`
- Every `get_flights(query)` → `get_flights(flight_data=..., trip=..., ...)`
- Estimated: **~500 lines of code changes across 10+ functions**

### Why This Happened

The v3.0 rewrite changed the entire API architecture:
- v2.2: Direct function calls with named parameters
- v3.0rc0: Query string generation (similar to Google Flights URL encoding)

This is why v3.0rc0 is a "release candidate" - it's a major API overhaul.

---

## Executive Summary

**CRITICAL FINDING:** Version 3.0rc0 (currently used) is an **incomplete early release candidate** that's **missing significant features** compared to both version 2.2 AND the GitHub main branch.

---

## Version Timeline

| Version | Release Date | Status | Notes |
|---------|-------------|--------|-------|
| **2.2** | Mar 8, 2025 | Stable | Added local Playwright support |
| **2.1** | Feb 25, 2025 | Stable | - |
| **2.0** | Jan 1, 2025 | Stable | Added fallback Playwright serverless |
| **3.0rc0** | Aug 27, 2025 | Pre-release | **NOT tagged on GitHub!** Only on PyPI |
| **GitHub main** | Aug 27, 2025+ | Development | Most complete version |

---

## Feature Comparison

### Version 2.2 (Stable) ✅

**Included:**
- ✅ Standard HTTP client scraping
- ✅ Playwright fallback support (serverless)
- ✅ Local Playwright browser automation
- ✅ `fetch_mode` parameter with options:
  - `"common"` - Standard HTTP
  - `"fallback"` - HTTP first, then Playwright
  - `"force-fallback"` - Force Playwright
  - `"local"` - Local browser automation
- ✅ Stable, tested, proven in production

**Flight Object Structure (v2.x):**
```python
flight.is_best          # Boolean - if this is a "best flight"
flight.name             # Airline name
flight.departure        # Departure time
flight.arrival          # Arrival time
flight.duration         # Duration in minutes
flight.stops            # Number of stops
flight.price            # Price
flight.airline          # Airline code
```

---

### Version 3.0rc0 (Current - INCOMPLETE) ⚠️

**What Changed:**
- 🔄 Restructured package (fetcher.py → core.py)
- ✅ Added `integration` parameter for BrightData (paid proxy service)
- ✅ New `Flights` object structure (more detailed)

**What's MISSING:**
- ❌ NO `fetch_mode` parameter
- ❌ NO Playwright fallback modules
- ❌ NO `local_playwright.py`
- ❌ NO `fallback_playwright.py`
- ❌ NOT tagged on GitHub (inconsistent release)

**Function Signature:**
```python
get_flights(q: Union[Query, str], /, *,
            proxy: Optional[str] = None,
            integration: Optional[Integration] = None)
```

**New Flights Object Structure (v3.0rc0):**
```python
flight.type             # "Round trip" | "One way" | etc.
flight.price            # Total price
flight.airlines         # List[str] - airline names
flight.flights          # List[SingleFlight] - segments
flight.carbon           # CarbonEmission data

# Each segment (SingleFlight):
segment.from_airport    # Airport (name, code)
segment.to_airport      # Airport (name, code)
segment.departure       # SimpleDatetime
segment.arrival         # SimpleDatetime
segment.duration        # int (minutes)
segment.plane_type      # str
```

**What's Better in 3.0rc0:**
- ✅ More detailed segment information
- ✅ Carbon emission data
- ✅ Better structure for multi-segment flights
- ✅ Clearer airport information

**What's WORSE in 3.0rc0:**
- ❌ Missing `is_best` flag
- ❌ Missing `flight_number`
- ❌ Missing Playwright fallback (less reliable)
- ❌ Incomplete release (transitional state)

---

### GitHub Main Branch (Development) 🚀

**Has EVERYTHING:**
- ✅ All features from v3.0rc0 (new structure)
- ✅ All features from v2.2 (Playwright fallback)
- ✅ `fetch_mode` parameter fully implemented
- ✅ `data_source` parameter
- ✅ Latest bug fixes

**Function Signature:**
```python
get_flights(...,
            fetch_mode: str = "common",
            data_source: str = "html",
            ...)
```

---

## The Problem with 3.0rc0

### Why It's Incomplete

The PyPI 3.0rc0 appears to be from a **transitional state** where:

1. ✅ Package was restructured
2. ✅ Integration system was added (BrightData)
3. ❌ **But Playwright fallback hadn't been integrated yet**
4. ❌ **Parser wasn't updated to extract all fields**

### Evidence

- **NOT tagged on GitHub:** The v3.0rc0 tag doesn't exist in the repository
- **Timeline mismatch:** Released same day as latest GitHub updates (Aug 27)
- **Incomplete features:** Missing modules present in v2.2

This strongly suggests **3.0rc0 was pushed to PyPI prematurely**.

---

## Impact on This Project

### What We're GAINING with 3.0rc0

✅ **Better data structure** for multi-segment flights
✅ **Carbon emissions** data
✅ **Clearer airport information**
✅ **Better round-trip handling** (when it works)

### What We're LOSING with 3.0rc0

❌ **Playwright fallback** - Less reliable scraping, more 403 errors
❌ **`is_best` flag** - Can't identify Google's recommended flights
❌ **Flight numbers** - Can't show specific flight codes
❌ **Fetch mode options** - Stuck with basic HTTP scraping
❌ **Local Playwright** - Can't use browser automation locally

### Critical Issues Discovered

1. **Direct round-trip bug:** `max_stops=0` + `trip="round-trip"` only returns outbound flights
   - **Workaround implemented:** Two-leg search
   - **Status:** FIXED in our code

2. **Missing return flights:** Related to the incomplete parser
   - **Status:** FIXED with our workaround

3. **No fallback reliability:** When Google blocks requests, no automatic retry with Playwright
   - **Status:** Using SerpApi as fallback instead

---

## Recommendations (UPDATED: API Incompatibility Discovered)

### Option 1: Stay on Version 3.0rc0 ⭐ RECOMMENDED (CHANGED)

**Why this changed:** API incompatibility makes downgrading to v2.2 require massive code rewrite (~500 lines).

**Pros:**
- ✅ No code changes needed - everything already works
- ✅ Better data structure (detailed segments, carbon data)
- ✅ Our workarounds fix the bugs (direct round-trip, return flights)
- ✅ SerpApi fallback compensates for missing Playwright

**Cons:**
- ❌ No Playwright fallback (must rely on SerpApi)
- ❌ No `is_best` flag
- ❌ No `fetch_mode` parameter
- ❌ Incomplete release

**Migration Effort:** None - just revert pyproject.toml to v3.0rc0

---

### Option 2: Downgrade to Version 2.2 (NOT RECOMMENDED)

**Why not recommended:** Requires massive API rewrite.

**Pros:**
- ✅ Playwright fallback for reliability
- ✅ `fetch_mode` parameter
- ✅ `is_best` flag
- ✅ Stable, production-ready

**Cons:**
- ❌ **MASSIVE code rewrite required (~500 lines)**
- ❌ Different API: `FlightData` vs `FlightQuery`
- ❌ No `create_query()` function
- ❌ All search functions must be rewritten
- ❌ High risk of introducing bugs

**Migration Effort:** Very High - rewrite all search functions

---

### Option 3: Switch to GitHub Main Branch

```bash
pip install git+https://github.com/AWeirdDev/flights.git
```

**Pros:**
- ✅ Best of both worlds (v3.0rc0 API + Playwright)
- ✅ Latest bug fixes
- ✅ All features
- ✅ No code changes needed

**Cons:**
- ❌ Unstable, development version
- ❌ May break without warning
- ❌ No version pinning
- ❌ Harder to debug

**Migration Effort:** Low - should work with current code

---

### Option 4: Wait for Official 3.0 Stable (Previously Option 4)

**Pros:**
- ✅ No migration needed
- ✅ Better data structure than v2.x
- ✅ Workarounds already implemented

**Cons:**
- ❌ Incomplete, buggy version
- ❌ No Playwright fallback
- ❌ Missing features vs v2.2
- ❌ Using a pre-release in production

**When to Use:** If current functionality is sufficient and SerpApi fallback covers reliability needs

---

### Option 4: Wait for Official 3.0 Stable

**Pros:**
- ✅ Best long-term solution
- ✅ Will have all features
- ✅ Stable release

**Cons:**
- ❌ Unknown timeline
- ❌ Stuck with current limitations until then

---

## Recommended Action Plan

### Immediate (This Week)

1. **Test with version 2.2:**
   ```bash
   pip install fast-flights==2.2
   ```

2. **Compare scraping reliability:**
   - Run the same queries with 2.2 vs 3.0rc0
   - Check failure rates
   - Test Playwright fallback

3. **Measure data quality:**
   - Do we get `is_best` flags?
   - Are flight numbers included?
   - How's the segment detail?

### Short-term (Next Month)

4. **If 2.2 is more reliable:** Migrate to 2.2
   - Update `flight_to_dict()` to handle v2.x structure
   - Test all search functions
   - Update documentation

5. **If 3.0rc0 is acceptable:** Stay on 3.0rc0
   - Keep SerpApi fallback
   - Monitor for official 3.0 stable release
   - Plan migration path

### Long-term

6. **Watch for official 3.0 stable release**
7. **Migrate when available**
8. **Maintain fallback strategies** (SerpApi) regardless of version

---

## Conclusion

**Version 3.0rc0 is incomplete and missing critical features compared to v2.2.**

The safest approach is to **downgrade to version 2.2** for reliability, or **wait for official 3.0 stable release**.

If immediate migration isn't possible, **continue with 3.0rc0 but maintain SerpApi fallback** and our custom workarounds.

---

## Further Investigation Needed

- [ ] Check if GitHub main branch fixes the direct round-trip bug
- [ ] Test actual reliability differences between versions
- [ ] Contact package maintainer about 3.0 release timeline
- [ ] Evaluate if v2.2 structure requires major refactoring
