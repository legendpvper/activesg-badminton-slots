# ActiveSG Badminton Slot Finder

A community web app that aggregates instant-bookable badminton slots across all 131 ActiveSG venues. No login required — data is publicly accessible and refreshed every 10 minutes.

## Features

- All 131 venues queried in parallel via `curl_cffi` (Cloudflare bypass)
- Filter by date, time window, and venue type (sport centres vs school halls)
- Shows court count and price per slot
- Auto-refreshes every 10 minutes, results served instantly from cache
- Mobile-friendly, no framework dependencies
- Self-hostable on your own machine or a VPS (e.g. via DuckDNS)

## Local development

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Open http://localhost:8000

## Deploy to Render

1. Push this repo to GitHub
2. Go to [render.com](https://render.com) → New Web Service → connect your repo
3. Render detects `render.yaml` automatically — just click Deploy
4. Configure proxy environment variables (see [DEPLOY.md](DEPLOY.md))

> **Note:** ActiveSG blocks requests from cloud provider IPs. A proxy is required when hosting on Render or similar platforms. See [DEPLOY.md](DEPLOY.md) for setup instructions and debugging tips.

## Live Demo

http://activesg-slots.duckdns.org:8000

## API

| Endpoint | Description |
|----------|-------------|
| `GET /api/slots?date=YYYY-MM-DD` | Available slots for a date |
| `GET /api/slots?date=...&start=07:00&end=11:00` | Filter by time window |
| `GET /api/slots?date=...&type=SRC` | Filter by venue type (`SRC` or `DUS`) |
| `GET /api/status` | Cache status and proxy configuration |
| `GET /api/health` | Basic health check |
| `GET /api/diag` | Test connectivity against ActiveSG (useful for debugging) |
| `POST /api/refresh` | Trigger a manual cache refresh |

## How it works

`curl_cffi` impersonates Chrome's TLS fingerprint to bypass Cloudflare's bot detection on activesg.gov.sg. The underlying tRPC API is publicly accessible — no ActiveSG login required. Slot data is cached in memory and served to all users instantly.

## Project structure

```
activesg-slots/
├── main.py           # FastAPI + APScheduler + curl_cffi fetcher
├── static/
│   └── index.html    # Single-file frontend
├── requirements.txt
├── render.yaml
├── DEPLOY.md         # Proxy setup and deployment troubleshooting
└── README.md
```
