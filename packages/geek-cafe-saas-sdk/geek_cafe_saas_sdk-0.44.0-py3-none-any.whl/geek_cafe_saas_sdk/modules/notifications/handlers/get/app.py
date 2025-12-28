"""Lambda handler for getting a notification."""

from typing import Dict, Any
from geek_cafe_saas_sdk.lambda_handlers import create_handler, LambdaEvent
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.modules.notifications.services import NotificationService


handler_wrapper = create_handler(
    service_class=NotificationService,
    require_body=False,
    convert_request_case=True
)


def lambda_handler(event: Dict[str, Any], context: Any, injected_service=None) -> Dict[str, Any]:
    """
    Get a notification by ID.
    
    GET /notifications/{notificationId}
    """
    return handler_wrapper.execute(event, context, get_notification, injected_service)


def get_notification(event: LambdaEvent, service: NotificationService) -> ServiceResult:
    """Business logic for getting notification."""
    tenant_id = user_context.get("tenant_id")
    
    path_params = event.get("pathParameters") or {}
    notification_id = path_params.get("notification_id")
    
    if not notification_id:
        raise ValueError("notification_id is required in path")
    
    result = service.get_notification(tenant_id, notification_id)
    
    return result
