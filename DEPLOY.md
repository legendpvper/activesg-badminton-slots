# Deploying to Render

## The Problem
ActiveSG blocks requests from cloud provider IPs (AWS, GCP, Azure, etc.) including Render's servers. When running locally, your home/work IP is used which is not blocked.

## Solution: Configure a Proxy

You need to set up a proxy server and configure it via environment variables.

### Option 1: Using a Proxy URL (recommended)

Set a single environment variable in Render Dashboard:

```
PROXY_URL=http://username:password@proxy-host.com:8080
```

### Option 2: Using Individual Proxy Settings

Set these environment variables in Render Dashboard:

```
PROXY_HOST=proxy-host.com
PROXY_PORT=8080
PROXY_USER=username      (optional, if proxy requires auth)
PROXY_PASS=password      (optional, if proxy requires auth)
```

### Where to get a proxy

Options for Singapore-based residential/ISP proxies:
- **Bright Data** (formerly Luminati) - residential proxies
- **Oxylabs** - residential proxies
- **PacketStream** - peer-to-peer residential proxies
- **Any cheap VPS** in Singapore with a residential IP (e.g., DigitalOcean, Vultr)

## Debugging

After deploying, visit these endpoints to diagnose issues:

- `GET /api/health` - Basic health check
- `GET /api/status` - Shows cache status and proxy configuration
- `GET /api/diag` - Runs a test fetch against ActiveSG to verify connectivity

Check your Render logs for detailed error messages.

## Local Development (no proxy needed)

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Open http://localhost:8000
