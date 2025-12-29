"""
WHOOP SDK - A Python SDK for the WHOOP Developer API.

This package provides easy access to WHOOP fitness data through a simple Python interface.
"""

from .auth import AuthManager
from .client import Whoop

__all__ = ["Whoop", "AuthManager"]

