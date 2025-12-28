# Community Member Service

from typing import Dict, Any, List, Optional
from boto3_assist.dynamodb.dynamodb import DynamoDB
from geek_cafe_saas_sdk.core.services.database_service import DatabaseService
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.lambda_handlers._base.decorators import service_method
from geek_cafe_saas_sdk.core.service_errors import ValidationError, NotFoundError, AccessDeniedError
from geek_cafe_saas_sdk.modules.communities.models import CommunityMember
import datetime as dt


class CommunityMemberService(DatabaseService[CommunityMember]):
    """
    Service for CommunityMember operations.
    
    Manages scalable membership using adjacent record pattern.
    """
    
    
    # Required abstract methods from DatabaseService
    @service_method("create")
    def create(self, **kwargs) -> ServiceResult[CommunityMember]:
        """Create method - delegates to add_member()."""
        self.request_context.require_authentication()
        user_id = self.request_context.target_user_id
        
        if 'community_id' not in kwargs:
            return ServiceResult.error_result("community_id is required", "VALIDATION_ERROR")
        
        return self.add_member(
            community_id=kwargs['community_id'],
            user_id=user_id,
            invited_by_id=kwargs.get('invited_by_id'),
            status=kwargs.get('status', 'active')
        )
    
    @service_method("get_by_id")
    def get_by_id(self, member_id: str) -> ServiceResult[CommunityMember]:
        """Get method - member_id should be in format 'community_id:user_id'."""
        self.request_context.require_authentication()
        try:
            if ':' in member_id:
                community_id, member_user_id = member_id.split(':', 1)
                return self.get_membership(community_id, member_user_id)
            return ServiceResult.error_result("Invalid member_id format. Expected 'community_id:user_id'")
        except Exception as e:
            return self._handle_service_exception(e, 'get_by_id', member_id=member_id)
    
    @service_method("update")
    def update(self, member_id: str, updates: Dict[str, Any]) -> ServiceResult[CommunityMember]:
        """Update method - updates member record."""
        self.request_context.require_authentication()
        try:
            if ':' in member_id:
                community_id, member_user_id = member_id.split(':', 1)
                membership = self.get_membership(community_id, member_user_id)
                
                if not membership.success or not membership.data:
                    return ServiceResult.error_result("Membership not found")
                
                # Apply updates
                member = membership.data
                if 'status' in updates:
                    member.status = updates['status']
                if 'dues_status' in updates:
                    member.dues_status = updates['dues_status']
                if 'last_payment_at' in updates:
                    member.last_payment_at = updates['last_payment_at']
                if 'next_payment_due' in updates:
                    member.next_payment_due = updates['next_payment_due']
                
                member.prep_for_save()
                return self._save_model(member)
                
            return ServiceResult.error_result("Invalid member_id format. Expected 'community_id:user_id'")
        except Exception as e:
            return self._handle_service_exception(e, 'update', member_id=member_id)
    
    @service_method("delete")
    def delete(self, member_id: str) -> ServiceResult[bool]:
        """Delete method - soft deletes member."""
        self.request_context.require_authentication()
        try:
            if ':' in member_id:
                community_id, member_user_id = member_id.split(':', 1)
                return self.remove_member(community_id, member_user_id)
            return ServiceResult.error_result("Invalid member_id format. Expected 'community_id:user_id'")
        except Exception as e:
            return self._handle_service_exception(e, 'delete', member_id=member_id)

    def add_member(self, community_id: str, user_id: str, invited_by_id: str = None, 
                   status: str = "active") -> ServiceResult[CommunityMember]:
        """
        Add a member to a community.
        
        Args:
            community_id: Community ID
            user_id: User ID to add
            invited_by_id: Optional ID of user who invited
            status: Member status (active, pending, etc.)
        """
        try:
            # Check if already a member
            existing = self.get_membership(community_id, user_id)
            if existing.success and existing.data:
                if existing.data.status == "active":
                    return ServiceResult.success_result(existing.data)
                # Reactivate if previously left or banned
                existing.data.status = status
                existing.data.joined_at = dt.datetime.now(dt.UTC).timestamp()
                existing.data.prep_for_save()
                return self._save_model(existing.data)
            
            # Create new membership
            member = CommunityMember()
            member.community_id = community_id
            member.user_id = user_id
            member.status = status
            member.invited_by_id = invited_by_id
            member.joined_at = dt.datetime.now(dt.UTC).timestamp()
            member.tenant_id = community_id  # For tenant isolation if needed
            member.prep_for_save()
            
            return self._save_model(member)
            
        except Exception as e:
            return self._handle_service_exception(
                e, 'add_member', 
                community_id=community_id, 
                user_id=user_id
            )

    def remove_member(self, community_id: str, user_id: str) -> ServiceResult[bool]:
        """
        Remove a member from a community (soft delete by status change).
        
        Args:
            community_id: Community ID
            user_id: User ID to remove
        """
        try:
            membership = self.get_membership(community_id, user_id)
            
            if not membership.success or not membership.data:
                return ServiceResult.success_result(True)  # Already not a member
            
            # Mark as left instead of hard delete
            membership.data.status = "left"
            membership.data.prep_for_save()
            
            return self._save_model(membership.data).map(lambda _: True)
            
        except Exception as e:
            return self._handle_service_exception(
                e, 'remove_member',
                community_id=community_id,
                user_id=user_id
            )

    def get_membership(self, community_id: str, user_id: str) -> ServiceResult[CommunityMember]:
        """
        Get a specific membership record.
        
        Args:
            community_id: Community ID
            user_id: User ID
        """
        try:
            # Create temp object to build the primary key
            temp = CommunityMember()
            temp.community_id = community_id
            temp.user_id = user_id
            
            # Get by primary key (community + user)
            result = self._get_by_primary_key(temp)
            
            if not result.success or not result.data:
                raise NotFoundError("Membership not found")
            
            return result
            
        except Exception as e:
            return self._handle_service_exception(
                e, 'get_membership',
                community_id=community_id,
                user_id=user_id
            )

    def is_member(self, community_id: str, user_id: str, active_only: bool = True) -> bool:
        """
        Check if user is a member of community.
        
        Args:
            community_id: Community ID
            user_id: User ID
            active_only: Only count active members (default True)
        """
        try:
            result = self.get_membership(community_id, user_id)
            
            if not result.success or not result.data:
                return False
            
            if active_only:
                return result.data.is_active()
            
            return result.data.status in ["active", "pending"]
            
        except:
            return False

    def list_members(self, community_id: str, status: str = None, 
                     limit: int = 50) -> ServiceResult[List[CommunityMember]]:
        """
        List members of a community.
        
        Args:
            community_id: Community ID
            status: Optional status filter (active, pending, etc.)
            limit: Max results
        """
        try:
            temp = CommunityMember()
            temp.community_id = community_id
            
            if status:
                # Query by status using GSI2
                temp.status = status
                result = self._query_by_index(temp, "gsi2", limit=limit, ascending=True)
            else:
                # Query all members using primary key begins_with
                result = self._query_by_index(temp, "primary", limit=limit, ascending=True)
            
            if not result.success:
                return result
            
            # Filter out deleted/left members if no status specified
            if not status:
                active_members = [m for m in result.data if m.status in ["active", "pending"]]
                return ServiceResult.success_result(active_members)
            
            return result
            
        except Exception as e:
            return self._handle_service_exception(
                e, 'list_members',
                community_id=community_id
            )

    def list_user_communities(self, user_id: str, status: str = "active",
                             limit: int = 50) -> ServiceResult[List[CommunityMember]]:
        """
        List communities a user is a member of.
        
        Args:
            user_id: User ID
            status: Member status filter (default: active)
            limit: Max results
        """
        try:
            temp = CommunityMember()
            temp.user_id = user_id
            
            # Query by user using GSI1
            result = self._query_by_index(
                temp, 
                "gsi1", 
                limit=limit,
                ascending=False  # Most recently joined first
            )
            
            if not result.success:
                return result
            
            # Filter by status if specified
            if status:
                filtered = [m for m in result.data if m.status == status]
                return ServiceResult.success_result(filtered)
            
            return result
            
        except Exception as e:
            return self._handle_service_exception(
                e, 'list_user_communities',
                user_id=user_id
            )

    def get_member_count(self, community_id: str, status: str = "active") -> ServiceResult[int]:
        """
        Get count of members in a community.
        
        Args:
            community_id: Community ID
            status: Status filter (default: active)
        """
        try:
            members_result = self.list_members(community_id, status=status, limit=1000)
            
            if not members_result.success:
                return ServiceResult.error_result("Failed to count members")
            
            count = len(members_result.data)
            return ServiceResult.success_result(count)
            
        except Exception as e:
            return self._handle_service_exception(
                e, 'get_member_count',
                community_id=community_id
            )

    def update_member_status(self, community_id: str, user_id: str, 
                            status: str) -> ServiceResult[CommunityMember]:
        """
        Update a member's status.
        
        Args:
            community_id: Community ID
            user_id: User ID
            status: New status (active, pending, banned, left)
        """
        try:
            membership = self.get_membership(community_id, user_id)
            
            if not membership.success or not membership.data:
                raise NotFoundError("Membership not found")
            
            membership.data.status = status
            membership.data.prep_for_save()
            
            return self._save_model(membership.data)
            
        except Exception as e:
            return self._handle_service_exception(
                e, 'update_member_status',
                community_id=community_id,
                user_id=user_id
            )

    def approve_pending_member(self, community_id: str, user_id: str) -> ServiceResult[CommunityMember]:
        """
        Approve a pending member.
        
        Args:
            community_id: Community ID
            user_id: User ID to approve
        """
        return self.update_member_status(community_id, user_id, "active")

    def ban_member(self, community_id: str, user_id: str) -> ServiceResult[CommunityMember]:
        """
        Ban a member from the community.
        
        Args:
            community_id: Community ID
            user_id: User ID to ban
        """
        return self.update_member_status(community_id, user_id, "banned")

    def update_dues_status(self, community_id: str, user_id: str,
                          dues_status: str, next_payment_due: float = None) -> ServiceResult[CommunityMember]:
        """
        Update member's dues status.
        
        Args:
            community_id: Community ID
            user_id: User ID
            dues_status: New dues status (current, overdue, exempt, pending)
            next_payment_due: Optional next payment due date (timestamp)
        """
        try:
            membership = self.get_membership(community_id, user_id)
            
            if not membership.success or not membership.data:
                raise NotFoundError("Membership not found")
            
            membership.data.dues_status = dues_status
            if dues_status == "current":
                membership.data.last_payment_at = dt.datetime.now(dt.UTC).timestamp()
            if next_payment_due:
                membership.data.next_payment_due = next_payment_due
                
            membership.data.prep_for_save()
            
            return self._save_model(membership.data)
            
        except Exception as e:
            return self._handle_service_exception(
                e, 'update_dues_status',
                community_id=community_id,
                user_id=user_id
            )

    def list_members_with_overdue_dues(self, community_id: str, 
                                       limit: int = 50) -> ServiceResult[List[CommunityMember]]:
        """
        List members with overdue dues using GSI3.
        
        Args:
            community_id: Community ID
            limit: Max results
        """
        try:
            temp = CommunityMember()
            temp.community_id = community_id
            temp.dues_status = "overdue"
            
            result = self._query_by_index(
                temp,
                "gsi3",
                limit=limit,
                ascending=True  # Oldest overdue first
            )
            
            return result
            
        except Exception as e:
            return self._handle_service_exception(
                e, 'list_members_with_overdue_dues',
                community_id=community_id
            )
