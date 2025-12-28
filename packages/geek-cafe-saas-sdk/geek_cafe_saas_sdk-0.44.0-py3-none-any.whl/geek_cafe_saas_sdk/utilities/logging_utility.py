import json
from typing import Any, Dict
from aws_lambda_powertools import Logger
from geek_cafe_saas_sdk.utilities.environment_variables import (
    EnvironmentVariables,
)


LOG_LEVEL = EnvironmentVariables.get_logging_level()


class LoggingUtility:
    def __init__(self, service=None) -> None:
        self.logger: Logger
        self.logger = Logger(service=service)
        self.logger.setLevel(LOG_LEVEL)

    @staticmethod
    def get_logger(
        service: str | None = None, level: str | None | int = None
    ) -> Logger:
        if level is None:
            level = LOG_LEVEL
        logger = Logger(service=service)
        logger.setLevel(level)
        return logger

    @staticmethod
    def build_message(
        source: str,
        action: str,
        message: str | None = None,
        metric_filter: str | None = None,
    ) -> dict:
        """
        Build a formatted message for logging
        Args:
            source (str): _description_
            action (str): _description_
            message (str, optional): _description_. Defaults to None.
            metric_filter (str, optional): _description_. Defaults to None.

        Returns:
            dict: _description_
        """
        response = {
            "source": source,
            "action": action,
            "details": message,
            "metric_filter": metric_filter,
        }
        return response
    
    @staticmethod
    def sanitize_event_for_logging(event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize a Lambda event dictionary by masking sensitive fields.
        
        This removes or masks sensitive information like:
        - Authorization headers
        - API keys
        - Passwords
        - Tokens
        - SSNs, credit cards, etc.
        
        Args:
            event: The Lambda event dictionary to sanitize
            
        Returns:
            A sanitized copy of the event safe for logging
        """
        if not isinstance(event, dict):
            return event
        
        # Fields that should be completely removed
        REMOVE_FIELDS = {
            'password', 'passwd', 'pwd',
            'secret', 'api_key', 'apikey',
            'token', 'access_token', 'refresh_token',
            'private_key', 'privatekey',
            'ssn', 'credit_card', 'creditcard',
            'cvv', 'pin'
        }
        
        # Fields that should be masked (show first few chars)
        MASK_FIELDS = {
            'authorization', 'x_api_key',
            'cookie', 'session'
        }
        
        def sanitize_value(key: str, value: Any) -> Any:
            """Recursively sanitize values."""
            try:
                key_lower = key.lower().replace('-', '_').replace(' ', '_')
                
                # Remove sensitive fields entirely (exact match)
                if key_lower in REMOVE_FIELDS:
                    return '[REDACTED]'
                
                # Mask partially visible fields (exact match)
                if key_lower in MASK_FIELDS:
                    if isinstance(value, str) and len(value) > 20:
                        return f"{value[:4]}...{value[-4:]}"
                    return '[MASKED]'
                
                # Recursively handle nested structures
                if isinstance(value, dict):
                    return {k: sanitize_value(k, v) for k, v in value.items()}
                elif isinstance(value, list):
                    return [sanitize_value(key, item) if isinstance(item, dict) else item 
                            for item in value]
                
                return value
            except Exception:
                # If we can't safely process the value, redact it
                return '[SANITIZATION_ERROR]'
        
        # Create a deep copy and sanitize
        try:
            sanitized = {k: sanitize_value(k, v) for k, v in event.items()}
            # Validate that the result is JSON-serializable
            import json
            json.dumps(sanitized)
            return sanitized
        except Exception as e:
            # If sanitization fails, return safe fallback
            return {"error": "Failed to sanitize event"}


class LogLevels:
    def __init__(self) -> None:
        pass

    CRITICAL = 50
    FATAL = CRITICAL
    ERROR = 40
    WARNING = 30
    WARN = WARNING
    INFO = 20
    DEBUG = 10
    NOTSET = 0
