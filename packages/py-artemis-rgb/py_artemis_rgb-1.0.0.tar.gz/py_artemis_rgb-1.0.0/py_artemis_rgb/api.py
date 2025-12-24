"""API interaction module for Artemis RGB.

This module provides functions for interacting with Artemis RGB API endpoints.
"""

import logging
from contextlib import asynccontextmanager
from typing import Any
from uuid import UUID

from aiohttp import ClientError, ClientSession
from pydantic import ValidationError

from .config import ArtemisConfig
from .exceptions import ArtemisCannotConnectError, ArtemisUnknownType
from .types import ArtemisCategory, ArtemisProfile, BoolString

_LOGGER = logging.getLogger(__name__)


class ArtemisAPI:
    """Class for interacting with Artemis RGB API."""

    config: ArtemisConfig
    session: ClientSession

    def __init__(self, config: ArtemisConfig) -> None:
        """Initialize the Artemis API client."""
        self.config = config
        self.session = config.session

    @asynccontextmanager
    async def _get_session_context(self) -> Any:
        if self.session:
            yield self.session
        else:
            async with ClientSession() as session:
                yield session

    async def _fetch(self, endpoint: str) -> Any:
        """Send a get command to Artemis API."""

        url = f"http://{self.config.host}:{self.config.port}/{endpoint}"
        _LOGGER.debug("Fetching %s", url)
        try:
            async with self._get_session_context() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise ArtemisCannotConnectError(
                            f"Server returned status {response.status}: {error_text}"
                        )

                    if "application/json" not in response.headers.get(
                        "Content-Type", ""
                    ):
                        raise ArtemisCannotConnectError(
                            "Expected JSON response but got different content type"
                        )

                    return await response.json()

        except ClientError as exc:
            raise ArtemisCannotConnectError(f"Failed to fetch {url}") from exc

    async def _post(
        self,
        endpoint: str,
        data: Any = None,
        params: dict[str, Any] | None = None,
    ) -> None:
        """Send a post to Artemis API."""

        url = f"http://{self.config.host}:{self.config.port}/{endpoint}"
        _LOGGER.debug(
            "Post sent to %s with data: %s and params: %s", url, data, params
        )
        try:
            if data is None:
                kwargs = {}
            elif isinstance(data, (list, dict)):
                kwargs = {"json": data}
            else:
                kwargs = {"data": data}
            async with self._get_session_context() as session:
                async with session.post(
                    url, params=params, **kwargs
                ) as response:
                    response_text = await response.text()

            if response.status != 204:
                raise ArtemisCannotConnectError(
                    f"Server returned status {response.status}: {response_text}"
                )
            _LOGGER.debug("Got post response: %s", response_text)
        except ClientError as exc:
            raise ArtemisCannotConnectError(f"Failed to push to {url}") from exc

    async def get_profiles(self) -> list[ArtemisProfile]:
        """Get Artemis profile data."""
        _LOGGER.info("Getting Artemis RGB profiles")

        endpoint = "profiles"

        result = await self._fetch(endpoint)
        try:
            typed_result = [ArtemisProfile(**category) for category in result]
        except ValidationError as exc:
            raise ArtemisUnknownType(
                "The profiles received are not typed as expected. Has the API been modified ?"
            ) from exc
        return typed_result

    async def get_profile_categories(self) -> list[ArtemisCategory]:
        """Get Artemis profile categories data."""
        _LOGGER.info("Getting Artemis RGB profile categories")

        endpoint = "profiles/categories"

        result = await self._fetch(endpoint)
        try:
            typed_result = [ArtemisCategory(**category) for category in result]
        except ValidationError as exc:
            raise ArtemisUnknownType(
                "The profile categories received are not typed as expected. Has the API been modified ?"
            ) from exc
        return typed_result

    async def post_bring_to_foreground(self, route: str = "") -> None:
        """Bring Artemis to the foreground, with an optional route to view."""
        _LOGGER.info("Bringing Artemis to the foreground with the route '%s'", route)

        endpoint = "remote/bring-to-foreground"

        await self._post(endpoint, route)

    async def post_restart(self, args: list[str] = []) -> None:
        """Restart Artemis with optional command line arguments."""
        _LOGGER.info("Restarting Artemis")

        endpoint = "remote/restart"

        await self._post(endpoint, args)

    async def post_shutdown(self) -> None:
        """Shutdown Artemis."""
        _LOGGER.info("Shutting down Artemis")

        endpoint = "remote/shutdown"

        await self._post(endpoint)

    async def post_suspend_profile(
        self, profile_id: UUID, suspend_state: BoolString
    ) -> None:
        """Suspend or resume an Artemis profile."""
        _LOGGER.info(
            "Changing profile %s suspend state to %s", profile_id, suspend_state
        )

        endpoint = f"profiles/suspend/{profile_id}"
        params = {
            "suspend": suspend_state,
        }

        await self._post(endpoint, params=params)
