"""Custom exceptions for the Artemis RGB API wrapper.

This module contains all custom exceptions that may be raised by the Artemis RGB API wrapper.
Each exception provides specific error information to help diagnose issues.
"""


class ArtemisError(Exception):
    """Base exception for all Artemis-related errors.

    All custom exceptions in this module inherit from this base class.
    """


class ArtemisCannotConnectError(ArtemisError):
    """Exception raised when connection to Artemis RGB API fails.

    This may be due to network issues, server unavailability, or invalid IP address.
    """


class ArtemisUnknownType(ArtemisError):
    """Exception raised when the data received does not correspond to expected types.

    This may be raised when the API has changed.
    """


class ArtemisUnknownProfile(ArtemisError):
    """Exception raised when a request is made with a profile id that does not exist."""
