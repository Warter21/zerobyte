"""Zerobyte DataUpdateCoordinator."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import ZerobyteClient, ZerobyteConnectionError

_LOGGER = logging.getLogger(__name__)


class ZerobyteCoordinator(DataUpdateCoordinator[dict]):
    """Fetch and cache all Zerobyte data."""

    def __init__(self, hass: HomeAssistant, client: ZerobyteClient, scan_interval: int) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="Zerobyte",
            update_interval=timedelta(seconds=scan_interval),
        )
        self.client = client

    async def _async_update_data(self) -> dict:
        try:
            volumes = await self.client.get_volumes()
            repositories = await self.client.get_repositories()
            backups_raw = await self.client.get_backups()

            backups: list[dict] = []
            for b in backups_raw:
                bid = b.get("id")

                try:
                    detail = await self.client.get_backup_detail(bid)
                except Exception:
                    _LOGGER.debug("Failed to fetch backup detail for %s", bid, exc_info=True)
                    detail = {}

                b.update(detail)
                backups.append(b)

            return {
                "volumes": volumes,
                "repositories": repositories,
                "backups": backups,
            }

        except ZerobyteConnectionError as err:
            raise UpdateFailed(f"Error communicating with Zerobyte: {err}") from err
