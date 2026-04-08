# ActiveSG Badminton Slot Finder

A community web app that aggregates instant-bookable badminton slots across all 120+ ActiveSG venues. No login required — data is publicly accessible and refreshed every 10 minutes.

## Features

- All 120+ venues queried in parallel via `curl_cffi` (Cloudflare bypass)
- Filter by date, time window, and venue type (sport centres vs school halls)
- Shows court count and price per slot
- Auto-refreshes every 10 minutes, results served instantly from cache
- Mobile-friendly, no framework dependencies

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
4. No environment variables needed

## API

| Endpoint | Description |
|----------|-------------|
| `GET /api/slots?date=YYYY-MM-DD` | Available slots for a date |
| `GET /api/slots?date=...&start=07:00&end=11:00` | Filter by time window |
| `GET /api/slots?date=...&type=SRC` | Filter by venue type (SRC or DUS) |
| `GET /api/status` | Cache status |
| `POST /api/refresh` | Trigger manual refresh |

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
└── README.md
```
