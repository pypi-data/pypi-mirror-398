# Event handler

from typing import Dict, Any
from geek_cafe_saas_sdk.lambda_handlers import create_handler, LambdaEvent
from geek_cafe_saas_sdk.modules.events.services.event_service import EventService
from geek_cafe_saas_sdk.core.service_result import ServiceResult

handler_wrapper = create_handler(
    service_class=EventService,
    convert_request_case=True
)

def lambda_handler(event: Dict[str, Any], context: Any, injected_service=None) -> Dict[str, Any]:
    return handler_wrapper.execute(event, context, cancel_event_logic, injected_service)

def cancel_event_logic(event: LambdaEvent, service: EventService) -> ServiceResult:
    event_id = event.path('id')
    body = event.body()
    reason = body.get('cancellation_reason')
    return service.cancel(event_id=event_id, cancellation_reason=reason)
