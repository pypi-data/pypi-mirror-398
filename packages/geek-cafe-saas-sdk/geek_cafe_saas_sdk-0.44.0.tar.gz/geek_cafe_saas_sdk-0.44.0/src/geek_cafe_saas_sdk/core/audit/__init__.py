"""
Audit Logging Infrastructure for 21 CFR Part 11 Compliance.

This module provides centralized, automatic audit logging for all database operations.
Audit logs capture who did what, when, and the before/after state of records.

Components:
- AuditLog: DynamoDB model for audit log entries (follows standard model patterns)
- AuditEvent: Alias for AuditLog (backward compatibility)
- AuditAction: Enum of standard audit actions
- IAuditLogger: Protocol defining the audit logger interface
- DynamoDBAuditLogger: Logs to DynamoDB table
- S3AuditLogger: Logs to S3 bucket (JSON files)
- CompositeAuditLogger: Logs to multiple destinations
- NoOpAuditLogger: No-op implementation for when auditing is disabled
- AuditLoggerFactory: Auto-configures audit logger from environment

Multi-Tenancy:
- Actor: The user/tenant performing the action (actor_tenant_id, actor_user_id)
- Resource Owner: The user/tenant whose data is being modified (tenant_id, user_id)

Usage:
    # Auto-configured from environment variables
    from geek_cafe_saas_sdk.core.audit import AuditLoggerFactory
    
    audit_logger = AuditLoggerFactory.create_from_environment()
    
    # Or inject specific implementation
    from geek_cafe_saas_sdk.core.audit import DynamoDBAuditLogger
    
    audit_logger = DynamoDBAuditLogger(
        dynamodb=db,
        table_name="audit-logs"
    )

Environment Variables:
    AUDIT_LOG_ENABLED: "true" to enable audit logging (default: "false")
    AUDIT_LOG_DESTINATION: "dynamodb", "s3", or "both" (default: "dynamodb")
    AUDIT_LOG_TABLE_NAME: DynamoDB table name for audit logs
    AUDIT_LOG_BUCKET_NAME: S3 bucket name for audit logs
    AUDIT_LOG_FAIL_OPEN: "true" to continue on audit failures (default: "true")

Copyright 2024-2025 Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

from .audit_log_model import AuditLog
from .audit_event import AuditEvent, AuditAction
from .audit_logger_protocol import IAuditLogger
from .dynamodb_audit_logger import DynamoDBAuditLogger
from .s3_audit_logger import S3AuditLogger
from .composite_audit_logger import CompositeAuditLogger
from .noop_audit_logger import NoOpAuditLogger
from .audit_logger_factory import AuditLoggerFactory

__all__ = [
    "AuditLog",
    "AuditEvent",
    "AuditAction",
    "IAuditLogger",
    "DynamoDBAuditLogger",
    "S3AuditLogger",
    "CompositeAuditLogger",
    "NoOpAuditLogger",
    "AuditLoggerFactory",
]
