import os
from datetime import datetime, timezone
from pathlib import Path
from time import monotonic
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse


PROJECT_ROOT = Path(__file__).resolve().parent
HTML_FILE = PROJECT_ROOT / "astronaut-health-console-nasa.html"
METEOMATICS_URL = "https://api.meteomatics.com"
CACHE_SECONDS = int(os.getenv("METEO_CACHE_SECONDS", "600"))

app = FastAPI(title="Astronaut Health Environment Service", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000", "http://localhost:8000", "null"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

_cache: dict[tuple[float, float], dict[str, Any]] = {}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def meteomatics_credentials() -> tuple[str, str]:
    username = os.getenv("METEOMATICS_USERNAME", "").strip()
    password = os.getenv("METEOMATICS_PASSWORD", "")
    if not username or not password:
        raise HTTPException(
            status_code=503,
            detail="Meteomatics credentials are not configured on the backend.",
        )
    return username, password


def cached_value(key: tuple[float, float]) -> dict[str, Any] | None:
    item = _cache.get(key)
    if item is None:
        return None
    if monotonic() - item["cached_at"] > CACHE_SECONDS:
        return item
    return item


def parse_radiation(payload: dict[str, Any]) -> tuple[float, str]:
    try:
        date_item = payload["data"][0]["coordinates"][0]["dates"][0]
        value = float(date_item["value"])
        timestamp = str(date_item.get("date", utc_now()))
    except (KeyError, IndexError, TypeError, ValueError) as error:
        raise HTTPException(
            status_code=502,
            detail="Meteomatics returned an unexpected radiation response.",
        ) from error
    return value, timestamp


@app.get("/", response_class=FileResponse)
async def dashboard() -> FileResponse:
    if not HTML_FILE.is_file():
        raise HTTPException(status_code=404, detail="Dashboard HTML file was not found.")
    return FileResponse(HTML_FILE)


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "astronaut-health-environment"}


@app.get("/api/environment/radiation")
async def radiation(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
) -> dict[str, Any]:
    username, password = meteomatics_credentials()
    key = (round(lat, 4), round(lon, 4))
    cached = cached_value(key)
    now = utc_now()

    if cached and monotonic() - cached["cached_at"] <= CACHE_SECONDS:
        return {**cached["response"], "cached": True, "stale": False}

    valid_time = now
    request_url = f"{METEOMATICS_URL}/{valid_time}/global_rad:W/{lat},{lon}/json"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(request_url, auth=(username, password))
            response.raise_for_status()
            value, observed_at = parse_radiation(response.json())
    except httpx.HTTPStatusError as error:
        if cached:
            return {
                **cached["response"],
                "cached": True,
                "stale": True,
                "warning": f"Meteomatics returned HTTP {error.response.status_code}; showing the last successful value.",
            }
        raise HTTPException(
            status_code=502,
            detail=f"Meteomatics returned HTTP {error.response.status_code}.",
        ) from error
    except (httpx.HTTPError, ValueError) as error:
        if cached:
            return {
                **cached["response"],
                "cached": True,
                "stale": True,
                "warning": "Meteomatics is unavailable; showing the last successful value.",
            }
        raise HTTPException(
            status_code=502,
            detail="Meteomatics is unavailable and no cached value exists.",
        ) from error

    result = {
        "source": "Meteomatics",
        "parameter": "global_rad:W",
        "latitude": lat,
        "longitude": lon,
        "value": value,
        "unit": "W/m²",
        "observed_at": observed_at,
        "fetched_at": now,
        "cached": False,
        "stale": False,
    }
    _cache[key] = {"cached_at": monotonic(), "response": result}
    return result
