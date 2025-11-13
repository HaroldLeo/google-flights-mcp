# Google Flights vs Amadeus MCP Servers - Comparison

This repository now contains **two independent MCP servers** for flight and travel data. Here's when to use each:

## Quick Comparison

| Feature | Google Flights Server | Amadeus Server |
|---------|----------------------|----------------|
| **Entry Point** | `mcp-server-google-flights` | `mcp-server-amadeus` |
| **Cost** | Free (with optional SerpApi fallback) | Free tier available, paid for production |
| **Setup Complexity** | Easy (no API key required for basic use) | Moderate (requires Amadeus account) |
| **Authentication** | Optional SerpApi key | Required OAuth2 credentials |
| **Flight Search** | ✅ Excellent | ✅ Excellent |
| **Flight Booking** | ❌ No | ✅ Yes |
| **Hotels** | ❌ No | ✅ Yes (5 tools) |
| **Tours & Activities** | ❌ No | ✅ Yes (2 tools) |
| **Airport Transfers** | ❌ No | ✅ Yes (2 tools) |
| **Market Insights** | ❌ No | ✅ Yes (3 tools) |
| **Flight Analytics** | ❌ Limited | ✅ Advanced (AI-powered) |
| **Real-time Data** | ✅ Yes (Google Flights) | ✅ Yes (Amadeus API) |
| **Total Tools** | ~6 flight tools | 32 travel tools |

## Detailed Breakdown

### Google Flights MCP Server

**Best for:**
- Quick flight searches without setup
- Users who don't want to create API accounts
- Simple price comparisons
- Getting started quickly

**Strengths:**
- ✅ No API credentials required for basic use
- ✅ Fast and simple setup
- ✅ Direct access to Google Flights data
- ✅ SerpApi fallback for round-trip searches
- ✅ Free for most use cases

**Limitations:**
- ❌ Flight search only (no hotels, activities, etc.)
- ❌ Cannot make actual bookings
- ❌ Limited analytics and predictions
- ❌ Round-trip searches require SerpApi for some routes
- ❌ No access to ancillary services

**Available Tools:**
1. `search_flights` - Search one-way and round-trip flights
2. `get_airports` - Get airport information
3. `search_flight_fallback` - SerpApi fallback for complex searches

---

### Amadeus MCP Server

**Best for:**
- Complete travel booking workflows
- Professional travel applications
- Users needing hotels, tours, and transfers
- Advanced analytics and predictions
- Production booking systems

**Strengths:**
- ✅ Complete travel ecosystem (flights + hotels + activities + transfers)
- ✅ Actual booking capabilities
- ✅ AI-powered price analysis and predictions
- ✅ Market insights and travel trends
- ✅ Professional-grade API
- ✅ Reference data (airports, airlines, routes)
- ✅ Hotel ratings and reviews
- ✅ Real-time flight status

**Limitations:**
- ❌ Requires Amadeus developer account
- ❌ OAuth2 setup needed
- ❌ Free tier has rate limits
- ❌ Production use requires paid plan

**Available Tools (32 total):**

**Flights (14 tools):**
1. `search_flights` - Comprehensive flight search
2. `confirm_flight_price` - Price validation
3. `book_flight` - Create bookings
4. `get_flight_order` - Retrieve bookings
5. `cancel_flight_order` - Cancel bookings
6. `flight_inspiration_search` - Destination discovery
7. `flight_cheapest_dates` - Find best dates
8. `analyze_flight_price` - AI price analysis
9. `predict_flight_delay` - Delay forecasting
10. `get_flight_status` - Real-time tracking
11-14. Additional flight analytics tools

**Hotels (5 tools):**
15. `search_hotels_by_city`
16. `search_hotels_by_location`
17. `get_hotel_offers`
18. `book_hotel`
19. `get_hotel_ratings`

**Tours & Activities (2 tools):**
20. `search_activities`
21. `get_activity_details`

**Transfers (2 tools):**
22. `search_transfers`
23. `book_transfer`

**Reference Data (6 tools):**
24. `search_airports`
25. `search_cities`
26. `get_nearest_airports`
27. `get_airline_info`
28. `get_airline_routes`
29. `get_airport_routes`

**Market Insights (3 tools):**
30. `get_travel_insights`
31. `get_booking_insights`
32. `predict_trip_purpose`

## Usage Scenarios

### Scenario 1: Quick Flight Price Check
**Use: Google Flights Server**
```
User: "What's the cheapest flight from NYC to LA next week?"
→ Uses fast-flights for instant results, no API key needed
```

### Scenario 2: Complete Trip Planning
**Use: Amadeus Server**
```
User: "Plan a trip to Paris: flights, hotel, airport transfer, and tours"
→ Uses Amadeus to search flights, hotels, transfers, and activities all in one
```

### Scenario 3: Flight Booking
**Use: Amadeus Server**
```
User: "Book flight #3 for John Doe"
→ Only Amadeus can complete actual bookings
```

### Scenario 4: Travel Research
**Use: Both Servers Together**
```
User: "Compare flight prices and find the most popular destinations from Boston"
→ Google Flights for quick price checks
→ Amadeus for market insights and travel trends
```

## Running Both Servers Together

