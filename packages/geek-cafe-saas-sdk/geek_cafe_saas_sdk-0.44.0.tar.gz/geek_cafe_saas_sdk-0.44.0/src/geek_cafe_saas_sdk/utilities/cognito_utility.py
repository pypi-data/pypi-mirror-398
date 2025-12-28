"""
Cognito Utility
"""

import os
import time
from typing import List, Dict, Any, Optional
import boto3

from geek_cafe_saas_sdk.utilities.logging_utility import LoggingUtility, LogLevels
from geek_cafe_saas_sdk.utilities.environment_variables import (
    EnvironmentVariables,
)
from geek_cafe_saas_sdk.modules.users.models import User
from geek_cafe_saas_sdk.utilities.string_functions import StringFunctions
from geek_cafe_saas_sdk.utilities.dictionary_utility import DictionaryUtility

AWS_PROFILE = os.getenv("AWS_PROFILE")
AWS_REGION = os.getenv("AWS_REGION")
# Create a Cognito client
PROVISIONED_SESSION = None
PROVISIONED_CLIENT = None
try:
    PROVISIONED_SESSION = boto3.Session(
        profile_name=AWS_PROFILE, region_name=AWS_REGION
    )
    PROVISIONED_CLIENT = PROVISIONED_SESSION.client("cognito-idp")
except:  # noqa: E722, pylint: disable=w0702
    pass

logger = LoggingUtility.get_logger(__name__, LogLevels.INFO)


class CognitoCustomAttributes:
    """Defines the Cognito Custom Attributes we have available"""

    USER_ID_KEY_NAME: str = "custom:user_id"
    TENANT_ID_KEY_NAME: str = "custom:tenant_id"
    USER_ROLES_KEY_NAME: str = "custom:roles"
    USER_PERMISSIONS_KEY_NAME: str = "custom:permissions"


