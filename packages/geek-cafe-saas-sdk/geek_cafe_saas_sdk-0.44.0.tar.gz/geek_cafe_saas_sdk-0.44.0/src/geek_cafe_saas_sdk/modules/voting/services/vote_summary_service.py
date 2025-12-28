# Vote Summary Service

from typing import Dict, Any
from boto3_assist.dynamodb.dynamodb import DynamoDB
from geek_cafe_saas_sdk.core.services.database_service import DatabaseService
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.lambda_handlers._base.decorators import service_method
from geek_cafe_saas_sdk.core.service_errors import ValidationError, NotFoundError
from geek_cafe_saas_sdk.modules.voting.models import VoteSummary


class VoteSummaryService(DatabaseService[VoteSummary]):
    """Service for VoteSummary database operations."""
    
    @service_method("create")
    def create(self, **kwargs) -> ServiceResult[VoteSummary]:
        """Create or update (upsert) a vote summary for a target.
        
        Security:
            - Requires authentication
            - Creates summary for target tenant/user (auto-extracted from request)
        """
        try:
            # Security handled by _save_model
            tenant_id = self.request_context.authenticated_tenant_id
            user_id = self.request_context.authenticated_user_id
            
            # Validate required fields
            required_fields = ['target_id']
            self._validate_required_fields(kwargs, required_fields)

            # First check if a summary already exists for this target
            existing = self._get_by_target_id(kwargs.get('target_id'))
            if existing:
                # Update the existing summary with all new data
                return self._update_existing_summary(existing, **kwargs)
            
            # Create new vote summary instance
            summary = VoteSummary()
            summary.tenant_id = tenant_id
            summary.user_id = user_id
            summary.target_id = kwargs.get('target_id')
            summary.created_by_id = user_id
            
            # Set enhanced fields
            summary.vote_type = kwargs.get('vote_type', 'single_choice')
            summary.choice_breakdown = kwargs.get('choice_breakdown', {})
            summary.choice_percentages = kwargs.get('choice_percentages', {})
            summary.choice_averages = kwargs.get('choice_averages', {})  # For rating votes
            summary.total_participants = int(kwargs.get('total_participants', 0) or 0)
            summary.total_selections = int(kwargs.get('total_selections', 0) or 0)
            
            # Set legacy fields for backward compatibility
            summary.total_up_votes = int(kwargs.get('total_up_votes', 0) or 0)
            summary.total_down_votes = int(kwargs.get('total_down_votes', 0) or 0)
            summary.total_votes = int(kwargs.get('total_votes', 0) or 0)
            
            # Set content
            summary.content = kwargs.get('content', {})
            
            # Calculate percentages if not provided
            if not summary.choice_percentages and summary.choice_breakdown:
                summary.calculate_percentages()
            
            # Prepare for save (sets ID and timestamps)
            summary.prep_for_save()
            
            # Save to database
            return self._save_model(summary)
            
        except Exception as e:
            return self._handle_service_exception(e, 'create_vote_summary')

    def _update_existing_summary(self, existing_summary: VoteSummary, **kwargs) -> ServiceResult[VoteSummary]:
        """Update an existing summary with new data."""
        user_id = self.request_context.authenticated_user_id
        # Update enhanced fields
        existing_summary.vote_type = kwargs.get('vote_type', existing_summary.vote_type)
        existing_summary.choice_breakdown = kwargs.get('choice_breakdown', existing_summary.choice_breakdown)
        existing_summary.choice_percentages = kwargs.get('choice_percentages', existing_summary.choice_percentages)
        existing_summary.choice_averages = kwargs.get('choice_averages', existing_summary.choice_averages)
        existing_summary.total_participants = int(kwargs.get('total_participants', existing_summary.total_participants) or 0)
        existing_summary.total_selections = int(kwargs.get('total_selections', existing_summary.total_selections) or 0)
        
        # Update legacy fields
        existing_summary.total_up_votes = int(kwargs.get('total_up_votes', existing_summary.total_up_votes) or 0)
        existing_summary.total_down_votes = int(kwargs.get('total_down_votes', existing_summary.total_down_votes) or 0)
        existing_summary.total_votes = int(kwargs.get('total_votes', existing_summary.total_votes) or 0)
        
        # Update content
        existing_summary.content = kwargs.get('content', existing_summary.content or {})
        
        # Recalculate percentages if needed
        if not existing_summary.choice_percentages and existing_summary.choice_breakdown:
            existing_summary.calculate_percentages()
        
        # Update metadata
        existing_summary.updated_by_id = user_id
        existing_summary.prep_for_save()  # Updates timestamp
        
        # Save updated summary
        return self._save_model(existing_summary)

    def _get_by_target_id(self, target_id: str) -> VoteSummary | None:
        """Helper: get a vote summary by target_id via GSI2."""
        model = VoteSummary()
        model.target_id = target_id
        result = self._query_by_index(model, "gsi2")
        if result.success and result.data:
            return result.data[0]
        return None
    
    @service_method("get_by_id")
    def get_by_id(self, summary_id: str) -> ServiceResult[VoteSummary]:
        """Get vote summary by ID. Security is automatic via _get_by_id."""
        try:
            summary = self._get_by_id(summary_id, VoteSummary)
            if not summary:
                raise NotFoundError(f"VoteSummary with ID {summary_id} not found")
            
            return ServiceResult.success_result(summary)
            
        except Exception as e:
            return self._handle_service_exception(e, 'get_vote_summary', summary_id=summary_id)

    @service_method("get_by_target_id")
    def get_by_target_id(self, target_id: str) -> ServiceResult[VoteSummary]:
        """Get vote summary by target_id. Security via tenant check."""
        try:
            summary = self._get_by_target_id(target_id)
            if not summary:
                raise NotFoundError(f"VoteSummary for target {target_id} not found")
            
            # Verify same tenant
            tenant_id = self.request_context.authenticated_tenant_id
            if summary.tenant_id != tenant_id:
                raise NotFoundError(f"VoteSummary for target {target_id} not found")
            
            return ServiceResult.success_result(summary)
            
        except Exception as e:
            return self._handle_service_exception(e, 'get_vote_summary_by_target', target_id=target_id)
    
    @service_method("update")
    def update(self, summary_id: str, 
               updates: Dict[str, Any]) -> ServiceResult[VoteSummary]:
        """Update vote summary. Security is automatic via _get_by_id."""
        try:
            summary = self._get_by_id(summary_id, VoteSummary)
            if not summary:
                raise NotFoundError(f"VoteSummary with ID {summary_id} not found")
            
            old_summary = self._fetch_model_raw(summary_id, VoteSummary)
            
            # Apply updates
            for field, value in updates.items():
                if hasattr(summary, field) and field not in ['id', 'created_utc_ts', 'tenant_id']:
                    setattr(summary, field, value)
            
            summary.prep_for_save()
            return self._save_model(summary, old_model=old_summary)
            
        except Exception as e:
            return self._handle_service_exception(e, 'update_vote_summary', summary_id=summary_id)
    
    @service_method("delete")
    def delete(self, summary_id: str) -> ServiceResult[bool]:
        """Delete vote summary. Security is automatic via _get_by_id."""
        try:
            summary = self._get_by_id(summary_id, VoteSummary)
            if not summary:
                raise NotFoundError(f"VoteSummary with ID {summary_id} not found")
            
            return self._delete_model(summary)
            
        except Exception as e:
            return self._handle_service_exception(e, 'delete_vote_summary', summary_id=summary_id)
    
    def list_by_tenant(self) -> ServiceResult[list[VoteSummary]]:
        """List vote summaries by tenant."""
        try:
            tenant_id = self.request_context.authenticated_tenant_id
            
            model = VoteSummary()
            model.tenant_id = tenant_id
            return self._query_by_index(model, "gsi3")
        except Exception as e:
            return self._handle_service_exception(e, 'list_vote_summaries')

    def list_all(self) -> ServiceResult[list[VoteSummary]]:
        """List all vote summaries."""
        try:
            model = VoteSummary()
            return self._query_by_index(model, "gsi1")
        except Exception as e:
            return self._handle_service_exception(e, 'list_all_vote_summaries')
