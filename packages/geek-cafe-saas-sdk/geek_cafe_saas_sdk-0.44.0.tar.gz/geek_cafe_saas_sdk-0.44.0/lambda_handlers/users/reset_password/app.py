"""
Lambda Handler: Reset User Password (Admin Operation)

POST /users/{user_id}/reset-password

Admin resets a user's password (force change on next login).

Authorization: Admin only
"""

import os
from typing import Dict, Any

from geek_cafe_saas_sdk.utilities.lambda_event_utility import LambdaEventUtility
from geek_cafe_saas_sdk.utilities.response import error_response, success_response
from geek_cafe_saas_sdk.lambda_handlers import ServicePool
from geek_cafe_saas_sdk.utilities.cognito_utility import CognitoUtility
from geek_cafe_saas_sdk.modules.users.services import UserService
from geek_cafe_saas_sdk.utilities.environment_variables import EnvironmentVariables
from geek_cafe_saas_sdk.core.request_context import RequestContext
from boto3_assist.dynamodb.dynamodb import DynamoDB

# Initialize services
user_service_pool = ServicePool(UserService)


def lambda_handler(event: Dict[str, Any], context: Any, 
                   injected_user_service: UserService = None,
                   injected_cognito_utility: CognitoUtility = None) -> Dict[str, Any]:
    """
    Reset a user's password (admin operation).
    
    Creates a new temporary password and forces user to change on next login.
    
    Path Parameters:
        user_id: User ID to reset password for
        
    Body:
        {
            "temp_password": "optional - if not provided, auto-generates",
            "send_email": false  // Optional - send password reset email
        }
    
    Returns:
        200: Password reset successfully
        {
            "message": "Password reset successfully",
            "temp_password": "TempPass123!" // Only if auto-generated and send_email=false
        }
        
        400: Invalid request
        403: Not authorized (requires admin role)
        404: User not found
        500: Server error
    """
    try:
        # Extract authentication
        tenant_id, user_id, user_roles = LambdaEventUtility.get_authenticated_user_context(event)
        
        # Verify admin role
        if 'tenant_admin' not in user_roles and 'platform_admin' not in user_roles:
            return error_response(
                "Admin access required to reset passwords",
                "FORBIDDEN",
                403
            )
        
        # Extract target user ID from path
        target_user_id = LambdaEventUtility.get_value_from_path_parameters(event, 'user_id')
        if not target_user_id:
            return error_response(
                "user_id is required in path",
                "INVALID_REQUEST",
                400
            )
        
        # Parse request body
        body = LambdaEventUtility.get_body_from_event(event, raise_on_error=False) or {}
        temp_password = body.get('temp_password')
        send_email = body.get('send_email', False)
        
        # Initialize services with request context
        if injected_user_service:
            user_svc = injected_user_service
        else:
            # Create request context from event for security enforcement
            request_context = RequestContext(event)
            db = DynamoDB()
            table_name = os.environ.get('DYNAMODB_TABLE_NAME', os.environ.get('APPLICATION_TABLE_NAME'))
            user_svc = UserService(dynamodb=db, table_name=table_name, request_context=request_context)
        
        cognito = injected_cognito_utility or CognitoUtility()
        
        # Get target user from DynamoDB (uses request_context internally)
        user_result = user_svc.get_by_id(user_id=target_user_id)
        
        if not user_result.success:
            return error_response(
                user_result.message,
                user_result.error_code or "USER_NOT_FOUND",
                404
            )
        
        target_user = user_result.data
        
        # Verify user has Cognito account
        if not target_user.cognito_user_name:
            return error_response(
                "User does not have a Cognito account",
                "NO_COGNITO_ACCOUNT",
                400
            )
        
        # Reset password in Cognito
        try:
            user_pool_id = EnvironmentVariables.get_cognito_user_pool()
            cognito.admin_set_user_password(
                user_name=target_user.cognito_user_name,
                password=temp_password,  # None = auto-generate
                user_pool_id=user_pool_id,
                is_permanent=False  # Force change on next login
            )
            
            return success_response(
                data={"user_id": target_user_id},
                message="Password reset successfully"
            )
            
        except Exception as cognito_error:
            return error_response(
                f"Failed to reset password in Cognito: {str(cognito_error)}",
                "COGNITO_ERROR",
                500
            )
    
    except Exception as e:
        return error_response(
            f"Failed to reset password: {str(e)}",
            "INTERNAL_ERROR",
            500
        )
