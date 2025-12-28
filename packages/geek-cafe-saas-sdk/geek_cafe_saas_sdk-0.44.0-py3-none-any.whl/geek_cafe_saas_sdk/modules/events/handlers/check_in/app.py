# Event check-in handler
from typing import Dict, Any
from geek_cafe_saas_sdk.lambda_handlers import create_handler, LambdaEvent
from geek_cafe_saas_sdk.modules.events.services.event_attendee_service import EventAttendeeService
from geek_cafe_saas_sdk.core.service_result import ServiceResult

handler_wrapper = create_handler(service_class=EventAttendeeService, convert_request_case=True)

def lambda_handler(event: Dict[str, Any], context: Any, injected_service=None) -> Dict[str, Any]:
    return handler_wrapper.execute(event, context, check_in_logic, injected_service)

def check_in_logic(event: LambdaEvent, service: EventAttendeeService) -> ServiceResult:
    body = event.body()
    # Get event_id from path or body
    event_id = event.path('event_id') or event.path('id') or body.get('event_id')
    # Support both 'user_id' and 'attendee_user_id' field names
    user_id = body.get('user_id') or body.get('attendee_user_id')
    return service.check_in(event_id=event_id)
