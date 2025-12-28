from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex, DynamoDBKey
from typing import List, Dict, Any
from geek_cafe_saas_sdk.core.models.base_tenant_user_model import BaseTenantUserModel


class EventAttendee(BaseTenantUserModel):
    """
    Event attendee/invitation record (adjacent record pattern).
    
    Similar to ChatChannelMember, this enables:
    - Unlimited attendees (no DynamoDB item size limit)
    - Full RSVP tracking with history
    - Multiple hosts/co-organizers per event
    - Guest +1 support
    - Custom registration data
    - Check-in tracking
    
    Each attendee gets their own record with their RSVP status and role.
    """

    def __init__(self):
        super().__init__()
        
        
        # Relationship
        self._event_id: str | None = None
        self._user_id: str | None = None  # Also in BaseModel, but key for this model
        
        # RSVP Status
        self._rsvp_status: str | None = None  # invited, accepted, declined, tentative, wait_list (defaults to "invited" when saved)
        self._invited_at_utc_ts: float | None = None
        self._responded_at_utc_ts: float | None = None
        self._invited_by_user_id: str | None = None
        
        # Role (enables multiple hosts)
        self._role: str | None = None  # organizer, co_host, attendee, speaker, volunteer (defaults to "attendee" when saved)
        
        # Guest +1
        self._plus_one_count: int = 0
        self._plus_one_names: List[str] = []
        
        # Check-in
        self._checked_in: bool = False
        self._checked_in_at_utc_ts: float | None = None
        self._checked_in_by_user_id: str | None = None
        self._can_check_in_others: bool = False  # Permission to check in other attendees
        
        # Custom Registration
        self._registration_data: Dict[str, Any] = {}  # Answers to custom fields
        self._registration_notes: str | None = None
        
        # Notifications
        self._notification_preferences: Dict[str, bool] = {
            "event_updates": True,
            "reminders": True,
            "cancellations": True
        }
        self._reminder_sent: bool = False
        self._reminder_sent_at_utc_ts: float | None = None

        self._setup_indexes()

    def _setup_indexes(self):
        """Setup DynamoDB indexes for event attendee queries."""

        # Primary index: attendee by composite ID
        primary: DynamoDBIndex = DynamoDBIndex()
        primary.name = "primary"
        primary.partition_key.attribute_name = "pk"
        primary.partition_key.value = lambda: DynamoDBKey.build_key(("event", self.event_id), ("user", self.user_id))
        primary.sort_key.attribute_name = "sk"
        primary.sort_key.value = lambda: DynamoDBKey.build_key(("attendee", self.id))
        self.indexes.add_primary(primary)

        ## GSI1: Attendees by event (most common query)
        gsi: DynamoDBIndex = DynamoDBIndex()
        gsi.name = "gsi1"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(("event", self.event_id))
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(
            ("role", self.role),
            ("status", self.rsvp_status),
            ("ts", self.invited_at_utc_ts)
        )
        self.indexes.add_secondary(gsi)

        ## GSI2: User's events (my RSVPs)
        gsi: DynamoDBIndex = DynamoDBIndex()
        gsi.name = "gsi2"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(("user", self.user_id))
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(
            ("status", self.rsvp_status),
            ("ts", self.invited_at_utc_ts)
        )
        self.indexes.add_secondary(gsi)

        ## GSI3: Event hosts (organizers and co-hosts)
        gsi: DynamoDBIndex = DynamoDBIndex()
        gsi.name = "gsi3"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(
            ("event", self.event_id),
            ("role", self.role if self.role in ["organizer", "co_host"] else None)
        )
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(("ts", self.invited_at_utc_ts))
        self.indexes.add_secondary(gsi)

        ## GSI4: Confirmed attendees (for display)
        gsi: DynamoDBIndex = DynamoDBIndex()
        gsi.name = "gsi4"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(
            ("event", self.event_id),
            ("status", self.rsvp_status if self.rsvp_status == "accepted" else None)
        )
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(("ts", self.responded_at_utc_ts))
        self.indexes.add_secondary(gsi)

        ## GSI5: Who invited this user (networking)
        gsi: DynamoDBIndex = DynamoDBIndex()
        gsi.name = "gsi5"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(("inviter", self.invited_by_user_id))
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(("ts", self.invited_at_utc_ts))
        self.indexes.add_secondary(gsi)

    # Properties - Relationship
    @property
    def event_id(self) -> str | None:
        """Event ID."""
        return self._event_id

    @event_id.setter
    def event_id(self, value: str | None):
        self._event_id = value

    # user_id is inherited from BaseModel but we need it for this model
    # No need to override, just use self.user_id from BaseModel

    # Properties - RSVP Status
    @property
    def rsvp_status(self) -> str:
        """RSVP status: invited, accepted, declined, tentative, wait_list."""
        return self._rsvp_status

    @rsvp_status.setter
    def rsvp_status(self, value: str | None):
        if value is None or value in ["invited", "accepted", "declined", "tentative", "wait_list"]:
            self._rsvp_status = value

    @property
    def invited_at_utc_ts(self) -> float | None:
        """When invitation was sent (UTC timestamp)."""
        return self._invited_at_utc_ts

    @invited_at_utc_ts.setter
    def invited_at_utc_ts(self, value: float | None):
        self._invited_at_utc_ts = value

    @property
    def responded_at_utc_ts(self) -> float | None:
        """When user responded to RSVP (UTC timestamp)."""
        return self._responded_at_utc_ts

    @responded_at_utc_ts.setter
    def responded_at_utc_ts(self, value: float | None):
        self._responded_at_utc_ts = value

    @property
    def invited_by_user_id(self) -> str | None:
        """Who invited this attendee."""
        return self._invited_by_user_id

    @invited_by_user_id.setter
    def invited_by_user_id(self, value: str | None):
        self._invited_by_user_id = value

    # Properties - Role
    @property
    def role(self) -> str:
        """Attendee role: organizer, co_host, attendee, speaker, volunteer."""
        return self._role

    @role.setter
    def role(self, value: str | None):
        if value is None or value in ["organizer", "co_host", "attendee", "speaker", "volunteer"]:
            self._role = value

    # Properties - Guest +1
    @property
    def plus_one_count(self) -> int:
        """Number of +1 guests."""
        return self._plus_one_count

    @plus_one_count.setter
    def plus_one_count(self, value: int):
        self._plus_one_count = max(0, value)

    @property
    def plus_one_names(self) -> List[str]:
        """Names of +1 guests."""
        return self._plus_one_names

    @plus_one_names.setter
    def plus_one_names(self, value: List[str] | None):
        self._plus_one_names = value if isinstance(value, list) else []

    # Properties - Check-in
    @property
    def checked_in(self) -> bool:
        """Has attendee checked in."""
        return self._checked_in

    @checked_in.setter
    def checked_in(self, value: bool):
        self._checked_in = bool(value)

    @property
    def checked_in_at_utc_ts(self) -> float | None:
        """When attendee checked in (UTC timestamp)."""
        return self._checked_in_at_utc_ts

    @checked_in_at_utc_ts.setter
    def checked_in_at_utc_ts(self, value: float | None):
        self._checked_in_at_utc_ts = value

    @property
    def checked_in_by_user_id(self) -> str | None:
        """Who checked in this attendee."""
        return self._checked_in_by_user_id

    @checked_in_by_user_id.setter
    def checked_in_by_user_id(self, value: str | None):
        self._checked_in_by_user_id = value

    @property
    def can_check_in_others(self) -> bool:
        """Whether this attendee can check in other attendees."""
        return self._can_check_in_others

    @can_check_in_others.setter
    def can_check_in_others(self, value: bool):
        self._can_check_in_others = bool(value)

    # Properties - Custom Registration
    @property
    def registration_data(self) -> Dict[str, Any]:
        """Custom registration field answers."""
        return self._registration_data

    @registration_data.setter
    def registration_data(self, value: Dict[str, Any] | None):
        self._registration_data = value if isinstance(value, dict) else {}

    @property
    def registration_notes(self) -> str | None:
        """Additional registration notes."""
        return self._registration_notes

    @registration_notes.setter
    def registration_notes(self, value: str | None):
        self._registration_notes = value

    # Properties - Notifications
    @property
    def notification_preferences(self) -> Dict[str, bool]:
        """Notification preferences."""
        return self._notification_preferences

    @notification_preferences.setter
    def notification_preferences(self, value: Dict[str, bool] | None):
        self._notification_preferences = value if isinstance(value, dict) else {}

    @property
    def reminder_sent(self) -> bool:
        """Has reminder been sent."""
        return self._reminder_sent

    @reminder_sent.setter
    def reminder_sent(self, value: bool):
        self._reminder_sent = bool(value)

    @property
    def reminder_sent_at_utc_ts(self) -> float | None:
        """When reminder was sent (UTC timestamp)."""
        return self._reminder_sent_at_utc_ts

    @reminder_sent_at_utc_ts.setter
    def reminder_sent_at_utc_ts(self, value: float | None):
        self._reminder_sent_at_utc_ts = value

    # Helper Methods
    def is_organizer(self) -> bool:
        """Check if this attendee is an organizer."""
        return self._role == "organizer"

    def is_host(self) -> bool:
        """Check if this attendee is organizer or co-host."""
        return self._role in ["organizer", "co_host"]

    def has_accepted(self) -> bool:
        """Check if attendee accepted invitation."""
        return self._rsvp_status == "accepted"

    def has_declined(self) -> bool:
        """Check if attendee declined invitation."""
        return self._rsvp_status == "declined"

    def is_on_wait_list(self) -> bool:
        """Check if attendee is on wait_list."""
        return self._rsvp_status == "wait_list"

    def has_responded(self) -> bool:
        """Check if attendee has responded to invitation."""
        return self._rsvp_status != "invited"

    def has_plus_ones(self) -> bool:
        """Check if attendee is bringing +1 guests."""
        return self._plus_one_count > 0

    def total_attendee_count(self) -> int:
        """Total number of people attending (including +1s)."""
        return 1 + (self._plus_one_count or 0)

    def can_check_in(self) -> bool:
        """Check if attendee can check in (must be accepted)."""
        return self.has_accepted() and not self._checked_in
