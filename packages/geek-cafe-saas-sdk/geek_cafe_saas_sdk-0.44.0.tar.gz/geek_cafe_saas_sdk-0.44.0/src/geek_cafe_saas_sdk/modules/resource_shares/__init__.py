"""
Resource Shares module for permission-based resource sharing.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

from .models.resource_share import ResourceShare
from .services.resource_share_service import ResourceShareService

__all__ = [
    "ResourceShare",
    "ResourceShareService",
]
