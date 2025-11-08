# Analysis: Playwright Fallback in fast-flights

## What We Discovered

### 1. **GitHub Main Branch HAS Playwright Fallback**

The GitHub repository (https://github.com/AWeirdDev/flights) main branch contains:
- `fallback_playwright.py` - Fallback Playwright implementation
- `local_playwright.py` - Local Playwright browser automation
- `fetch_mode` parameter with options:
  - `"common"` - Standard HTTP client
  - `"fallback"` - Try HTTP first, then Playwright on failure
  - `"force-fallback"` - Force Playwright usage
  - `"local"` - Use local Playwright
  - `"bright-data"` - Use BrightData proxy service

### 2. **PyPI Version 3.0rc0 is INCOMPLETE**

The installed package from PyPI (`fast-flights==3.0rc0`) has:
- ✅ `integration` parameter support
- ✅ BrightData integration (paid proxy service)
- ❌ NO `fetch_mode` parameter
- ❌ NO Playwright fallback modules
- ❌ NO local_playwright or fallback_playwright

**Function signature from PyPI package:**
```python
get_flights(q: Union[Query, str], /, *, proxy: Optional[str] = None,
            integration: Optional[Integration] = None)
```

**Function signature from GitHub main:**
```python
get_flights(..., fetch_mode: str = "common", data_source: str = "html", ...)
```

### 3. **Version History**

From the GitHub tags:
- v2.2 (Mar 8, 2025) - Added local Playwright support
- v2.1 (Feb 25, 2025)
- v2.0 (Jan 1, 2025) - Added fallback Playwright serverless functions
- v1.1 (Jul 14, 2024)
- **v3.0rc0** - NOT tagged on GitHub! Only on PyPI

This suggests `3.0rc0` is an early release candidate that was pushed to PyPI before the Playwright features were added.

### 4. **Why We Don't Have Playwright Fallback**

The PyPI `3.0rc0` appears to be from a transitional state where:
1. The package was being restructured (moved from fetcher.py to core.py)
2. Integration system was added (BrightData)
3. But Playwright fallback hadn't been integrated yet

The current GitHub main branch (updated Aug 27, 2025) has much more complete functionality that hasn't been released to PyPI.

## Potential Solutions

### Option 1: Install from GitHub Instead
```bash
pip install git+https://github.com/AWeirdDev/flights.git
```
This would give us the Playwright fallback, but might be less stable.

### Option 2: Wait for Official 3.0 Release
The 3.0rc0 is a release candidate - a stable 3.0 with Playwright might come later.

### Option 3: Use BrightData Integration (Paid)
We could use the BrightData integration that's available in 3.0rc0, but this requires:
- API key from BrightData
- Paid service

### Option 4: Stay with Current Version
Accept the limitations and use what's available in 3.0rc0.

## Recommendation

For this project, I recommend **staying with 3.0rc0** because:
1. It's the version specified in `pyproject.toml`
2. The main functionality works (primp with browser impersonation)
3. Installing from GitHub could introduce instability
4. The missing features (flight numbers, best_flights) wouldn't be fixed by Playwright anyway - those are parser limitations, not fetching limitations

However, if you're encountering scraping failures (403s, blocks, etc.), then switching to the GitHub version with Playwright fallback would be worth considering.
