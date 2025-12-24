"""Type definitions for Artemis RGB client.

This module contains type definitions and data structures used
throughout the Artemis RGB client.
"""

from typing import Literal
from uuid import UUID
from pydantic import BaseModel

BoolString = Literal["true", "false"]


class ArtemisCategory(BaseModel):
    """Type definition for Artemis category data.

    Represents a category with all its attributes.
    """

    Id: UUID
    Name: str
    Order: int
    IsSuspended: bool


class ArtemisProfile(BaseModel):
    """Type definition for Artemis profile data.

    Represents a profile with all its attributes.
    """

    Id: UUID
    Name: str
    Order: int
    IsActive: bool
    IsSuspended: bool
    IsMissingModule: bool
    HasActivationCondition: bool
    ActivationConditionMet: bool
    Category: ArtemisCategory
