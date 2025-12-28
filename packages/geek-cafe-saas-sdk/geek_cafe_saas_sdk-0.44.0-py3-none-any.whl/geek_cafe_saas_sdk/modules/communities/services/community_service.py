# Community Service

from typing import Dict, Any, Optional, List
from boto3_assist.dynamodb.dynamodb import DynamoDB
from geek_cafe_saas_sdk.core.services.database_service import DatabaseService
from .community_member_service import CommunityMemberService
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.core.service_errors import ValidationError, NotFoundError, AccessDeniedError
from geek_cafe_saas_sdk.lambda_handlers._base.decorators import service_method
from geek_cafe_saas_sdk.modules.communities.models import Community
import datetime as dt


class CommunityService(DatabaseService[Community]):
    """Service for Community database operations."""

    def __init__(self, *, dynamodb: DynamoDB = None, table_name: str = None, request_context: Optional[Dict[str, str]] = None):
        super().__init__(dynamodb=dynamodb, table_name=table_name, request_context=request_context)
        # Initialize member service with same DB connection
        self.member_service = CommunityMemberService(dynamodb=dynamodb, table_name=table_name, request_context=request_context)

    @service_method("create")
    def create(self, **kwargs) -> ServiceResult[Community]:
        """Create a new community.
        
        Security:
            - Requires authentication
            - Creator becomes owner
        """
        # Validate authentication
        self.request_context.require_authentication()
        
        # Get targets (auto-extracted)
        tenant_id = self.request_context.target_tenant_id
        user_id = self.request_context.target_user_id
        
        # Validate required fields
        required_fields = ['name', 'description', 'category']
        self._validate_required_fields(kwargs, required_fields)

        # Validate community name uniqueness per user
        if self._community_name_exists_for_user(kwargs['name'], user_id, tenant_id):
            raise ValidationError("Community name already exists for this user")

        # Validate category
        if not self._is_valid_category(kwargs['category']):
            raise ValidationError("Invalid category")

        # Create community instance using map() approach
        community = Community().map(kwargs)
        community.owner_id = user_id  # Creator is the owner
        community.member_count = 1  # Owner is first member
        community.tenant_id = tenant_id
        community.user_id = user_id
        community.created_by_id = user_id

        # Prepare for save (sets ID and timestamps)
        community.prep_for_save()

        # Save to database
        save_result = self._save_model(community)
        
        if save_result.success:
            # Add owner as first member (adjacent record)
            member_result = self.member_service.add_member(
                community_id=community.id,
                user_id=user_id,
                status="active"
            )
            
            if not member_result.success:
                # Log warning but don't fail - community is created
                pass
        
        return save_result

    @service_method("get_by_id")
    def get_by_id(self, community_id: str) -> ServiceResult[Community]:
        """Get community by ID with access control.
        
        Security:
            - Requires authentication
            - Validates tenant access
        """
        # Security is automatic via _get_by_id
        community = self._get_by_id(community_id, Community)
        if not community:
            raise NotFoundError(f"Community with ID {community_id} not found")

        return ServiceResult.success_result(community)

    def get_communities_by_owner(self, owner_id: str,
                          limit: int = 50) -> ServiceResult[List[Community]]:
        """Get communities owned by a specific user using GSI1.
        
        Security:
            - Requires authentication
        """
        self.request_context.require_authentication()
        tenant_id = self.request_context.target_tenant_id
        try:
            # Create a temporary community instance to get the GSI key
            temp_community = Community()
            temp_community.owner_id = owner_id

            # Query by GSI1 (communities by owner), most recent first
            result = self._query_by_index(
                temp_community,
                "gsi1",
                ascending=False,  # Most recent first
                limit=limit
            )

            if not result.success:
                return result

            # Filter out deleted communities and validate tenant access
            active_communities = []
            for community in result.data:
                if not community.is_deleted() and community.tenant_id == tenant_id:
                    active_communities.append(community)

            return ServiceResult.success_result(active_communities)

        except Exception as e:
            return self._handle_service_exception(e, 'get_communities_by_owner',
                                               owner_id=owner_id)

    def get_communities_by_member(self, member_id: str,
                           limit: int = 50) -> ServiceResult[List[Community]]:
        """Get communities where a user is a member.
        
        Security:
            - Requires authentication
        """
        self.request_context.require_authentication()
        try:
            # This is more complex - we'd need a GSI that indexes membership
            # For now, we'll query all communities and filter client-side
            # In production, we'd want a GSI for user->communities membership

            all_communities_result = self.get_all_communities(limit=limit*2)

            if not all_communities_result.success:
                return all_communities_result

            member_communities = [
                community for community in all_communities_result.data
                if community.is_user_member(member_id)
            ][:limit]

            return ServiceResult.success_result(member_communities)

        except Exception as e:
            return self._handle_service_exception(e, 'get_communities_by_member',
                                               member_id=member_id)

    def get_communities_by_privacy(self, privacy: str,
                            limit: int = 50) -> ServiceResult[List[Community]]:
        """Get communities by privacy level using GSI2.
        
        Security:
            - Requires authentication
        """
        self.request_context.require_authentication()
        tenant_id = self.request_context.target_tenant_id
        try:
            # Create a temporary community instance to get the GSI key
            temp_community = Community()
            temp_community.privacy = privacy

            # Query by GSI2 (communities by privacy), most recent first
            result = self._query_by_index(
                temp_community,
                "gsi2",
                ascending=False,  # Most recent first
                limit=limit
            )

            if not result.success:
                return result

            # Filter out deleted communities and validate tenant access
            active_communities = []
            for community in result.data:
                if not community.is_deleted() and community.tenant_id == tenant_id:
                    active_communities.append(community)

            return ServiceResult.success_result(active_communities)

        except Exception as e:
            return self._handle_service_exception(e, 'get_communities_by_privacy',
                                               privacy=privacy)

    def get_all_communities(self, limit: int = 50) -> ServiceResult[List[Community]]:
        """Get all communities for a tenant using GSI4.
        
        Security:
            - Requires authentication
        """
        self.request_context.require_authentication()
        tenant_id = self.request_context.target_tenant_id
        try:
            # Create a temporary community instance to get the GSI key
            temp_community = Community()
            temp_community.tenant_id = tenant_id

            # Query by GSI4 (communities by tenant), most recent first
            result = self._query_by_index(
                temp_community,
                "gsi4",
                ascending=False,  # Most recent first
                limit=limit
            )

            if not result.success:
                return result

            # Filter out deleted communities
            active_communities = []
            for community in result.data:
                if not community.is_deleted():
                    active_communities.append(community)

            return ServiceResult.success_result(active_communities)

        except Exception as e:
            return self._handle_service_exception(e, 'get_all_communities')

    def get_communities_by_category(self, category: str,
                             limit: int = 50) -> ServiceResult[List[Community]]:
        """Get communities by category using GSI3.
        
        Security:
            - Requires authentication
        """
        self.request_context.require_authentication()
        tenant_id = self.request_context.target_tenant_id
        try:
            # Create a temporary community instance to get the GSI key
            temp_community = Community()
            temp_community.category = category

            # Query by GSI3 (communities by category), most recent first
            result = self._query_by_index(
                temp_community,
                "gsi3",
                ascending=False,  # Most recent first
                limit=limit
            )

            if not result.success:
                return result

            # Filter out deleted communities and validate tenant access
            active_communities = []
            for community in result.data:
                if not community.is_deleted() and community.tenant_id == tenant_id:
                    active_communities.append(community)

            return ServiceResult.success_result(active_communities)

        except Exception as e:
            return self._handle_service_exception(e, 'get_communities_by_category',
                                               category=category)

    @service_method("update")
    def update(self, community_id: str, updates: Dict[str, Any]) -> ServiceResult[Community]:
        """Update community with access control.
        
        Security:
            - Requires authentication
            - Only managers can update
        """
        tenant_id = self.request_context.authenticated_tenant_id
        user_id = self.request_context.authenticated_user_id
        
        # Security is automatic via _get_by_id
        community = self._get_by_id(community_id, Community)
        if not community:
            raise NotFoundError(f"Community with ID {community_id} not found")

        # Check permissions (organizers only)
        if not community.can_user_manage(user_id):
            raise AccessDeniedError("Access denied: insufficient permissions")

        # Cannot change owner
        if 'owner_id' in updates:
            raise ValidationError("Cannot change community owner")

        # Validate category if being updated
        if 'category' in updates and not self._is_valid_category(updates['category']):
            raise ValidationError("Invalid category")

        # Validate community name uniqueness if being updated
        if 'name' in updates:
            existing_community = self._get_community_by_name_and_owner(updates['name'], community.owner_id, tenant_id)
            if existing_community and existing_community.id != community_id:
                raise ValidationError("Community name already exists for this user")

        # Apply updates
        for field, value in updates.items():
            if hasattr(community, field) and field not in ['id', 'created_utc_ts', 'tenant_id', 'owner_id']:
                if field == 'name':
                    community.name = value
                elif field == 'description':
                    community.description = value
                elif field == 'category':
                    community.category = value
                elif field == 'privacy':
                    community.privacy = value
                elif field == 'tags':
                    community.tags = value
                elif field == 'joinApproval':
                    community.join_approval = value
                elif field == 'requiresDues':
                    community.requires_dues = value
                elif field == 'duesMonthly':
                    community.dues_monthly = value
                elif field == 'duesYearly':
                    community.dues_yearly = value
                elif field == 'co_owners':
                    community.co_owners = value
                elif field == 'moderators':
                    community.moderators = value
                elif field == 'members':
                    community.members = value

        # Update metadata
        community.updated_by_id = user_id
        community.prep_for_save()  # Updates timestamp

        # Save updated community
        return self._save_model(community)

    @service_method("delete")
    def delete(self, community_id: str) -> ServiceResult[bool]:
        """Soft delete community with access control.
        
        Security:
            - Requires authentication
            - Only owner can delete
        """
        user_id = self.request_context.authenticated_user_id
        
        # Security is automatic via _get_by_id
        community = self._get_by_id(community_id, Community)
        if not community:
            raise NotFoundError(f"Community with ID {community_id} not found")

        # Check if already deleted
        if community.is_deleted():
            return ServiceResult.success_result(True)

        # Check permissions (owner only)
        if community.owner_id != user_id:
            raise AccessDeniedError("Access denied: only community owner can delete")

        # Soft delete: set deleted timestamp and metadata
        community.deleted_utc_ts = dt.datetime.now(dt.UTC).timestamp()
        community.deleted_by_id = user_id
        community.prep_for_save()  # Updates timestamp

        # Save the updated community
        save_result = self._save_model(community)
        if save_result.success:
            return ServiceResult.success_result(True)
        else:
            return save_result

    @service_method("list_by_tenant")
    def list_by_tenant(self, limit: int = 50) -> ServiceResult[List[Community]]:
        """List all communities for tenant.
        
        Security:
            - Requires authentication
        """
        return self.get_all_communities(limit)

    def _community_name_exists_for_user(self, name: str, user_id: str, tenant_id: str) -> bool:
        """Check if community name already exists for this user."""
        try:
            community = self._get_community_by_name_and_owner(name, user_id, tenant_id)
            return community is not None
        except:
            return False

    def _get_community_by_name_and_owner(self, name: str, owner_id: str, tenant_id: str) -> Optional[Community]:
        """Get community by name and owner (helper method)."""
        # This would require a GSI for name+owner
        # For now, we'll query owner's communities and check names
        owner_communities_result = self.get_communities_by_owner(owner_id, limit=100)
        if owner_communities_result.success:
            for community in owner_communities_result.data:
                if community.name == name:
                    return community
        return None

    def _is_valid_category(self, category: str) -> bool:
        """Validate community category."""
        # This should come from a predefined list
        valid_categories = [
            "sports", "hobby", "professional", "educational",
            "social", "religious", "political", "charity",
            "entertainment", "other"
        ]
        return category.lower() in valid_categories
    
    # Member Management Methods (delegates to CommunityMemberService)
    
    def add_member(self, community_id: str, user_id: str, invited_by_id: str = None,
                   status: str = "active", tenant_id: str = None) -> ServiceResult:
        """
        Add a member to the community.
        
        Args:
            community_id: Community ID
            user_id: User ID to add
            invited_by_id: Optional ID of user who invited
            status: Member status (default: active)
            tenant_id: Tenant ID for access control
        """
        try:
            # Get community to update count
            if tenant_id:
                community_result = self.get_by_id(community_id, tenant_id, invited_by_id or user_id)
                if not community_result.success:
                    return community_result
                community = community_result.data
            
            # Add member via member service
            result = self.member_service.add_member(community_id, user_id, invited_by_id, status)
            
            # Update cached member count if successful and we have community
            if result.success and tenant_id and community:
                community.increment_member_count()
                self._save_model(community)
            
            return result
            
        except Exception as e:
            return self._handle_service_exception(e, 'add_member', community_id=community_id, user_id=user_id)
    
    def remove_member(self, community_id: str, user_id: str, tenant_id: str = None) -> ServiceResult:
        """
        Remove a member from the community.
        
        Args:
            community_id: Community ID
            user_id: User ID to remove
            tenant_id: Optional tenant ID for updating cached count
        """
        try:
            # Remove member via member service
            result = self.member_service.remove_member(community_id, user_id)
            
            # Update cached member count if we have tenant context
            if result.success and tenant_id:
                try:
                    community_result = self.get_by_id(community_id, tenant_id, user_id)
                    if community_result.success:
                        community = community_result.data
                        community.decrement_member_count()
                        self._save_model(community)
                except:
                    pass  # Don't fail removal if count update fails
            
            return result
            
        except Exception as e:
            return self._handle_service_exception(e, 'remove_member', community_id=community_id, user_id=user_id)
    
    def is_member(self, community_id: str, user_id: str, active_only: bool = True) -> bool:
        """
        Check if user is a member of the community.
        
        Args:
            community_id: Community ID
            user_id: User ID
            active_only: Only check active members (default: True)
        """
        return self.member_service.is_member(community_id, user_id, active_only)
    
    def get_members(self, community_id: str, status: str = None, limit: int = 50) -> ServiceResult:
        """
        Get members of a community.
        
        Args:
            community_id: Community ID
            status: Optional status filter
            limit: Max results
        """
        return self.member_service.list_members(community_id, status, limit)
    
    def get_member_count_realtime(self, community_id: str, status: str = "active") -> ServiceResult:
        """
        Get real-time member count from database.
        
        Args:
            community_id: Community ID
            status: Status filter (default: active)
        """
        return self.member_service.get_member_count(community_id, status)
    
    def get_user_communities(self, user_id: str, status: str = "active", limit: int = 50) -> ServiceResult:
        """
        Get communities a user is a member of.
        
        Args:
            user_id: User ID
            status: Member status filter
            limit: Max results
        """
        return self.member_service.list_user_communities(user_id, status, limit)
