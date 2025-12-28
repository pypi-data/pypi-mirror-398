"""
S3 Event Parser - Centralized parsing of S3 Lambda event payloads.

Provides standardized methods for parsing S3 event records from Lambda triggers.
Extracts bucket, key, and file metadata from S3 notification events.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

from typing import Dict, Any, List, Optional, Union, TYPE_CHECKING
from dataclasses import dataclass, field
from urllib.parse import unquote_plus

from geek_cafe_saas_sdk.utilities.datetime_utility import DatetimeUtility
from geek_cafe_saas_sdk.core.error_codes import ErrorCode
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.modules.file_system.services.s3_path_service import (
    S3PathService,
    S3PathComponents,
)
from geek_cafe_saas_sdk.modules.file_system.models.file import File

if TYPE_CHECKING:
    from geek_cafe_saas_sdk.lambda_handlers._base.lambda_event import LambdaEvent


@dataclass
class S3EventRecord:
    """Parsed S3 event record with all relevant fields."""
    
    # Core S3 data
    bucket_name: str
    object_key: str
    size: int
    etag: str
    
    # Event metadata
    event_name: str
    event_time: Optional[str] = None
    event_source: str = "aws:s3"
    aws_region: str = "us-east-1"
    
    # Request/response info
    source_ip: Optional[str] = None
    request_id: Optional[str] = None
    
    # Version info (for versioned buckets)
    version_id: Optional[str] = None
    
    # Parsed path components (populated if key matches expected pattern)
    path_components: Optional[S3PathComponents] = None
    
    # Raw record for access to any additional fields
    raw_record: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_create_event(self) -> bool:
        """Check if this is an object creation event."""
        return self.event_name.startswith("ObjectCreated:")
    
    @property
    def is_delete_event(self) -> bool:
        """Check if this is an object deletion event."""
        return self.event_name.startswith("ObjectRemoved:")
    
    @property
    def is_copy_event(self) -> bool:
        """Check if this is an object copy event."""
        return self.event_name == "ObjectCreated:Copy"
    
    @property
    def tenant_id(self) -> Optional[str]:
        """Get tenant ID from path components if available."""
        return self.path_components.tenant_id if self.path_components else None
    
    @property
    def user_id(self) -> Optional[str]:
        """Get user ID from path components if available."""
        return self.path_components.user_id if self.path_components else None
    
    @property
    def file_id(self) -> Optional[str]:
        """Get file ID from path components if available."""
        return self.path_components.file_id if self.path_components else None
    
    @property
    def file_name(self) -> Optional[str]:
        """Get file name from path components if available."""
        return self.path_components.file_name if self.path_components else None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = {
            "bucket_name": self.bucket_name,
            "object_key": self.object_key,
            "size": self.size,
            "etag": self.etag,
            "event_name": self.event_name,
            "event_time": self.event_time,
            "event_source": self.event_source,
            "aws_region": self.aws_region,
            "source_ip": self.source_ip,
            "request_id": self.request_id,
            "version_id": self.version_id,
            "is_create_event": self.is_create_event,
            "is_delete_event": self.is_delete_event,
        }
        
        if self.path_components:
            result["path_components"] = self.path_components.to_dict()
            result["tenant_id"] = self.tenant_id
            result["user_id"] = self.user_id
            result["file_id"] = self.file_id
            result["file_name"] = self.file_name
        
        return result

    def to_file(self, file: Optional[File] = None) -> File:
        """
        Convert S3EventRecord to a File model with basic properties.
        
        Maps the parsed S3 event data to a File model. The calling service
        should handle any additional business logic (generating IDs, setting
        state, timestamps, etc.).
        
        Returns:
            File model populated with S3 event data
            
        Raises:
            ValueError: If object_key or bucket_name is missing
        """
        if not self.object_key:
            raise ValueError("Key is required")
        if not self.bucket_name:
            raise ValueError("Bucket name is required")
        
        if file is None:
            file = File()
        file.key = self.object_key
        file.bucket = self.bucket_name
        file.tenant_id = self.tenant_id
        file.user_id = self.user_id
        file.id = self.file_id
        file.name = self.file_name
        file.version_id = self.version_id
        file.size = self.size
        file.uploaded_utc = DatetimeUtility.to_datetime_utc(self.event_time)
        file.uploaded_utc_ts = DatetimeUtility.to_timestamp_utc(self.event_time)
        
        return file

class S3EventParser:
    """
    Centralized S3 event parser for Lambda handlers.
    
    Supports TWO event formats:
    
    1. S3 Direct Notification (Records format):
       {"Records": [{"s3": {"bucket": {...}, "object": {...}}}]}
    
    2. EventBridge S3 Event (detail format):
       {"detail-type": "Object Created", "detail": {"bucket": {...}, "object": {...}}}
    
    Usage:
        # Parse entire event (auto-detects format)
        result = S3EventParser.parse_event(event)
        if result.success:
            for record in result.data:
                print(f"File: {record.object_key}")
                print(f"Tenant: {record.tenant_id}")
        
        # Parse single record (S3 direct format)
        record_result = S3EventParser.parse_record(event["Records"][0])
        
        # Parse EventBridge event
        record_result = S3EventParser.parse_eventbridge_event(event)
    """
    
    @staticmethod
    def _normalize_event(event: Union[Dict[str, Any], "LambdaEvent", None]) -> Optional[Dict[str, Any]]:
        """
        Normalize event input to a raw dictionary.
        
        Handles:
        - Raw dict: returned as-is
        - LambdaEvent: extracts .raw property
        - None: returns None
        
        Args:
            event: Raw dict, LambdaEvent object, or None
            
        Returns:
            Raw event dictionary or None
        """
        if event is None:
            return None
        
        # Check if it's a LambdaEvent by duck-typing (has .raw property)
        if hasattr(event, 'raw') and callable(getattr(type(event), 'raw', None).__get__):
            return event.raw
        
        # Check for _event attribute (internal LambdaEvent storage)
        if hasattr(event, '_event'):
            return event._event
        
        # Assume it's already a dict
        return event
    
    @staticmethod
    def parse_event(event: Union[Dict[str, Any], "LambdaEvent", None]) -> ServiceResult[List[S3EventRecord]]:
        """
        Parse an S3 event, auto-detecting the format.
        
        Supports:
        - S3 Direct Notification: {"Records": [...]}
        - EventBridge S3 Event: {"detail-type": "Object Created", "detail": {...}}
        - LambdaEvent wrapper: extracts raw event automatically
        
        Args:
            event: Lambda event dict, LambdaEvent object, or either format
            
        Returns:
            ServiceResult containing list of S3EventRecord objects
            
        Example:
            >>> result = S3EventParser.parse_event(event)
            >>> for record in result.data:
            ...     print(record.object_key)
            
            >>> # Also works with LambdaEvent wrapper
            >>> lambda_event = LambdaEvent(raw_event)
            >>> result = S3EventParser.parse_event(lambda_event)
        """
        # Normalize to raw dict
        raw_event = S3EventParser._normalize_event(event)
        
        if not raw_event:
            return ServiceResult.error_result(
                message="Event is empty or None",
                error_code=ErrorCode.VALIDATION_ERROR
            )
        
        # Auto-detect format: EventBridge has "detail-type" and "detail"
        if "detail-type" in raw_event and "detail" in raw_event:
            result = S3EventParser.parse_eventbridge_event(raw_event)
            if result.success:
                return ServiceResult.success_result([result.data])
            return ServiceResult.error_result(
                message=result.message,
                error_code=result.error_code
            )
        
        # S3 Direct Notification format with Records array
        records = raw_event.get("Records", [])
        if not records:
            return ServiceResult.error_result(
                message="No Records found in event. Expected 'Records' array (S3 direct) or 'detail-type'/'detail' (EventBridge)",
                error_code=ErrorCode.VALIDATION_ERROR
            )
        
        parsed_records: List[S3EventRecord] = []
        errors: List[str] = []
        
        for i, raw_record in enumerate(records):
            result = S3EventParser.parse_record(raw_record)
            if result.success:
                parsed_records.append(result.data)
            else:
                errors.append(f"Record {i}: {result.message}")
        
        if not parsed_records and errors:
            return ServiceResult.error_result(
                message=f"Failed to parse all records: {'; '.join(errors)}",
                error_code=ErrorCode.VALIDATION_ERROR
            )
        
        return ServiceResult.success_result(parsed_records)
    
    @staticmethod
    def parse_eventbridge_event(event: Dict[str, Any]) -> ServiceResult[S3EventRecord]:
        """
        Parse an EventBridge S3 event.
        
        EventBridge format:
        {
            "detail-type": "Object Created",
            "source": "aws.s3",
            "time": "2025-12-09T22:19:45Z",
            "detail": {
                "bucket": {"name": "bucket-name"},
                "object": {"key": "path/to/file.txt", "size": 1234, "etag": "..."}
            }
        }
        
        Args:
            event: EventBridge event dict
            
        Returns:
            ServiceResult containing S3EventRecord object
        """
        if not event:
            return ServiceResult.error_result(
                message="Event is empty or None",
                error_code=ErrorCode.VALIDATION_ERROR
            )
        
        try:
            detail = event.get("detail", {})
            if not detail:
                return ServiceResult.error_result(
                    message="No 'detail' found in EventBridge event",
                    error_code=ErrorCode.VALIDATION_ERROR
                )
            
            # Get bucket info
            bucket_data = detail.get("bucket", {})
            bucket_name = bucket_data.get("name")
            if not bucket_name:
                return ServiceResult.error_result(
                    message="Missing bucket name in EventBridge event",
                    error_code=ErrorCode.VALIDATION_ERROR
                )
            
            # Get object info
            object_data = detail.get("object", {})
            raw_key = object_data.get("key")
            if not raw_key:
                return ServiceResult.error_result(
                    message="Missing object key in EventBridge event",
                    error_code=ErrorCode.VALIDATION_ERROR
                )
            
            # URL-decode the key
            object_key = unquote_plus(raw_key)
            
            # Extract object metadata
            size = object_data.get("size", 0)
            etag = object_data.get("etag", "")
            version_id = object_data.get("version-id")
            
            # Map EventBridge detail-type to S3 event name
            detail_type = event.get("detail-type", "Unknown")
            event_name = S3EventParser._map_eventbridge_detail_type(detail_type)
            
            # Extract event metadata
            event_time = event.get("time")
            event_source = event.get("source", "aws.s3")
            aws_region = event.get("region", "us-east-1")
            
            # Extract request info from detail
            source_ip = detail.get("source-ip-address")
            request_id = detail.get("request-id")
            
            # Try to parse path components
            path_components = None
            path_result = S3PathService.parse_path(object_key)
            if path_result.success:
                path_components = path_result.data
            
            # Build the parsed record
            parsed_record = S3EventRecord(
                bucket_name=bucket_name,
                object_key=object_key,
                size=size,
                etag=etag,
                event_name=event_name,
                event_time=event_time,
                event_source=event_source,
                aws_region=aws_region,
                source_ip=source_ip,
                request_id=request_id,
                version_id=version_id,
                path_components=path_components,
                raw_record=event,
            )
            
            return ServiceResult.success_result(parsed_record)
            
        except Exception as e:
            return ServiceResult.error_result(
                message=f"Failed to parse EventBridge event: {str(e)}",
                error_code=ErrorCode.INTERNAL_ERROR
            )
    
    @staticmethod
    def _map_eventbridge_detail_type(detail_type: str) -> str:
        """Map EventBridge detail-type to S3 event name."""
        mapping = {
            "Object Created": "ObjectCreated:Put",
            "Object Deleted": "ObjectRemoved:Delete",
            "Object Restore Initiated": "ObjectRestore:Post",
            "Object Restore Completed": "ObjectRestore:Completed",
            "Object Restore Expired": "ObjectRestore:Delete",
            "Object Tags Added": "ObjectTagging:Put",
            "Object Tags Deleted": "ObjectTagging:Delete",
            "Object ACL Updated": "ObjectAcl:Put",
        }
        return mapping.get(detail_type, f"EventBridge:{detail_type}")
    
    @staticmethod
    def parse_record(record: Dict[str, Any]) -> ServiceResult[S3EventRecord]:
        """
        Parse a single S3 event record.
        
        Args:
            record: Single record from S3 event Records array
            
        Returns:
            ServiceResult containing S3EventRecord object
        """
        if not record:
            return ServiceResult.error_result(
                message="Record is empty or None",
                error_code=ErrorCode.VALIDATION_ERROR
            )
        
        try:
            # Extract S3 data
            s3_data = record.get("s3", {})
            if not s3_data:
                return ServiceResult.error_result(
                    message="No s3 data in record",
                    error_code=ErrorCode.VALIDATION_ERROR
                )
            
            # Get bucket info
            bucket_data = s3_data.get("bucket", {})
            bucket_name = bucket_data.get("name")
            if not bucket_name:
                return ServiceResult.error_result(
                    message="Missing bucket name in record",
                    error_code=ErrorCode.VALIDATION_ERROR
                )
            
            # Get object info
            object_data = s3_data.get("object", {})
            raw_key = object_data.get("key")
            if not raw_key:
                return ServiceResult.error_result(
                    message="Missing object key in record",
                    error_code=ErrorCode.VALIDATION_ERROR
                )
            
            # URL-decode the key (S3 events have URL-encoded keys)
            object_key = unquote_plus(raw_key)
            
            # Extract other object metadata
            size = object_data.get("size", 0)
            etag = object_data.get("eTag", "")
            version_id = object_data.get("versionId")
            
            # Extract event metadata
            event_name = record.get("eventName", "Unknown")
            event_time = record.get("eventTime")
            event_source = record.get("eventSource", "aws:s3")
            aws_region = record.get("awsRegion", "us-east-1")
            
            # Extract request info
            request_params = record.get("requestParameters", {})
            source_ip = request_params.get("sourceIPAddress")
            
            response_elements = record.get("responseElements", {})
            request_id = response_elements.get("x-amz-request-id")
            
            # Try to parse path components
            path_components = None
            path_result = S3PathService.parse_path(object_key)
            if path_result.success:
                path_components = path_result.data
            
            # Build the parsed record
            parsed_record = S3EventRecord(
                bucket_name=bucket_name,
                object_key=object_key,
                size=size,
                etag=etag,
                event_name=event_name,
                event_time=event_time,
                event_source=event_source,
                aws_region=aws_region,
                source_ip=source_ip,
                request_id=request_id,
                version_id=version_id,
                path_components=path_components,
                raw_record=record,
            )
            
            return ServiceResult.success_result(parsed_record)
            
        except Exception as e:
            return ServiceResult.error_result(
                message=f"Failed to parse record: {str(e)}",
                error_code=ErrorCode.INTERNAL_ERROR
            )
    
    @staticmethod
    def extract_file_info(event: Dict[str, Any]) -> ServiceResult[List[Dict[str, Any]]]:
        """
        Extract simplified file info from S3 event.
        
        Convenience method that returns just the essential file information
        without the full S3EventRecord structure.
        
        Args:
            event: Lambda event dict containing S3 Records
            
        Returns:
            ServiceResult containing list of file info dicts with keys:
            - bucket, key, size, etag, tenant_id, user_id, file_id, file_name
        """
        result = S3EventParser.parse_event(event)
        if not result.success:
            return result
        
        file_infos = []
        for record in result.data:
            info = {
                "bucket": record.bucket_name,
                "key": record.object_key,
                "size": record.size,
                "etag": record.etag,
                "event_name": record.event_name,
                "event_time": record.event_time,
            }
            
            # Add path components if available
            if record.path_components:
                info.update({
                    "tenant_id": record.tenant_id,
                    "user_id": record.user_id,
                    "file_id": record.file_id,
                    "file_name": record.file_name,
                })
            
            file_infos.append(info)
        
        return ServiceResult.success_result(file_infos)
    
    @staticmethod
    def filter_by_event_type(
        records: List[S3EventRecord],
        event_type: str
    ) -> List[S3EventRecord]:
        """
        Filter records by event type prefix.
        
        Args:
            records: List of S3EventRecord objects
            event_type: Event type prefix (e.g., "ObjectCreated", "ObjectRemoved")
            
        Returns:
            Filtered list of records
        """
        return [r for r in records if r.event_name.startswith(event_type)]
    
    @staticmethod
    def filter_creates(records: List[S3EventRecord]) -> List[S3EventRecord]:
        """Filter to only ObjectCreated events."""
        return [r for r in records if r.is_create_event]
    
    @staticmethod
    def filter_deletes(records: List[S3EventRecord]) -> List[S3EventRecord]:
        """Filter to only ObjectRemoved events."""
        return [r for r in records if r.is_delete_event]
