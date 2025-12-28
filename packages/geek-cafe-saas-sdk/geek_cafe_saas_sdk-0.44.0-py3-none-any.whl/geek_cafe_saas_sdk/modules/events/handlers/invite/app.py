# Event invite handler
from typing import Dict, Any
from geek_cafe_saas_sdk.lambda_handlers import create_handler, LambdaEvent
from geek_cafe_saas_sdk.modules.events.services.event_attendee_service import EventAttendeeService
from geek_cafe_saas_sdk.core.service_result import ServiceResult

handler_wrapper = create_handler(service_class=EventAttendeeService, convert_request_case=True)

def lambda_handler(event: Dict[str, Any], context: Any, injected_service=None) -> Dict[str, Any]:
    return handler_wrapper.execute(event, context, invite_logic, injected_service)

def invite_logic(event: LambdaEvent, service: EventAttendeeService) -> ServiceResult:
    body = event.body()
    # Get event_id from path parameters first, then from body
    event_id = event.path('event_id') or event.path('id') or body.get('event_id')
    # Remove event_id from body to avoid duplicate keyword argument
    body.pop('event_id', None)
    
    # Validate required event_id
    if not event_id:
        return ServiceResult.error_result("event_id is required", "MISSING_EVENT_ID")
    
    # Check if this is a bulk invite (user_ids present)
    if 'user_ids' in body:
        user_ids = body.pop('user_ids')
        return service.bulk_invite(event_id=event_id, user_ids=user_ids, **body)
    
    return service.invite(event_id=event_id, **body)
