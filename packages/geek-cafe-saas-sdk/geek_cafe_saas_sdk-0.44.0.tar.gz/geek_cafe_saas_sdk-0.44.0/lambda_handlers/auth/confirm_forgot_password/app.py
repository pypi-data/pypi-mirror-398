"""
Lambda Handler: Confirm Forgot Password (Public)

POST /auth/confirm-forgot-password

Public endpoint to complete forgot password flow.
User provides the code received via email and their new password.

Authorization: Public (no auth required)
"""

import os
from typing import Dict, Any

from geek_cafe_saas_sdk.utilities.lambda_event_utility import LambdaEventUtility
from geek_cafe_saas_sdk.utilities.response import error_response, success_response
from geek_cafe_saas_sdk.utilities.cognito_utility import CognitoUtility


def lambda_handler(event: Dict[str, Any], context: Any,
                   injected_cognito_utility: CognitoUtility = None) -> Dict[str, Any]:
    """
    Confirm forgot password with verification code.
    
    User provides the code from email and their new password to complete reset.
    
    Body:
        {
            "email": "user@example.com",
            "code": "123456",
            "new_password": "NewPass123!"
        }
    
    Returns:
        200: Password reset successfully
        {
            "message": "Password reset successfully"
        }
        
        400: Invalid request or code
        500: Server error
    """
    try:
        # Parse request body
        body = LambdaEventUtility.get_body_from_event(event)
        if not body:
            return error_response(
                "Request body is required",
                "INVALID_REQUEST",
                400
            )
        
        email = body.get('email')
        code = body.get('code')
        new_password = body.get('new_password')
        
        # Validate required fields
        if not email:
            return error_response(
                "email is required",
                "INVALID_REQUEST",
                400
            )
        
        if not code:
            return error_response(
                "code is required",
                "INVALID_REQUEST",
                400
            )
        
        if not new_password:
            return error_response(
                "new_password is required",
                "INVALID_REQUEST",
                400
            )
        
        # Initialize Cognito utility
        cognito = injected_cognito_utility or CognitoUtility()
        
        try:
            # Confirm forgot password with code
            response = cognito.client.confirm_forgot_password(
                ClientId=os.getenv("COGNITO_CLIENT_ID"),
                Username=email.lower(),
                ConfirmationCode=code,
                Password=new_password
            )
            
            return success_response(
                {
                    "message": "Password reset successfully"
                },
                200
            )
            
        except cognito.client.exceptions.CodeMismatchException:
            return error_response(
                "Invalid verification code",
                "INVALID_CODE",
                400
            )
        
        except cognito.client.exceptions.ExpiredCodeException:
            return error_response(
                "Verification code has expired. Please request a new one",
                "EXPIRED_CODE",
                400
            )
        
        except cognito.client.exceptions.InvalidPasswordException:
            return error_response(
                "Password does not meet password policy requirements",
                "INVALID_PASSWORD",
                400
            )
        
        except cognito.client.exceptions.UserNotFoundException:
            return error_response(
                "User not found",
                "USER_NOT_FOUND",
                404
            )
        
        except cognito.client.exceptions.LimitExceededException:
            return error_response(
                "Too many attempts. Please try again later",
                "RATE_LIMIT_EXCEEDED",
                429
            )
        
        except Exception as cognito_error:
            return error_response(
                f"Failed to reset password: {str(cognito_error)}",
                "COGNITO_ERROR",
                500
            )
    
    except Exception as e:
        return error_response(
            f"Failed to process password reset: {str(e)}",
            "INTERNAL_ERROR",
            500
        )
