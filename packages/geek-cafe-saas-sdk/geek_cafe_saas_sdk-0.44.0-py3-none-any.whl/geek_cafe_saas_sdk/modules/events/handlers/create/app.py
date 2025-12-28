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
    return handler_wrapper.execute(event, context, create_event_logic, injected_service)

def create_event_logic(event: LambdaEvent, service: EventService) -> ServiceResult:
    body = event.body()
    return service.create(**body)
