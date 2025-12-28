"""
Audit Event types and enums.

This module defines the AuditAction enum for standard audit actions.
The AuditLog model (audit_log_model.py) is the primary class for audit entries.

Copyright 2024-2025 Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

from enum import Enum

# Re-export AuditLog for backward compatibility
from geek_cafe_saas_sdk.core.audit.audit_log_model import AuditLog

# Alias for backward compatibility
AuditEvent = AuditLog


class AuditAction(str, Enum):
    """Standard audit actions for database operations."""
    CREATE = "CREATE"
    READ = "READ"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    SOFT_DELETE = "SOFT_DELETE"
    RESTORE = "RESTORE"
    SIGN = "SIGN"  # Electronic signature
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    SHARE = "SHARE"
    UNSHARE = "UNSHARE"
    DOWNLOAD = "DOWNLOAD"
    UPLOAD = "UPLOAD"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    ACCESS_DENIED = "ACCESS_DENIED"
