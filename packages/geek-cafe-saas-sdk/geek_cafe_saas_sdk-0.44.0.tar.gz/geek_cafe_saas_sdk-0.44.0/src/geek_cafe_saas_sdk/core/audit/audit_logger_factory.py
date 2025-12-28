"""
Audit Logger Factory - Auto-configures audit logging from environment.

This factory creates the appropriate audit logger based on environment
variables, making it easy to configure audit logging without code changes.

Copyright 2024-2025 Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

import os
from typing import Optional, Union
from boto3_assist.dynamodb.dynamodb import DynamoDB
from aws_lambda_powertools import Logger

from .audit_logger_protocol import IAuditLogger
from .dynamodb_audit_logger import DynamoDBAuditLogger
from .s3_audit_logger import S3AuditLogger
from .composite_audit_logger import CompositeAuditLogger
from .noop_audit_logger import NoOpAuditLogger

logger = Logger()


class AuditLoggerFactory:
    """
    Factory for creating audit loggers from environment configuration.
    
    Environment Variables:
        AUDIT_LOG_ENABLED: "true" to enable audit logging (default: "false")
        AUDIT_LOG_DESTINATION: "dynamodb", "s3", or "both" (default: "dynamodb")
        AUDIT_LOG_TABLE_NAME: DynamoDB table name for audit logs
        AUDIT_LOG_BUCKET_NAME: S3 bucket name for audit logs
        AUDIT_LOG_BUCKET_PREFIX: S3 key prefix (default: "audit-logs")
        AUDIT_LOG_FAIL_OPEN: "true" to continue on failures (default: "true")
    
    Example:
        # In Lambda handler or application startup
        audit_logger = AuditLoggerFactory.create_from_environment()
        
        # Or with explicit configuration
        audit_logger = AuditLoggerFactory.create(
            enabled=True,
            destination="both",
            dynamodb_table_name="audit-logs",
            s3_bucket_name="audit-archive"
        )
    
    Usage in DatabaseService:
        class MyService(DatabaseService):
            def __init__(self, ..., audit_logger=None):
                super().__init__(...)
                self._audit_logger = audit_logger or AuditLoggerFactory.create_from_environment()
    """
    
    # Environment variable names
    ENV_ENABLED = "AUDIT_LOG_ENABLED"
    ENV_DESTINATION = "AUDIT_LOG_DESTINATION"
    ENV_TABLE_NAME = "AUDIT_LOG_TABLE_NAME"
    ENV_BUCKET_NAME = "AUDIT_LOG_BUCKET_NAME"
    ENV_BUCKET_PREFIX = "AUDIT_LOG_BUCKET_PREFIX"
    ENV_FAIL_OPEN = "AUDIT_LOG_FAIL_OPEN"
    
    # Valid destinations
    DESTINATION_DYNAMODB = "dynamodb"
    DESTINATION_S3 = "s3"
    DESTINATION_BOTH = "both"
    
    # Singleton instance for reuse
    _instance: Optional[IAuditLogger] = None
    
    @classmethod
    def create_from_environment(
        cls,
        *,
        dynamodb: Optional[DynamoDB] = None,
        force_new: bool = False
    ) -> IAuditLogger:
        """
        Create audit logger from environment variables.
        
        Args:
            dynamodb: Optional DynamoDB client to reuse
            force_new: If True, create new instance even if one exists
            
        Returns:
            Configured audit logger instance
            
        Environment Variables:
            AUDIT_LOG_ENABLED: "true" to enable (default: "false")
            AUDIT_LOG_DESTINATION: "dynamodb", "s3", or "both"
            AUDIT_LOG_TABLE_NAME: DynamoDB table name
            AUDIT_LOG_BUCKET_NAME: S3 bucket name
            AUDIT_LOG_BUCKET_PREFIX: S3 key prefix
            AUDIT_LOG_FAIL_OPEN: "true" to continue on failures
        """
        # Return cached instance if available and not forcing new
        if cls._instance is not None and not force_new:
            return cls._instance
        
        # Check if enabled
        enabled = os.getenv(cls.ENV_ENABLED, "false").lower() == "true"
        
        if not enabled:
            logger.info("Audit logging disabled (AUDIT_LOG_ENABLED != 'true')")
            cls._instance = NoOpAuditLogger()
            return cls._instance
        
        # Get configuration
        destination = os.getenv(cls.ENV_DESTINATION, cls.DESTINATION_DYNAMODB).lower()
        table_name = os.getenv(cls.ENV_TABLE_NAME)
        bucket_name = os.getenv(cls.ENV_BUCKET_NAME)
        bucket_prefix = os.getenv(cls.ENV_BUCKET_PREFIX, "audit-logs")
        fail_open = os.getenv(cls.ENV_FAIL_OPEN, "true").lower() == "true"
        
        # Create logger based on destination
        cls._instance = cls.create(
            enabled=True,
            destination=destination,
            dynamodb_table_name=table_name,
            s3_bucket_name=bucket_name,
            s3_bucket_prefix=bucket_prefix,
            fail_open=fail_open,
            dynamodb=dynamodb
        )
        
        return cls._instance
    
    @classmethod
    def create(
        cls,
        *,
        enabled: bool = True,
        destination: str = DESTINATION_DYNAMODB,
        dynamodb_table_name: Optional[str] = None,
        s3_bucket_name: Optional[str] = None,
        s3_bucket_prefix: str = "audit-logs",
        fail_open: bool = True,
        dynamodb: Optional[DynamoDB] = None
    ) -> IAuditLogger:
        """
        Create audit logger with explicit configuration.
        
        Args:
            enabled: Whether audit logging is enabled
            destination: "dynamodb", "s3", or "both"
            dynamodb_table_name: DynamoDB table name (required for dynamodb/both)
            s3_bucket_name: S3 bucket name (required for s3/both)
            s3_bucket_prefix: S3 key prefix
            fail_open: If True, logging failures don't raise exceptions
            dynamodb: Optional DynamoDB client to reuse
            
        Returns:
            Configured audit logger instance
            
        Raises:
            ValueError: If required configuration is missing
        """
        if not enabled:
            return NoOpAuditLogger()
        
        destination = destination.lower()
        
        # Validate configuration
        if destination in (cls.DESTINATION_DYNAMODB, cls.DESTINATION_BOTH):
            if not dynamodb_table_name:
                logger.warning(
                    f"AUDIT_LOG_TABLE_NAME not set but destination={destination}. "
                    "Falling back to NoOpAuditLogger."
                )
                return NoOpAuditLogger()
        
        if destination in (cls.DESTINATION_S3, cls.DESTINATION_BOTH):
            if not s3_bucket_name:
                logger.warning(
                    f"AUDIT_LOG_BUCKET_NAME not set but destination={destination}. "
                    "Falling back to NoOpAuditLogger."
                )
                return NoOpAuditLogger()
        
        # Create loggers based on destination
        if destination == cls.DESTINATION_DYNAMODB:
            logger.info(
                f"Creating DynamoDB audit logger",
                extra={"table_name": dynamodb_table_name}
            )
            return DynamoDBAuditLogger(
                dynamodb=dynamodb,
                table_name=dynamodb_table_name,
                fail_open=fail_open
            )
        
        elif destination == cls.DESTINATION_S3:
            logger.info(
                f"Creating S3 audit logger",
                extra={"bucket_name": s3_bucket_name, "prefix": s3_bucket_prefix}
            )
            return S3AuditLogger(
                bucket_name=s3_bucket_name,
                prefix=s3_bucket_prefix,
                fail_open=fail_open
            )
        
        elif destination == cls.DESTINATION_BOTH:
            logger.info(
                f"Creating composite audit logger (DynamoDB + S3)",
                extra={
                    "table_name": dynamodb_table_name,
                    "bucket_name": s3_bucket_name
                }
            )
            dynamodb_logger = DynamoDBAuditLogger(
                dynamodb=dynamodb,
                table_name=dynamodb_table_name,
                fail_open=fail_open
            )
            s3_logger = S3AuditLogger(
                bucket_name=s3_bucket_name,
                prefix=s3_bucket_prefix,
                fail_open=fail_open
            )
            return CompositeAuditLogger(
                loggers=[dynamodb_logger, s3_logger],
                primary_logger=dynamodb_logger,  # DynamoDB for queries
                fail_open=fail_open
            )
        
        else:
            logger.warning(
                f"Unknown audit destination '{destination}'. "
                "Valid values: 'dynamodb', 's3', 'both'. "
                "Falling back to NoOpAuditLogger."
            )
            return NoOpAuditLogger()
    
    @classmethod
    def reset(cls) -> None:
        """
        Reset the cached instance.
        
        Useful for testing or when configuration changes.
        """
        cls._instance = None
    
    @classmethod
    def get_instance(cls) -> Optional[IAuditLogger]:
        """
        Get the cached instance without creating a new one.
        
        Returns:
            Cached audit logger instance or None if not created
        """
        return cls._instance
