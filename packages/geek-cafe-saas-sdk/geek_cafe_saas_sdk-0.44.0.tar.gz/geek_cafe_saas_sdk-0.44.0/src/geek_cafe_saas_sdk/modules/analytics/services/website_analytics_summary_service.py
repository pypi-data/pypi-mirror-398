# Website Analytics Summary Service

from typing import Dict, Any, List, Optional
from boto3_assist.dynamodb.dynamodb import DynamoDB
from geek_cafe_saas_sdk.core.services.database_service import DatabaseService
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.lambda_handlers._base.decorators import service_method
from geek_cafe_saas_sdk.core.service_errors import ValidationError, NotFoundError
from geek_cafe_saas_sdk.modules.analytics.models import WebsiteAnalyticsSummary


class WebsiteAnalyticsSummaryService(DatabaseService[WebsiteAnalyticsSummary]):
    """Service for WebsiteAnalyticsSummary database operations."""
        
    
    @service_method("create")

        
    
    def create(self, **kwargs) -> ServiceResult[WebsiteAnalyticsSummary]:
        """Create or update (upsert) an analytics summary."""
        # Security handled by _save_model
        tenant_id = self.request_context.authenticated_tenant_id
        user_id = self.request_context.authenticated_user_id
        
        try:
            # Validate required fields
            required_fields = ['analytics_type', 'period_start_ts', 'period_end_ts']
            self._validate_required_fields(kwargs, required_fields)
            
            # At least one of route or slug should be provided
            if not kwargs.get('route') and not kwargs.get('slug'):
                raise ValidationError("Either 'route' or 'slug' must be provided", "route")

            # Check if a summary already exists for this route/period
            existing = self._get_by_route_and_period(
                kwargs.get('route') or kwargs.get('slug'),
                kwargs.get('period_start_ts'),
                kwargs.get('analytics_type')
            )
            
            if existing:
                # Update the existing summary
                return self._update_existing_summary(existing, tenant_id, user_id, **kwargs)
            
            # Create new summary instance
            summary = WebsiteAnalyticsSummary()
            summary.tenant_id = tenant_id
            summary.user_id = user_id
            summary.created_by_id = user_id
            
            # Set summary fields
            summary.route = kwargs.get('route')
            summary.slug = kwargs.get('slug')
            summary.analytics_type = kwargs.get('analytics_type', 'general')
            summary.period_start_ts = float(kwargs.get('period_start_ts'))
            summary.period_end_ts = float(kwargs.get('period_end_ts'))
            summary.period_type = kwargs.get('period_type', 'hourly')
            
            # Set aggregated metrics
            summary.total_events = int(kwargs.get('total_events', 0) or 0)
            summary.unique_sessions = int(kwargs.get('unique_sessions', 0) or 0)
            summary.unique_users = int(kwargs.get('unique_users', 0) or 0)
            summary.metrics = kwargs.get('metrics', {})
            summary.content = kwargs.get('content', {})
            
            # Prepare for save (sets ID and timestamps)
            summary.prep_for_save()
            
            # Save to database
            return self._save_model(summary)
            
        except Exception as e:
            return self._handle_service_exception(e, 'create_analytics_summary', tenant_id=tenant_id, user_id=user_id)
    
    def _update_existing_summary(self, existing_summary: WebsiteAnalyticsSummary, 
                                 tenant_id: str, user_id: str, **kwargs) -> ServiceResult[WebsiteAnalyticsSummary]:
        """Update an existing summary with new data."""
        # Update fields
        existing_summary.period_end_ts = float(kwargs.get('period_end_ts', existing_summary.period_end_ts))
        existing_summary.period_type = kwargs.get('period_type', existing_summary.period_type)
        
        # Update aggregated metrics
        existing_summary.total_events = int(kwargs.get('total_events', existing_summary.total_events) or 0)
        existing_summary.unique_sessions = int(kwargs.get('unique_sessions', existing_summary.unique_sessions) or 0)
        existing_summary.unique_users = int(kwargs.get('unique_users', existing_summary.unique_users) or 0)
        existing_summary.metrics = kwargs.get('metrics', existing_summary.metrics or {})
        existing_summary.content = kwargs.get('content', existing_summary.content or {})
        
        # Update metadata
        existing_summary.updated_by_id = user_id
        existing_summary.prep_for_save()  # Updates timestamp
        
        # Save updated summary
        return self._save_model(existing_summary)
    
    def _get_by_route_and_period(self, route: str, period_start_ts: float, 
                                 analytics_type: str) -> WebsiteAnalyticsSummary | None:
        """Helper: get a summary by route and period via GSI2."""
        model = WebsiteAnalyticsSummary()
        model.route = route
        result = self._query_by_index(model, "gsi2")
        
        if result.success and result.data:
            # Filter by period_start_ts and analytics_type
            for summary in result.data:
                if (summary.period_start_ts == period_start_ts and 
                    summary.analytics_type == analytics_type):
                    return summary
        return None
    
    @service_method("get_by_id")

    
    def get_by_id(self, summary_id: str) -> ServiceResult[WebsiteAnalyticsSummary]:
        """Get analytics summary by ID. Security is automatic via _get_by_id."""
        try:
            summary = self._get_by_id(summary_id, WebsiteAnalyticsSummary)
            if not summary:
                raise NotFoundError(f"WebsiteAnalyticsSummary with ID {summary_id} not found")
            
            return ServiceResult.success_result(summary)
            
        except Exception as e:
            return self._handle_service_exception(e, 'get_analytics_summary', summary_id=summary_id)
    
    @service_method("update")

    
    def update(self, summary_id: str, 
               updates: Dict[str, Any]) -> ServiceResult[WebsiteAnalyticsSummary]:
        """Update analytics summary. Security is automatic via _get_by_id."""
        try:
            summary = self._get_by_id(summary_id, WebsiteAnalyticsSummary)
            if not summary:
                raise NotFoundError(f"WebsiteAnalyticsSummary with ID {summary_id} not found")
            
            old_summary = self._fetch_model_raw(summary_id, WebsiteAnalyticsSummary)
            
            # Apply updates
            for field, value in updates.items():
                if hasattr(summary, field) and field not in ['id', 'created_utc_ts', 'tenant_id']:
                    setattr(summary, field, value)
            
            summary.updated_by_id = self.request_context.authenticated_user_id
            summary.prep_for_save()
            
            return self._save_model(summary, old_model=old_summary)
            
        except Exception as e:
            return self._handle_service_exception(e, 'update_analytics_summary', summary_id=summary_id)
    
    @service_method("delete")

    
    def delete(self, summary_id: str) -> ServiceResult[bool]:
        """Delete analytics summary. Security is automatic via _get_by_id."""
        try:
            summary = self._get_by_id(summary_id, WebsiteAnalyticsSummary)
            if not summary:
                raise NotFoundError(f"WebsiteAnalyticsSummary with ID {summary_id} not found")
            
            return self._delete_model(summary)
            
        except Exception as e:
            return self._handle_service_exception(e, 'delete_analytics_summary', summary_id=summary_id)
    
    def list_by_route(self, route: str, start_key: dict = None, limit: int = None) -> ServiceResult[List[WebsiteAnalyticsSummary]]:
        """List analytics summaries by route/slug."""
        try:
            model = WebsiteAnalyticsSummary()
            model.route = route
            return self._query_by_index(model, "gsi2", start_key=start_key, limit=limit)
        except Exception as e:
            return self._handle_service_exception(e, 'list_summaries_by_route', route=route)
    
    def list_by_tenant(self, start_key: dict = None, limit: int = None) -> ServiceResult[List[WebsiteAnalyticsSummary]]:
        """List analytics summaries by tenant."""
        tenant_id = self.request_context.authenticated_tenant_id
        
        try:
            model = WebsiteAnalyticsSummary()
            model.tenant_id = tenant_id
            return self._query_by_index(model, "gsi3", start_key=start_key, limit=limit)
        except Exception as e:
            return self._handle_service_exception(e, 'list_summaries_by_tenant', tenant_id=tenant_id)
    
    def list_by_type(self, analytics_type: str, start_key: dict = None, limit: int = None) -> ServiceResult[List[WebsiteAnalyticsSummary]]:
        """List analytics summaries by type."""
        try:
            model = WebsiteAnalyticsSummary()
            model.analytics_type = analytics_type
            return self._query_by_index(model, "gsi4", start_key=start_key, limit=limit)
        except Exception as e:
            return self._handle_service_exception(e, 'list_summaries_by_type', analytics_type=analytics_type)
    
    def list_by_tenant_and_type(self, analytics_type: str,
                                start_key: dict = None, limit: int = None) -> ServiceResult[List[WebsiteAnalyticsSummary]]:
        """List analytics summaries by tenant and type."""
        tenant_id = self.request_context.authenticated_tenant_id
        
        try:
            model = WebsiteAnalyticsSummary()
            model.tenant_id = tenant_id
            model.analytics_type = analytics_type
            return self._query_by_index(model, "gsi5", start_key=start_key, limit=limit)
        except Exception as e:
            return self._handle_service_exception(e, 'list_summaries_by_tenant_and_type',
                                                 tenant_id=tenant_id, analytics_type=analytics_type)
    
    def list_all(self, start_key: dict = None, limit: int = None) -> ServiceResult[List[WebsiteAnalyticsSummary]]:
        """List all analytics summaries."""
        try:
            model = WebsiteAnalyticsSummary()
            return self._query_by_index(model, "gsi1", start_key=start_key, limit=limit)
        except Exception as e:
            return self._handle_service_exception(e, 'list_all_summaries')