### Why Run Both?

Running both servers gives you:
1. **Redundancy:** If one API is down, use the other
2. **Best of Both:** Free Google Flights + Comprehensive Amadeus
3. **Price Comparison:** Cross-reference prices from multiple sources
4. **Flexibility:** Simple searches on Google, complex bookings on Amadeus

### Configuration

In your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "google-flights": {
      "command": "mcp-server-google-flights",
      "env": {
        "SERPAPI_API_KEY": "optional_serpapi_key"
      }
    },
    "amadeus": {
      "command": "mcp-server-amadeus",
      "env": {
        "AMADEUS_CLIENT_ID": "your_client_id",
        "AMADEUS_CLIENT_SECRET": "your_client_secret",
        "AMADEUS_ENV": "test"
      }
    }
  }
}
```

### How Claude Chooses

When both servers are running, Claude will intelligently choose:

- **Simple flight search?** → Likely uses Google Flights (faster, no auth)
- **Need to book?** → Must use Amadeus (only one with booking)
- **Hotel search?** → Must use Amadeus (only one with hotels)
- **Price comparison?** → May use both and compare results

## Installation

Both servers are installed together:

```bash
# Install both servers
pip install -e .

# Or install dependencies
pip install -r requirements.txt

# Both entry points are now available:
mcp-server-google-flights
mcp-server-amadeus
```

## Credentials Needed

### For Google Flights Server (Optional)
```bash
export SERPAPI_API_KEY="your_key"  # Optional, for fallback
```

### For Amadeus Server (Required)
```bash
export AMADEUS_CLIENT_ID="your_client_id"
export AMADEUS_CLIENT_SECRET="your_client_secret"
export AMADEUS_ENV="test"  # or "production"
```

## Cost Comparison

### Google Flights Server
- **Base (fast-flights):** FREE ✅
- **SerpApi Fallback:** $50/month for 5,000 searches (optional)

### Amadeus Server
- **Test Environment:** FREE tier available ✅
  - Limited requests per month
  - Test bookings (not real)
- **Production:** Paid plans based on usage
  - Real bookings
  - Higher rate limits
  - Enterprise support

## Recommendations

### For Personal Use / Prototyping
```
✅ Start with Google Flights Server
  - No setup required
  - Free unlimited searches
  - Perfect for experimenting

➕ Add Amadeus Server when you need:
  - Hotel bookings
  - Complete trip planning
  - Advanced analytics
```

### For Production Applications
```
✅ Use Amadeus Server
  - Professional-grade API
  - Booking capabilities
  - SLA guarantees
  - Comprehensive travel data

➕ Keep Google Flights as backup
  - Fallback option
  - Price comparison
  - Redundancy
```

### For Travel Agencies / Apps
```
✅ Use Both Together
  - Amadeus for bookings and core features
  - Google Flights for price discovery
  - Maximum coverage and reliability
```

## Technical Architecture

```
Repository: google-flights-mcp/
│
├── src/
│   ├── mcp_server_google_flights/    ← Server #1
│   │   ├── __init__.py
│   │   └── server.py                  (fast-flights + SerpApi)
│   │
│   └── mcp_server_amadeus/            ← Server #2
│       ├── __init__.py
│       └── server.py                  (Amadeus REST API)
│
├── pyproject.toml                     (Both servers configured)
│   [project.scripts]
│   mcp-server-google-flights = "mcp_server_google_flights:main"
│   mcp-server-amadeus = "mcp_server_amadeus:main"
│
└── requirements.txt                   (All dependencies)
    - mcp>=1.2.0
    - fast-flights==2.2              (for Google Flights)
    - google-search-results>=2.4.2   (for SerpApi fallback)
    - aiohttp>=3.9.0                 (for Amadeus)
```

## Summary

| Aspect | Google Flights | Amadeus | Both Together |
|--------|---------------|---------|---------------|
| **Setup Time** | 1 minute | 5 minutes | 6 minutes |
| **Cost** | Free | Free tier + paid | Mixed |
| **Capabilities** | Flight search only | Full travel suite | Best of both |
| **Use Case** | Quick searches | Complete bookings | Production apps |
| **Recommended For** | Individuals | Businesses | Professionals |

## Getting Started

### Quick Start (Google Flights Only)
```bash
pip install -e .
mcp-server-google-flights
# No credentials needed!
```

### Full Setup (Both Servers)
```bash
# 1. Install
pip install -e .

# 2. Set up Amadeus credentials
export AMADEUS_CLIENT_ID="..."
export AMADEUS_CLIENT_SECRET="..."

# 3. Configure Claude Desktop with both servers
# (See configuration example above)

# 4. Start using both!
```

## Documentation

- **Google Flights Server:** See main README.md
- **Amadeus Server:** See AMADEUS_README.md
- **Amadeus Examples:** See AMADEUS_EXAMPLE.md
- **API Reference:** See AMADEUS_API_ENDPOINTS_ANALYSIS.md
- **This Comparison:** You're reading it!

---

**Bottom Line:**
- Use **Google Flights** for quick, free flight searches
- Use **Amadeus** for professional travel bookings and comprehensive services
- Use **Both** for maximum flexibility and coverage
