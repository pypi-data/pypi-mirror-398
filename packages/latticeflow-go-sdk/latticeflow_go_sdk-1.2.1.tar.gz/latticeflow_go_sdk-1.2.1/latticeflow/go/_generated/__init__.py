"""A client library for accessing AI GO! API"""
from __future__ import annotations

from .client import AuthenticatedClient
from .client import Client


__all__ = ("AuthenticatedClient", "Client")
