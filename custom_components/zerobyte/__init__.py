"""Zerobyte integration init."""
from __future__ import annotations

import logging
import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .api import ZerobyteClient
from .coordinator import ZerobyteCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Zerobyte from a config entry."""
    host = entry.data["host"]
    username = entry.data["username"]
    password = entry.data["password"]
    scan_interval = entry.data.get("scan_interval", 300)

    session = aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar(unsafe=True))
    client = ZerobyteClient(host, username, password, session)

    # Initial login
    await client.authenticate()

    coordinator = ZerobyteCoordinator(hass, client, scan_interval)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "client": client,
        "coordinator": coordinator,
        "session": session,
    }

    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload Zerobyte config entry."""
    data = hass.data[DOMAIN].pop(entry.entry_id, None)

    if data:
        session = data.get("session")
        if session:
            await session.close()

    return await hass.config_entries.async_unload_platforms(entry, ["sensor"])
