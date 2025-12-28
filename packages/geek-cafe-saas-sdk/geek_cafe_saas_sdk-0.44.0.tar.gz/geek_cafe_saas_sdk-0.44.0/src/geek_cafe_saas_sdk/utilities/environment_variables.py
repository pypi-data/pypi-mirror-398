"""
Geek Cafe SaaS Services Environment Services.

This module provides utilities for loading and accessing environment variables
used throughout the Geek Cafe SaaS Services application. It includes classes for
loading environment files and accessing specific environment variables in a
consistent manner.
"""

import os
from typing import Optional
from aws_lambda_powertools import Logger


logger = Logger(__name__)

DEBUGGING = os.getenv("DEBUGGING", "false").lower() == "true"





class EnvironmentVariables:
    """
    Centralized access to environment variables used throughout the application.
    
    This class provides static methods to access environment variables in a consistent manner,
    with proper typing and default values where appropriate. Using this class instead of direct
    os.getenv calls helps track and manage all environment variables in one place, making
    maintenance and documentation easier.
    """

    @staticmethod
    def get_aws_region() -> Optional[str]:
        """
        Get the AWS region from environment variables.
        
        Returns:
            The AWS region as a string, or None if not set.
        """
        value = os.getenv("AWS_REGION")
        return value

    @staticmethod
    def get_aws_profile() -> Optional[str]:
        """
        Get the AWS profile used for CLI/boto3 commands.
        
        This should only be set with temporary credentials and only for development purposes.
        
        Returns:
            The AWS profile name as a string, or None if not set.
        """
        value = os.getenv("AWS_PROFILE")
        return value

    @staticmethod
    def get_aws_account_id() -> Optional[str]:
        """
        Get the AWS account ID from environment variables.
        
        Returns:
            The AWS account ID as a string, or None if not set.
        """
        value = os.getenv("AWS_ACCOUNT_ID")
        return value

    @staticmethod
    def get_auth_target_validation_level() -> Optional[str]:
        """
        Get the authentication target validation level from environment variables.
        
        Validation levels:
            PASS_THROUGH: Allows the logged in user to be listed as the target
                if the target user isn't explicitly listed. This provides backward compatibility
                during conversion from short URLs to more detailed URL routes.
                
            STRICT: Requires a target user/tenant to be explicitly specified in the path.
                This will be required for all new endpoints. The endpoints have been created
                but some UI and tests have not been updated yet.
        
        Returns:
            The validation level as a string ("PASS_THROUGH" or "STRICT"), or None if not set.
        """
        value = os.getenv("AUTH_TARGET_VALIDATION_LEVEL")
        return value

    

    @staticmethod
    def get_logging_level(default: str = "INFO") -> str:
        """
        Get the logging level from environment variables.
        
        Args:
            default: Default logging level to use if not set in environment (default: "INFO").
            
        Returns:
            The logging level as a string.
        """
        value = os.getenv("LOG_LEVEL", default)
        return value

    @staticmethod
    def get_app_domain():
        """
        gets the app domain name from an environment var
        """
        value = os.getenv("APP_DOMAIN")
        return value

    @staticmethod
    def get_ses_user_name():
        """
        gets the ses user-name from an environment var
        """
        value = os.getenv("SES_USER_NAME")
        return value

    @staticmethod
    def get_ses_password():
        """
        gets the ses password from an environment var
        """
        value = os.getenv("SES_PASSWORD")
        return value

    @staticmethod
    def get_ses_endpoint():
        """
        gets the ses endpoint from an environment var
        """
        value = os.getenv("SES_END_POINT")
        return value

    @staticmethod
    def get_cognito_user_pool() -> str | None:
        """
        gets the cognito user pool from an environment var
        """
        value = os.getenv("COGNITO_USER_POOL")
        return value

    @staticmethod
    def get_dynamodb_table_name():
        """
        gets the dynamodb table name from an environment var
        """
        value = os.getenv("APPLICATION_TABLE_NAME")
        return value

    @staticmethod
    def get_dynamodb_raise_on_error_setting() -> bool:
        """
        gets the dynamodb table name from an environment var
        """
        value = str(os.getenv("RAISE_ON_DB_ERROR", "true")).lower() == "true"

        return value

    @staticmethod
    def get_tenant_user_file_bucket_name():
        """
        gets the tenant user file bucket name from an environment var
        """
        value = os.getenv("TENANT_USER_FILE_BUCKET")
        return value

    @staticmethod
    def get_tenant_user_upload_bucket_name():
        """
        gets the tenant user upload bucket name from an environment var
        """
        value = os.getenv("UPLOAD_BUCKET")
        return value

    @staticmethod
    def get_lambda_function_to_invoke() -> str | None:
        """
        gets the lambda function to invoke from an environment var
        this is used by sync to async lambda invocation, or by the queue
        """
        value = os.getenv("LAMBDA_FUNCTION_TO_INVOKE")
        return value

    @staticmethod
    def get_amazon_trace_id():
        """
        gets the amazon trace id from an environment var
        """
        value = os.getenv("_X_AMZN_TRACE_ID", "NA")
        return value

    @staticmethod
    def get_integration_tests_setting() -> bool:
        """
        determine if integration tests are run from an environment var
        """
        value = str(os.getenv("RUN_INTEGRATION_TESTS", "False")).lower() == "true"
        env = EnvironmentVariables.get_environment_setting()

        if env.lower().startswith("prod"):
            value = False

        return value

    @staticmethod
    def get_environment_setting() -> str:
        """
        gets the environment name from an environment var
        """
        value = os.getenv("ENVIRONMENT") or os.getenv("ENVIRONMENT_NAME")

        if not value:
            logger.warning(
                "ENVIRONMENT var is not set. A future version will throw an error."
            )
            return ""

        return value

    @staticmethod
    def is_development_environment() -> bool:
        """
        determine if the environment is development
        """
        env = EnvironmentVariables.get_environment_setting()
        return env.lower().startswith("dev")
    
    @staticmethod
    def should_log_lambda_events() -> bool:
        """
        Determine if Lambda event payloads should be logged.
        
        Set LOG_LAMBDA_EVENTS=true to enable event logging for debugging.
        Useful for troubleshooting Lambda invocations.
        
        Note: Event payloads are sanitized to remove sensitive fields before logging.
        
        Returns:
            True if event logging is enabled, False otherwise.
        """
        value = os.getenv("LOG_LAMBDA_EVENTS", "false").lower() == "true"
        return value
