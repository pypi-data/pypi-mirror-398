from geek_cafe_saas_sdk.utilities.lambda_event_utility import LambdaEventUtility


class HttpBodyParameters:
    """Search Http QueryString Parameters"""

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

    def type(self, event: dict) -> str | None:
        """The type parameter"""
        return self.find(event, "type")

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
        value = LambdaEventUtility.get_value_from_event(event, key)
        if isinstance(value, str):
            return value
        return None
