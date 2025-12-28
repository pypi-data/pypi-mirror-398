from typing import Optional, Dict
from datetime import datetime
import logging


class AuditMixin:
    """Mixin for services that need audit logging."""
    
    def _log_activity(self, action: str, resource_type: str, resource_id: str,
                     tenant_id: str, user_id: str, metadata: Optional[Dict] = None) -> None:
        """Log activity for audit purposes."""
        logger = logging.getLogger(f"{__name__}.audit")
        
        audit_data = {
            'action': action,
            'resource_type': resource_type,
            'resource_id': resource_id,
            'tenant_id': tenant_id,
            'user_id': user_id,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        
        logger.info(
            f"AUDIT: {action} on {resource_type} {resource_id} by user {user_id}",
            extra=audit_data
        )
        
        # Also print for console visibility
        print(f"📋 AUDIT: {action} on {resource_type} {resource_id} by user {user_id}")
        
    # TODO: Implement activity logging to database such as dynamodb or put into a queue
        
