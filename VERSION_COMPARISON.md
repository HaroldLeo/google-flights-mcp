# fast-flights Version Comparison: 2.2 vs 3.0rc0 vs GitHub Main

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

## Recommendations

### Option 1: Switch to Version 2.2 (Stable) ⭐ RECOMMENDED

**Pros:**
- ✅ Stable, proven in production
- ✅ Playwright fallback for reliability
- ✅ All scraping features work
- ✅ No unexpected bugs

**Cons:**
- ❌ Older data structure (less detailed segments)
- ❌ No carbon emissions data
- ❌ Requires code changes to adapt

**Migration Effort:** Medium - need to update `flight_to_dict()` to handle old structure

---

### Option 2: Switch to GitHub Main Branch

```bash
pip install git+https://github.com/AWeirdDev/flights.git
```

**Pros:**
- ✅ Best of both worlds (new structure + Playwright)
- ✅ Latest bug fixes
- ✅ All features

**Cons:**
- ❌ Unstable, development version
- ❌ May break without warning
- ❌ No version pinning
- ❌ Harder to debug

**Migration Effort:** Low - should work with current code

---

### Option 3: Stay with 3.0rc0 (Current)

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
