# Amadeus MCP Tools Simplification

## Summary

Simplified from **32 tools to 26 tools** by disabling booking tools and predict_trip_purpose that provide minimal practical value.

---

## Disabled Tools (6 total)

### 1. Booking Tools (5 tools) ❌

**Disabled:**
- `book_flight`
- `get_flight_order`
- `cancel_flight_order`
- `book_hotel`
- `book_transfer`

**Reasons for Removal:**

1. **Test Environment Limitations**
   - Amadeus test environment doesn't create real bookings
   - No actual tickets or confirmations are issued
   - Cannot test end-to-end booking flow properly

2. **Complex Requirements**
   - Requires extensive traveler information:
     - Full passenger details (name, DOB, gender)
     - Passport information (number, expiry, nationality)
     - Contact details (email, phone)
     - Payment information (card details)
   - Error-prone data entry
   - Privacy/security concerns with handling payment data

3. **User Preferences**
   - Users overwhelmingly prefer to book directly on:
     - Airline websites (for flights)
     - Hotel websites or OTAs like Booking.com (for hotels)
     - Direct provider websites (for transfers)
   - Reasons:
     - Loyalty programs and points
     - Customer service and support
     - Seat selection and upgrades
     - Trust and familiarity

4. **Limited MCP Value**
   - MCP tools excel at **search and discovery**
   - Booking is a **transactional operation** better suited for dedicated UIs
   - Users want visual confirmation before booking
   - Complex booking flows don't translate well to chat interfaces

**What Users Should Use Instead:**
- ✅ `confirm_flight_price` - Get detailed pricing and taxes
- ✅ `get_hotel_offers` - Get hotel availability and rates
- ✅ `search_transfers` - Find transfer options and prices
- Then book directly on the provider's website

---

### 2. predict_trip_purpose ❌

**Disabled:**
- `predict_trip_purpose` - AI prediction of business vs leisure travel

**Reasons for Removal:**

1. **Users Already Know**
   - Business travelers know they're on a business trip
   - Vacationers know they're on vacation
   - No need for AI to tell them what they already know

2. **No Actionable Value**
   - Prediction doesn't influence:
     - Flight search results
     - Pricing
     - Availability
     - Booking decisions
   - Users make choices based on:
     - Price
     - Schedule
     - Airline preference
     - Loyalty programs

3. **Limited Use Cases**
   - Potential B2B applications (corporate travel management)
   - Market research (aggregate data analysis)
   - Neither are primary MCP use cases
   - Individual travelers don't benefit

4. **Example of "Cool" but Not Useful**
   ```
   User: "I'm flying NYC to Chicago Monday-Friday"
   AI: "This is probably a business trip (92% confidence)"
   User: "...okay? I already knew that. What flights are available?"
   ```

**Better Alternatives:**
- Users can simply state their preferences directly
- "I need a flight for a business trip" - if it matters
- "Looking for a vacation package" - explicit intent
- No need for AI inference

---

## Remaining Tools (26) ✅

### Core Search & Discovery (14 tools)

**Flights (11):**
1. `search_flights` ⭐⭐⭐⭐⭐
2. `confirm_flight_price` ⭐⭐⭐⭐
3. `flight_inspiration_search` ⭐⭐⭐⭐
4. `flight_cheapest_dates` ⭐⭐⭐⭐⭐
5. `analyze_flight_price` ⭐⭐⭐
6. `predict_flight_delay` ⭐⭐
7. `get_flight_status` ⭐⭐

**Hotels (4):**
8. `search_hotels_by_city` ⭐⭐⭐⭐⭐
9. `search_hotels_by_location` ⭐⭐⭐⭐
10. `get_hotel_offers` ⭐⭐⭐⭐⭐
11. `get_hotel_ratings` ⭐⭐

**Activities & Transfers (3):**
12. `search_activities` ⭐⭐⭐
13. `get_activity_details` ⭐⭐
14. `search_transfers` ⭐⭐⭐

### Reference Data (6 tools)
15. `search_airports` ⭐⭐⭐⭐
16. `search_cities` ⭐⭐⭐
17. `get_nearest_airports` ⭐⭐
18. `get_airline_info` ⭐⭐
19. `get_airline_routes` ⭐⭐
20. `get_airport_routes` ⭐⭐

### Market Insights (2 tools)
21. `get_travel_insights` ⭐⭐
22. `get_booking_insights` ⭐⭐

---

## Benefits of Simplification

### 1. **Clearer Focus**
- MCP server now clearly focused on **search** and **discovery**
- Removed confusion about booking capabilities
- Users know to search with MCP, book elsewhere

### 2. **Reduced Complexity**
- Less code to maintain
- Fewer edge cases and error scenarios
- Simpler documentation

### 3. **Better User Experience**
- No false expectations about booking
- Faster responses (fewer unused tools)
- Clear workflow: Search → Compare → Book externally

### 4. **Easier Testing**
- Focus testing on search functionality
- Don't need mock booking data
- More reliable test coverage

### 5. **Security**
- Don't handle sensitive payment information
- Reduced liability
- Better privacy

---

## Future Considerations

### Tools to Consider Removing Next

Based on usage analysis, these tools could also be candidates for removal:

**Low Priority Analytics (4 tools) - ⭐⭐:**
- `analyze_flight_price` - "Is this a good price?" - subjective
- `predict_flight_delay` - Requires complete flight details
- `get_flight_status` - Users check airline apps directly
- `predict_trip_purpose` - Already removed!

**Niche Reference Data (3 tools) - ⭐⭐:**
- `get_airline_info` - Just airline names, low value
- `get_airline_routes` - "What routes does AA fly?" - limited use
- `get_airport_routes` - Can use `flight_inspiration_search` instead

**Market Insights (2 tools) - ⭐⭐:**
- `get_travel_insights` - "Most popular destinations" - interesting but not essential
- `get_booking_insights` - Similar to above

### Core Tools to Always Keep (11 tools) - ⭐⭐⭐⭐⭐

**These are the absolute essentials:**
1. `search_flights` - Primary use case
2. `flight_cheapest_dates` - High value for budget travelers
3. `flight_inspiration_search` - Great for discovery
4. `confirm_flight_price` - Important for accurate pricing
5. `search_hotels_by_city` - Core hotel search
6. `search_hotels_by_location` - Alternative hotel search
7. `get_hotel_offers` - Get availability and pricing
8. `search_airports` - Essential reference data
9. `search_cities` - Essential reference data
10. `search_activities` - Good for trip planning
11. `search_transfers` - Useful airport transport info

---

## Implementation Notes

### How Tools Were Disabled

Tools were disabled by:
1. Commenting out `@mcp.tool()` decorator
2. Replacing function body with error message
3. Keeping function in codebase for reference

Example:
```python
# @mcp.tool()
async def book_flight(...):
    """[DISABLED] Book a flight..."""
    return json.dumps({
        "error": "Booking tools are disabled. Use confirm_flight_price then book on airline website.",
        "reason": "Test environment does not create real bookings"
    })
```

### To Re-enable

If needed, simply:
1. Uncomment `@mcp.tool()` decorator
2. Restore original function implementation

---

## Conclusion

By focusing on **search and discovery**, this MCP server now provides:
- ✅ Clear, practical value
- ✅ Easier to understand and use
- ✅ Better aligned with user needs
- ✅ More maintainable codebase

**Bottom line:** 26 useful tools > 32 tools with 6 that don't work well.
