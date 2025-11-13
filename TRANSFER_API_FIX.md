# Transfer API Location Format Fix

## Problem Summary

The Amadeus Transfer API was failing with multiple errors due to incomplete location formatting:

### Test Results (CDG → ORY)
- ❌ **PRIVATE**: Error 830 - INVALID/MISSING COUNTRY CODE
- ⚠️ **TAXI**: 22/23 providers failed with INVALID SERVICE TYPE or NO RATES
- ❌ **HOURLY**: Error 34499 - THE DURATION IS MANDATORY
- ❌ **SHUTTLE**: Error 450 - INVALID SERVICE TYPE
- ❌ **SHARED**: Error 830 - INVALID/MISSING COUNTRY CODE

## Root Cause

The previous implementation only sent airport codes (e.g., "CDG", "ORY") to the API, but Amadeus Transfer API requires complete location information including:

- Address line
- City name
- Country code
- Geographic coordinates (latitude, longitude)
- Location name

## Solution Implemented

### 1. Airport Location Database

Created `AIRPORT_LOCATIONS` dictionary with complete information for 20+ major airports:

```python
AIRPORT_LOCATIONS = {
    "CDG": {
        "name": "Paris Charles de Gaulle Airport",
        "cityName": "Paris",
        "countryCode": "FR",
        "geoCode": "49.0097,2.5479",
        "addressLine": "95700 Roissy-en-France"
    },
    "ORY": {
        "name": "Paris Orly Airport",
        "cityName": "Paris",
        "countryCode": "FR",
        "geoCode": "48.7233,2.3794",
        "addressLine": "94390 Orly"
    },
    # ... 18 more major airports
}
```

**Airports included:**
- Paris: CDG, ORY
- New York: JFK, LGA, EWR
- London: LHR, LGW, STN
- Los Angeles: LAX
- Tokyo: NRT, HND
- San Francisco: SFO
- Miami: MIA
- Dubai: DXB
- Frankfurt: FRA
- Amsterdam: AMS
- Madrid: MAD
- Barcelona: BCN
- Singapore: SIN
- Hong Kong: HKG
- Seoul: ICN

### 2. Location Formatting Function

Created `format_location_for_transfer()` function that:

1. **Detects airport codes** and enriches them with full location data
2. **Handles coordinates** in "lat,long" format
3. **Passes through addresses** for custom locations
4. **Differentiates start vs end locations** (API has different requirements)

### 3. Updated search_transfers Tool

**New features:**
- ✅ Automatic location enrichment for airport codes
- ✅ Support for all transfer types: PRIVATE, TAXI, HOURLY, SHUTTLE, SHARED
- ✅ Duration parameter for HOURLY transfers
- ✅ Better error messages
- ✅ Flexible input formats (airport codes, coordinates, addresses)

**Updated signature:**
```python
async def search_transfers(
    start_location: str,
    end_location: str,
    transfer_type: str,
    start_date_time: str,
    passengers: int = 1,
    duration: Optional[str] = None  # NEW: for HOURLY transfers
) -> str
```

## API Payload Format

### Before (Incorrect)
```json
{
  "startLocationCode": "CDG",
  "endAddressLine": "ORY",
  "transferType": "PRIVATE",
  "startDateTime": "2024-11-20T10:30:00",
  "passengers": 1
}
```

### After (Correct)
```json
{
  "startLocationCode": "CDG",
  "endLocationCode": "ORY",
  "endAddressLine": "94390 Orly",
  "endCityName": "Paris",
  "endCountryCode": "FR",
  "endGeoCode": "48.7233,2.3794",
  "endName": "Paris Orly Airport",
  "transferType": "PRIVATE",
  "startDateTime": "2024-11-20T10:30:00",
  "passengers": 1
}
```

## Usage Examples

### Airport to Airport
```python
search_transfers(
    start_location="CDG",
    end_location="ORY",
    transfer_type="PRIVATE",
    start_date_time="2024-11-20T10:30:00",
    passengers=2
)
```

### Airport to Custom Address
```python
search_transfers(
    start_location="JFK",
    end_location="Times Square, New York, NY",
    transfer_type="TAXI",
    start_date_time="2024-11-20T14:00:00",
    passengers=1
)
```

### Using Coordinates
```python
search_transfers(
    start_location="LHR",
    end_location="51.5074,-0.1278",  # London city center
    transfer_type="PRIVATE",
    start_date_time="2024-11-20T09:00:00",
    passengers=3
)
```

### Hourly Rental
```python
search_transfers(
    start_location="LAX",
    end_location="Santa Monica Pier",
    transfer_type="HOURLY",
    start_date_time="2024-11-20T10:00:00",
    passengers=4,
    duration="PT4H30M"  # 4 hours 30 minutes
)
```

## Expected Improvements

With these fixes, all transfer types should now work correctly:

- ✅ **PRIVATE**: Full location data prevents country code errors
- ✅ **TAXI**: Proper formatting should increase provider success rate
- ✅ **HOURLY**: Duration parameter now supported
- ✅ **SHUTTLE**: Valid service type with complete location data
- ✅ **SHARED**: Country code and full location info provided

## Files Modified

1. `src/mcp_server_amadeus/server.py`:
   - Added `AIRPORT_LOCATIONS` dictionary (lines 1001-1155)
   - Added `format_location_for_transfer()` function (lines 1158-1207)
   - Updated `search_transfers()` tool (lines 1210-1272)

2. `AMADEUS_README.md`:
   - Updated transfer types documentation
   - Added transfer usage examples

## Testing Recommendations

Re-test with the same CDG → ORY scenario:

```bash
# Test PRIVATE
search_transfers("CDG", "ORY", "PRIVATE", "2024-11-25T10:00:00", 1)

# Test TAXI
search_transfers("CDG", "ORY", "TAXI", "2024-11-25T10:00:00", 1)

# Test HOURLY (with duration)
search_transfers("CDG", "ORY", "HOURLY", "2024-11-25T10:00:00", 1, "PT3H")

# Test SHUTTLE
search_transfers("CDG", "ORY", "SHUTTLE", "2024-11-25T10:00:00", 1)

# Test SHARED
search_transfers("CDG", "ORY", "SHARED", "2024-11-25T10:00:00", 1)
```

## Future Enhancements

1. **Expand airport database**: Add more airports as needed
2. **Geocoding integration**: Auto-lookup coordinates for addresses
3. **Address validation**: Verify address format for different countries
4. **Provider filtering**: Allow filtering by specific providers
5. **Cache location data**: Avoid repeated lookups
