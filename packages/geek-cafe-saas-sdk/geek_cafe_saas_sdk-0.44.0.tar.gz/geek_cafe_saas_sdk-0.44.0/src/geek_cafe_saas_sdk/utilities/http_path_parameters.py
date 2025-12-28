"""
Geek Cafe SaaS Services Http Path Parameters
"""

import os
from .lambda_event_utility import LambdaEventUtility

DEFAULT_RESPONSE_LIMIT = os.getenv("DEFAULT_RESPONSE_LIMIT")


class HttpPathParameters:
    """Search Http Path Parameters"""

    def start_date(self, event: dict) -> str | None:
        """A start date path parameter (start-date)"""
        return self.find(event, "start-date")

    def end_date(self, event: dict) -> str | None:
        """An end date path parameter (end-date)"""
        return self.find(event, "end-date")

    def user_id(self, event: dict) -> str | None:
        """The userId path parameter (user-id)"""
        return self.find(event, "user-id")

    def status(self, event: dict) -> str | None:
        """The status parameter"""
        return self.find(event, "status")

    def file_id(self, event: dict) -> str | None:
        """The file id parameter"""
        return self.find(event, "file-id")

    def tenant_id(self, event: dict) -> str | None:
        """The tenant id parameter"""
        return self.find(event, "tenant-id")

    def subscription_id(self, event: dict) -> str | None:
        """The subscription id parameter"""
        return self.find(event, "subscription-id")

    def find(self, event: dict, key: str) -> str | None:
        """Generic Search/Find a key in the path parameters"""
        value = LambdaEventUtility.get_value_from_path_parameters(event, key)
        if isinstance(value, str):
            return value
        return None

    def limit(self, event: dict) -> int | None:
        """
        Returns the limit if any. Used for response limits on datasets
        responses from DynamoDB
        """
        value = self.find(event, "limit")
        if isinstance(value, str):
            try:
                return int(value)
            except:  # noqa: E722, pylint: disable=w0702
                pass
        return None
