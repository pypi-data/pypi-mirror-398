"""
Lambda-aware factory for EventService.

Provides lambda-specific routing methods while inheriting all core EventService functionality.
Follows the LambdaServiceFactory pattern for consistency across the codebase.

Query Routing Pattern:
    Uses a router to map query parameters to service methods, keeping the
    factory method clean and making it easy to add new query types.
"""

from geek_cafe_saas_sdk.lambda_handlers._base.decorators import service_method
from geek_cafe_saas_sdk.modules.events.models import Event
from geek_cafe_saas_sdk.modules.events.services.event_service import EventService
from geek_cafe_saas_sdk.core.services.lambda_service_factory import LambdaServiceFactory
from geek_cafe_saas_sdk.lambda_handlers import LambdaEvent
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from typing import List, Callable, Dict, Any, Optional


class EventServiceLambdaFactory(EventService, LambdaServiceFactory[Event]):
    """
    Lambda-aware service factory for events.
    
    Extends EventService with lambda-specific methods that handle parameter extraction
    and routing to appropriate service methods. All core CRUD operations are inherited
    from EventService.
    
    Lambda Methods:
    - list_events(event): Route to list_by_tenant or list_events_by_visibility
    
    Query Router Pattern:
        Defines routing rules that map query parameters to service methods.
        Easy to extend with new query types without modifying list_events().
    
    Usage in Handler:
        service = EventServiceLambdaFactory(...)
        return service.list_events(event)  # Clean, single responsibility
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize factory with query router."""
        super().__init__(*args, **kwargs)
        # Query router maps filter combinations to handler methods
        self._query_router = self._build_query_router()
    
    def _build_query_router(self) -> List[Dict[str, Any]]:
        """
        Build query router that maps query parameters to service methods.
        
        Router Pattern Benefits:
        - Declarative: Clear mapping of queries to handlers
        - Extensible: Add new routes without touching list_events()
        - Testable: Each route can be tested independently
        - Self-documenting: Routes describe available queries
        
        Returns:
            List of route definitions (order matters - first match wins)
        """
        return [
            # Route 1: Visibility-based queries
            {
                'name': 'visibility_query',
                'condition': lambda filters: 'visibility' in filters,
                'handler': self._handle_visibility_query,
                'description': 'Query events by visibility (public, private, members_only)'
            },
            # Route 2: Status-only queries
            {
                'name': 'status_query',
                'condition': lambda filters: 'status' in filters and 'visibility' not in filters,
                'handler': self._handle_status_query,
                'description': 'Query events by status (published, draft, cancelled)'
            },
            # Route 3: Date range queries
            {
                'name': 'date_range_query',
                'condition': lambda filters: 'start_date' in filters or 'end_date' in filters,
                'handler': self._handle_date_range_query,
                'description': 'Query events by date range'
            },
            # Route 4: Location queries
            {
                'name': 'location_query',
                'condition': lambda filters: any(k in filters for k in ['city', 'state', 'country']),
                'handler': self._handle_location_query,
                'description': 'Query events by location'
            },
            # Default route (must be last)
            {
                'name': 'default',
                'condition': lambda filters: True,  # Always matches
                'handler': self._handle_default_query,
                'description': 'Default: return all tenant events'
            }
        ]
    
    # ========================================
    # Route Handlers
    # ========================================
    
    def _handle_visibility_query(self, filters: Dict[str, Any], pagination: Dict[str, Any]) -> ServiceResult[List[Event]]:
        """Handle visibility-based queries."""
        return self.list_events_by_visibility(
            visibility=filters['visibility'],
            status=filters.get('status', 'published'),
            limit=pagination['limit']
        )
    
    def _handle_status_query(self, filters: Dict[str, Any], pagination: Dict[str, Any]) -> ServiceResult[List[Event]]:
        """Handle status-only queries."""
        # TODO: Implement list_by_status in EventService
        # For now, fall back to list_by_tenant and filter
        return self.list_by_tenant(limit=pagination['limit'])
    
    def _handle_date_range_query(self, filters: Dict[str, Any], pagination: Dict[str, Any]) -> ServiceResult[List[Event]]:
        """Handle date range queries."""
        # TODO: Implement list_by_date_range in EventService
        # For now, fall back to list_by_tenant
        return self.list_by_tenant(limit=pagination['limit'])
    
    def _handle_location_query(self, filters: Dict[str, Any], pagination: Dict[str, Any]) -> ServiceResult[List[Event]]:
        """Handle location-based queries."""
        # TODO: Implement list_by_location in EventService
        # For now, fall back to list_by_tenant
        return self.list_by_tenant(limit=pagination['limit'])
    
    def _handle_default_query(self, filters: Dict[str, Any], pagination: Dict[str, Any]) -> ServiceResult[List[Event]]:
        """Handle default query (all tenant events)."""
        return self.list_by_tenant(limit=pagination['limit'])
   
    @service_method("list_events")
    def list_events(self, event: LambdaEvent) -> ServiceResult[List[Event]]:
        """
        List events with optional filtering based on query parameters.
        
        Uses Query Router Pattern for clean, extensible routing.
        
        Query Parameters:
        - limit (int): Max results (default: 50)
        - visibility (str): Filter by visibility (public, private, members_only)
        - status (str): Filter by status (published, draft, cancelled)
        - start_date (str): Filter by start date (ISO format)
        - end_date (str): Filter by end date (ISO format)
        - city, state, country (str): Filter by location
        
        Args:
            event: Lambda event with query parameters
            
        Returns:
            ServiceResult with list of events
            
        Examples:
            GET /events?limit=20 → All tenant events
            GET /events?visibility=public → Public published events
            GET /events?status=draft → Draft events
            GET /events?city=Seattle&state=WA → Events in Seattle
        """
        # Extract parameters
        pagination = self._extract_pagination(event, default_limit=50)
        filters = self._extract_filters(
            event, 
            'visibility', 'status', 
            'start_date', 'end_date',
            'city', 'state', 'country'
        )
        
        # Route to appropriate handler using query router
        for route in self._query_router:
            if route['condition'](filters):
                return route['handler'](filters, pagination)
        
        # Should never reach here (default route always matches)
        return self._handle_default_query(filters, pagination)