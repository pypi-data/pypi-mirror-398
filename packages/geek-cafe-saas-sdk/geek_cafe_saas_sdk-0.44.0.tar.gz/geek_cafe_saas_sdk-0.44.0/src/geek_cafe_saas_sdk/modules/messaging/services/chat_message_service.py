"""
Geek Cafe, LLC
MIT License.  See Project Root for the license information.

ChatMessageService for managing individual chat messages.
"""

from typing import Dict, Any, Optional, List
from boto3_assist.dynamodb.dynamodb import DynamoDB
from geek_cafe_saas_sdk.core.services.database_service import DatabaseService
from geek_cafe_saas_sdk.core.request_context import RequestContext
from .chat_channel_service import ChatChannelService
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.core.service_errors import ValidationError, NotFoundError, AccessDeniedError
from geek_cafe_saas_sdk.lambda_handlers._base.decorators import service_method
from geek_cafe_saas_sdk.modules.messaging.models import ChatMessage
from geek_cafe_saas_sdk.utilities.message_query_helper import MessageQueryHelper
import datetime as dt


class ChatMessageService(DatabaseService[ChatMessage]):
    """Service for ChatMessage database operations."""

    def __init__(self, *, dynamodb: DynamoDB = None, table_name: str = None,
                 request_context: Optional[RequestContext] = None,
                 channel_service: ChatChannelService = None):
        super().__init__(dynamodb=dynamodb, table_name=table_name, request_context=request_context)
        # Channel service for updating channel metadata (share request_context)
        self.channel_service = channel_service or ChatChannelService(
            dynamodb=dynamodb, table_name=table_name, request_context=request_context
        )
        # Query helper for sharded message reads
        self.query_helper = MessageQueryHelper(dynamodb, table_name)

    @service_method("create")
    def create(self, payload: Dict[str, Any]) -> ServiceResult[ChatMessage]:
        """
        Create a new chat message from a payload.
        
        Args:
            payload: Message data including channel_id, content
            
        Returns:
            ServiceResult with ChatMessage
            
        Security:
            - Requires authentication
            - Validates channel membership
        """
        # Security handled by _save_model
        tenant_id = self.request_context.authenticated_tenant_id
        user_id = self.request_context.authenticated_user_id
        
        # Validate required fields
        required_fields = ['channel_id', 'content']
        self._validate_required_fields(payload, required_fields)

        channel_id = payload['channel_id']

        # Verify user has access to the channel and can post
        channel_result = self.channel_service.get_by_id(channel_id)
        if not channel_result.success:
            return channel_result

        channel = channel_result.data

        # Check if user can post to this channel
        # For now, all members can post unless it's announcement-only
        if not self.channel_service.is_member(channel_id, user_id):
            raise AccessDeniedError("You must be a member to post to this channel")

        if channel.is_announcement:
            # TODO: Add admin check when user roles are implemented
            # For now, only channel creator can post to announcement channels
            if channel.created_by != user_id:
                raise AccessDeniedError("Only admins can post to announcement channels")

        # Create and map message instance from the payload
        message = ChatMessage().map(payload)
        message.tenant_id = tenant_id
        message.user_id = user_id
        message.created_by_id = user_id
        message.channel_id = channel_id
        message.sender_id = user_id
        message.sender_name = payload.get('sender_name', '')
        
        # Pass sharding config from channel for GSI1 key computation
        if channel.is_sharded():
            message._sharding_config = channel.sharding_config

        # Handle parent message for threading
        if message.parent_message_id:
            # Verify parent message exists and belongs to same channel
            parent_result = self.get_by_id(message.parent_message_id)
            if not parent_result.success:
                raise ValidationError("Parent message not found")
            
            parent = parent_result.data
            if parent.channel_id != channel_id:
                raise ValidationError("Parent message must be in the same channel")

        # Prepare for save (sets ID and timestamps)
        message.prep_for_save()

        # Save to database
        save_result = self._save_model(message)
        if not save_result.success:
            return save_result

        # Update channel's last message tracking
        self.channel_service.update_last_message(
            channel_id, message.id, message.created_utc_ts
        )

        # If this is a reply, increment parent's thread count
        if message.parent_message_id:
            self._increment_parent_thread_count(message.parent_message_id)

        return save_result

    @service_method("get_by_id")
    def get_by_id(self, message_id: str) -> ServiceResult[ChatMessage]:
        """
        Get chat message by ID with access control.
        
        Args:
            message_id: Message ID
            
        Returns:
            ServiceResult with ChatMessage
            
        Security:
            - Requires authentication
            - Validates tenant access
            - Validates channel membership
        """
        try:
            # Security is automatic via _get_by_id
            message = self._get_by_id(message_id, ChatMessage)
            if not message:
                raise NotFoundError(f"Chat message with ID {message_id} not found")

            # Verify user has access to the channel
            channel_result = self.channel_service.get_by_id(message.channel_id)
            if not channel_result.success:
                raise AccessDeniedError("Access denied to this message")

            return ServiceResult.success_result(message)

        except Exception as e:
            return self._handle_service_exception(e, 'get_chat_message', message_id=message_id)

    @service_method("list_by_channel")
    def list_by_channel(self, channel_id: str,
                        limit: int = 50, cursor: Optional[str] = None,
                        ascending: bool = False) -> ServiceResult[List[ChatMessage]]:
        """
        List messages in a channel with support for both normal and sharded channels.
        
        Uses MessageQueryHelper to transparently handle:
        - Normal channels (single partition)
        - Sharded channels (multiple buckets/shards)
        
        Args:
            channel_id: Channel ID
            limit: Maximum number of results (default 50)
            cursor: Pagination cursor (base64 encoded, opaque)
            ascending: Sort order (False = newest first, True = oldest first)
            
        Returns:
            ServiceResult with list of ChatMessages and pagination metadata
            
        Security:
            - Requires authentication
            - Validates channel access
        """
        try:
            # Verify user has access to the channel
            channel_result = self.channel_service.get_by_id(channel_id)
            if not channel_result.success:
                return channel_result
            
            channel = channel_result.data
            
            # Use MessageQueryHelper for sharding support
            items, next_cursor = self.query_helper.query_messages(
                channel_id=channel_id,
                sharding_config=channel.sharding_config,
                limit=limit,
                cursor=cursor,
                lookback_buckets=7  # Query last 7 days/hours of buckets
            )
            
            # Convert items to ChatMessage objects
            messages = []
            for item in items:
                msg = ChatMessage().map(item)
                # Filter out deleted messages
                if not msg.is_deleted():
                    messages.append(msg)
            
            # Handle ascending sort if requested (default is descending/newest first)
            if ascending:
                messages.reverse()
            
            # Return with pagination cursor
            response = ServiceResult.success_result(messages)
            if next_cursor:
                response.metadata = {"next_cursor": next_cursor}
            
            return response

        except Exception as e:
            return self._handle_service_exception(e, 'list_messages_by_channel',
                                                channel_id=channel_id)

    @service_method("list_thread_replies")
    def list_thread_replies(self, parent_message_id: str,
                           limit: int = 50) -> ServiceResult[List[ChatMessage]]:
        """
        List all replies to a parent message using GSI2.
        
        Args:
            parent_message_id: Parent message ID
            limit: Maximum number of results
            
        Returns:
            ServiceResult with list of reply ChatMessages
            
        Security:
            - Requires authentication
            - Validates access to parent message
        """
        try:
            # Get parent message to verify access
            parent_result = self.get_by_id(parent_message_id)
            if not parent_result.success:
                return parent_result

            temp_message = ChatMessage()
            temp_message.parent_message_id = parent_message_id

            result = self._query_by_index(
                temp_message,
                "gsi2",
                ascending=True,  # Oldest first for thread replies
                limit=limit
            )

            if not result.success:
                return result

            # Filter out deleted messages
            active_messages = [m for m in result.data if not m.is_deleted()]
            return ServiceResult.success_result(active_messages)

        except Exception as e:
            return self._handle_service_exception(e, 'list_thread_replies',
                                                parent_message_id=parent_message_id)

    @service_method("list_by_sender")
    def list_by_sender(self, sender_id: str,
                       limit: int = 50) -> ServiceResult[List[ChatMessage]]:
        """
        List messages by sender using GSI3.
        
        Args:
            sender_id: Sender user ID
            limit: Maximum number of results
            
        Returns:
            ServiceResult with list of ChatMessages
            
        Security:
            - Requires authentication
            - Users can only see their own messages
        """
        try:
            tenant_id = self.request_context.authenticated_tenant_id
            user_id = self.request_context.authenticated_user_id
            
            # Users can only see their own message history
            # TODO: Add admin check when user roles are implemented
            if sender_id != user_id:
                raise AccessDeniedError("Cannot view other users' message history")

            temp_message = ChatMessage()
            temp_message.sender_id = sender_id

            result = self._query_by_index(
                temp_message,
                "gsi3",
                ascending=False,  # Most recent first
                limit=limit
            )

            if not result.success:
                return result

            # Filter by tenant and exclude deleted messages
            user_messages = [
                m for m in result.data 
                if not m.is_deleted() and m.tenant_id == tenant_id
            ]

            return ServiceResult.success_result(user_messages)

        except Exception as e:
            return self._handle_service_exception(e, 'list_messages_by_sender',
                                                sender_id=sender_id)

    @service_method("add_reaction")
    def add_reaction(self, message_id: str,
                     emoji: str) -> ServiceResult[ChatMessage]:
        """
        Add a reaction to a message.
        
        Args:
            message_id: Message ID
            emoji: Emoji to add (e.g., "👍", "❤️")
            
        Returns:
            ServiceResult with updated ChatMessage
            
        Security:
            - Requires authentication
        """
        try:
            user_id = self.request_context.authenticated_user_id
            
            message_result = self.get_by_id(message_id)
            if not message_result.success:
                return message_result

            message = message_result.data
            message.add_reaction(emoji, user_id)
            message.updated_by_id = user_id
            message.prep_for_save()

            return self._save_model(message)

        except Exception as e:
            return self._handle_service_exception(e, 'add_message_reaction',
                                                message_id=message_id, emoji=emoji)

    @service_method("remove_reaction")
    def remove_reaction(self, message_id: str,
                        emoji: str) -> ServiceResult[ChatMessage]:
        """
        Remove a reaction from a message.
        
        Args:
            message_id: Message ID
            emoji: Emoji to remove
            
        Returns:
            ServiceResult with updated ChatMessage
            
        Security:
            - Requires authentication
        """
        try:
            user_id = self.request_context.authenticated_user_id
            
            message_result = self.get_by_id(message_id)
            if not message_result.success:
                return message_result

            message = message_result.data
            message.remove_reaction(emoji, user_id)
            message.updated_by_id = user_id
            message.prep_for_save()

            return self._save_model(message)

        except Exception as e:
            return self._handle_service_exception(e, 'remove_message_reaction',
                                                message_id=message_id, emoji=emoji)

    @service_method("update")
    def update(self, message_id: str,
               updates: Dict[str, Any]) -> ServiceResult[ChatMessage]:
        """
        Update chat message with access control.
        
        Args:
            message_id: Message ID
            updates: Dictionary of fields to update
            
        Returns:
            ServiceResult with updated ChatMessage
            
        Security:
            - Requires authentication
            - Only sender can edit
        """
        try:
            user_id = self.request_context.authenticated_user_id
            
            # Security is automatic via _get_by_id
            message = self._get_by_id(message_id, ChatMessage)
            if not message:
                raise NotFoundError(f"Chat message with ID {message_id} not found")

            # Only the sender can edit their own message
            if message.sender_id != user_id:
                raise AccessDeniedError("Only the message sender can edit the message")

            # Apply updates (only content can be edited)
            if 'content' in updates:
                message.content = updates['content']
                message.mark_as_edited()

            # Update metadata
            message.updated_by_id = user_id
            message.prep_for_save()

            # Save updated message
            return self._save_model(message)

        except Exception as e:
            return self._handle_service_exception(e, 'update_chat_message', message_id=message_id)

    @service_method("delete")
    def delete(self, message_id: str) -> ServiceResult[bool]:
        """
        Soft delete chat message with access control.
        
        Args:
            message_id: Message ID
            
        Returns:
            ServiceResult with boolean success
            
        Security:
            - Requires authentication
            - Only sender can delete
        """
        try:
            user_id = self.request_context.authenticated_user_id
            
            # Security is automatic via _get_by_id
            message = self._get_by_id(message_id, ChatMessage)
            if not message:
                raise NotFoundError(f"Chat message with ID {message_id} not found")

            # Check if already deleted
            if message.is_deleted():
                return ServiceResult.success_result(True)

            # Only the sender can delete their own message
            # TODO: Add channel admin check when user roles are implemented
            if message.sender_id != user_id:
                raise AccessDeniedError("Only the message sender can delete the message")

            # Soft delete: set deleted timestamp and metadata
            message.deleted_utc_ts = dt.datetime.now(dt.UTC).timestamp()
            message.deleted_by_id = user_id
            message.prep_for_save()

            # Save the updated message
            save_result = self._save_model(message)
            if save_result.success:
                return ServiceResult.success_result(True)
            else:
                return save_result

        except Exception as e:
            return self._handle_service_exception(e, 'delete_chat_message', message_id=message_id)

    def _increment_parent_thread_count(self, parent_message_id: str):
        """
        Increment the thread count of a parent message.
        
        Args:
            parent_message_id: Parent message ID
        """
        try:
            parent = self._get_model_by_id(parent_message_id, ChatMessage)
            if parent:
                parent.increment_thread_count()
                parent.prep_for_save()
                self._save_model(parent)
        except Exception:
            # Non-critical operation, just log and continue
            pass

    def _handle_service_exception(self, exception: Exception, operation: str, **context) -> ServiceResult:
        """
        Handle service exceptions with consistent error responses.
        
        Delegates to parent class for proper error code mapping.
        
        Args:
            exception: The exception that occurred
            operation: Name of the operation that failed
            **context: Additional context for debugging
            
        Returns:
            ServiceResult with error details
        """
        # Use parent's exception handler for proper error code mapping
        return super()._handle_service_exception(exception, operation, **context)
