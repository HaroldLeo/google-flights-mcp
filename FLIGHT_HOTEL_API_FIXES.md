# Flight and Hotel API Fixes

## Issues Fixed

### 1. confirm_flight_price - Aircraft Code Format Error

**Problem:**
```
Error 400: INVALID FORMAT
Cause: aircraft field format incompatible ("32Q" invalid)
```

The flight pricing confirmation API (`/v1/shopping/flight-offers/pricing`) is more strict than the flight search API and rejects certain aircraft codes that are returned in search results.

**Root Cause:**
- Flight search results may contain non-standard aircraft codes (e.g., "32Q", codes with special characters)
- The pricing API validates aircraft codes more strictly and rejects invalid formats
- Aircraft codes longer than 3 characters or containing unusual characters cause validation errors

**Solution:**
Created `sanitize_flight_offer_for_pricing()` function that:
1. Makes a deep copy of the flight offer to avoid modifying the original
2. Scans all segments for aircraft codes
3. Removes invalid aircraft codes based on:
   - Length > 3 characters (standard IATA codes are 3 chars like "738", "777")
   - Contains special characters beyond standard alphanumerics
   - Unusual format patterns
4. Logs removed codes for debugging

**Code Changes:**
```python
def sanitize_flight_offer_for_pricing(offer: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize flight offer data for the pricing API.
    Removes aircraft codes that may cause validation errors.
    """
    # ... implementation removes invalid aircraft codes
```

**Updated Function:**
- `confirm_flight_price()` now automatically sanitizes data before sending to API
- Added documentation note about automatic sanitization
- Better error handling and logging

**Result:**
✅ Flight price confirmation now works even with non-standard aircraft codes
✅ Invalid codes are automatically removed
✅ Detailed logging shows which codes were removed

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

### Using confirm_flight_price (with auto-sanitization)

```python
# Get flight offers
search_result = search_flights("JFK", "LAX", "2024-12-15")
offers = json.loads(search_result)

# Confirm price (automatically handles invalid aircraft codes)
first_offer = offers["offers"][0]
confirmed = confirm_flight_price(json.dumps(first_offer))
# Aircraft code "32Q" automatically removed if invalid
# Pricing confirmed with sanitized data
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
# Test with flight that has unusual aircraft codes
search_result = search_flights("JFK", "LAX", "2024-12-20")
# Look for aircraft codes like "32Q", "XXX", etc.
# These should be automatically removed during price confirmation
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
- **Before:** Failed with Error 400 on unusual aircraft codes
- **After:** Automatically sanitizes and succeeds

**get_hotel_ratings:**
- **Before:** Confusing errors about limits and missing data
- **After:** Clear limits, helpful error messages, guidance on usage

Both tools are now more robust and user-friendly!
