from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex, DynamoDBKey
import datetime as dt
from typing import List, Dict, Any
from geek_cafe_saas_sdk.core.models.base_tenant_user_model import BaseTenantUserModel


class Event(BaseTenantUserModel):
    """
    Event model for event scheduling system (MeetUp/Calendar style).

    Uses adjacent records pattern with EventAttendee for unlimited guests and RSVP tracking.
    All datetime fields stored as float UTC timestamps for better indexing and querying.
    
    Features:
    - Start/end timestamps with timezone support
    - Location-based discovery (city, state, geo)
    - Multiple hosts via EventAttendee records
    - Capacity management and wait-list support
    - Recurring events support
    - Custom registration fields
    - Event visibility and access control
    """

    def __init__(self):
        super().__init__()
        
        # Basic Info
        self._title: str | None = None
        self._description: str | None = None
        self._event_type: str = "meetup"  # meetup, conference, workshop, social, networking, etc.
        
        # Date/Time (ALL STORED AS FLOAT UTC TIMESTAMPS)
        self._start_utc_ts: float | None = None
        self._end_utc_ts: float | None = None
        self._timezone: str | None = None  # IANA timezone for display (e.g., "America/New_York")
        self._is_all_day: bool = False
        
        # Location
        self._location_type: str = "physical"  # physical, virtual, hybrid
        self._location_name: str | None = None
        self._location_address: str | None = None
        self._location_city: str | None = None
        self._location_state: str | None = None  # State/Province/Region
        self._location_country: str | None = None
        self._location_postal_code: str | None = None
        self._location_latitude: float | None = None
        self._location_longitude: float | None = None
        self._virtual_link: str | None = None  # For virtual/hybrid events
        
                
        # Capacity & Registration
        self._max_attendees: int | None = None
        self._registration_deadline_utc_ts: float | None = None
        self._requires_approval: bool = False
        self._allow_wait_list: bool = False
        self._allow_guest_plus_one: bool = False
        
        # Visibility & Status
        self._visibility: str = "public"  # public, private, members_only
        self._status: str = "draft"  # draft, published, cancelled, completed
        self._cancellation_reason: str | None = None
        self._group_id: str | None = None
        
        # Recurring Events
        self._is_recurring: bool = False
        self._recurrence_rule: str | None = None  # RRULE format
        self._recurrence_end_utc_ts: float | None = None
        self._parent_event_id: str | None = None  # For recurring event instances
        
        # Metadata
        self._tags: List[str] = []
        self._custom_fields: Dict[str, Any] = {}  # Flexible registration fields
        
        # Legacy fields (keep for backward compatibility, but deprecated)
        self._date: str | None = None  # DEPRECATED: Use start_utc_ts
        self._invited_guests: List[str] = []  # DEPRECATED: Use EventAttendee records
        self._organizer_id: str | None = None  # DEPRECATED: Use owner_id
        self._is_draft: bool = False  # DEPRECATED: Use status

        self._setup_indexes()

    def _setup_indexes(self):
        """Setup DynamoDB indexes for event queries."""

        # Primary index: events by ID
        primary: DynamoDBIndex = DynamoDBIndex()
        primary.name = "primary"
        primary.partition_key.attribute_name = "pk"
        primary.partition_key.value = lambda: DynamoDBKey.build_key(("event", self.id))
        primary.sort_key.attribute_name = "sk"
        primary.sort_key.value = lambda: DynamoDBKey.build_key(("event", self.id))
        self.indexes.add_primary(primary)

        ## GSI1: Events by owner/organizer
        gsi: DynamoDBIndex = DynamoDBIndex()
        gsi.name = "gsi1"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(("owner", self.owner_id))
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(("date", self.start_utc_ts))
        self.indexes.add_secondary(gsi)

        ## GSI2: Events by city (MeetUp-style discovery)
        gsi: DynamoDBIndex = DynamoDBIndex()
        gsi.name = "gsi2"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(
            ("city", self.location_city),
            ("state", self.location_state),
            ("country", self.location_country)
        )
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(("date", self.start_utc_ts))
        self.indexes.add_secondary(gsi)

        ## GSI3: Events by state/region
        gsi: DynamoDBIndex = DynamoDBIndex()
        gsi.name = "gsi3"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(
            ("state", self.location_state),
            ("country", self.location_country)
        )
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(("date", self.start_utc_ts))
        self.indexes.add_secondary(gsi)

        ## GSI4: Events by geo-location (geohash grid for nearby events)
        gsi: DynamoDBIndex = DynamoDBIndex()
        gsi.name = "gsi4"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(("geo", self._get_geohash()))
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(("date", self.start_utc_ts))
        self.indexes.add_secondary(gsi)

        ## GSI5: Events by tenant and date
        gsi: DynamoDBIndex = DynamoDBIndex()
        gsi.name = "gsi5"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(("tenant", self.tenant_id))
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(("date", self.start_utc_ts))
        self.indexes.add_secondary(gsi)

        ## GSI6: Events by type
        gsi: DynamoDBIndex = DynamoDBIndex()
        gsi.name = "gsi6"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(
            ("type", self.event_type),
            ("status", self.status)
        )
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(("date", self.start_utc_ts))
        self.indexes.add_secondary(gsi)

        ## GSI7: Events by group
        gsi: DynamoDBIndex = DynamoDBIndex()
        gsi.name = "gsi7"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(("group", self.group_id))
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(("date", self.start_utc_ts))
        self.indexes.add_secondary(gsi)

        ## GSI8: Published public events (discovery feed)
        gsi: DynamoDBIndex = DynamoDBIndex()
        gsi.name = "gsi8"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(
            ("visibility", self.visibility if self.status == "published" else None),
            ("status", self.status)
        )
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(("date", self.start_utc_ts))
        self.indexes.add_secondary(gsi)

    # Helper Methods
    def _get_geohash(self, precision: int = 4) -> str | None:
        """Generate geohash for geo-location indexing (4-char = ~20km grid)."""
        if self._location_latitude is None or self._location_longitude is None:
            return None
        
        # Simple geohash implementation (4-char precision for ~20km grid)
        lat, lng = self._location_latitude, self._location_longitude
        
        # Normalize to 0-1 range
        lat_norm = (lat + 90) / 180
        lng_norm = (lng + 180) / 360
        
        # Create hash string
        hash_str = f"{int(lat_norm * 1000):04d}{int(lng_norm * 1000):04d}"
        return hash_str[:precision]
    
    @staticmethod
    def datetime_to_utc_ts(datetime_str: str) -> float:
        """Convert ISO8601 datetime string to UTC timestamp.
        
        Args:
            datetime_str: ISO8601 string (e.g., "2025-11-15T18:00:00-08:00")
            
        Returns:
            float: UTC timestamp
        """
        dt_obj = dt.datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        return dt_obj.timestamp()
    
    @staticmethod
    def utc_ts_to_datetime_str(timestamp: float, timezone: str = "UTC") -> str:
        """Convert UTC timestamp to ISO8601 string in specified timezone.
        
        Args:
            timestamp: UTC timestamp
            timezone: IANA timezone (e.g., "America/New_York")
            
        Returns:
            str: ISO8601 datetime string
        """
        import zoneinfo
        dt_utc = dt.datetime.fromtimestamp(timestamp, tz=dt.UTC)
        if timezone != "UTC":
            try:
                tz = zoneinfo.ZoneInfo(timezone)
                dt_local = dt_utc.astimezone(tz)
                return dt_local.isoformat()
            except:
                pass
        return dt_utc.isoformat()

    # Properties - Basic Info
    @property
    def title(self) -> str | None:
        """Event title."""
        return self._title

    @title.setter
    def title(self, value: str | None):
        self._title = value

    @property
    def description(self) -> str | None:
        """Event description."""
        return self._description

    @description.setter
    def description(self, value: str | None):
        self._description = value

    @property
    def event_type(self) -> str:
        """Event type (meetup, conference, workshop, etc.)."""
        return self._event_type

    @event_type.setter
    def event_type(self, value: str):
        self._event_type = value

    # Properties - Date/Time (FLOAT UTC TIMESTAMPS)
    @property
    def start_utc_ts(self) -> float | None:
        """Event start time as UTC timestamp."""
        return self._start_utc_ts

    @start_utc_ts.setter
    def start_utc_ts(self, value: float | None):
        self._start_utc_ts = value

    @property
    def end_utc_ts(self) -> float | None:
        """Event end time as UTC timestamp."""
        return self._end_utc_ts

    @end_utc_ts.setter
    def end_utc_ts(self, value: float | None):
        self._end_utc_ts = value

    @property
    def timezone(self) -> str | None:
        """IANA timezone for display (e.g., 'America/New_York')."""
        return self._timezone

    @timezone.setter
    def timezone(self, value: str | None):
        self._timezone = value

    @property
    def is_all_day(self) -> bool:
        """Is this an all-day event."""
        return self._is_all_day

    @is_all_day.setter
    def is_all_day(self, value: bool):
        self._is_all_day = bool(value)

    # Properties - Location
    @property
    def location_type(self) -> str:
        """Location type: physical, virtual, hybrid."""
        return self._location_type

    @location_type.setter
    def location_type(self, value: str):
        if value in ["physical", "virtual", "hybrid"]:
            self._location_type = value

    @property
    def location_name(self) -> str | None:
        """Venue name."""
        return self._location_name

    @location_name.setter
    def location_name(self, value: str | None):
        self._location_name = value

    @property
    def location_address(self) -> str | None:
        """Full address."""
        return self._location_address

    @location_address.setter
    def location_address(self, value: str | None):
        self._location_address = value

    @property
    def location_city(self) -> str | None:
        """City."""
        return self._location_city

    @location_city.setter
    def location_city(self, value: str | None):
        self._location_city = value

    @property
    def location_state(self) -> str | None:
        """State/Province/Region."""
        return self._location_state

    @location_state.setter
    def location_state(self, value: str | None):
        self._location_state = value

    @property
    def location_country(self) -> str | None:
        """Country."""
        return self._location_country

    @location_country.setter
    def location_country(self, value: str | None):
        self._location_country = value

    @property
    def location_postal_code(self) -> str | None:
        """Postal/ZIP code."""
        return self._location_postal_code

    @location_postal_code.setter
    def location_postal_code(self, value: str | None):
        self._location_postal_code = value

    @property
    def location_latitude(self) -> float | None:
        """Latitude."""
        return self._location_latitude

    @location_latitude.setter
    def location_latitude(self, value: float | None):
        self._location_latitude = value

    @property
    def location_longitude(self) -> float | None:
        """Longitude."""
        return self._location_longitude

    @location_longitude.setter
    def location_longitude(self, value: float | None):
        self._location_longitude = value

    @property
    def virtual_link(self) -> str | None:
        """Virtual meeting link (Zoom, Teams, etc.)."""
        return self._virtual_link

    @virtual_link.setter
    def virtual_link(self, value: str | None):
        self._virtual_link = value
    

    # Properties - Capacity & Registration
    @property
    def max_attendees(self) -> int | None:
        """Maximum number of attendees."""
        return self._max_attendees

    @max_attendees.setter
    def max_attendees(self, value: int | None):
        self._max_attendees = value

    @property
    def registration_deadline_utc_ts(self) -> float | None:
        """Registration deadline as UTC timestamp."""
        return self._registration_deadline_utc_ts

    @registration_deadline_utc_ts.setter
    def registration_deadline_utc_ts(self, value: float | None):
        self._registration_deadline_utc_ts = value

    @property
    def requires_approval(self) -> bool:
        """Does RSVP require approval."""
        return self._requires_approval

    @requires_approval.setter
    def requires_approval(self, value: bool):
        self._requires_approval = bool(value)

    @property
    def allow_wait_list(self) -> bool:
        """Allow wait_list when full."""
        return self._allow_wait_list

    @allow_wait_list.setter
    def allow_wait_list(self, value: bool):
        self._allow_wait_list = bool(value)

    @property
    def allow_guest_plus_one(self) -> bool:
        """Allow guests to bring +1."""
        return self._allow_guest_plus_one

    @allow_guest_plus_one.setter
    def allow_guest_plus_one(self, value: bool):
        self._allow_guest_plus_one = bool(value)

    # Properties - Visibility & Status
    @property
    def visibility(self) -> str:
        """Event visibility: public, private, members_only."""
        return self._visibility

    @visibility.setter
    def visibility(self, value: str):
        if value in ["public", "private", "members_only"]:
            self._visibility = value

    @property
    def status(self) -> str:
        """Event status: draft, published, cancelled, completed."""
        return self._status

    @status.setter
    def status(self, value: str):
        if value in ["draft", "published", "cancelled", "completed"]:
            self._status = value

    @property
    def cancellation_reason(self) -> str | None:
        """Reason for cancellation."""
        return self._cancellation_reason

    @cancellation_reason.setter
    def cancellation_reason(self, value: str | None):
        self._cancellation_reason = value

    @property
    def group_id(self) -> str | None:
        """Associated group ID."""
        return self._group_id

    @group_id.setter
    def group_id(self, value: str | None):
        self._group_id = value

    # Properties - Recurring Events
    @property
    def is_recurring(self) -> bool:
        """Is this a recurring event."""
        return self._is_recurring

    @is_recurring.setter
    def is_recurring(self, value: bool):
        self._is_recurring = bool(value)

    @property
    def recurrence_rule(self) -> str | None:
        """Recurrence rule in RRULE format."""
        return self._recurrence_rule

    @recurrence_rule.setter
    def recurrence_rule(self, value: str | None):
        self._recurrence_rule = value

    @property
    def recurrence_end_utc_ts(self) -> float | None:
        """Recurrence end time as UTC timestamp."""
        return self._recurrence_end_utc_ts

    @recurrence_end_utc_ts.setter
    def recurrence_end_utc_ts(self, value: float | None):
        self._recurrence_end_utc_ts = value

    @property
    def parent_event_id(self) -> str | None:
        """Parent event ID for recurring instances."""
        return self._parent_event_id

    @parent_event_id.setter
    def parent_event_id(self, value: str | None):
        self._parent_event_id = value

    # Properties - Metadata
    @property
    def tags(self) -> List[str]:
        """Event tags."""
        return self._tags

    @tags.setter
    def tags(self, value: List[str] | None):
        self._tags = value if isinstance(value, list) else []

    @property
    def custom_fields(self) -> Dict[str, Any]:
        """Custom registration fields."""
        return self._custom_fields

    @custom_fields.setter
    def custom_fields(self, value: Dict[str, Any] | None):
        self._custom_fields = value if isinstance(value, dict) else {}

    # Legacy Properties (DEPRECATED)
    @property
    def date(self) -> str | None:
        """DEPRECATED: Use start_utc_ts instead."""
        if self._start_utc_ts:
            return self.utc_ts_to_datetime_str(self._start_utc_ts, self._timezone or "UTC")
        return self._date

    @date.setter
    def date(self, value: str | None):
        """DEPRECATED: Use start_utc_ts instead."""
        self._date = value
        if value:
            try:
                self._start_utc_ts = self.datetime_to_utc_ts(value)
            except:
                pass

    @property
    def organizer_id(self) -> str | None:
        """DEPRECATED: Use owner_id instead."""
        return self._owner_id or self._organizer_id

    @organizer_id.setter
    def organizer_id(self, value: str | None):
        """DEPRECATED: Use owner_id instead."""
        self._organizer_id = value
        if value and not self._owner_id:
            self._owner_id = value

    @property
    def invited_guests(self) -> List[str]:
        """DEPRECATED: Use EventAttendee records instead."""
        return self._invited_guests

    @invited_guests.setter
    def invited_guests(self, value: List[str] | None):
        """DEPRECATED: Use EventAttendee records instead."""
        self._invited_guests = value if isinstance(value, list) else []

    @property
    def is_draft(self) -> bool:
        """DEPRECATED: Use status property instead."""
        return self._status == "draft" or self._is_draft

    @is_draft.setter
    def is_draft(self, value: bool):
        """DEPRECATED: Use status property instead."""
        self._is_draft = bool(value)
        if value:
            self._status = "draft"

    # Helper Methods
    def is_upcoming(self) -> bool:
        """Check if the event is in the future."""
        if self._start_utc_ts:
            now_ts = dt.datetime.now(dt.UTC).timestamp()
            return self._start_utc_ts > now_ts
        return False

    def is_past(self) -> bool:
        """Check if the event is in the past."""
        if self._end_utc_ts:
            now_ts = dt.datetime.now(dt.UTC).timestamp()
            return self._end_utc_ts < now_ts
        return False

    def is_happening_now(self) -> bool:
        """Check if the event is currently happening."""
        if self._start_utc_ts and self._end_utc_ts:
            now_ts = dt.datetime.now(dt.UTC).timestamp()
            return self._start_utc_ts <= now_ts <= self._end_utc_ts
        return False

    def duration_hours(self) -> float | None:
        """Get event duration in hours."""
        if self._start_utc_ts and self._end_utc_ts:
            return (self._end_utc_ts - self._start_utc_ts) / 3600
        return None

    def is_published(self) -> bool:
        """Check if event is published."""
        return self._status == "published"

    def is_cancelled(self) -> bool:
        """Check if event is cancelled."""
        return self._status == "cancelled"

    def is_physical_location(self) -> bool:
        """Check if event has physical location."""
        return self._location_type in ["physical", "hybrid"]

    def is_virtual_event(self) -> bool:
        """Check if event is virtual."""
        return self._location_type in ["virtual", "hybrid"]

    def has_location_coordinates(self) -> bool:
        """Check if event has lat/lng coordinates."""
        return self._location_latitude is not None and self._location_longitude is not None

    # Legacy helper methods for invited_guests (DEPRECATED)
    def add_invited_guest(self, user_id: str):
        """DEPRECATED: Add a user to invited guests list. Use EventAttendee records instead."""
        if user_id not in self._invited_guests:
            self._invited_guests.append(user_id)

    def remove_invited_guest(self, user_id: str):
        """DEPRECATED: Remove a user from invited guests list. Use EventAttendee records instead."""
        if user_id in self._invited_guests:
            self._invited_guests.remove(user_id)

    def is_user_invited(self, user_id: str) -> bool:
        """DEPRECATED: Check if user is invited. Use EventAttendee records instead."""
        return user_id in self._invited_guests

    @property
    def event_date_timestamp(self) -> float:
        """Get event date as timestamp. Returns start_utc_ts or converts date string."""
        if self._start_utc_ts:
            return self._start_utc_ts
        if self._date:
            try:
                return self.datetime_to_utc_ts(self._date)
            except:
                return 0.0
        return 0.0

    @property
    def is_private(self) -> bool:
        """Check if event visibility is private."""
        return self._visibility == "private"

    @property
    def is_standalone(self) -> bool:
        """Check if event is standalone (not associated with a group)."""
        return self._group_id is None or self._group_id == ""


