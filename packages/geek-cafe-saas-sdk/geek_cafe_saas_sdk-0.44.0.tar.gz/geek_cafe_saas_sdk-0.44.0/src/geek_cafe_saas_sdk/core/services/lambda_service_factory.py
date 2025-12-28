"""
Base factory pattern for creating lambda-aware service wrappers.

This provides a consistent pattern for services that need lambda-specific routing logic
while maintaining clean separation between business logic (in services) and 
lambda parameter handling (in factories).
"""

from abc import ABC
from typing import TypeVar, Generic
from geek_cafe_saas_sdk.lambda_handlers import LambdaEvent
from geek_cafe_saas_sdk.core.service_result import ServiceResult

T = TypeVar('T')


class LambdaServiceFactory(ABC, Generic[T]):
    """
    Base class for lambda-aware service factories.
    
    Pattern:
    1. Factory extends the core service class
    2. Adds lambda-specific methods that accept LambdaEvent
    3. Routes to appropriate service methods based on parameters
    4. Handler logic remains simple: service.lambda_method(event)
    
    Benefits:
    - Single Responsibility: Routing logic separate from business logic
    - DRY: Reusable pattern across all services
    - Testable: Can inject in tests, works with existing fixtures
    - Type-safe: LambdaEvent parameter makes intent explicit
    
    Example:
        class MyServiceFactory(MyService, LambdaServiceFactory[MyModel]):
            
            @service_method("list_items")
            def list_items(self, event: LambdaEvent) -> ServiceResult[List[MyModel]]:
                # Extract parameters
                limit = event.query_int('limit', default=50)
                status = event.query('status')
                
                # Route to appropriate service method
                if status:
                    return self.list_by_status(status=status, limit=limit)
                return self.list_all(limit=limit)
    """
    
    def _extract_pagination(self, event: LambdaEvent, default_limit: int = 50) -> dict:
        """
        Standard pagination parameter extraction.
        
        Returns:
            dict with 'limit' and optional 'next_token'
        """
        return {
            'limit': event.query_int('limit', default=default_limit),
            'next_token': event.query('next_token')
        }
    
    def _extract_filters(self, event: LambdaEvent, *filter_names: str) -> dict:
        """
        Extract multiple filter parameters from query string.
        
        Args:
            event: Lambda event
            *filter_names: Names of query parameters to extract
            
        Returns:
            dict of {name: value} for filters that are present
            
        Example:
            filters = self._extract_filters(event, 'status', 'visibility', 'type')
            # Returns: {'status': 'active', 'visibility': 'public'}
        """
        return {
            name: value 
            for name in filter_names 
            if (value := event.query(name)) is not None
        }
