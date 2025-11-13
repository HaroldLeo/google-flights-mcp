# Flight and Hotel API Fixes

## Issues Fixed

### 1. confirm_flight_price - Missing Mandatory Fields Error

**Problem:**
```
Error 400: MANDATORY DATA MISSING
Missing fields: travelerPricings, source, segment IDs
Cause: Using simplified flight offer format instead of complete raw data
```

The flight pricing confirmation API (`/v1/shopping/flight-offers/pricing`) requires the COMPLETE raw flight offer data from the Amadeus API, but users were passing the simplified summary format returned by `search_flights`.

**Root Cause:**
- `search_flights` was returning only a simplified summary for readability
- The simplified format was missing mandatory fields required by the pricing API:
  - `travelerPricings` - passenger pricing breakdown
  - `source` - offer source identifier (e.g., "GDS")
  - Segment `id` fields - unique identifiers for flight segments
- Users didn't know they needed the complete raw data, not the summary

**Solution:**
Enhanced both `search_flights` and `confirm_flight_price`:

1. **search_flights now returns BOTH formats:**
   - `offers` - Simplified summary for easy reading
   - `raw_offers` - Complete raw data for use with confirm_flight_price

2. **confirm_flight_price validates input:**
   - Checks for missing mandatory fields
   - Provides clear error message if simplified data is used
   - Shows example of correct usage
   - Still automatically removes aircraft codes to prevent validation errors

**Code Changes:**
```python
# search_flights now includes raw offers
summary = {
    "offers": [...],  # Simplified summary
    "raw_offers": offers[:max_results]  # Complete raw data
}

# confirm_flight_price validates input
if "travelerPricings" not in offer or "source" not in offer:
    return helpful_error_message_with_solution()
```

**Updated Functions:**
- `search_flights()` returns both simplified and raw offer data
- `confirm_flight_price()` validates input format and provides helpful errors
- Documentation updated with clear usage examples

**Result:**
✅ Users have access to both simplified and complete flight offer data
✅ Clear error messages when wrong format is used
✅ Easy-to-follow examples in documentation
✅ Automatic aircraft code sanitization still works

---

### 2. get_hotel_ratings - Maximum Properties Limit Error

**Problem:**
```
Error: "Number of properties exceeds maximum allowed"
OR: "Properties not found in database"
Cause: Incomplete/separated database, too many hotel IDs queried
```

The hotel sentiments API (`/v2/e-reputation/hotel-sentiments`) has:
1. A limit on how many hotels can be queried at once
2. An incomplete database - not all hotels have sentiment data

**Root Cause:**
- API limits the number of hotel IDs that can be queried in a single request
- No validation was performed on the number of hotel IDs
- No helpful error messages when hotels aren't in the sentiment database
- Users didn't know if the error was due to too many IDs or missing data

**Solution:**
Enhanced `get_hotel_ratings()` with:

1. **Input Validation:**
   - Parses and validates comma-separated hotel IDs
   - Trims whitespace and converts to uppercase
   - Checks for empty input

2. **Limit Enforcement:**
   - Hard limit: 10 hotels per request
   - Recommended: 1-3 hotels per request
   - Returns clear error if limit exceeded

3. **Better Error Messages:**
   - Explains why no results were returned
   - Suggests using hotel IDs from search results
   - Lists which hotel IDs were requested
   - Differentiates between "too many IDs" and "no data found"

4. **Result Validation:**
   - Checks if any data was returned
   - Reports how many hotels had ratings vs. how many were requested
   - Provides helpful suggestions

**Code Changes:**
```python
@mcp.tool()
async def get_hotel_ratings(hotel_ids: str) -> str:
    """
    Get hotel ratings based on sentiment analysis of reviews.

    The API has a limit on the number of hotels that can be queried at once.
    For best results, query 1-3 hotels at a time.

    Args:
        hotel_ids: Comma-separated hotel IDs (max recommended: 3 hotels)
    """
    # Input validation
    ids_list = [id.strip().upper() for id in hotel_ids.split(",") if id.strip()]

    # Limit checking
    if len(ids_list) > 10:
        return error_message_with_limit

    # Result validation
    if not data:
        return helpful_error_with_suggestions
```

