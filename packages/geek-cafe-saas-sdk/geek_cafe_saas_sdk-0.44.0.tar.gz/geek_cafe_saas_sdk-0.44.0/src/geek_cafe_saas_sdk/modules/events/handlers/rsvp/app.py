# Event RSVP handler
from typing import Dict, Any
from geek_cafe_saas_sdk.lambda_handlers import create_handler, LambdaEvent
from geek_cafe_saas_sdk.modules.events.services.event_attendee_service import EventAttendeeService
from geek_cafe_saas_sdk.core.service_result import ServiceResult

handler_wrapper = create_handler(service_class=EventAttendeeService, convert_request_case=True)

def lambda_handler(event: Dict[str, Any], context: Any, injected_service=None) -> Dict[str, Any]:
    return handler_wrapper.execute(event, context, rsvp_logic, injected_service)

def rsvp_logic(event: LambdaEvent, service: EventAttendeeService) -> ServiceResult:
    event_id = event.path('event_id') or event.path('id') or event.body().get('event_id')
    body = event.body()
    rsvp_status = body.get('rsvp_status', 'accepted')
    user_id = body.get('user_id') or service.request_context.target_user_id
    
    # Remove fields that shouldn't be passed to update_rsvp
    body.pop('event_id', None)
    body.pop('user_id', None)
    body.pop('rsvp_status', None)
    
    return service.update_rsvp(event_id=event_id, user_id=user_id, rsvp_status=rsvp_status, **body)
