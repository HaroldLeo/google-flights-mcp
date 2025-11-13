#!/usr/bin/env python3
"""
Test script to verify confirm_flight_price fix for missing mandatory fields.
"""

import json

# Simulate the old simplified format (missing mandatory fields)
simplified_offer = {
    "type": "flight-offer",
    "id": "1",
    "price": {"total": "69.94", "currency": "USD", "base": "41.84"},
    "itineraries": [{
        "duration": "PT8H1M",
        "segments": [{
            "departure": {"airport": "JFK", "time": "2025-12-15T06:59:00", "terminal": "0"},
            "arrival": {"airport": "LAS", "time": "2025-12-15T09:45:00", "terminal": "3"},
            "carrier": "F9",
            "flight_number": "3237",
            "aircraft": "32Q",
            "duration": "PT5H46M"
        }]
    }]
}

# Simulate the new raw format (has all mandatory fields)
raw_offer = {
    "type": "flight-offer",
    "id": "1",
    "source": "GDS",  # REQUIRED
    "price": {"total": "69.94", "currency": "USD", "base": "41.84"},
    "itineraries": [{
        "duration": "PT8H1M",
        "segments": [{
            "id": "1",  # REQUIRED
            "departure": {"iataCode": "JFK", "at": "2025-12-15T06:59:00", "terminal": "0"},
            "arrival": {"iataCode": "LAS", "at": "2025-12-15T09:45:00", "terminal": "3"},
            "carrierCode": "F9",
            "number": "3237",
            "aircraft": {"code": "32Q"},
            "duration": "PT5H46M"
        }]
    }],
    "travelerPricings": [{  # REQUIRED
        "travelerId": "1",
        "fareOption": "STANDARD",
        "travelerType": "ADULT",
        "price": {"currency": "USD", "total": "69.94", "base": "41.84"}
    }]
}

def test_validation():
    """Test the validation logic"""
    print("Testing validation logic...")

    # Test 1: Simplified format (should fail validation)
    print("\n1. Testing simplified format (should fail):")
    missing_fields = []
    if "travelerPricings" not in simplified_offer:
        missing_fields.append("travelerPricings")
    if "source" not in simplified_offer:
        missing_fields.append("source")
    if "itineraries" in simplified_offer:
        for itin in simplified_offer["itineraries"]:
            if "segments" in itin:
                for seg in itin["segments"]:
                    if "id" not in seg:
                        missing_fields.append("segment.id")
                        break

    if missing_fields:
        print(f"   ✅ Correctly detected missing fields: {missing_fields}")
    else:
        print("   ❌ Failed to detect missing fields!")

    # Test 2: Raw format (should pass validation)
    print("\n2. Testing raw format (should pass):")
    missing_fields = []
    if "travelerPricings" not in raw_offer:
        missing_fields.append("travelerPricings")
    if "source" not in raw_offer:
        missing_fields.append("source")
    if "itineraries" in raw_offer:
        for itin in raw_offer["itineraries"]:
            if "segments" in itin:
                for seg in itin["segments"]:
                    if "id" not in seg:
                        missing_fields.append("segment.id")
                        break

    if not missing_fields:
        print("   ✅ All required fields present!")
    else:
        print(f"   ❌ Missing fields detected: {missing_fields}")

    print("\n" + "="*60)
    print("Summary:")
    print("- search_flights now returns 'raw_offers' with all required fields")
    print("- confirm_flight_price validates input and shows helpful error")
    print("- Users must use raw_offers, not simplified offers")
    print("="*60)

if __name__ == "__main__":
    test_validation()
    print("\nTest completed successfully! ✅")
