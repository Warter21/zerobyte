from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
import aiohttp

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .api import ZerobyteAuthError, ZerobyteClient, ZerobyteConnectionError
from .const import (
    DOMAIN,
    DEFAULT_SCAN_INTERVAL,
    CONF_SCAN_INTERVAL,
    CONF_API_KEY,
    API_KEY_HEADER,
)

_LOGGER = logging.getLogger(__name__)


def normalize_host(host: str) -> str:
    host = host.strip()
    if not host.startswith(("http://", "https://")):
        host = "http://" + host
    return host.rstrip("/")


STEP_PASSWORD_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): int,
    }
)

STEP_API_KEY_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_API_KEY): str,
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): int,
    }
)


class ZerobyteConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Let the user pick an authentication method."""
        return self.async_show_menu(
            step_id="user",
            menu_options=["password", "api_key"],
        )

    async def async_step_password(self, user_input: dict[str, Any] | None = None):
        """Set up Zerobyte using a username and password."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = normalize_host(user_input[CONF_HOST])
            user_input[CONF_HOST] = host

            session = aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar(unsafe=True))

            client = ZerobyteClient(
                host=host,
                username=user_input[CONF_USERNAME],
                password=user_input[CONF_PASSWORD],
                session=session,
            )

            errors = await self._validate_and_finish(client, session, host)
            if not errors:
                return self.async_create_entry(
                    title=f"Zerobyte ({host})",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="password",
            data_schema=STEP_PASSWORD_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_api_key(self, user_input: dict[str, Any] | None = None):
        """Set up Zerobyte using an API key."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = normalize_host(user_input[CONF_HOST])
            user_input[CONF_HOST] = host
            api_key = user_input[CONF_API_KEY]

            session = aiohttp.ClientSession(headers={API_KEY_HEADER: api_key})

            client = ZerobyteClient(
                host=host,
                api_key=api_key,
                session=session,
            )

            errors = await self._validate_and_finish(client, session, host)
            if not errors:
                return self.async_create_entry(
                    title=f"Zerobyte ({host})",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="api_key",
            data_schema=STEP_API_KEY_DATA_SCHEMA,
            errors=errors,
        )

    async def _validate_and_finish(
        self, client: ZerobyteClient, session: aiohttp.ClientSession, host: str
    ) -> dict[str, str]:
        """Validate the client can authenticate and fetch data. Returns errors dict."""
        errors: dict[str, str] = {}
        try:
            await client.authenticate()
            await client.get_volumes()
            await client.get_backups()
        except ZerobyteAuthError:
            errors["base"] = "invalid_auth"
        except ZerobyteConnectionError:
            errors["base"] = "cannot_connect"
        except Exception:
            _LOGGER.exception("Unexpected error during Zerobyte setup")
            errors["base"] = "unknown"
        else:
            await self.async_set_unique_id(host)
            self._abort_if_unique_id_configured()
        finally:
            if errors:
                await session.close()

        return errors
