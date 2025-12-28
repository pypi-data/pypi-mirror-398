"""Lambda Event Utilities

This module provides utility functions for working with AWS Lambda event payloads.
"""

from typing import List, Dict, Any, Optional, Union
import re
import json
from aws_lambda_powertools import Logger
from geek_cafe_saas_sdk.utilities.custom_exceptions import Error
from geek_cafe_saas_sdk.utilities.http_status_code import HttpStatusCodes
from geek_cafe_saas_sdk.utilities.environment_variables import (
    EnvironmentVariables,
)
from geek_cafe_saas_sdk.utilities.jwt_utility import JwtUtility

from boto3_assist.utilities.serialization_utility import JsonConversions


logger = Logger(__name__)


TABLE_NAME_NOT_AVAILABLE = "FAKE_TABLE_ENVIRONMENT_VAR_IS_NOT_SET"


class LambdaEventUtility:
    """Utility class for extracting and processing data from AWS Lambda event payloads.
    
    This class provides static methods to extract common data elements from Lambda events,
    including user information, path parameters, query parameters, and more.
    """

    @staticmethod
    def get_dynamodb_table_name() -> str | None:
        """Get the application DynamoDB table name from environment variables.
        
        Returns:
            str | None: The DynamoDB table name or TABLE_NAME_NOT_AVAILABLE if not set.
                      Returns None if the value is not a string.
        """
        value = EnvironmentVariables.get_dynamodb_table_name()
        if value is None:
            raise Error("The DynamoDB table name is not set")
        if not isinstance(value, str):
            raise Error("The DynamoDB table name is not a string")
        return value

   

    @staticmethod
    def get_file_name_from_event(event: Dict[str, Any]) -> Optional[str]:
        """Extract the file name from the event payload.
        
        Args:
            event: The Lambda event dictionary
            
        Returns:
            The file name as a string, or None if not found or not a string
        """
        value = LambdaEventUtility.get_value_from_event(event, "file_name")
        if not isinstance(value, str):
            return None
        return value

    @staticmethod
    def get_resource_type_from_event(event: Dict[str, Any]) -> Optional[str]:
        """Extract the file type from the event payload.
        
        Args:
            event: The Lambda event dictionary
            
        Returns:
            The file type as a string, or None if not found or not a string
        """
        value = LambdaEventUtility.get_value_from_event(event, "resource_type")
        if not isinstance(value, str):
            return None
        return value

    @staticmethod
    def get_method_type_from_event(event: Dict[str, Any]) -> Optional[str]:
        """Extract the HTTP method type from the event payload.
        
        Args:
            event: The Lambda event dictionary
            
        Returns:
            The HTTP method (GET, POST, PUT, DELETE, etc.) as a string, or None if not found or not a string
        """
        value = LambdaEventUtility.get_value_from_event(event, "method_type")
        if not isinstance(value, str):
            return None
        return value

    @staticmethod
    def get_token_use(event: Dict[str, Any]) -> Optional[str]:
        """Extract the token use information from the event payload.
        
        Retrieves the token_use claim from the authorizer context, which indicates
        whether the token is an 'id', 'access', or other type of token.
        
        Args:
            event: The Lambda event dictionary
            
        Returns:
            The token use value as a string, or None if not found or not a string
        """
        path = "requestContext/authorizer/claims/token_use"
        value = LambdaEventUtility.get_value_from_event(event, path)

        if not isinstance(value, str):
            return None
        return value

    @staticmethod
    def get_target_user_id(event: Dict[str, Any]) -> Optional[str]:
        """Extract the target user ID from the event path parameters.
        
        Target users are the users we are performing an action on, such as CRUD operations.
        The user ID is typically found in the route path parameters.
        
        Args:
            event: The Lambda event dictionary
            
        Returns:
            The target user ID as a string, or None if not found or not a string
        """
        value = LambdaEventUtility.get_value_from_path_parameters(event, "user-id")
        if not isinstance(value, str):
            return None
        return value

    @staticmethod
    def get_target_tenant_id(event: Dict[str, Any]) -> Optional[str]:
        """Extract the target tenant ID from the event path parameters.
        
        Target tenants are the tenants we are performing an action on, such as CRUD operations.
        The tenant ID is typically found in the route path parameters.
        
        Args:
            event: The Lambda event dictionary
            
        Returns:
            The target tenant ID as a string, or None if not found or not a string
        """
        value = LambdaEventUtility.get_value_from_path_parameters(event, "tenant-id")
        if not isinstance(value, str):
            return None
        return value

    @staticmethod
    def get_authenticated_user_id(event: Dict[str, Any]) -> Optional[str]:
        """Extract the authenticated user ID from the event claims.
        
        Retrieves the user ID from the custom:user_id claim in the authorizer context.
        
        Args:
            event: The Lambda event dictionary
            
        Returns:
            The authenticated user ID as a string, or None if not found or not a string
        """
        return LambdaEventUtility.get_claims_data(
            event, "custom:user_id"
        )

    @staticmethod
    def get_authenticated_user_email(event: Dict[str, Any]) -> Optional[str]:
        """Extract the authenticated user email from the event claims.
        
        Retrieves the user email from the email claim in the authorizer context.
        
        Args:
            event: The Lambda event dictionary
            
        Returns:
            The authenticated user email as a string, or None if not found or not a string
        """
        return LambdaEventUtility.get_claims_data(event, "email")

    @staticmethod
    def get_authenticated_user_tenant_id(event: Dict[str, Any]) -> Optional[str]:
        """Extract the authenticated user's tenant ID from the event claims.
        
        Retrieves the tenant ID from the custom:tenant_id claim in the authorizer context.
        
        Args:
            event: The Lambda event dictionary
            
        Returns:
            The authenticated user's tenant ID as a string, or None if not found or not a string
        """
        return LambdaEventUtility.get_claims_data(
            event, "custom:tenant_id"
        )

    @staticmethod
    def get_authenticated_user_roles(event: Dict[str, Any]) -> List[str]:
        """Extract the authenticated user's roles from the event claims.
        
        Retrieves the user roles from the custom:user_roles claim in the authorizer context.
        The roles are returned as a comma-separated string and converted to a list.
        
        Args:
            event: The Lambda event dictionary
            
        Returns:
            A list of role strings, or an empty list if no roles are found
        """
        roles = LambdaEventUtility.get_claims_data(
            event, "custom:user_roles"
        )
        if roles:
            return str(roles).split(",")

        return []

    @staticmethod
    def get_authenticated_user_context(event: Dict[str, Any]) -> tuple[Optional[str], Optional[str], List[str]]:
        """Extract the authenticated user's context (tenant_id, user_id, roles) from the event.
        
        Convenience method that retrieves all three common authentication values
        from the authorizer context in a single call.
        
        Args:
            event: The Lambda event dictionary
            
        Returns:
            A tuple containing (tenant_id, user_id, roles)
            - tenant_id: The user's tenant ID (or None)
            - user_id: The user's ID (or None)
            - roles: A list of role strings (or empty list)
        """
        tenant_id = LambdaEventUtility.get_authenticated_user_tenant_id(event)
        user_id = LambdaEventUtility.get_authenticated_user_id(event)
        roles = LambdaEventUtility.get_authenticated_user_roles(event)
        
        return tenant_id, user_id, roles

    @staticmethod
    def get_claims(event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract the complete claims dictionary from the event.
        
        Retrieves all claims from the authorizer context in the request context.
        
        Args:
            event: The Lambda event dictionary
            
        Returns:
            The claims dictionary, or None if not found or invalid format
            
        Raises:
            ValueError: If the event payload is empty
        """
        if not event or len(event) == 0:
            raise ValueError("The event payload is empty")
            
        path = "requestContext/authorizer/claims"
        value = LambdaEventUtility.get_value_from_event(event, path)
        if isinstance(value, str):
            value = None
        return value

    @staticmethod
    def get_claims_data(event: Dict[str, Any], key: str) -> Optional[str]:
        """Extract a specific claim value from the event claims.
        
        First attempts to find the claim in the authorizer context, then falls back to
        extracting it from the JWT token if available.
        
        Args:
            event: The Lambda event dictionary
            key: The claim key to extract
            
        Returns:
            The claim value as a string, or None if not found
            
        Raises:
            ValueError: If the event payload is empty
            Error: If the claim cannot be found or if there's an error processing the JWT token
        """
        try:
            if not event or len(event) == 0:
                raise ValueError("The event payload is empty")
                
            path = f"requestContext/authorizer/claims/{key}"
            value = LambdaEventUtility.get_value_from_event(event, path)
            
            if not value:
                value = LambdaEventUtility.get_value_from_token(event, key)
                
            if value:
                logger.debug(
                    {
                        "message": f"Found key in JWT with {key}",
                        f"{key}": value,
                    }
                )
                if isinstance(value, str):
                    return value
                else:
                    return str(value)
            else:
                raise Error(
                    message=f"Failed to locate {key} info in JWT Token",
                    status_code=HttpStatusCodes.HTTP_404_NOT_FOUND.value
                )
        except Exception as e:
            raise Error(
                message=f"Failed to locate {key} info in JWT Token",
                status_code=HttpStatusCodes.HTTP_401_UNAUTHENTICATED.value,
                details=str(e)
            ) from e

    @staticmethod
    def get_value_from_token(event: Dict[str, Any], key: str) -> Optional[str]:
        """Extract a specific claim value directly from the JWT token in the Authorization header.
        
        This is used as a fallback when the claim is not available in the authorizer context.
        
        Args:
            event: The Lambda event dictionary
            key: The claim key to extract from the token
            
        Returns:
            The claim value as a string, or None if not found or if the token is invalid
            
        Raises:
            ValueError: If the event payload is empty
        """
        try:
            if not event or len(event) == 0:
                raise ValueError("The event payload is empty")
                
            path = "headers/Authorization"
            jwt_token = LambdaEventUtility.get_value_from_event(event, path)
            value: Optional[str] = None
            if jwt_token and isinstance(jwt_token, str):
                # Use the generic JWT utility to parse the token
                value = JwtUtility.get_claim_from_token(jwt_token, key)
                logger.debug(f"Extracted claim '{key}' from JWT token: {value is not None}")

            if value:
                return value

            else:
                raise Error(
                    {
                        "status_code": HttpStatusCodes.HTTP_404_NOT_FOUND.value,
                        "message": f"Failed to locate {key} info it JWT Token",
                    }
                )
        except Exception as e:
            raise Error(
                {
                    "status_code": HttpStatusCodes.HTTP_401_UNAUTHENTICATED.value,
                    "message": f"Failed to locate {key} info it JWT Token",
                    "exception": str(e),
                }
            ) from e

    @staticmethod
    def get_user_email_from_event(event) -> str | None:
        """Get the user email from the event for claims"""
        if not event:
            return None

        token_use = LambdaEventUtility.get_token_use(event)
        path: str | None = None
        if token_use == "id":
            path = "requestContext/authorizer/claims/email"

        elif token_use == "access":
            path = "requestContext/authorizer/claims/client_id"

        value: str | None = None
        if path:
            value = str(LambdaEventUtility.get_value_from_event(event, path))
        else:
            value = LambdaEventUtility.get_claims_data(event, "email")

        if not isinstance(value, str):
            return None
        return value

    @staticmethod
    def get_message_id_from_event(event: dict, index: int = 0) -> str | None:
        """Gets the message id from an event"""
        records = event.get("Records")
        if records:
            item: dict = records[index]
            value = item.get("messageId")
            if not isinstance(value, str):
                return None
            return value

        return None

    

    
    @staticmethod
    def get_http_method_from_event(event: Dict[str, Any]) -> Optional[str]:
        """Extract the HTTP method from the event.
        
        Returns the HTTP method (e.g., GET, POST, PUT, DELETE) from the event.
        
        Args:
            event: The Lambda event dictionary
            
        Returns:
            The HTTP method as a string, or None if not found or invalid format
        """
        value = LambdaEventUtility.get_value_from_event_ex(event, "httpMethod")
        if not isinstance(value, str):
            return None
        return value

    @staticmethod
    def get_resource_path_from_event(event: Dict[str, Any]) -> Optional[str]:
        """Extract the resource path from the event.
        
        Returns the actual resource path (route) from the event.
        
        Args:
            event: The Lambda event dictionary
            
        Returns:
            The resource path as a string, or None if not found or invalid format
        """
        value = LambdaEventUtility.get_value_from_event_ex(event, "path")
        if not isinstance(value, str):
            return None
        return value

    @staticmethod
    def get_resource_pattern_from_event(event: Dict[str, Any]) -> Optional[str]:
        """Extract the resource pattern from the event.
        
        Returns the resource path with placeholders instead of actual values.
        For example, instead of returning:
        "/tenants/d46814e8-d061-7036-3c81-e37152773912/subscriptions/8925f80c344f0096a5fe6bfb159cdd370ad888c7d914bb6568797701003f155b"
        
        it returns:
        "/tenants/{tenant-id}/subscriptions/{subscription-id}"
        
        Args:
            event: The Lambda event dictionary
            
        Returns:
            The resource pattern as a string, or None if not found or invalid format
        """
        value = LambdaEventUtility.get_value_from_event_ex(event, "resourcePath")
        if not isinstance(value, str):
            return None
        return value

    @staticmethod
    def get_value_from_event_ex(event: Dict[str, Any], key: str) -> Union[str, Dict[str, Any], None]:
        """Get a value from the event, checking both direct key and requestContext path.
        
        This is an extended version of get_value_from_event that also checks in the requestContext
        if the value is not found in the main event object.
        
        Args:
            event: The Lambda event dictionary
            key: The key to look for in the event
            
        Returns:
            The value if found, or None if not found
        """
        value = LambdaEventUtility.get_value_from_event(event, key)
        if not value:
            key = f"requestContext/{key}"
            value = LambdaEventUtility.get_value_from_event(event, key)
        return value

    

    

    

    @staticmethod
    def get_value_from_event(
        event: Dict[str, Any],
        key: str | List[str],
    ) -> str | Dict[str, Any] | None:
        """
        get the value from the event payload
        """
        logger.debug({"source": "get_value_from_event", "event": event, "key": key})

        if not event:
            return None

        if "event" in event:
            event = event["event"]

        if not key:
            logger.warning(
                {
                    "source": "get_value_from_event",
                    "warning": "missing key for lookup",
                    "event": event,
                    "key": key,
                }
            )
            return None

        if "/" in key:
            key = str(key).split("/")

        elif "." in key:
            key = str(key).split(".")

        if isinstance(key, str):
            if key in event:
                return event[key]
            else:
                logger.debug(f'key "{key}" is not in event, checking body.')

            return LambdaEventUtility.get_value_from_event_body(event, key)
        elif isinstance(key, list):
            # loop through
            value: str | Dict[str, Any] | None = event
            for k in key:
                if isinstance(value, dict):
                    value = LambdaEventUtility.get_value_from_event(value, k)
                if not value:
                    break

            return value

        return None

    

    @staticmethod
    def get_value_from_header(event, key, default=None) -> str | dict | None:
        value = LambdaEventUtility.search_payload_for_container_element(
            event, "headers", key, default
        )

        return value

    @staticmethod
    def get_value_from_path_parameters(event, key, default=None) -> str | dict | None:
        value = LambdaEventUtility.search_payload_for_container_element(
            event, "pathParameters", key, default
        )
        if value is None:
            path = LambdaEventUtility.get_resource_path_from_event(event=event)
            pattern = LambdaEventUtility.get_resource_pattern_from_event(event=event)
            if path and pattern:
                value = LambdaEventUtility.extract_value_from_path(
                    path=path, pattern=pattern, variable_name=key
                )
        return value

    @staticmethod
    def extract_value_from_path(
        path: str, pattern: str, variable_name: str
    ) -> str | None:
        # Convert the pattern into a regex pattern to match the variable placeholders
        regex_pattern = re.sub(
            r"\{([^}]+)\}",
            lambda m: f"(?P<{m.group(1).replace('-', '_')}>[^/]+)",
            pattern,
        )

        # Replace hyphens with underscores in the variable name for matching
        variable_name = variable_name.replace("-", "_")

        # Use regex to match the path against the pattern
        match = re.match(regex_pattern, path)

        if match:
            # Extract the value corresponding to the variable_name
            try:
                return match.group(variable_name)
            except:  # noqa: E722, pylint: disable=W0702
                pass
        # else:
        # raise ValueError(f"No match found for the variable '{variable_name}' in the provided path and pattern.")
        return None

    @staticmethod
    def get_value_from_query_string_parameters(
        event, key, default=None
    ) -> str | dict | None:
        value = LambdaEventUtility.search_payload_for_container_element(
            event, "queryStringParameters", key, default
        )

        return value

    @staticmethod
    def get_value_from_multi_value_query_string_parameters(
        event, key, default=None
    ) -> str | dict | None:
        value = LambdaEventUtility.search_payload_for_container_element(
            event, "multiValueQueryStringParameters", key, default
        )

        return value

    @staticmethod
    def search_payload_for_container_element(
        event, container, key, default=None
    ) -> str | dict | None:
        logger.debug(
            {
                "action": "search_payload_for_container_element",
                "event": event,
                "container": container,
                "key": key,
                "metric_filter": "search_payload_for_container_element",
            }
        )

        events = []
        events.append(event)

        if isinstance(event, dict):
            if "message" in event:
                event = event["message"]
                events.append(event)
            if "Records" in event:
                event = event["Records"][0]
                events.append(event)
            if "body" in event:
                body = event["body"]
                if isinstance(body, str):
                    body = JsonConversions.string_to_json_obj(body)
                if isinstance(body, dict):
                    events.append(body)
                    if "requestContext" in body:
                        events.append(body["requestContext"])

        value = None
        for e in events:
            if container in e:
                if container:
                    item = e[container]
                    if item is not None and key in item:
                        value = item[key]

        logger.debug(
            {
                "action": "search_payload_for_container_element",
                "event": event,
                "container": container,
                "key": key,
                "value": value,
                "default": default,
                "metric_filter": "search_payload_for_container_element",
            }
        )

        if value is None:
            value = default

        return value

    @staticmethod
    def get_value_from_event_body(event: dict, key: str) -> str | dict | None:
        """Gets the value from the body section of the event"""
        body = LambdaEventUtility.get_body_from_event(event)
        if body is not None and key in body:
            return body[key]

        logger.debug(
            {
                "info": "Could not find key in event",
                "key": key,
                "found": "False",
                "event": event,
            }
        )
        return None

    @staticmethod
    def get_body_from_event(event, raise_on_error=True) -> dict | None:
        """
        Get the payload from the event. If more than one record is found,
        the first record is returned.
        """
        tmp = event
        if "Records" in tmp:
            tmp = tmp["Records"][0]

        if "body" in tmp:
            tmp = tmp["body"]

        if isinstance(tmp, str):
            try:
                tmp = JsonConversions.string_to_json_obj(tmp, raise_on_error)
            except Exception as e:  # noqa: E722, pylint: disable=W0702
                raise ValueError("Invalid json body in the payload.") from e
        return tmp

    @staticmethod
    def update_event_info(event: dict, key: str, value: str | dict) -> dict:
        """
        update the event with the key and value
        """
        original = event
        status = "processing"
        outcome = "success"
        logger.debug({"update_event_info": {"status": f"{status}", "event": event}})
        body: dict | None = event
        if "body" in event:
            body = LambdaEventUtility.get_body_from_event(event)

        if body is not None and isinstance(body, dict):
            body[key] = value
        else:
            outcome = "failed / not found"

        logger.debug(
            {
                "update_event_info": {
                    "status": f"{status}",
                    "outcome": f"{outcome}",
                    "event": body,
                    "original": original,
                }
            }
        )

        return body or original

    @staticmethod
    def to_snake_case_for_backend(event: Dict[str, Any] | None) -> Dict[str, Any]:
        """
        Convert UI payloads from camelCase to snake_case for backend processing.
        
        Args:
            event: The event payload from the UI in camelCase format
            
        Returns:
            The payload converted to snake_case format
            
        Raises:
            ValueError: If the event is None or not a dictionary
        """
        if event is None:
            raise ValueError("Event payload cannot be None")
        if not isinstance(event, dict):
            raise ValueError(f"Event payload must be a dictionary, got {type(event)}")
        if not event:
            return {}
            
        return JsonConversions.json_camel_to_snake(event)

    @staticmethod
    def to_camel_case_for_ui(payload: Union[List[Dict[str, Any]], Dict[str, Any], None]) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Convert backend data from snake_case to camelCase for UI consumption.
        
        Args:
            payload: The backend data in snake_case format (dict or list of dicts)
            
        Returns:
            The payload converted to camelCase format, maintaining the same structure
            
        Raises:
            ValueError: If the payload is None
        """
        if payload is None:
            raise ValueError("Payload cannot be None")
        if not payload:
            return payload  # Return empty dict/list as-is
            
        return JsonConversions.json_snake_to_camel(payload)