class CognitoUtility:
    """AWS Cognito Utility"""

    def __init__(
        self, aws_profile: Optional[str] = None, aws_region: Optional[str] = None
    ) -> None:
        aws_profile = aws_profile or os.getenv("AWS_PROFILE")
        aws_region = aws_region or os.getenv("AWS_REGION")
        if aws_profile is not None:
            self.session = boto3.Session(
                profile_name=aws_profile, region_name=aws_region
            )
            # use one with the profile provided
            self.client = self.session.client("cognito-idp")
        else:
            # use the one already provisioned
            self.client = PROVISIONED_CLIENT

        self.use_custom_attributes: bool = True

    def admin_create_user(
        self,
        user_pool_id: Optional[str] = None,
        temp_password: Optional[str] = None,
        *,
        user: User,
        send_invitation: bool = False,
        retry_count: int = 0,
    ) -> dict:
        """
        Creates a user for the geek cafe saas system.  The user is created
        in the environment for the Cognito User Pool and added to DynamoDB
        for tracking in the SaaS system.

        Users will have a sub/id which is the Cognito Id however we'll use an
        internal id (user_id), which will be useful if we need failover
        Cognito User Pools in the future.

        """
        user_supplied_password = temp_password is not None

        if temp_password is None:
            temp_password = StringFunctions.generate_random_password(15)

        if user.id is None:
            raise ValueError("User id is required")

        if user.tenant_id is None:
            raise ValueError("Tenant id is required")

        user_attributes = self.__set_user_attributes(user=user)

        # email_verified
        # this sets their email address as if it's had been verified.
        # we may want to remove this in the future.
        # if this is not set then they are in a locked state and must use a temp password
        if not send_invitation:
            user_attributes.append({"Name": "email_verified", "Value": "true"})

        try:
            kwargs = {
                "UserPoolId": user_pool_id,
                "Username": user.email,
                "UserAttributes": user_attributes,
                # "TemporaryPassword": temp_password,
                # ForceAliasCreation=True|False,
                "DesiredDeliveryMediums": [
                    "EMAIL",
                ],
            }

            if not send_invitation:
                # add to the args
                kwargs["MessageAction"] = "SUPPRESS"

            # create the user in cognito
            response = self.client.admin_create_user(**kwargs)

            # something changed and we need to reset the password
            # otherwise they get into a force password change and they're locked out
            # (they need the temp password which we sending them at the moment)
            self.admin_set_user_password(
                user_name=user.email,
                password=temp_password,
                user_pool_id=user_pool_id,
                is_permanent=True,
            )

            return response

        except self.client.exceptions.UsernameExistsException as e:
            logger.error(f"Error: {e.response['Error']['Message']}")
            logger.error(
                f"The username {user.email} already exists. Please choose a different username."
            )
            raise e

        except self.client.exceptions.InvalidPasswordException as e:
            logger.error(f"Error: {e.response['Error']['Message']}")
            logger.error(
                "Password does not meet the requirements. Please choose a stronger password."
            )
            if not user_supplied_password and retry_count < 5:
                logger.debug(
                    {
                        "action": "admin_create_user",
                        "user_pool_id": user_pool_id,
                        "user_name": user.email,
                        "user_supplied_password": user_supplied_password,
                        "retry_count": retry_count,
                        "message": (
                            "User did not supply the password. We created one automatically, "
                            "but it did not meet the requirements. Trying again."
                        ),
                        "error": f"Error: {e.response['Error']['Message']}",
                    }
                )
                retry_count += 1
                return self.admin_create_user(
                    user_pool_id=user_pool_id,
                    temp_password=None,
                    send_invitation=send_invitation,
                    user=user,
                    retry_count=retry_count,
                )
            else:
                logger.debug(
                    {
                        "action": "admin_create_user",
                        "user_pool_id": user_pool_id,
                        "user_name": user.email,
                        "user_supplied_password": user_supplied_password,
                        "retry_count": retry_count,
                    }
                )
                raise e
        except self.client.exceptions.InvalidParameterException as e:
            logger.error(f"Error: {e.response['Error']['Message']}")
            logger.error(
                "An invalid parameter was added.  This is mostlikely an attempt to add a custome attribute that isn't registered."
            )
            raise e
        except Exception as e:
            logger.error(f"Error: {e}")
            raise e

    def admin_disable_user(
        self, user_name: str, user_pool_id: str, reset_password: bool = True
    ) -> dict:
        """Disable a user in cognito"""
        response = self.client.admin_disable_user(
            UserPoolId=user_pool_id, Username=user_name
        )

        if reset_password:
            self.admin_set_user_password(
                user_name=user_name, user_pool_id=user_pool_id, password=None
            )

        return response

    def admin_delete_user(self, user_name: str, user_pool_id: str) -> dict:
        """Delete the user account"""

        # we need to disbale a user first
        self.admin_disable_user(
            user_name=user_name, user_pool_id=user_pool_id, reset_password=False
        )

        response = self.client.admin_delete_user(
            UserPoolId=user_pool_id, Username=user_name
        )

        return response

    def admin_enable_user(
        self, user_name: str, user_pool_id: str, reset_password: bool = True
    ) -> dict:
        """Enable the user account"""
        response = self.client.admin_enable_user(
            UserPoolId=user_pool_id, Username=user_name
        )

        if reset_password:
            # reset the password
            self.admin_set_user_password(
                user_name=user_name, user_pool_id=user_pool_id, password=None
            )
        return response

    def admin_set_user_password(
        self, user_name, password: str | None, user_pool_id, is_permanent=True
    ) -> dict:
        """Set a user password"""

        if not password:
            password = StringFunctions.generate_random_password(15)
        logger.debug(
            {
                "action": "admin_set_user_password",
                "UserPoolId": user_pool_id,
                "Username": user_name,
                "Password": "****************",
                "Permanent": is_permanent,
            }
        )

        for i in range(5):
            try:
                response = self.client.admin_set_user_password(
                    UserPoolId=user_pool_id,
                    Username=user_name,
                    Password=password,
                    Permanent=is_permanent,
                )
                break
            except Exception as e:  # pylint: disable=w0718
                time.sleep(5 * i + 1)
                logger.error(f"Error: {e}")
                if i >= 4:
                    raise e

        return response

    def update_user_account(self, *, user_pool_id: str, user: User) -> dict:
        """
        Update the cognito user account
        """
        user_attributes = self.__set_user_attributes(user=user)

        if user.cognito_user_name is None:
            raise ValueError("User cognito user name is required")

        response = self.client.admin_update_user_attributes(
            UserPoolId=f"{user_pool_id}",
            Username=f"{user.cognito_user_name}",
            UserAttributes=user_attributes,
            ClientMetadata={"string": "string"},
        )
        return response

    def sign_up_cognito_user(self, email, password, client_id) -> dict | None:
        """
        This is only allowed if the admin only flag is not being enforced.
        Under most circumstances we won't have this enabled
        """
        email = self.__format_email(email=email)
        try:
            # Create the user in Cognito
            response = self.client.sign_up(
                ClientId=client_id,
                Username=email,
                Password=password,
                UserAttributes=[{"Name": "email", "Value": email}],
            )

            logger.debug(
                f"User {email} created successfully. Confirmation code sent to {email}."
            )
            return response

        except self.client.exceptions.UsernameExistsException as e:
            logger.error(f"Error: {e.response['Error']['Message']}")
            logger.error(
                f"The username {email} already exists. Please choose a different username."
            )
            return None

        except self.client.exceptions.InvalidPasswordException as e:
            logger.error(f"Error: {e.response['Error']['Message']}")
            logger.error(
                "Password does not meet the requirements. Please choose a stronger password."
            )
            return None

        except Exception as e:  # pylint: disable=w0718
            logger.error(f"Error: {e}")
            return None

    def authenticate_user_pass_auth(
        self, username, password, client_id
    ) -> tuple[str, str, str]:
        """
        Login with the username/passwrod combo + client_id
        Returns:
            Tuple: id_token, access_token, refresh_token
            Use the id_token as the jwt
            Use the access_token if you are directly accessing aws resources
            Use the refresh_token if you are attempting to get a 'refreshed' jwt token
        """
        # Initiate the authentication process and get the session
        auth_response = self.client.initiate_auth(
            ClientId=client_id,
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters={"USERNAME": username, "PASSWORD": password},
        )

        if "ChallengeName" in auth_response:
            raise RuntimeError("New password required before a token can be provided")

        # Extract the session tokens
        id_token = auth_response["AuthenticationResult"]["IdToken"]
        access_token = auth_response["AuthenticationResult"]["AccessToken"]
        refresh_token = auth_response["AuthenticationResult"]["RefreshToken"]

        return id_token, access_token, refresh_token

    def create_resource_server(
        self,
        user_pool_id: str,
        resource_server_name: str,
        resource_server_identifier: str,
        scopes: list[dict[str, str]],
    ) -> dict:
        if not resource_server_name:
            raise ValueError("resource_server_name is required")

        if not resource_server_identifier:
            raise ValueError("resource_server_identifier is required")

        if scopes is None or len(scopes) == 0:
            raise ValueError("scopes is required")

        response = self.client.create_resource_server(
            UserPoolId=user_pool_id,
            Identifier=resource_server_identifier,
            Name=f"{resource_server_name}",
            Scopes=scopes,
        )

        return response

    def create_client_app_machine_to_machine(
        self,
        user_pool_id: str,
        client_name: str,
        id_token_time_out: int = 60,
        id_token_units: str = "minutes",
        access_token_time_out: int = 60,
        access_token_units: str = "minutes",
        refresh_token_time_out: int = 60,
        refresh_token_units: str = "minutes",
    ) -> dict:
        # valid units: 'seconds'|'minutes'|'hours'|'days'

        response = self.client.create_user_pool_client(
            UserPoolId=f"{user_pool_id}",
            ClientName=f"{client_name}",
            GenerateSecret=True,
            RefreshTokenValidity=refresh_token_time_out,
            AccessTokenValidity=access_token_time_out,
            IdTokenValidity=id_token_time_out,
            TokenValidityUnits={
                "AccessToken": f"{access_token_units}",
                "IdToken": f"{id_token_units}",
                "RefreshToken": f"{refresh_token_units}",
            },
            # ReadAttributes=[
            #     'string',
            # ],
            # WriteAttributes=[
            #     'string',
            # ],
            # ExplicitAuthFlows=[
            #     'ADMIN_NO_SRP_AUTH'|'CUSTOM_AUTH_FLOW_ONLY'|'USER_PASSWORD_AUTH'|'ALLOW_ADMIN_USER_PASSWORD_AUTH'|'ALLOW_CUSTOM_AUTH'|'ALLOW_USER_PASSWORD_AUTH'|'ALLOW_USER_SRP_AUTH'|'ALLOW_REFRESH_TOKEN_AUTH',
            # ],
            # SupportedIdentityProviders=[
            #     'string',
            # ],
            # CallbackURLs=[
            #     'string',
            # ],
            # LogoutURLs=[
            #     'string',
            # ],
            # DefaultRedirectURI='string',
            AllowedOAuthFlows=["client_credentials"],
            AllowedOAuthScopes=[
                "string",
            ],
            AllowedOAuthFlowsUserPoolClient=True,
            # AnalyticsConfiguration={
            #     'ApplicationId': 'string',
            #     'ApplicationArn': 'string',
            #     'RoleArn': 'string',
            #     'ExternalId': 'string',
            #     'UserDataShared': True|False
            # },
            # PreventUserExistenceErrors='LEGACY'|'ENABLED',
            EnableTokenRevocation=True,
            # EnablePropagateAdditionalUserContextData=True|False,
            # AuthSessionValidity=123
        )

        return response

    def search_cognito(self, email_address: str, user_pool_id: str) -> dict:
        """Search cognito for an existing user"""

        email_address = self.__format_email(email=email_address) or ""
        filter_string = f'email = "{email_address}"'

        # Call the admin_list_users method with the filter
        response = self.client.list_users(UserPoolId=user_pool_id, Filter=filter_string)

        return response

    def __set_user_attributes(self, *, user: User) -> List[dict]:
        """Set the user attributes"""

        user_attributes: List[Dict[str, Any]] = [
            {"Name": "email", "Value": str(user.email).lower()}
        ]

        user_attributes.append({"Name": "email_verified", "Value": "true"})

        if user.first_name is not None:
            user_attributes.append({"Name": "given_name", "Value": user.first_name})

        if user.last_name is not None:
            user_attributes.append({"Name": "family_name", "Value": user.last_name})

        if self.use_custom_attributes:
            # we have the ability to turn this off for backward compatibility
            # once early access is over we can always allow this.
            # if we try to add them and they aren't registered we will get an error
            # one workaround is to manually add them to the user pool
            if user.id is not None:
                user_attributes.append(
                    {
                        "Name": CognitoCustomAttributes.USER_ID_KEY_NAME,
                        "Value": user.id,
                    }
                )

            if user.roles is not None:
                roles: str = ""
                if isinstance(user.roles, list):
                    roles = ",".join(user.roles)
                elif isinstance(user.roles, str):
                    roles = user.roles
                user_attributes.append(
                    {
                        "Name": CognitoCustomAttributes.USER_ROLES_KEY_NAME,
                        "Value": roles,
                    }
                )

            if user.tenant_id is not None:
                user_attributes.append(
                    {
                        "Name": CognitoCustomAttributes.TENANT_ID_KEY_NAME,
                        "Value": user.tenant_id,
                    }
                )

        return user_attributes

    def map(self, cognito_response: dict) -> User:
        """Map the cognito response to a user object"""
        user = User()
        user.cognito_user_name = self.get_cognito_attribute(
            cognito_response, "Username"
        )
        user.email = self.get_cognito_attribute(cognito_response, "email", None)
        user.first_name = self.get_cognito_attribute(
            cognito_response, "given_name", None
        )
        user.last_name = self.get_cognito_attribute(
            cognito_response, "family_name", None
        )
        user.id = self.get_cognito_attribute(
            cognito_response, CognitoCustomAttributes.USER_ID_KEY_NAME, None
        )
        user.tenant_id = self.get_cognito_attribute(
            cognito_response, CognitoCustomAttributes.TENANT_ID_KEY_NAME, None
        )

        roles: str | None | List[str] = self.get_cognito_attribute(
            cognito_response, CognitoCustomAttributes.USER_ROLES_KEY_NAME, None
        )
        if roles is None:
            roles = []
        if isinstance(roles, str):
            roles = roles.split(",")
        user.roles = roles
        return user

    def get_cognito_attribute(
        self, response: dict, name: str, default: Optional[str] = None
    ) -> Optional[str]:
        if name in response:
            return response.get(name, default)

        attributes = response.get("Attributes", [])
        attribute = DictionaryUtility.find_dict_by_name(attributes, "Name", name)
        if attribute and isinstance(attribute, list):
            return str(attribute[0].get("Value", default))
        return default

    def __format_email(self, email: str | None) -> str | None:
        """
        Format the email to be used in the cognito user pool.
        We have some installations that were set up case-sensitive, until we can
        migrate them over to a case-insensitive system, we make sure we only
        deal with lower case usernames.
        """

        if email is None:
            return None

        return str(email).lower()


if __name__ == "__main__":
    pass
