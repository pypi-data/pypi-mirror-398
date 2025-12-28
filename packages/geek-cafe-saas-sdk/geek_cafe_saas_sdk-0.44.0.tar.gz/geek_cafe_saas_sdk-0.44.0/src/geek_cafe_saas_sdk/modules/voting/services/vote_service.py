# Vote Service

from typing import Dict, Any
from boto3_assist.dynamodb.dynamodb import DynamoDB
from geek_cafe_saas_sdk.core.services.database_service import DatabaseService
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.core.service_errors import ValidationError, NotFoundError
from geek_cafe_saas_sdk.lambda_handlers._base.decorators import service_method
from geek_cafe_saas_sdk.modules.voting.models import Vote


class VoteService(DatabaseService[Vote]):
    """Service for Vote database operations."""
    
    @service_method("create")
    def create(self, **kwargs) -> ServiceResult[Vote]:
        """Create or update (upsert) a vote for a target by a user.
        
        Security:
            - Requires authentication
            - Creates vote for target tenant/user (auto-extracted from request)
        """
        # Validate authentication
        self.request_context.require_authentication()
        
        # Get targets (auto-extracted from path or defaults to authenticated user)
        tenant_id = self.request_context.target_tenant_id
        user_id = self.request_context.target_user_id
        
        # Validate required fields
        required_fields = ['target_id']
        self._validate_required_fields(kwargs, required_fields)

        # First check if a vote already exists for this user+target
        existing = self._get_by_user_and_target(user_id, kwargs.get('target_id'))
        if existing:
            # Update the existing vote with new data
            return self._update_existing_vote(existing, **kwargs)
        
        # Create new vote instance
        vote = Vote()
        vote.tenant_id = tenant_id
        vote.user_id = user_id
        vote.target_id = kwargs.get('target_id')
        vote.created_by_id = user_id
        
        # Set vote data based on type
        self._set_vote_data(vote, **kwargs)
        
        # Prepare for save (sets ID and timestamps)
        vote.prep_for_save()
        
        # Save to database
        return self._save_model(vote)

    def _update_existing_vote(self, existing_vote: Vote, **kwargs) -> ServiceResult[Vote]:
        """Update an existing vote with new data."""
        # Get user from request context
        user_id = self.request_context.target_user_id
        
        # Set new vote data
        self._set_vote_data(existing_vote, **kwargs)
        
        # Update metadata (updated_by_id will be set automatically by _save_model)
        existing_vote.prep_for_save()  # Updates timestamp
        
        # Save updated vote
        return self._save_model(existing_vote)

    def _set_vote_data(self, vote: Vote, **kwargs):
        """Set vote data based on the voting pattern."""
        # Check if this is a legacy binary vote (has up_vote or down_vote but no vote_type)
        has_legacy_fields = 'up_vote' in kwargs or 'down_vote' in kwargs
        has_vote_type = 'vote_type' in kwargs
        
        if has_legacy_fields and not has_vote_type:
            # This is a legacy binary vote
            vote.vote_type = 'legacy'
            vote.up_vote = int(kwargs.get('up_vote', 0) or 0)
            vote.down_vote = int(kwargs.get('down_vote', 0) or 0)
            vote.choices = kwargs.get('choices', {})
            vote.content = kwargs.get('content', {})
            return
        
        # Enhanced voting patterns
        vote_type = kwargs.get('vote_type', 'single_choice')
        vote.vote_type = vote_type
        vote.content = kwargs.get('content', {})
        
        if vote_type == 'single_choice':
            choice_id = kwargs.get('choice_id') or kwargs.get('selected_choice')
            available_choices = kwargs.get('available_choices', [])
            if choice_id:
                vote.set_single_choice(choice_id, available_choices)
        
        elif vote_type == 'multi_select':
            selected_choices = kwargs.get('selected_choices', [])
            available_choices = kwargs.get('available_choices', [])
            max_selections = kwargs.get('max_selections')
            vote.set_multi_select(selected_choices, available_choices, max_selections)
        
        elif vote_type == 'ranking':
            ranked_choices = kwargs.get('ranked_choices', [])
            vote.set_ranking(ranked_choices)
        
        elif vote_type == 'rating':
            ratings = kwargs.get('ratings', {})
            vote.set_rating(ratings)
        
        elif vote_type == 'legacy':
            # Explicit legacy support
            vote.up_vote = int(kwargs.get('up_vote', 0) or 0)
            vote.down_vote = int(kwargs.get('down_vote', 0) or 0)
            vote.choices = kwargs.get('choices', {})
        
        else:
            # Default to single choice if unknown type
            vote.up_vote = int(kwargs.get('up_vote', 0) or 0)
            vote.down_vote = int(kwargs.get('down_vote', 0) or 0)
            vote.choices = kwargs.get('choices', {})

    # Enhanced creation methods for specific vote types
    @service_method("create_single_choice_vote")
    def create_single_choice_vote(self, target_id: str, choice_id: str, 
                                 available_choices: list[str] = None, 
                                 content: Dict[str, Any] = None) -> ServiceResult[Vote]:
        """Create a single choice vote (A/B/C/D test)."""
        return self.create(
            target_id=target_id,
            vote_type='single_choice',
            choice_id=choice_id,
            available_choices=available_choices or [],
            content=content or {}
        )

    def create_multi_select_vote(self, target_id: str,
                                selected_choices: list[str], available_choices: list[str] = None,
                                max_selections: int = None, content: Dict[str, Any] = None) -> ServiceResult[Vote]:
        """Create a multi-select vote."""
        return self.create(
            target_id=target_id,
            vote_type='multi_select',
            selected_choices=selected_choices,
            available_choices=available_choices or [],
            max_selections=max_selections,
            content=content or {}
        )

    def create_ranking_vote(self, target_id: str,
                           ranked_choices: list[str], content: Dict[str, Any] = None) -> ServiceResult[Vote]:
        """Create a ranking vote."""
        return self.create(
            target_id=target_id,
            vote_type='ranking',
            ranked_choices=ranked_choices,
            content=content or {}
        )

    def create_rating_vote(self, target_id: str,
                          ratings: Dict[str, float], content: Dict[str, Any] = None) -> ServiceResult[Vote]:
        """Create a rating vote."""
        return self.create(
            target_id=target_id,
            vote_type='rating',
            ratings=ratings,
            content=content or {}
        )

    def _get_by_user_and_target(self, user_id: str, target_id: str) -> Vote | None:
        """Helper: get a vote by user and target via GSI4."""
        model = Vote()
        model.user_id = user_id
        model.target_id = target_id
        result = self._query_by_index(model, "gsi4")
        if result.success and result.data:
            return result.data[0]
        return None
    
    @service_method("get_by_id")
    def get_by_id(self, vote_id: str) -> ServiceResult[Vote]:
        """Get vote by ID.
        
        Security is automatic via _get_by_id():
            - Requires authentication
            - Validates owner/admin/tenant/share access
        """
        # Security is automatic - authentication + access checks built-in
        vote = self._get_by_id(vote_id, Vote)
        
        if not vote:
            raise NotFoundError(f"Vote with ID {vote_id} not found")
        
        return ServiceResult.success_result(vote)
    
    @service_method("update")
    def update(self, vote_id: str, updates: Dict[str, Any]) -> ServiceResult[Vote]:
        """Update vote. Security is automatic via _get_by_id."""
        # Get with security check
        vote = self._get_by_id(vote_id, Vote)
        if not vote:
            raise NotFoundError(f"Vote with ID {vote_id} not found")
        
        old_vote = self._fetch_model_raw(vote_id, Vote)
        
        # Apply updates
        for field, value in updates.items():
            if hasattr(vote, field) and field not in ['id', 'created_utc_ts', 'tenant_id']:
                setattr(vote, field, value)
        
        vote.prep_for_save()
        return self._save_model(vote, old_model=old_vote)
    
    @service_method("delete")
    def delete(self, vote_id: str) -> ServiceResult[bool]:
        """Delete vote. Security is automatic via _get_by_id."""
        vote = self._get_by_id(vote_id, Vote)
        if not vote:
            raise NotFoundError(f"Vote with ID {vote_id} not found")
        
        return self._delete_model(vote)
    
    def list_by_user(self, user_id: str, ascending: bool = False) -> ServiceResult[list[Vote]]:
        """List votes by user."""
        tenant_id = self.request_context.authenticated_tenant_id
        
        try:
            model = Vote()
            model.user_id = user_id
            model.tenant_id = tenant_id
            return self._query_by_index(model, "gsi2", ascending=ascending)
        except Exception as e:
            return self._handle_service_exception(e, 'list_votes', user_id=user_id)

    @service_method("list_by_tenant")
    def list_by_tenant(self) -> ServiceResult[list[Vote]]:
        """List votes by tenant."""
        tenant_id = self.request_context.authenticated_tenant_id
        
        model = Vote()
        model.tenant_id = tenant_id
        return self._query_by_index(model, "gsi3")

    def list_by_target(self, target_id: str, *, start_key: dict = None, limit: int = None) -> ServiceResult[list[Vote]]:
        """List votes by target with optional pagination."""
        try:
            model = Vote()
            model.target_id = target_id
            return self._query_by_index(model, "gsi5", start_key=start_key, limit=limit)
        except Exception as e:
            return self._handle_service_exception(e, 'list_votes', target_id=target_id)
