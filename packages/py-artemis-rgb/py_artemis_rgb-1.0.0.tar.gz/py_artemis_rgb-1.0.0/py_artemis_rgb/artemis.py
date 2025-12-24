"""Service class for Artemis RGB.

This is the main service class that wraps the API layer.
"""

from uuid import UUID

from .api import ArtemisAPI
from .config import ArtemisConfig
from .exceptions import ArtemisUnknownProfile
from .types import ArtemisCategory, ArtemisProfile
from .utils import bool_to_string, profile_id_exists


class Artemis:
    """Class for interacting with Artemis RGB."""

    api: ArtemisAPI

    def __init__(self, config: ArtemisConfig) -> None:
        """Initialize the Artemis object."""
        self.api = ArtemisAPI(config)

    async def get_profiles(self) -> list[ArtemisProfile]:
        """Get Artemis profile data."""
        return await self.api.get_profiles()

    async def get_profile_categories(self) -> list[ArtemisCategory]:
        """Get Artemis profile categories data."""
        return await self.api.get_profile_categories()

    async def bring_to_foreground(self, route: str = "") -> None:
        """Bring Artemis to the foreground, with an optional route to view."""
        await self.api.post_bring_to_foreground(route)

    async def restart(self, args: list[str] = []) -> None:
        """Restart Artemis with optional command line arguments."""
        await self.api.post_restart(args)

    async def shutdown(self) -> None:
        """Shutdown Artemis."""
        await self.api.post_shutdown()

    async def suspend_profile(
        self, profile_id: UUID | str, suspend_state: bool
    ) -> None:
        """Suspend or resume an Artemis profile."""

        if isinstance(profile_id, str):
            profile_id = UUID(profile_id)

        profiles = await self.get_profiles()
        if not profile_id_exists(profiles, profile_id):
            raise ArtemisUnknownProfile(f"The profile id {profile_id} does not exist")

        await self.api.post_suspend_profile(profile_id, bool_to_string(suspend_state))
