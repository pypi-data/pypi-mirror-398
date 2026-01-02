"""
Public exports for the UserHub async client to the Chill Services platform.
"""

from .auth import detect_type, auth, token
from .model import BaseUser


__version__ = "0.18"

__all__ = (
    "__version__",
    "detect_type",
    "auth",
    "token",
    "BaseUser",
)
