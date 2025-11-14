# SerpAPI vs fast-flights: Feature Comparison

This document compares the two data sources used by the Google Flights MCP Server.

## Quick Summary

- **SerpAPI**: Primary source with rich data (250 free searches/month)
- **fast-flights**: Fallback source with basic data (unlimited, free)

## Feature Comparison Table

| Feature | SerpAPI | fast-flights |
|---------|---------|--------------|
| **Basic Flight Info** | ✅ | ✅ |
| Price, airline, times | ✅ | ✅ |
| Is best flag | ✅ | ✅ |
| **Flight Details** |||
| Flight numbers (e.g., "DL 548") | ✅ | ❌ |
| Airplane model | ✅ | ❌ |
| Legroom measurements | ✅ | ❌ |
| Overnight flag | ✅ | ❌ |
| Delay history | ✅ | ❌ |
| Amenities (Wi-Fi, power, etc.) | ✅ | ❌ |
| **Layovers** |||
| Layover details | ✅ Full details | ❌ Count only |
| Airport name | ✅ | ❌ |
| Duration (minutes) | ✅ | ❌ |
| Overnight flag | ✅ | ❌ |
| **Carbon Emissions** |||
| Per-flight emissions | ✅ | ❌ |
| Typical for route | ✅ | ❌ |
| Difference percentage | ✅ | ❌ |
| **Price Intelligence** |||
| Historical prices | ✅ | ❌ |
| Price level (high/low) | ✅ | ❌ |
| Typical price range | ✅ | ❌ |
| Price trends | ✅ | ❌ |
| **Booking** |||
| Multi-seller comparison | ✅ | ❌ |
| Baggage fee comparison | ✅ | ❌ |
| Direct booking links | ✅ | ✅ |
| **Cost** |||
| Free tier | 250/month | Unlimited |
| Paid plans | From $50/month | N/A |
| **Architecture** |||
| Round-trip requests | 2 (outbound + return) | 1 |
| Response time | ~0.7s | ~2-5s |

## Detailed Feature Breakdown

### 1. Flight Numbers

**SerpAPI Example:**
```json
{
  "flight_number": "DL 548",
  "marketed_as": ["DL 548", "KL 6123"]
}
```

**fast-flights:** Not available

**Why it matters:** Needed for check-in, seat selection, flight tracking

---

### 2. Layover Details

**SerpAPI Example:**
```json
{
  "layovers": [
    {
      "airport_code": "ATL",
      "airport_name": "Hartsfield-Jackson Atlanta International Airport",
      "duration": 180,
      "overnight": false
    }
  ]
}
```

**fast-flights:** Only provides `"stops": 1`

**Why it matters:**
- Know where you'll be waiting
- See if layover is overnight (might need hotel)
- Plan for short connections vs long waits

---

### 3. Carbon Emissions

**SerpAPI Example:**
```json
{
  "carbon_emissions": {
    "this_flight_grams": 850000,
    "typical_for_route_grams": 780000,
    "difference_percent": 9
  }
}
```

**fast-flights:** Not available

**Why it matters:** Eco-conscious travelers can choose greener options

---

### 4. Price Insights

**SerpAPI Example:**
```json
{
  "price_insights": {
    "lowest_price": 1339,
    "price_level": "high",
    "typical_price_range": [570, 1050],
    "price_history": [
      [1691424000, 1877],
      [1696176000, 2512]
    ]
  }
}
```

**fast-flights:** Not available

**Why it matters:**
- **Critical for booking decisions**: "Should I book now or wait?"
- Shows if current price is high/low/typical
- Historical trends reveal if prices are rising or falling

---

### 5. Multi-Seller Booking Options

**SerpAPI Example:**
```json
{
  "booking_options": [
    {
      "book_with": "Delta",
      "price": 464,
      "baggage_prices": ["1st checked bag: $35"]
    },
    {
      "book_with": "Expedia",
      "price": 478,
      "baggage_prices": ["1st checked bag: $40"]
    }
  ]
}
```

**fast-flights:** Single Google Flights URL only

**Why it matters:**
- Compare prices across booking sites
- See different baggage policies
- Find the best total price (flight + bags)

---

### 6. Delay History

**SerpAPI Example:**
```json
{
  "often_delayed_by_over_30_min": true
}
```

**fast-flights:** Not available

**Why it matters:** Avoid unreliable flights for important trips

---

## When to Use Each

### Use SerpAPI When:
- ✅ You have API key (free 250/month)
- ✅ Users need detailed trip planning
- ✅ Price insights matter ("book now or wait?")
- ✅ Flight numbers needed for check-in
- ✅ Layover details important
- ✅ Eco-conscious travelers (carbon data)
- ✅ Multi-seller price comparison needed

### Use fast-flights When:
- ✅ No SerpAPI key available
- ✅ Quick basic searches only
- ✅ High volume (>250 searches/month)
- ✅ Simplicity over features

## Cost Analysis

### SerpAPI Free Tier
- **250 searches/month free**
- Perfect for personal use
- ~8 searches per day
- Example: Search LAX→NYC = 1 search

### SerpAPI Paid Plans
Starting at **$50/month** for:
- 5,000 searches/month
- Commercial usage
- Priority support

### fast-flights
- **Unlimited searches**
- **Always free**
- Self-hosted scraping
- May be rate-limited by Google

## Migration Impact

The server **automatically handles** the choice:

1. **SerpAPI key present** → Use SerpAPI
2. **SerpAPI fails or quota exhausted** → Fall back to fast-flights
3. **No SerpAPI key** → Use fast-flights

**No code changes needed** - just set `SERPAPI_API_KEY` environment variable.

## Getting SerpAPI Key

1. Sign up: [serpapi.com/users/sign_up](https://serpapi.com/users/sign_up)
2. Get free 250 searches/month
3. Copy your API key
4. Set environment variable: `SERPAPI_API_KEY=your_key_here`

## Response Format Differences

### SerpAPI Response
```json
{
  "source": "serpapi",
  "flights": [...],
  "price_insights": {...},
  "search_metadata": {...}
}
```

### fast-flights Response
```json
{
  "source": "fast-flights",
  "flights": [...],
  "booking_url": "https://...",
  "note": "Using fast-flights v2.2. For richer data, configure SERPAPI_API_KEY."
}
```

## Recommendation

**For best experience:**
1. ✅ Get free SerpAPI key (250 searches/month)
2. ✅ Configure `SERPAPI_API_KEY` environment variable
3. ✅ Enjoy rich flight data with automatic fallback to fast-flights

This gives you the best of both worlds:
- Rich data when available
- Unlimited fallback when quota exhausted
