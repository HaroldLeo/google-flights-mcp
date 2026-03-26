---
title: Google Flights MCP
emoji: ✈️
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
---

# Google Flights MCP Server

<div align="center">

**A Model Context Protocol (MCP) server for intelligent flight search and travel planning**

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

</div>

---

## Overview

Integrates Google Flights data directly into your AI workflow with natural language searches, intelligent price comparisons, and automated travel planning.

**Data Sources:**
- **SerpAPI (Primary):** Rich data including flight numbers, layovers, carbon emissions, price insights, and multi-seller booking options (250 free searches/month)
- **fast-flights (Fallback):** Free alternative when SerpAPI quota is exhausted or key is not configured

---

## Tools

| Tool | Description |
|------|-------------|
| `search_one_way_flights` | One-way flights for a specific date |
| `search_round_trip_flights` | Round-trip flights with fixed dates (supports `max_stops`) |
| `search_round_trips_in_date_range` | Search all round-trip combinations within a date range |
| `search_flights_by_airline` | Filter flights by airline codes or alliance (STAR_ALLIANCE, SKYTEAM, ONEWORLD) |
| `get_travel_dates` | Calculate travel dates relative to today |
| `generate_google_flights_url` | Generate a shareable Google Flights search link |

### Resources

- `airports://all` — Browse available airports
- `airports://{code}` — Get info for a specific airport (e.g. `airports://LAX`)

### Prompts

10 built-in travel planning prompts: `find_best_deal`, `weekend_getaway`, `last_minute_travel`, `business_trip`, `family_vacation`, `budget_backpacker`, `loyalty_program_optimizer`, `holiday_peak_travel`, `long_haul_international`, `stopover_explorer`.

---

## Quick Start

### Option 1: Install from PyPI

```bash
uvx mcp-server-google-flights
```

### Option 2: Run from source

```bash
git clone https://github.com/HaroldLeo/google-flights-mcp.git
cd google-flights-mcp
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

---

## Configuration

### Claude Desktop

```json
{
  "mcpServers": {
    "google-flights": {
      "command": "uvx",
      "args": ["mcp-server-google-flights"],
      "env": {
        "SERPAPI_API_KEY": "your_serpapi_key_here"
      }
    }
  }
}
```

### From source

```json
{
  "mcpServers": {
    "google-flights": {
      "command": "/absolute/path/to/.venv/bin/python",
      "args": ["/absolute/path/to/google-flights-mcp/src/mcp_server_google_flights/server.py"],
      "env": {
        "SERPAPI_API_KEY": "your_serpapi_key_here"
      }
    }
  }
}
```

**Get a free SerpAPI key:** [serpapi.com/users/sign_up](https://serpapi.com/users/sign_up) (250 free searches/month)

---

## Remote Deployment (Hugging Face Spaces)

This server supports remote deployment as an SSE MCP server.

### Deploy to HF Spaces

1. Create a new Space at [huggingface.co/new-space](https://huggingface.co/new-space) with **Docker** SDK
2. Push this repository to the Space
3. (Optional) Add `SERPAPI_API_KEY` as a Space secret

The `Dockerfile` and transport switching are already configured — set `MCP_TRANSPORT=sse` (done automatically in the Dockerfile) to run in SSE mode.

### Connect to a deployed Space

```json
{
  "mcpServers": {
    "google-flights": {
      "url": "https://YOUR-USERNAME-google-flights-mcp.hf.space/sse"
    }
  }
}
```

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `SERPAPI_API_KEY` | SerpAPI key for richer flight data (optional) |
| `MCP_TRANSPORT` | `stdio` (default) or `sse` for remote deployment |
| `HOST` | Host for SSE mode (default: `0.0.0.0`) |
| `PORT` | Port for SSE mode (default: `7860`) |

---

## Troubleshooting

**No flights found:** Try a different date or route. Google Flights rate-limits scraping — SerpAPI fallback is more reliable.

**401 error:** Update to the latest version. Older versions used a remote Playwright service that now requires auth.

**Slow searches:** `search_round_trips_in_date_range` is limited to 30 date combinations to avoid rate limiting. Narrow your date range or use `min_stay_days`/`max_stay_days`.

---

## License

MIT — see [LICENSE](LICENSE)
