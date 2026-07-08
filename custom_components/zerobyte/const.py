"""Constants for Zerobyte integration."""
from __future__ import annotations

DOMAIN = "zerobyte"

DEFAULT_SCAN_INTERVAL = 300  # seconds

CONF_SCAN_INTERVAL = "scan_interval"
CONF_API_KEY = "api_key"
API_KEY_HEADER = "x-api-key"
PLATFORMS: list[str] = ["sensor"]
