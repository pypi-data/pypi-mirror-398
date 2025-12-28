"""
Geek Cafe, LLC
MIT License.  See Project Root for the license information.
"""

import datetime as dt
from boto3_assist.utilities.string_utility import StringUtility
from boto3_assist.dynamodb.dynamodb_model_base import (
    DynamoDBModelBase,   
    exclude_from_serialization 
)
from boto3_assist.utilities.serialization_utility import JsonConversions
from typing import Optional, Dict, Any, Union, List
from geek_cafe_saas_sdk.utilities.datetime_utility import DatetimeUtility

class BaseModel(DynamoDBModelBase):
    """
    The Base DB Model
    Sets a common set of properties for all models
    """
    
    # Define required properties that subclasses must set before saving
    # Override this in subclasses to enforce specific requirements
    _required_properties: List[str] = []
    
    # Flag to control strict property enforcement
    _strict_properties: bool = True

    def __init__(self) -> None:
        # Mark that we're initializing (only set once at the start)
        if not hasattr(self, '_initializing'):
            object.__setattr__(self, '_initializing', True)
            object.__setattr__(self, '_init_complete', False)
        
        super().__init__()
        self.id: str | None= None  # make the id's sortable        
        self._created_utc_ts: float | None = None
        self._modified_utc_ts: float | None = None
        self._deleted_utc_ts: Optional[float] = None
        
        self._table_name: Optional[str] = None
        self.created_by_id: Optional[str]= None
        self.updated_by_id: Optional[str]= None
        self.deleted_by_id: Optional[str]= None
        self.version: float= 1.0        

        self.__model_version: str = "1.0.0"
        self._metadata: Dict[str, Any] | None = None
        self._errors: Dict[str, Any] | None = None
       
    
    def __setattr__(self, name: str, value: Any) -> None:
        """
        Override to prevent dynamic property assignment after initialization.
        
        Allows setting:
        - Private attributes (starting with _)
        - Attributes that already exist on the instance or in the class hierarchy
        - Attributes during __init__ (when _initializing is True)
        
        Raises:
            AttributeError: If trying to set an undefined property after initialization
        """
        # Allow private attributes (needed for internal operations)
        if name.startswith('_'):
            object.__setattr__(self, name, value)
            return
        
        # Allow during initialization
        if hasattr(self, '_initializing') and self._initializing:
            object.__setattr__(self, name, value)
            return
        
        # Check if strict property enforcement is enabled
        if not hasattr(self, '_strict_properties'):
            # Fallback during early initialization
            object.__setattr__(self, name, value)
            return
            
        if self._strict_properties:
            # Check if property exists in class hierarchy (includes @property decorators)
            has_property = False
            for cls in type(self).__mro__:
                if name in cls.__dict__:
                    has_property = True
                    break
            
            # Also check if the attribute already exists on the instance
            if not has_property and not hasattr(self, name):
                raise AttributeError(
                    f"Cannot set undefined property '{name}' on {self.__class__.__name__}. "
                    f"Property must be defined in the model class or its base classes."
                )
        
        # Property exists or strict mode is disabled, allow setting
        object.__setattr__(self, name, value)
    
    def validate_required_properties(self) -> None:
        """
        Validates that all required properties are set.
        Raises ValueError if any required property is None or empty.
        
        This is called automatically by prep_for_save() but can also be
        called manually for validation during tests.
        
        Raises:
            ValueError: If any required property is not set
        """
        missing_properties = []
        
        for prop_name in self._required_properties:
            # Get the actual value (handle both direct attributes and properties)
            value = getattr(self, prop_name, None)
            
            # Check if value is None or empty string
            if value is None or (isinstance(value, str) and not value.strip()):
                missing_properties.append(prop_name)
        
        if missing_properties:
            class_name = self.__class__.__name__
            props_str = ", ".join(missing_properties)
            raise ValueError(
                f"{class_name} validation failed: Required properties are not set: {props_str}"
            )
    
    def prep_for_save(self, preserve_timestamps: bool = False):
        """
        Prepares the model for saving by setting the id and timestamps.
        Also validates that all required properties are set.
        
        Args:
            preserve_timestamps: If True, don't update modified_utc_ts.
                               Useful for migrations and data imports where
                               you want to preserve the original timestamps.
        
        Raises:
            ValueError: If any required property is not set
        """
        # Validate required properties first
        self.validate_required_properties()
        
        self.id = self.id or StringUtility.generate_sortable_uuid()
        self.created_utc_ts = self.created_utc_ts or dt.datetime.now(dt.UTC).timestamp()
        
        # Update modified timestamp unless preserving for migrations
        if not preserve_timestamps:
            self.modified_utc_ts = dt.datetime.now(dt.UTC).timestamp()

    def is_deleted(self) -> bool:
        """
        Returns True if the model is deleted (has a deleted timestamp).
        """
        from decimal import Decimal
        return self.deleted_utc_ts is not None and isinstance(self.deleted_utc_ts, (int, float, Decimal))
    
    

    @property
    def model_version(self) -> str:
        """
        Returns the model version for this model
        """
        return self.__model_version

    @model_version.setter
    def model_version(self, value: str):
        """
        Defines a model version.  All will start with the base model
        version, but you can override this as your model changes.
        Use your services to parse the older models correct (if needed)
        Which means a custom mapping of data between versioning for
        backward compatibility
        """
        self.__model_version = value

    @property
    def model_name(self) -> str:
        """
        Returns the record type for this model
        """
        return StringUtility.camel_to_snake(self.__class__.__name__)

    @model_name.setter
    def model_name(self, value: str):
        """
        This is read-only but we don't want an error during serialization
        """
        pass

    @property
    def model_name_plural(self) -> str:
        """
        Returns the record type for this model
        """
        return self.model_name + "s"

    @model_name_plural.setter
    def model_name_plural(self, value: str):
        """
        This is read-only but we don't want an error during serialization
        """
        pass

    @property
    def table_name(self) -> str | None:
        """
        Returns the table name for this model.
        This is useful if you create multiple tables
        For a single table design you can leave this as null
        """
        return self._table_name

    @table_name.setter
    def table_name(self, value: str | None):
        """
        Defines the table name for this model
        """
        self._table_name = value

    
    @property
    def metadata(self) -> Dict[str, Any] | None:
        """
        Returns the metadata for this model
        """
        return self._metadata
    
    @metadata.setter
    def metadata(self, value: Dict[str, Any] | None):
        """
        Defines the metadata for this model
        """

        if value is not None and not isinstance(value, dict):
            raise ValueError("metadata must be a dictionary")

        self._metadata = value

    def get_pk_id(self) -> str:
        """
        Returns the fully formed primary key for this model.
        This is typically in the form of "<resource_type>#<guid>"
        """
        pk = self.to_resource_dictionary().get("pk", None)
        if not pk:
            raise ValueError("The primary key is not set")
        return pk

    def get_sk_id(self) -> str | None:
        """
        Returns the fully formed sort key for this model.
        This is typically in the form of "<resource_type>#<guid>"
        """
        sk = self.to_resource_dictionary().get("sk", None)
        
        return sk

    def to_float_or_none(self, value: Any) -> float | None:
        """
        Converts a value to a float or None
        """
        if isinstance(value, str):
            value = value.strip().replace("$", "").replace(",", "").replace(".", "")

        if value is None:
            return None
        try:
            return float(value)
        except:
            return None

    @classmethod
    def load(cls, payload: Dict[str, Any]) -> 'BaseDBModel':
        """
        Create a model instance from a UI payload (camelCase).
        Automatically converts camelCase to snake_case before model creation.
        
        Args:
            payload: Dictionary with camelCase keys from the UI
            
        Returns:
            Model instance with data loaded from the converted payload
            
        Raises:
            ValueError: If payload is None or not a dictionary
        """
        if payload is None:
            raise ValueError("Payload cannot be None")
        if not isinstance(payload, dict):
            raise ValueError(f"Payload must be a dictionary, got {type(payload)}")
        
        # Convert camelCase to snake_case
        snake_case_payload = JsonConversions.json_camel_to_snake(payload)
        
        # Create instance and load data
        instance = cls()
        instance.load_from_dictionary(snake_case_payload)
        return instance

    def to_camel_case(self) -> Dict[str, Any]:
        """
        Convert model to UI payload format (camelCase).
        Automatically converts snake_case to camelCase for UI consumption.
        
        Returns:
            Dictionary with camelCase keys for the UI
        """
        # Get the model as a dictionary
        model_dict = self.to_dictionary()
        
        # Convert snake_case to camelCase
        return JsonConversions.json_snake_to_camel(model_dict)

    @staticmethod
    def to_snake_case(payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Static method to convert UI payload to backend format.
        Useful for preprocessing payloads before model operations.
        
        Args:
            payload: Dictionary with camelCase keys from the UI
            
        Returns:
            Dictionary with snake_case keys for backend processing
        """
        if payload is None:
            raise ValueError("Payload cannot be None")
        if not isinstance(payload, dict):
            raise ValueError(f"Payload must be a dictionary, got {type(payload)}")
            
        return JsonConversions.json_camel_to_snake(payload)

    @property
    def created_utc_ts(self) -> float | None:
        """
        Returns the created UTC timestamp
        """
        return self._created_utc_ts

    @created_utc_ts.setter
    def created_utc_ts(self, value: float | None):
        """
        Sets the created UTC timestamp
        """
        
        self._created_utc_ts = self._safe_number_conversion(value)


    @property
    def created_utc(self) -> dt.datetime | None:
        """
        Returns the created UTC timestamp
        """
        return self.created_utc_ts and dt.datetime.fromtimestamp(self.created_utc_ts, dt.UTC)
    
    @created_utc.setter
    def created_utc(self, value: Any | None):
        """
        Sets the created UTC timestamp
        """
        pass

    @property
    def modified_utc_ts(self) -> float | None:
        """
        Returns the updated UTC timestamp
        """
        return self._modified_utc_ts

    @modified_utc_ts.setter
    def modified_utc_ts(self, value: float | None):
        """
        Sets the updated UTC timestamp
        """

        self._modified_utc_ts = self._safe_number_conversion(value)

    @property
    def modified_utc(self) -> dt.datetime | None:
        """
        Returns the updated UTC timestamp
        """
        return self.modified_utc_ts and dt.datetime.fromtimestamp(self.modified_utc_ts, dt.UTC)
    
    @modified_utc.setter
    def modified_utc(self, value: Any | None):
        """
        Sets the updated UTC timestamp
        """
        pass

    @property
    def deleted_utc_ts(self) -> float | None:
        """
        Returns the deleted UTC timestamp
        """
        return self._deleted_utc_ts

    @deleted_utc_ts.setter
    def deleted_utc_ts(self, value: float | None):
        """
        Sets the deleted UTC timestamp
        """
        self._deleted_utc_ts = self._safe_number_conversion(value)


    @property
    def deleted_utc(self) -> dt.datetime | None:
        """
        Returns the deleted UTC timestamp
        """
        return self.deleted_utc_ts and dt.datetime.fromtimestamp(self.deleted_utc_ts, dt.UTC)
    
    @deleted_utc.setter
    def deleted_utc(self, value: Any | None):
        """
        Sets the deleted UTC timestamp
        """
        pass


    def set_metadata_key(self, key: str, value: str| Dict[str, Any]) -> None:
        """
        Set metadata value for a specific key
        
        Args:
            key: The key to set
            value: The value (e.g., "")
            
        Example:
            obj.set_metadata("review_status", "approved")
            obj.set_metadata("tags", {"category": "finance", "priority": 1})
        """
        if self._metadata is None:
            self._metadata = {}
        self._metadata[key] = value
    
    def get_metadata_key(self, key: str) -> str| Dict[str,Any] | None:
        """
        Get metadata for a specific key
        
        Args:
            key: The key to check
            
        Returns:
            Status string or None if not set
        """
        if self._metadata is None:
            return None
        return self._metadata.get(key)

    def _safe_number_conversion(self, value: Any | None) -> float | int | None:
        if value is not None and not isinstance(value, (int, float)):
            # attempt to convert to a float
            try:
                value = float(value)
            except:
                value = 0
        return value

    
    def _safe_date_conversion(self, value: dt.datetime | str | None) -> dt.datetime | None:
        value = DatetimeUtility.to_datetime_utc(value)
        return value

    
    @property
    def errors(self) -> Dict[str, Any] | None:
        """
        Returns the metadata for this model
        """
        return self._errors
    
    @errors.setter
    def errors(self, value: Dict[str, Any] | None):
        """
        Defines the metadata for this model
        """

        if value is not None and not isinstance(value, dict):
            raise ValueError("errors must be a dictionary")

        self._errors = value

    
    def set_error_key(self, key: str, value: str| Dict[str, Any]) -> None:
        """
        Set error value for a specific key
        
        Args:
            key: The key to set
            value: The value (e.g., "")
            
        Example:
            obj.set_error("review_status", "approved")
            obj.set_error("tags", {"category": "finance", "priority": 1})
        """
        if self._errors is None:
            self._errors = {}
        self._errors[key] = value
    
    def get_error_key(self, key: str) -> str| Dict[str,Any] | None:
        """
        Get error for a specific key
        
        Args:
            key: The key to check
            
        Returns:
            Status string or None if not set
        """
        if self._errors is None:
            return None
        return self._errors.get(key)

    @exclude_from_serialization
    def class_name(self) -> str:
        """
        Returns the class name for this model
        """
        return self.__class__.__name__