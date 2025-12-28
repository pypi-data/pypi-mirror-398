# Event handler

from typing import Dict, Any
from geek_cafe_saas_sdk.lambda_handlers import create_handler, LambdaEvent
from geek_cafe_saas_sdk.modules.events.services.event_service_lambda_factory import EventServiceLambdaFactory
from geek_cafe_saas_sdk.core.service_result import ServiceResult

handler_wrapper = create_handler(
    service_class=EventServiceLambdaFactory,
    convert_request_case=True
)

def lambda_handler(event: Dict[str, Any], context: Any, injected_service=None) -> Dict[str, Any]:
    return handler_wrapper.execute(event, context, list_events_logic, injected_service)

def list_events_logic(event: LambdaEvent, service: EventServiceLambdaFactory) -> ServiceResult:
        
    # list events
    return service.list_events(event=event)
