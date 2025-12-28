"""Lambda handler for creating webhook subscriptions."""

from typing import Dict, Any
from geek_cafe_saas_sdk.lambda_handlers import create_handler, LambdaEvent
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.modules.notifications.services import NotificationService


handler_wrapper = create_handler(
    service_class=NotificationService,
    require_body=True,
    convert_request_case=True
)


def lambda_handler(event: Dict[str, Any], context: Any, injected_service=None) -> Dict[str, Any]:
    """
    Create webhook subscription.
    
    POST /webhooks
    
    Body:
    {
        "subscriptionName": "Payment Events",
        "url": "https://example.com/webhooks/payments",
        "eventTypes": ["payment.completed", "payment.failed"],
        "secret": "webhook_secret_key"
    }
    """
    return handler_wrapper.execute(event, context, create_webhook, injected_service)


def create_webhook(event: LambdaEvent, service: NotificationService) -> ServiceResult:
    """Business logic for creating webhook."""
    tenant_id = user_context.get("tenant_id")
    payload = event.body()
    
    subscription_name = payload.get("subscription_name")
    if not subscription_name:
        raise ValueError("subscription_name is required")
    
    url = payload.get("url")
    if not url:
        raise ValueError("url is required")
    
    event_types = payload.get("event_types")
    if not event_types:
        raise ValueError("event_types is required")
    
    # Extract optional fields
    kwargs = {}
    optional_fields = [
        "secret", "api_key", "custom_headers", "http_method", "content_type",
        "timeout_seconds", "retry_enabled", "max_retries", "retry_delay_seconds",
        "event_filters", "description", "metadata"
    ]
    
    for field in optional_fields:
        if field in payload:
            kwargs[field] = payload[field]
    
    result = service.create_webhook_subscription(
        tenant_id=tenant_id,
        subscription_name=subscription_name,
        url=url,
        event_types=event_types,
        **kwargs
    )
    
    return result
