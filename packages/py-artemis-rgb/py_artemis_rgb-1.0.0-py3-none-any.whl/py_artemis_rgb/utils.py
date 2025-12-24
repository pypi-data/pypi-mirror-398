"""Utility functions for Artemis RGB client."""

from uuid import UUID

from .types import ArtemisProfile, BoolString


def bool_to_string(value: bool) -> BoolString:
    """Convert a Python boolean to a string"""
    return "true" if value else "false"


def profile_id_exists(profiles: list[ArtemisProfile], profile_id: UUID) -> bool:
    """Check that a profile id exists"""
    return any(profile.Id == profile_id for profile in profiles)
