"""
NotificationPreference Model - User notification channel preferences.

Manages per-user settings for notification delivery including:
- Channel enablement (email, SMS, push, in-app)
- Quiet hours/Do Not Disturb
- Notification type preferences
- Frequency controls

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

from typing import Dict, List, Any
from geek_cafe_saas_sdk.core.models.base_model import BaseModel
from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex, DynamoDBKey


class NotificationPreference(BaseModel):
    """
    User notification preferences model.
    
    Controls how and when a user receives notifications across all channels.
    Supports per-channel, per-type preferences with quiet hours.
    """
    
    def __init__(self):
        super().__init__()
        
        # User identification
        self._user_id: str = ""  # Required
        
        # Global preferences
        self._enabled: bool = True  # Master switch
        self._do_not_disturb: bool = False  # Temporary DND
        self._quiet_hours_enabled: bool = False
        self._quiet_hours_start: str | None = None  # "22:00"
        self._quiet_hours_end: str | None = None  # "08:00"
        self._timezone: str = "UTC"
        
        # Channel preferences
        self._email_enabled: bool = True
        self._email_address: str | None = None  # Override default
        self._email_frequency: str = "immediate"  # immediate, daily_digest, weekly_digest
        
        self._sms_enabled: bool = False  # Opt-in required
        self._sms_phone: str | None = None
        self._sms_frequency: str = "immediate"
        
        self._push_enabled: bool = True
        self._push_device_tokens: List[str] = []  # Multiple devices
        
        self._in_app_enabled: bool = True
        
        self._webhook_enabled: bool = False
        self._webhook_url: str | None = None
        
        # Type-specific preferences
        # Key = notification_type, Value = {channel: enabled}
        self._type_preferences: Dict[str, Dict[str, bool]] = {}
        
        # Digest settings
        self._digest_time: str = "09:00"  # When to send daily digest
        self._digest_day: str = "monday"  # For weekly digest
        
        # Metadata
        self._language: str = "en"  # Preferred language
        self._metadata: Dict[str, Any] = {}
        
        # CRITICAL: Call _setup_indexes() as LAST line in __init__
        self._setup_indexes()
    
    def _setup_indexes(self):
        """Setup DynamoDB indexes for notification preference queries."""
        
        # Primary index: Preference by user ID
        primary: DynamoDBIndex = DynamoDBIndex()
        primary.name = "primary"
        primary.partition_key.attribute_name = "pk"
        primary.partition_key.value = lambda: DynamoDBKey.build_key(("preferences", self.user_id))
        primary.sort_key.attribute_name = "sk"
        primary.sort_key.value = lambda: "metadata"
        self.indexes.add_primary(primary)
    
    # Core Properties
    @property
    def user_id(self) -> str:
        return self._user_id
    
    @user_id.setter
    def user_id(self, value: str):
        self._user_id = value
    
    @property
    def enabled(self) -> bool:
        return self._enabled
    
    @enabled.setter
    def enabled(self, value: bool):
        self._enabled = value
    
    @property
    def do_not_disturb(self) -> bool:
        return self._do_not_disturb
    
    @do_not_disturb.setter
    def do_not_disturb(self, value: bool):
        self._do_not_disturb = value
    
    @property
    def quiet_hours_enabled(self) -> bool:
        return self._quiet_hours_enabled
    
    @quiet_hours_enabled.setter
    def quiet_hours_enabled(self, value: bool):
        self._quiet_hours_enabled = value
    
    @property
    def quiet_hours_start(self) -> str | None:
        return self._quiet_hours_start
    
    @quiet_hours_start.setter
    def quiet_hours_start(self, value: str | None):
        self._quiet_hours_start = value
    
    @property
    def quiet_hours_end(self) -> str | None:
        return self._quiet_hours_end
    
    @quiet_hours_end.setter
    def quiet_hours_end(self, value: str | None):
        self._quiet_hours_end = value
    
    @property
    def timezone(self) -> str:
        return self._timezone
    
    @timezone.setter
    def timezone(self, value: str):
        self._timezone = value
    
    @property
    def email_enabled(self) -> bool:
        return self._email_enabled
    
    @email_enabled.setter
    def email_enabled(self, value: bool):
        self._email_enabled = value
    
    @property
    def email_address(self) -> str | None:
        return self._email_address
    
    @email_address.setter
    def email_address(self, value: str | None):
        self._email_address = value
    
    @property
    def email_frequency(self) -> str:
        return self._email_frequency
    
    @email_frequency.setter
    def email_frequency(self, value: str):
        self._email_frequency = value
    
    @property
    def sms_enabled(self) -> bool:
        return self._sms_enabled
    
    @sms_enabled.setter
    def sms_enabled(self, value: bool):
        self._sms_enabled = value
    
    @property
    def sms_phone(self) -> str | None:
        return self._sms_phone
    
    @sms_phone.setter
    def sms_phone(self, value: str | None):
        self._sms_phone = value
    
    @property
    def sms_frequency(self) -> str:
        return self._sms_frequency
    
    @sms_frequency.setter
    def sms_frequency(self, value: str):
        self._sms_frequency = value
    
    @property
    def push_enabled(self) -> bool:
        return self._push_enabled
    
    @push_enabled.setter
    def push_enabled(self, value: bool):
        self._push_enabled = value
    
    @property
    def push_device_tokens(self) -> List[str]:
        return self._push_device_tokens
    
    @push_device_tokens.setter
    def push_device_tokens(self, value: List[str]):
        self._push_device_tokens = value if value else []
    
    @property
    def in_app_enabled(self) -> bool:
        return self._in_app_enabled
    
    @in_app_enabled.setter
    def in_app_enabled(self, value: bool):
        self._in_app_enabled = value
    
    @property
    def webhook_enabled(self) -> bool:
        return self._webhook_enabled
    
    @webhook_enabled.setter
    def webhook_enabled(self, value: bool):
        self._webhook_enabled = value
    
    @property
    def webhook_url(self) -> str | None:
        return self._webhook_url
    
    @webhook_url.setter
    def webhook_url(self, value: str | None):
        self._webhook_url = value
    
    @property
    def type_preferences(self) -> Dict[str, Dict[str, bool]]:
        return self._type_preferences
    
    @type_preferences.setter
    def type_preferences(self, value: Dict[str, Dict[str, bool]]):
        self._type_preferences = value if value else {}
    
    @property
    def digest_time(self) -> str:
        return self._digest_time
    
    @digest_time.setter
    def digest_time(self, value: str):
        self._digest_time = value
    
    @property
    def digest_day(self) -> str:
        return self._digest_day
    
    @digest_day.setter
    def digest_day(self, value: str):
        self._digest_day = value
    
    @property
    def language(self) -> str:
        return self._language
    
    @language.setter
    def language(self, value: str):
        self._language = value
    
    @property
    def metadata(self) -> Dict[str, Any]:
        return self._metadata
    
    @metadata.setter
    def metadata(self, value: Dict[str, Any]):
        self._metadata = value if value else {}
    
    # Helper Methods
    def is_channel_enabled(self, channel: str) -> bool:
        """Check if a channel is globally enabled."""
        if not self._enabled or self._do_not_disturb:
            return False
        
        channel_map = {
            "email": self._email_enabled,
            "sms": self._sms_enabled,
            "push": self._push_enabled,
            "in_app": self._in_app_enabled,
            "webhook": self._webhook_enabled
        }
        
        return channel_map.get(channel, False)
    
    def is_type_enabled(self, notification_type: str, channel: str) -> bool:
        """Check if a specific notification type is enabled for a channel."""
        if not self.is_channel_enabled(channel):
            return False
        
        if notification_type in self._type_preferences:
            type_prefs = self._type_preferences[notification_type]
            return type_prefs.get(channel, True)
        
        return True
    
    def set_type_preference(self, notification_type: str, channel: str, enabled: bool):
        """Set preference for a notification type on a specific channel."""
        if notification_type not in self._type_preferences:
            self._type_preferences[notification_type] = {}
        
        self._type_preferences[notification_type][channel] = enabled
    
    def is_in_quiet_hours(self, current_time: str) -> bool:
        """Check if current time is within quiet hours (HH:MM format)."""
        if not self._quiet_hours_enabled:
            return False
        
        if not self._quiet_hours_start or not self._quiet_hours_end:
            return False
        
        try:
            current = self._time_to_minutes(current_time)
            start = self._time_to_minutes(self._quiet_hours_start)
            end = self._time_to_minutes(self._quiet_hours_end)
            
            if start > end:  # Overnight hours
                return current >= start or current <= end
            else:
                return start <= current <= end
        except:
            return False
    
    def _time_to_minutes(self, time_str: str) -> int:
        """Convert HH:MM to minutes since midnight."""
        hours, minutes = map(int, time_str.split(":"))
        return hours * 60 + minutes
    
    def add_device_token(self, token: str):
        """Add a push device token."""
        if token and token not in self._push_device_tokens:
            self._push_device_tokens.append(token)
    
    def remove_device_token(self, token: str):
        """Remove a push device token."""
        if token in self._push_device_tokens:
            self._push_device_tokens.remove(token)
    
    def validate(self) -> tuple[bool, list[str]]:
        """Validate preference data."""
        errors = []
        
        if not self._user_id:
            errors.append("user_id is required")
        
        # Validate quiet hours format
        if self._quiet_hours_enabled:
            if not self._quiet_hours_start or not self._quiet_hours_end:
                errors.append("quiet_hours_start and quiet_hours_end required when enabled")
            else:
                try:
                    self._time_to_minutes(self._quiet_hours_start)
                    self._time_to_minutes(self._quiet_hours_end)
                except:
                    errors.append("Invalid quiet hours format (use HH:MM)")
        
        # Validate SMS phone if enabled
        if self._sms_enabled and not self._sms_phone:
            errors.append("sms_phone required when SMS is enabled")
        
        # Validate webhook URL if enabled
        if self._webhook_enabled and not self._webhook_url:
            errors.append("webhook_url required when webhook is enabled")
        
        return (len(errors) == 0, errors)
