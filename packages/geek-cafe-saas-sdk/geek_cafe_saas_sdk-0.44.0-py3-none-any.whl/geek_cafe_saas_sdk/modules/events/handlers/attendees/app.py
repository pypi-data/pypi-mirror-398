# Event attendees handler
from typing import Dict, Any
from geek_cafe_saas_sdk.lambda_handlers import create_handler, LambdaEvent
from geek_cafe_saas_sdk.modules.events.services.event_attendee_service import EventAttendeeService
from geek_cafe_saas_sdk.core.service_result import ServiceResult

handler_wrapper = create_handler(service_class=EventAttendeeService, convert_request_case=True)

def lambda_handler(event: Dict[str, Any], context: Any, injected_service=None) -> Dict[str, Any]:
    return handler_wrapper.execute(event, context, list_attendees_logic, injected_service)

def list_attendees_logic(event: LambdaEvent, service: EventAttendeeService) -> ServiceResult:
    # Get event_id from path, query parameters, or body
    event_id = (event.path('event_id') or 
                event.path('id') or 
                event.query('event_id') or 
                event.body().get('event_id'))
    
    # Validate event_id is provided
    if not event_id:
        return ServiceResult.error_result("event_id is required", "MISSING_EVENT_ID")
    
    # Optional: filter by status
    rsvp_status = event.query('rsvp_status')
    
    # list_by_event supports optional rsvp_status filter
    return service.list_by_event(event_id=event_id, rsvp_status=rsvp_status)
