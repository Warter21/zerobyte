"""Zerobyte API client."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)

LOGIN_PATH = "/api/auth/sign-in/username"
VOLUMES_PATH = "/api/v1/volumes"
REPOSITORIES_PATH = "/api/v1/repositories"
BACKUPS_PATH = "/api/v1/backups"

_AUTH_RETRY_DELAYS = (5, 15, 30)  # seconds


class ZerobyteAuthError(Exception):
    pass


class ZerobyteConnectionError(Exception):
    pass


class ZerobyteClient:
    """Async Zerobyte API client.

    Supports two authentication modes:
    - Cookie-based session auth (username + password)
    - API key auth (static key sent on every request via the x-api-key header)
    """

    def __init__(
        self,
        host: str,
        session: aiohttp.ClientSession,
        username: str | None = None,
        password: str | None = None,
        api_key: str | None = None,
    ) -> None:
        self._host = host.rstrip("/")
        self._username = username
        self._password = password
        self._api_key = api_key
        self._session = session

    @property
    def uses_api_key(self) -> bool:
        """Return True if this client authenticates via API key."""
        return bool(self._api_key)

    async def authenticate(self) -> None:
        if self.uses_api_key:
            await self._verify_api_key()
            return

        url = f"{self._host}{LOGIN_PATH}"
        payload = {"username": self._username, "password": self._password}

        last_error: Exception | None = None
        attempts = [0] + list(_AUTH_RETRY_DELAYS)

        for delay in attempts:
            if delay:
                await asyncio.sleep(delay)

            try:
                async with self._session.post(url, json=payload) as resp:
                    if resp.status == 401:
                        raise ZerobyteAuthError("Invalid credentials")
                    if resp.status == 429:
                        text = await resp.text()
                        last_error = ZerobyteConnectionError(f"Login rate-limited (429): {text}")
                        continue
                    if resp.status not in (200, 201):
                        text = await resp.text()
                        raise ZerobyteConnectionError(f"Login failed ({resp.status}): {text}")
                    return

            except (ZerobyteAuthError, ZerobyteConnectionError):
                raise
            except aiohttp.ClientConnectorError as err:
                raise ZerobyteConnectionError(f"Cannot connect to {self._host}") from err

        raise last_error or ZerobyteConnectionError("Login failed after retries")

    async def _verify_api_key(self) -> None:
        """Lightweight check that the API key is accepted by the server."""
        url = f"{self._host}{VOLUMES_PATH}"
        try:
            async with self._session.get(url) as resp:
                if resp.status == 401:
                    raise ZerobyteAuthError("Invalid or revoked API key")
                if resp.status not in (200, 201):
                    text = await resp.text()
                    raise ZerobyteConnectionError(f"API key check failed ({resp.status}): {text}")
        except aiohttp.ClientConnectorError as err:
            raise ZerobyteConnectionError(f"Cannot connect to {self._host}") from err

    async def _get(self, path: str) -> Any:
        url = f"{self._host}{path}"
        try:
            async with self._session.get(url) as resp:
                if resp.status == 401:
                    if self.uses_api_key:
                        # A static API key won't become valid on retry.
                        raise ZerobyteAuthError("Invalid or revoked API key")
                    await self.authenticate()
                    async with self._session.get(url) as resp2:
                        resp2.raise_for_status()
                        return await resp2.json()
                resp.raise_for_status()
                return await resp.json()

        except aiohttp.ClientConnectorError as err:
            raise ZerobyteConnectionError(f"Cannot connect to {self._host}") from err

    async def get_volumes(self) -> list[dict]:
        raw = await self._get(VOLUMES_PATH)
        result: list[dict] = []

        for vol in raw:
            name = vol.get("shortId") or vol.get("name")

            try:
                detail = await self._get(f"{VOLUMES_PATH}/{name}")

                # Zerobyte API structure:
                # { "volume": {...}, "statfs": {...} }
                vol.update(detail.get("volume", {}))
                vol["statfs"] = detail.get("statfs", {})

            except Exception:
                vol["statfs"] = {}

            result.append(vol)

        return result

    async def get_repositories(self) -> list[dict]:
        repos = await self._get(REPOSITORIES_PATH)

        for r in repos:
            rid = r.get("shortId") or r.get("id")

            try:
                detail = await self.get_repository_detail(rid)
                r.update(detail)
            except Exception:
                pass

            try:
                snaps = await self.get_repository_snapshots(rid)
                r["snapshots"] = snaps
            except Exception:
                r["snapshots"] = []

        return repos

    async def get_repository_detail(self, repo_id: str) -> dict:
        return await self._get(f"{REPOSITORIES_PATH}/{repo_id}")

    async def get_repository_snapshots(self, repo_id: str) -> list[dict]:
        return await self._get(f"{REPOSITORIES_PATH}/{repo_id}/snapshots")

    async def get_backups(self) -> list[dict]:
        return await self._get(BACKUPS_PATH)

    async def get_backup_detail(self, backup_id: str) -> dict:
        return await self._get(f"{BACKUPS_PATH}/{backup_id}")

    @staticmethod
    def format_ts(ts: int | None) -> str | None:
        if ts is None:
            return None
        try:
            if ts > 1e10:
                ts = ts / 1000
            return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
        except Exception:
            return None
