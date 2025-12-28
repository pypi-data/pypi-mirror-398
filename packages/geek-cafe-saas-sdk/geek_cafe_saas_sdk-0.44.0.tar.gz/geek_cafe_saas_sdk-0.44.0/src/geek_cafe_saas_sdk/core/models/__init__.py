"""
Copyright 2024-2025 Geek Cafe, LLC
MIT License. See Project Root for the license information.

Geek Cafe SaaS SDK Models

NOTE: Models have been reorganized into domain-driven structure.
Import models directly from their domain modules:
  - geek_cafe_saas_sdk.modules.users.models
  - geek_cafe_saas_sdk.modules.tenancy.models
  - geek_cafe_saas_sdk.modules.communities.models
  - geek_cafe_saas_sdk.modules.events.models
  - geek_cafe_saas_sdk.modules.messaging.models
  - geek_cafe_saas_sdk.modules.voting.models
  - geek_cafe_saas_sdk.modules.analytics.models
"""

from geek_cafe_saas_sdk.core.models.base_model import BaseModel

__all__ = ["BaseModel"]
