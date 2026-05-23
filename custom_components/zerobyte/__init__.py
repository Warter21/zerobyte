"""Zerobyte integration init."""
from __future__ import annotations

import logging
import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PLATFORMS, DEFAULT_SCAN_INTERVAL
from .api import ZerobyteClient, ZerobyteAuthError, ZerobyteConnectionError
from .coordinator import ZerobyteCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Zerobyte from a config entry."""
    host = entry.data["host"]
    username = entry.data["username"]
    password = entry.data["password"]
    scan_interval = entry.data.get("scan_interval", DEFAULT_SCAN_INTERVAL)

    session = aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar(unsafe=True))
    client = ZerobyteClient(host, username, password, session)

    # Initial login
    try:
        await client.authenticate()
    except ZerobyteAuthError as err:
        raise ConfigEntryAuthFailed("Invalid credentials") from err
    except ZerobyteConnectionError as err:
        raise ConfigEntryNotReady(f"Cannot connect: {err}") from err

    coordinator = ZerobyteCoordinator(hass, client, scan_interval)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "client": client,
        "coordinator": coordinator,
        "session": session,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload Zerobyte config entry."""
    data = hass.data[DOMAIN].pop(entry.entry_id, None)

    if data:
        session = data.get("session")
        if session:
            await session.close()

    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
