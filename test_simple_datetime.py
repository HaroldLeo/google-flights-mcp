#!/usr/bin/env python
"""Test SimpleDatetime formatting edge cases."""
import sys
sys.path.insert(0, 'src')
from mcp_server_google_flights.server import format_datetime

# Test case 1: Normal SimpleDatetime with both date and time
class SimpleDatetime1:
    date = (2025, 11, 20)
    time = (12, 29)

print("Test 1 - Normal SimpleDatetime:")
print(f"  Input: SimpleDatetime(date={SimpleDatetime1.date}, time={SimpleDatetime1.time})")
print(f"  Output: {format_datetime(SimpleDatetime1())}")
print()

# Test case 2: SimpleDatetime with missing time attribute
class SimpleDatetime2:
    date = (2025, 11, 20)

print("Test 2 - SimpleDatetime with missing time attribute:")
print(f"  Input: SimpleDatetime(date={SimpleDatetime2.date})")
result = format_datetime(SimpleDatetime2())
print(f"  Output: {result}")
print()

# Test case 3: SimpleDatetime with None time
class SimpleDatetime3:
    date = (2025, 11, 20)
    time = None

print("Test 3 - SimpleDatetime with None time:")
print(f"  Input: SimpleDatetime(date={SimpleDatetime3.date}, time=None)")
result = format_datetime(SimpleDatetime3())
print(f"  Output: {result}")
print()

# Test case 4: None input
print("Test 4 - None input:")
result = format_datetime(None)
print(f"  Output: {result}")
