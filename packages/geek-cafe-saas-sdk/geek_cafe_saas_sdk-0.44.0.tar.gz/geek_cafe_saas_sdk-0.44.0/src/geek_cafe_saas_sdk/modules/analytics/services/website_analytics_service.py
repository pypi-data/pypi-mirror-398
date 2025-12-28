# Website Analytics Service

from typing import Dict, Any, List, Optional
from boto3_assist.dynamodb.dynamodb import DynamoDB
from geek_cafe_saas_sdk.core.services.database_service import DatabaseService
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.lambda_handlers._base.decorators import service_method
from geek_cafe_saas_sdk.core.service_errors import ValidationError, NotFoundError
from geek_cafe_saas_sdk.modules.analytics.models import WebsiteAnalytics


class WebsiteAnalyticsService(DatabaseService[WebsiteAnalytics]):
    """Service for WebsiteAnalytics database operations."""
    
        
    @service_method("create")

    
        
    def create(self, **kwargs) -> ServiceResult[WebsiteAnalytics]:
        """Create a new analytics record."""
        try:
            # Validate required fields
            required_fields = ['analytics_type']
            self._validate_required_fields(kwargs, required_fields)
            
            # At least one of route or slug should be provided
            if not kwargs.get('route') and not kwargs.get('slug'):
                raise ValidationError("Either 'route' or 'slug' must be provided", "route")

            # Create new analytics instance
            analytics = WebsiteAnalytics()
            analytics.tenant_id = tenant_id
            analytics.user_id = user_id
            analytics.created_by_id = user_id
            
            # Set analytics fields
            analytics.route = kwargs.get('route')
            analytics.slug = kwargs.get('slug')
            analytics.analytics_type = kwargs.get('analytics_type', 'general')
            analytics.data = kwargs.get('data', {})
            analytics.session_id = kwargs.get('session_id')
            analytics.user_agent = kwargs.get('user_agent')
            analytics.ip_address = kwargs.get('ip_address')
            analytics.referrer = kwargs.get('referrer')
            
            # Prepare for save (sets ID and timestamps)
            analytics.prep_for_save()
            
            # Save to database
            return self._save_model(analytics)
            
        except Exception as e:
            return self._handle_service_exception(e, 'create_analytics', tenant_id=tenant_id, user_id=user_id)
    
    # Convenience methods for different analytics types
    @service_method("create_page_view")
    def create_page_view(self, route: str, **kwargs) -> ServiceResult[WebsiteAnalytics]:
        """Create a page view analytics record."""
        # Security handled by _save_model
        tenant_id = self.request_context.authenticated_tenant_id
        user_id = self.request_context.authenticated_user_id
        
        analytics = WebsiteAnalytics()
        analytics.tenant_id = tenant_id
        analytics.user_id = user_id
        analytics.created_by_id = user_id
        analytics.set_page_view(route, **kwargs)
        
        # Set optional fields
        analytics.session_id = kwargs.get('session_id')
        analytics.user_agent = kwargs.get('user_agent')
        analytics.ip_address = kwargs.get('ip_address')
        analytics.referrer = kwargs.get('referrer')
        
        analytics.prep_for_save()
        return self._save_model(analytics)
    
    @service_method("create_error_log")
    def create_error_log(self, route: str, 
                        error_message: str, **kwargs) -> ServiceResult[WebsiteAnalytics]:
        """Create an error analytics record."""
        # Security handled by _save_model
        tenant_id = self.request_context.authenticated_tenant_id
        user_id = self.request_context.authenticated_user_id
        
        analytics = WebsiteAnalytics()
        analytics.tenant_id = tenant_id
        analytics.user_id = user_id
        analytics.created_by_id = user_id
        analytics.set_error(route, error_message, **kwargs)
        
        # Set optional fields
        analytics.session_id = kwargs.get('session_id')
        analytics.user_agent = kwargs.get('user_agent')
        analytics.ip_address = kwargs.get('ip_address')
        analytics.referrer = kwargs.get('referrer')
        
        analytics.prep_for_save()
        return self._save_model(analytics)
    
    @service_method("create_performance_log")
    def create_performance_log(self, route: str, 
                              **kwargs) -> ServiceResult[WebsiteAnalytics]:
        """Create a performance analytics record."""
        # Security handled by _save_model
        tenant_id = self.request_context.authenticated_tenant_id
        user_id = self.request_context.authenticated_user_id
        
        analytics = WebsiteAnalytics()
        analytics.tenant_id = tenant_id
        analytics.user_id = user_id
        analytics.created_by_id = user_id
        analytics.set_performance(route, **kwargs)
        
        # Set optional fields
        analytics.session_id = kwargs.get('session_id')
        analytics.user_agent = kwargs.get('user_agent')
        analytics.ip_address = kwargs.get('ip_address')
        analytics.referrer = kwargs.get('referrer')
        
        analytics.prep_for_save()
        return self._save_model(analytics)
    
    @service_method("create_custom_event")
    def create_custom_event(self, route: str,
                           event_name: str, **kwargs) -> ServiceResult[WebsiteAnalytics]:
        """Create a custom event analytics record."""
        # Security handled by _save_model
        tenant_id = self.request_context.authenticated_tenant_id
        user_id = self.request_context.authenticated_user_id
        
        analytics = WebsiteAnalytics()
        analytics.tenant_id = tenant_id
        analytics.user_id = user_id
        analytics.created_by_id = user_id
        analytics.set_custom_event(route, event_name, **kwargs)
        
        # Set optional fields
        analytics.session_id = kwargs.get('session_id')
        analytics.user_agent = kwargs.get('user_agent')
        analytics.ip_address = kwargs.get('ip_address')
        analytics.referrer = kwargs.get('referrer')
        
        analytics.prep_for_save()
        return self._save_model(analytics)
    
    @service_method("get_by_id")

    
    def get_by_id(self, analytics_id: str) -> ServiceResult[WebsiteAnalytics]:
        """Get analytics record by ID. Security is automatic via _get_by_id."""
        try:
            analytics = self._get_by_id(analytics_id, WebsiteAnalytics)
            
            if not analytics:
                raise NotFoundError(f"WebsiteAnalytics with ID {analytics_id} not found")
            
            return ServiceResult.success_result(analytics)
            
        except Exception as e:
            return self._handle_service_exception(e, 'get_analytics', analytics_id=analytics_id)
    
    @service_method("update")

    
    def update(self, analytics_id: str, 
               updates: Dict[str, Any]) -> ServiceResult[WebsiteAnalytics]:
        """Update analytics record. Security is automatic via _get_by_id."""
        try:
            # Get with security check
            analytics = self._get_by_id(analytics_id, WebsiteAnalytics)
            if not analytics:
                raise NotFoundError(f"WebsiteAnalytics with ID {analytics_id} not found")
            
            # Keep old model for audit
            old_analytics = self._fetch_model_raw(analytics_id, WebsiteAnalytics)
            
            # Apply updates
            for field, value in updates.items():
                if hasattr(analytics, field) and field not in ['id', 'created_utc_ts', 'tenant_id']:
                    setattr(analytics, field, value)
            
            # Update metadata
            analytics.updated_by_id = self.request_context.authenticated_user_id
            analytics.prep_for_save()
            
            return self._save_model(analytics, old_model=old_analytics)
            
        except Exception as e:
            return self._handle_service_exception(e, 'update_analytics', analytics_id=analytics_id)
    
    @service_method("delete")

    
    def delete(self, analytics_id: str) -> ServiceResult[bool]:
        """Delete analytics record. Security is automatic via _get_by_id."""
        try:
            analytics = self._get_by_id(analytics_id, WebsiteAnalytics)
            if not analytics:
                raise NotFoundError(f"WebsiteAnalytics with ID {analytics_id} not found")
            
            return self._delete_model(analytics)
            
        except Exception as e:
            return self._handle_service_exception(e, 'delete_analytics', analytics_id=analytics_id)
    
    def list_by_route(self, route: str, start_key: dict = None, limit: int = None) -> ServiceResult[List[WebsiteAnalytics]]:
        """List analytics records by route/slug."""
        try:
            model = WebsiteAnalytics()
            model.route = route
            return self._query_by_index(model, "gsi2", start_key=start_key, limit=limit)
        except Exception as e:
            return self._handle_service_exception(e, 'list_analytics_by_route', route=route)
    
    def list_by_tenant(self, start_key: dict = None, limit: int = None) -> ServiceResult[List[WebsiteAnalytics]]:
        """List analytics records by tenant."""
        try:
            model = WebsiteAnalytics()
            model.tenant_id = self.request_context.target_tenant_id
            return self._query_by_index(model, "gsi3", start_key=start_key, limit=limit)
        except Exception as e:
            return self._handle_service_exception(e, 'list_analytics_by_tenant')
    
    def list_by_type(self, analytics_type: str, start_key: dict = None, limit: int = None) -> ServiceResult[List[WebsiteAnalytics]]:
        """List analytics records by type (general, error, performance, custom)."""
        try:
            model = WebsiteAnalytics()
            model.analytics_type = analytics_type
            return self._query_by_index(model, "gsi4", start_key=start_key, limit=limit)
        except Exception as e:
            return self._handle_service_exception(e, 'list_analytics_by_type', analytics_type=analytics_type)
    
    def list_by_tenant_and_type(self, analytics_type: str, 
                                start_key: dict = None, limit: int = None) -> ServiceResult[List[WebsiteAnalytics]]:
        """List analytics records by tenant and type."""
        try:
            model = WebsiteAnalytics()
            model.tenant_id = tenant_id
            model.analytics_type = analytics_type
            return self._query_by_index(model, "gsi5", start_key=start_key, limit=limit)
        except Exception as e:
            return self._handle_service_exception(e, 'list_analytics_by_tenant_and_type', 
                                                 tenant_id=tenant_id, analytics_type=analytics_type)
    
    def list_all(self, start_key: dict = None, limit: int = None) -> ServiceResult[List[WebsiteAnalytics]]:
        """List all analytics records."""
        try:
            model = WebsiteAnalytics()
            return self._query_by_index(model, "gsi1", start_key=start_key, limit=limit)
        except Exception as e:
            return self._handle_service_exception(e, 'list_all_analytics')
