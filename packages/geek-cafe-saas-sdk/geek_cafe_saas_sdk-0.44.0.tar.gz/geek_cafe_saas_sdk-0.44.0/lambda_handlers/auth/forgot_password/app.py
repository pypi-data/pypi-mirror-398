"""
Lambda Handler: Forgot Password (Public)

POST /auth/forgot-password

Public endpoint to initiate forgot password flow.
Sends password reset code to user's email.

Authorization: Public (no auth required)
"""

import os
from typing import Dict, Any

from geek_cafe_saas_sdk.utilities.lambda_event_utility import LambdaEventUtility
from geek_cafe_saas_sdk.utilities.response import error_response, success_response
from geek_cafe_saas_sdk.utilities.cognito_utility import CognitoUtility
from geek_cafe_saas_sdk.utilities.environment_variables import EnvironmentVariables


def lambda_handler(event: Dict[str, Any], context: Any,
                   injected_cognito_utility: CognitoUtility = None) -> Dict[str, Any]:
    """
    Initiate forgot password flow.
    
    Sends a verification code to the user's registered email address.
    User must then call /auth/confirm-forgot-password with the code.
    
    Body:
        {
            "email": "user@example.com"
        }
    
    Returns:
        200: Reset code sent successfully
        {
            "message": "Password reset code sent to your email",
            "code_delivery_details": {
                "destination": "u***@example.com",
                "delivery_medium": "EMAIL"
            }
        }
        
        400: Invalid request
        404: User not found
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
        if not email:
            return error_response(
                "email is required",
                "INVALID_REQUEST",
                400
            )
        
        # Initialize Cognito utility
        cognito = injected_cognito_utility or CognitoUtility()
        
        try:
            # Initiate forgot password flow
            response = cognito.client.forgot_password(
                ClientId=os.getenv("COGNITO_CLIENT_ID"),  # Requires client ID
                Username=email.lower()
            )
            
            # Extract code delivery details
            code_delivery = response.get("CodeDeliveryDetails", {})
            
            return success_response(
                {
                    "message": "Password reset code sent to your email",
                    "code_delivery_details": {
                        "destination": code_delivery.get("Destination", ""),
                        "delivery_medium": code_delivery.get("DeliveryMedium", "EMAIL")
                    }
                },
                200
            )
            
        except cognito.client.exceptions.UserNotFoundException:
            # Don't reveal if user exists (security best practice)
            return success_response(
                {
                    "message": "If the email exists, a reset code has been sent"
                },
                200
            )
        
        except cognito.client.exceptions.InvalidParameterException as e:
            return error_response(
                "Invalid email format",
                "INVALID_EMAIL",
                400
            )
        
        except cognito.client.exceptions.LimitExceededException:
            return error_response(
                "Too many requests. Please try again later",
                "RATE_LIMIT_EXCEEDED",
                429
            )
        
        except Exception as cognito_error:
            return error_response(
                f"Failed to initiate password reset: {str(cognito_error)}",
                "COGNITO_ERROR",
                500
            )
    
    except Exception as e:
        return error_response(
            f"Failed to process forgot password request: {str(e)}",
            "INTERNAL_ERROR",
            500
        )