**Result:**
✅ Clear error when too many hotel IDs provided
✅ Helpful guidance on limits (1-3 recommended, 10 max)
✅ Better error messages explaining why no results
✅ Suggestions to use IDs from search results
✅ Reports success rate (e.g., "2 out of 3 hotels found")

---

## Usage Examples

### Using confirm_flight_price (with validation and auto-sanitization)

```python
# Get flight offers
search_result = search_flights("JFK", "LAX", "2024-12-15")
result = json.loads(search_result)

# WRONG - Using simplified format (missing required fields)
# first_offer = result["offers"][0]  # ❌ This will fail!

# CORRECT - Using complete raw format
first_raw_offer = result["raw_offers"][0]  # ✅ Has all required fields
confirmed = confirm_flight_price(json.dumps(first_raw_offer))
# - Validates that all required fields are present
# - Automatically removes invalid aircraft codes
# - Returns confirmed pricing with tax details
```

### Using get_hotel_ratings (with validation)

```python
# GOOD: Query 1-3 hotels
ratings = get_hotel_ratings("MCLONGHM,ADNYCCTB")
# ✅ Works well

# WARNING: Query 4-10 hotels
ratings = get_hotel_ratings("ID1,ID2,ID3,ID4,ID5,ID6,ID7")
# ⚠️ Works but some may not have data

# ERROR: Query too many hotels
ratings = get_hotel_ratings("ID1,ID2,ID3,...,ID15")
# ❌ Returns clear error: "Too many hotel IDs (15). Please query 10 or fewer."

# NO DATA: Invalid hotel IDs
ratings = get_hotel_ratings("INVALID,BADID")
# Returns helpful error with suggestions
```

---

## Files Modified

1. **src/mcp_server_amadeus/server.py**
   - Added `sanitize_flight_offer_for_pricing()` function (lines 320-356)
   - Updated `confirm_flight_price()` to use sanitization (lines 359-405)
   - Enhanced `get_hotel_ratings()` with validation and better errors (lines 942-1005)

2. **FLIGHT_HOTEL_API_FIXES.md** (this file)
   - Complete documentation of both fixes

---

## Testing Recommendations

### Test confirm_flight_price

```bash
# Test with complete raw offer data
search_result = search_flights("JFK", "LAX", "2024-12-20")
result = json.loads(search_result)

# Test with raw offer (should work)
confirm_flight_price(json.dumps(result["raw_offers"][0]))  # ✅ Should succeed

# Test with simplified offer (should give helpful error)
confirm_flight_price(json.dumps(result["offers"][0]))  # ❌ Should explain what's wrong
```

### Test get_hotel_ratings

```bash
# Test valid hotels (1-3)
get_hotel_ratings("MCLONGHM")  # Should work

# Test multiple hotels
get_hotel_ratings("MCLONGHM,ADNYCCTB,ELONMFS")  # Should work

# Test too many
get_hotel_ratings("ID1,ID2,ID3,ID4,ID5,ID6,ID7,ID8,ID9,ID10,ID11")  # Should error

# Test invalid IDs
get_hotel_ratings("INVALID,BADID")  # Should give helpful error
```

---

## Impact

**confirm_flight_price:**
- **Before:** Failed with Error 400 "MANDATORY DATA MISSING" when using simplified offer format
- **After:**
  - `search_flights` now returns both simplified and raw offer data
  - Validates input and provides clear error if wrong format used
  - Automatically sanitizes aircraft codes
  - Succeeds with proper raw offer data

**get_hotel_ratings:**
- **Before:** Confusing errors about limits and missing data
- **After:** Clear limits, helpful error messages, guidance on usage

Both tools are now more robust and user-friendly!
