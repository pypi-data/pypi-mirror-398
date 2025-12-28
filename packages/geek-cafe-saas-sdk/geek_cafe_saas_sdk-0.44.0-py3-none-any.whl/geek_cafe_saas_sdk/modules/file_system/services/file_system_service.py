"""
FileSystemService for file CRUD operations with S3 and DynamoDB.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

from typing import Dict, Any, Optional, List
from boto3.dynamodb.conditions import Key
from boto3_assist.dynamodb.dynamodb import DynamoDB
from geek_cafe_saas_sdk.core.services.database_service import DatabaseService
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.lambda_handlers._base.decorators import service_method
from geek_cafe_saas_sdk.core.error_codes import ErrorCode
from geek_cafe_saas_sdk.core.service_errors import (
    ValidationError,
    NotFoundError,
    AccessDeniedError,
)
from geek_cafe_saas_sdk.core.request_context import RequestContext
from geek_cafe_saas_sdk.core.model_field_validator import ModelFieldValidator
from geek_cafe_saas_sdk.core.field_transformer import FieldTransformer
from geek_cafe_saas_sdk.modules.file_system.models.file import File
from geek_cafe_saas_sdk.modules.file_system.services.s3_file_service import (
    S3FileService,
)
from geek_cafe_saas_sdk.modules.file_system.services.s3_path_service import (
    S3PathService,
)
from geek_cafe_saas_sdk.modules.file_system.services.directory_service import (
    DirectoryService,
)
from geek_cafe_saas_sdk.modules.file_system.services.file_share_service import (
    FileShareService,
)
from geek_cafe_saas_sdk.core.services.resource_meta_entry_service import (
    ResourceMetaEntryService,
)

import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class FileSystemService(DatabaseService[File]):
    """
    File system service for managing files with S3 storage and DynamoDB metadata.

    Handles:
    - File uploads with metadata storage
    - File downloads with access control
    - File metadata CRUD operations
    - Directory assignment
    - Versioning strategy management
    """

    def __init__(
        self,
        *,
        dynamodb: Optional[DynamoDB] = None,
        table_name: Optional[str] = None,
        s3_service: Optional[S3FileService] = None,
        default_bucket: Optional[str] = None,
        request_context: RequestContext,
    ):
        """
        Initialize FileSystemService.

        Args:
            dynamodb: DynamoDB instance
            table_name: DynamoDB table name
            s3_service: S3FileService instance
            default_bucket: Default S3 bucket
            request_context: Security context (REQUIRED) - refreshed per-invocation by ServicePool
        """
        super().__init__(
            dynamodb=dynamodb, table_name=table_name, request_context=request_context
        )
        self._s3_service = s3_service
        self._default_bucket = default_bucket or os.getenv("S3_FILE_BUCKET")
        
        # Lazy-loaded sub-services
        self._directory_service: Optional[DirectoryService] = None
        self._file_share_service: Optional[FileShareService] = None
        self._resource_meta_entry_service: Optional[ResourceMetaEntryService] = None

    @property
    def s3_service(self) -> S3FileService:
        """Lazy-loaded S3 file service."""
        if self._s3_service is None:
            self._s3_service = S3FileService(default_bucket=self._default_bucket)
        return self._s3_service

    @property
    def default_bucket(self) -> Optional[str]:
        """Default S3 bucket name."""
        return self._default_bucket

    @property
    def directory_service(self) -> DirectoryService:
        """Lazy-loaded directory service."""
        if self._directory_service is None:
            self._directory_service = DirectoryService(
                dynamodb=self.dynamodb,
                table_name=self.table_name,
                request_context=self.request_context,
            )
        return self._directory_service

    @property
    def file_share_service(self) -> FileShareService:
        """Lazy-loaded file share service."""
        if self._file_share_service is None:
            self._file_share_service = FileShareService(
                dynamodb=self.dynamodb,
                table_name=self.table_name,
                request_context=self.request_context,
            )
        return self._file_share_service

    @property
    def resource_meta_entry_service(self) -> ResourceMetaEntryService:
        """Lazy-loaded resource meta entry service."""
        if self._resource_meta_entry_service is None:
            self._resource_meta_entry_service = ResourceMetaEntryService(
                dynamodb=self.dynamodb,
                table_name=self.table_name,
                request_context=self.request_context,
                resource_type="file",
            )
        return self._resource_meta_entry_service

    def create(self, **kwargs) -> ServiceResult[File]:
        """
        Upload a file with metadata.

        Process:
        1. Validate fields (detect unknown fields)
        2. Transform data (base64 decode if needed)
        3. Map to model
        4. Auto-inject security context
        5. Validate business rules
        6. Upload to S3 (if data provided)
        7. Save metadata

        Args:
            **kwargs: File attributes from client
                     Security fields (tenant_id, owner_id) auto-injected from RequestContext

        Returns:
            ServiceResult with File model
        """
        try:
            # Chaos Engineering: Inject fault if configured
            if self._should_inject_chaos_fault("file_system_service.create"):
                return self._inject_chaos_fault("file_system_service.create")

            # STEP 1: Validate incoming fields against model
            validation_result = ModelFieldValidator.validate_fields(
                data=kwargs,
                model_class=File,
                allow_extra=False,  # Strict validation
                extras={"data"},  # Allow 'data' field for file upload
            )

            if not validation_result.is_valid:
                return ServiceResult.error_result(
                    message=validation_result.to_error_message(),
                    error_code=ErrorCode.VALIDATION_ERROR,
                    error_details={
                        "validation_errors": [
                            {
                                "field": err.field,
                                "type": err.error_type,
                                "message": err.message,
                            }
                            for err in validation_result.errors
                        ],
                        "supported_fields": ModelFieldValidator.get_supported_fields_list(
                            File, extras={"data"}
                        ),
                    },
                )

            # STEP 2: Transform data (base64 decode if needed)
            transformed_data = FieldTransformer.transform_for_file(kwargs)

            # STEP 3: Map to model
            file = File().map(transformed_data)

            if file.parent_id:
                parent_result = self.get_by_id(file_id=file.parent_id)
                if not parent_result.success:
                    return ServiceResult.error_result(
                        message="Parent file not found", error_code=ErrorCode.NOT_FOUND
                    )
                if file.root_id != parent_result.data.root_id:
                    logger.warning(
                        f"Parent file {file.parent_id} has different "
                        f"root_id {parent_result.data.root_id} than file {file.id}. "
                        f"Auto-correcting root_id to {parent_result.data.root_id}"
                    )
                    file.root_id = parent_result.data.root_id

            # STEP 4: Auto-inject security context
            if self.request_context:
                if not file.tenant_id:
                    file.tenant_id = self.request_context.target_tenant_id
                if not file.owner_id:
                    file.owner_id = self.request_context.target_user_id

            # STEP 5: Validate business rules
            self._validate_file_creation(file)

            # STEP 6: Validate security access
            if self.request_context and file.tenant_id:
                if not self.request_context.validate_tenant_access(file.tenant_id):
                    return ServiceResult.error_result(
                        message="Access denied to tenant",
                        error_code=ErrorCode.ACCESS_DENIED,
                    )

            # data is not required - file may have been uploaded via presigned url
            data = transformed_data.get("data")

            # Prepare for save to make sure we have values set
            file.prep_for_save()

            # Build virtual path
            if file.directory_id:
                directory_result = self.directory_service.get_by_id(
                    directory_id=file.directory_id
                )
                if directory_result.success:
                    file.virtual_path = (
                        f"/{directory_result.data.full_path}/{file.name}"
                    )
                else:
                    file.virtual_path = f"/{file.name}"
            else:
                file.virtual_path = f"/{file.name}"

            # STEP 7: Handle S3 upload (if data provided)
            if data:
                upload_result = self._upload_file_to_s3(file, data)
                if not upload_result.success:
                    return upload_result
            else:
                # Presigned URL workflow - file already in S3, so we need it here to save the file entry
                if not file.bucket or not file.key:
                    return ServiceResult.error_result(
                        message="bucket and key are required when data is not provided (presigned URL workflow)",
                        error_code=ErrorCode.VALIDATION_ERROR,
                    )

            # STEP 8: Save metadata to DynamoDB
            save_result = self._save_model(file)

            if not save_result.success:
                return save_result

            return ServiceResult.success_result(file)

        except ValidationError as e:
            return ServiceResult.error_result(
                message=str(e), error_code=ErrorCode.VALIDATION_ERROR
            )
        except Exception as e:
            return ServiceResult.exception_result(
                exception=e,
                error_code=ErrorCode.INTERNAL_ERROR,
                context="FileSystemService.create",
            )

    def save(self, file: File) -> ServiceResult[File]:
        """
        Upsert a file - create if new, update if exists.

        This method is designed for system-triggered operations (S3 events, etc.)
        where the file model is already populated and just needs to be persisted.

        Unlike create(), this method:
        - Accepts a File model directly (not kwargs)
        - Does NOT upload to S3 (assumes file is already there)
        - Does NOT require data field
        - Performs upsert (insert or update)

        For system-triggered operations, use SystemRequestContext:
            from geek_cafe_saas_sdk.core.system_request_context import SystemRequestContext

            context = SystemRequestContext(tenant_id="...", user_id="...", source="s3-upload")
            service = FileSystemService(request_context=context)
            result = service.save(file=file_model)

        Args:
            file: File model to save (must have tenant_id, id, bucket, key set)

        Returns:
            ServiceResult with saved File model
        """
        try:

            # do we have an saved version of this file?
            if file.id:
                existing = self.get_by_id(file_id=file.id)
                if existing.data:
                    file = existing.data.merge(file)

            # Validate required fields for save
            if not file.tenant_id:
                return ServiceResult.error_result(
                    message="tenant_id is required",
                    error_code=ErrorCode.VALIDATION_ERROR,
                )

            if not file.id:
                return ServiceResult.error_result(
                    message="file id is required", error_code=ErrorCode.VALIDATION_ERROR
                )

            # Validate security access (if request_context is available)
            if self.request_context and file.tenant_id:
                if not self.request_context.validate_tenant_access(file.tenant_id):
                    return ServiceResult.error_result(
                        message="Access denied to tenant",
                        error_code=ErrorCode.ACCESS_DENIED,
                    )

            # Auto-inject owner_id from context if not set
            if not file.owner_id and self.request_context:
                file.owner_id = self.request_context.target_user_id

            # Prepare for save (sets timestamps, generates keys, etc.)
            file.prep_for_save()

            # Set version_id if not already set
            if not file.version_id:
                file.version_id = file.id

            # Build virtual path if not set
            if not file.virtual_path and file.name:
                if file.directory_id:
                    directory_result = self.directory_service.get_by_id(
                        directory_id=file.directory_id
                    )
                    if directory_result.success:
                        file.virtual_path = (
                            f"/{directory_result.data.full_path}/{file.name}"
                        )
                    else:
                        file.virtual_path = f"/{file.name}"
                else:
                    file.virtual_path = f"/{file.name}"

            # Save to DynamoDB (upsert - DynamoDB put_item is idempotent)
            save_result = self._save_model(file)

            if not save_result.success:
                return save_result

            logger.info(
                f"File saved: id={file.id}, tenant={file.tenant_id}"
            )

            return ServiceResult.success_result(file)

        except ValidationError as e:
            return ServiceResult.error_result(
                message=str(e), error_code=ErrorCode.VALIDATION_ERROR
            )
        except AccessDeniedError as e:
            return ServiceResult.error_result(
                message=str(e), error_code=ErrorCode.ACCESS_DENIED
            )
        except Exception as e:
            return ServiceResult.exception_result(
                exception=e,
                error_code=ErrorCode.INTERNAL_ERROR,
                context="FileSystemService.save",
            )

    def _upload_file_to_s3(self, file: File, data: bytes) -> ServiceResult:
        """
        Upload file to S3.

        Args:
            file: File model with S3 key and data

        Returns:
            ServiceResult with S3 upload result
        """
        try:
            if not file.bucket:
                file.bucket = self.default_bucket

            if not file.key:
                file.key = self._generate_s3_key(file)

            if not file.bucket:
                return ServiceResult.error_result(
                    message="bucket is required when uploading file to S3",
                    error_code=ErrorCode.VALIDATION_ERROR,
                )

            if not file.key:
                return ServiceResult.error_result(
                    message="key is required when uploading file to S3",
                    error_code=ErrorCode.VALIDATION_ERROR,
                )

            if not data:
                return ServiceResult.error_result(
                    message="data is required when uploading file to S3",
                    error_code=ErrorCode.VALIDATION_ERROR,
                )

            # Upload to S3
            upload_result = self.s3_service.upload_file(
                file_data=data, key=file.key, bucket=file.bucket
            )

            if not upload_result.success:
                return ServiceResult.error_result(
                    message=f"Failed to upload file to S3: {upload_result.message}",
                    error_code=upload_result.error_code,
                )

            # Set file size from data
            file.size = len(data)

            return ServiceResult.success_result(upload_result.data)
        except Exception as e:
            return ServiceResult.exception_result(
                exception=e,
                error_code=ErrorCode.INTERNAL_ERROR,
                context="FileSystemService._upload_file_to_s3",
            )

    def get_by_id(self, **kwargs) -> ServiceResult[File]:
        """
        Get file by ID with access control.

        Args:
            **kwargs: Flexible parameters
                file_id: File ID (required)
                # tenant_id and user_id auto-injected from self.request_context

        Returns:
            ServiceResult with File model
        """
        try:
            # Extract required parameters
            file_id = kwargs.get("file_id")            

            # Validate required fields
            if not file_id:
                return ServiceResult.error_result(
                    message="file_id is required", error_code=ErrorCode.VALIDATION_ERROR
                )

            # Chaos Engineering: Inject fault if configured
            if self._should_inject_chaos_fault("file_system_service.get_by_id"):
                return self._inject_chaos_fault("file_system_service.get_by_id")

            # Use helper method with tenant check
            file = self._get_by_id(file_id, File)

            # Check if file exists
            if not file:
                raise NotFoundError(f"File not found: {file_id}")            

            return ServiceResult.success_result(file)

        except NotFoundError as e:
            return ServiceResult.error_result(
                message=str(e), error_code=ErrorCode.NOT_FOUND
            )
        except AccessDeniedError as e:
            return ServiceResult.error_result(
                message=str(e), error_code=ErrorCode.ACCESS_DENIED
            )
        except Exception as e:
            return ServiceResult.exception_result(
                exception=e,
                error_code=ErrorCode.INTERNAL_ERROR,
                context="FileSystemService.get_by_id",
            )

    def update(self, **kwargs) -> ServiceResult[File]:
        """
        Update file metadata.

        Args:
            **kwargs: Flexible parameters
                file_id: File ID (required)
                # tenant_id and user_id auto-injected from self.request_context
                <any other fields>: Update data (description, tags, directory_id, etc.)

        Returns:
            ServiceResult with updated File model
        """
        try:
            # Extract required parameters
            file_id = kwargs.get("file_id")

            # Get security context from self.request_context
            user_id = self.request_context.target_user_id

            # Validate required fields
            if not file_id:
                return ServiceResult.error_result(
                    message="file_id is required", error_code=ErrorCode.VALIDATION_ERROR
                )

            # Get existing file (uses self.request_context internally)
            get_result = self.get_by_id(file_id=file_id)
            if not get_result.success:
                return get_result

            file = get_result.data        

            # Extract update fields (everything except file_id)
            # items = kwargs.get('updates', {})
            updates = {k: v for k, v in kwargs.items() if k not in ["file_id"]}

            # Apply updates (only allowed fields)
            allowed_fields = [
                "name",
                "description",
                "tags",
                "directory_id",
                "status",
                "category",
                "metadata",
            ]

            # Track if GSI-affecting fields changed
            directory_changed = "directory_id" in updates
            name_changed = "name" in updates

            # Apply updates (only allowed fields)
            for field, value in updates.items():
                if field in allowed_fields:
                    setattr(file, field, value)

            # Update timestamp
            import datetime as dt

            file.modified_utc_ts = dt.datetime.now(dt.UTC).timestamp()

            # If directory or name changed, manually update the GSI1 lambda
            # because it was set during init and needs to be recreated with new values
            if directory_changed or name_changed:
                # get the directory
                directory_result = self.directory_service.get_by_id(
                    directory_id=file.directory_id
                )
                if not directory_result.success:
                    return directory_result

                directory = directory_result.data

                # update the file path
                file.virtual_path = f"{directory.full_path}/{file.name}"

                file.directory_id = directory.directory_id

            # Call prep_for_save() AFTER all properties are set
            file.prep_for_save()

            # Save to DynamoDB
            return self._save_model(file)

        except AccessDeniedError as e:
            return ServiceResult.error_result(
                message=str(e), error_code=ErrorCode.ACCESS_DENIED
            )
        except Exception as e:
            return ServiceResult.exception_result(
                exception=e,
                error_code=ErrorCode.INTERNAL_ERROR,
                context="FileSystemService.update",
            )

    def delete(self, **kwargs) -> ServiceResult[bool]:
        """
        Delete file (soft or hard delete).

        Args:
            **kwargs: Flexible parameters
                file_id: File ID (required)
                # tenant_id and user_id auto-injected from self.request_context
                hard_delete: If True, delete from S3 and DynamoDB (optional, default: False)

        Returns:
            ServiceResult with success boolean
        """
        try:
            # Extract required parameters
            file_id = kwargs.get("file_id")
            hard_delete = kwargs.get("hard_delete", False)

            # Get security context from self.request_context
            tenant_id = self.request_context.target_tenant_id
            user_id = self.request_context.target_user_id

            # Validate required fields
            if not file_id:
                return ServiceResult.error_result(
                    message="file_id is required", error_code=ErrorCode.VALIDATION_ERROR
                )

            # Get existing file (uses self.request_context internally)
            get_result = self.get_by_id(file_id=file_id)
            if not get_result.success:
                return get_result

            file = get_result.data
            

            if hard_delete:
                # Delete from S3

                # Delete from DynamoDB
                delete_result = self._delete_model(model=file)

                if not delete_result.success:
                    return delete_result

                if file.key:
                    delete_result = self.s3_service.delete_file(
                        key=file.key, bucket=file.bucket
                    )

                    if not delete_result.success:
                        return ServiceResult.error_result(
                            message=f"Failed to delete file from S3: {delete_result.message}",
                            error_code=delete_result.error_code,
                        )

                
            else:
                # Soft delete - update status
                import datetime as dt

                file.status = "deleted"
                file.deleted_utc_ts = dt.datetime.now(dt.UTC).timestamp()

                file.prep_for_save()
                save_result = self._save_model(file)

                if not save_result.success:
                    return save_result

            return ServiceResult.success_result(True)

        except AccessDeniedError as e:
            return ServiceResult.error_result(
                message=str(e), error_code=ErrorCode.ACCESS_DENIED
            )
        except Exception as e:
            return ServiceResult.exception_result(
                exception=e,
                error_code=ErrorCode.INTERNAL_ERROR,
                context="FileSystemService.delete",
            )

    def download_file(self, **kwargs) -> ServiceResult[Dict[str, Any]]:
        """
        Download file with access control.

        Args:
            **kwargs: Flexible parameters
                file_id: File ID (required)
                # tenant_id and user_id auto-injected from self.request_context

        Returns:
            ServiceResult with file data and metadata
        """
        try:
            # Extract required parameters
            file_id = kwargs.get("file_id")

            # Validate required fields
            if not file_id:
                return ServiceResult.error_result(
                    message="file_id is required", error_code=ErrorCode.VALIDATION_ERROR
                )

            # Get file metadata (uses self.request_context internally)
            get_result = self.get_by_id(file_id=file_id)
            if not get_result.success:
                return get_result

            file = get_result.data

            # Download from S3
            download_result = self.s3_service.download_file(
                key=file.key, bucket=file.bucket
            )

            if not download_result.success:
                return ServiceResult.error_result(
                    message=f"Failed to download file from S3: {download_result.message}",
                    error_code=download_result.error_code,
                )

            # Combine file data with metadata
            return ServiceResult.success_result(
                {
                    "file": file.to_dict(),
                    "path": download_result.data["path"]                    
                }
            )

        except Exception as e:
            return ServiceResult.exception_result(
                exception=e,
                error_code=ErrorCode.INTERNAL_ERROR,
                context="FileSystemService.download_file",
            )

    def stream_data(self, **kwargs) -> ServiceResult[Dict[str, Any]]:
        """
        Download file with access control.

        Args:
            **kwargs: Flexible parameters
                file_id: File ID (required)
                # tenant_id and user_id auto-injected from self.request_context

        Returns:
            ServiceResult with file data and metadata
        """
        try:
            # Extract required parameters
            file_id = kwargs.get("file_id")

            # Validate required fields
            if not file_id:
                return ServiceResult.error_result(
                    message="Internal error: missing required parameter: file_id", error_code=ErrorCode.MISSING_REQUIRED_FIELD, 
                    message_details= {
                        "parameters_provided": kwargs,
                        "parameters_required": ["file_id"]
                    }
                )

            # Get file metadata (uses self.request_context internally)
            get_result = self.get_by_id(file_id=file_id)
            if not get_result.success:
                return get_result

            file = get_result.data

            # Download from S3
            stream_result = self.s3_service.stream_data(
                key=file.key, bucket=file.bucket
            )

            if not stream_result.success:
                return ServiceResult.error_result(
                    message=f"Failed to download file from S3: {stream_result.message}",
                    error_code=stream_result.error_code,
                )

            # Combine file data with metadata
            return ServiceResult.success_result(
                {
                    "id": file.id,
                    "name": file.name,
                    "data": stream_result.data["data"],
                    "content_type": stream_result.data.get(
                        "content_type", file.mime_type
                    ),
                    "size": stream_result.data.get("size", file.size),
                }
            )

        except Exception as e:
            return ServiceResult.exception_result(
                exception=e,
                error_code=ErrorCode.INTERNAL_ERROR,
                context="FileSystemService.download_file",
            )

    def generate_download_url(self, **kwargs) -> ServiceResult[Dict[str, Any]]:
        """
        Generate presigned download URL with access control.

        Supports two modes:
        1. By file_id: Looks up file metadata (includes tenant access control)
        2. By bucket + key: Direct S3 URL generation (no file metadata lookup)

        Args:
            **kwargs: Flexible parameters
                # Option 1: File ID (recommended - includes access control)
                file_id: File ID to look up

                # Option 2: Direct S3 path (use with caution - minimal access control)
                bucket: S3 bucket name
                key: S3 object key

                # Optional for both:
                file_name: Filename for Content-Disposition header (optional)
                expires_in: URL expiration in seconds (optional, default: 300)

                # tenant_id and user_id auto-injected from self.request_context

        Returns:
            ServiceResult with presigned URL data:
            {
                "download_url": "https://...",
                "expires_in": 300,
                "expires_at": "2024-01-01T12:00:00Z",
                "key": "...",
                "file_name": "...",
                "file_id": "..." (if file_id was provided)
            }
        """
        try:
            # Extract parameters
            file_id = kwargs.get("file_id")
            bucket = kwargs.get("bucket")
            key = kwargs.get("key")
            file_name = kwargs.get("file_name")
            expires_in = kwargs.get("expires_in")

            # Determine mode: file_id OR (bucket + key)
            if file_id:
                # Mode 1: Lookup file by ID (includes tenant access control)
                get_result = self.get_by_id(file_id=file_id)
                if not get_result.success:
                    return get_result

                file = get_result.data

                # Extract S3 location from file model
                bucket = file.bucket
                key = file.key
                file_name = file_name or file.name  # Use file.name if not provided

            elif bucket and key:
                # Mode 2: Direct bucket/key with access control validation
                # Validate user has access to this S3 key path
                # Raises AccessDeniedError if tenant/user doesn't match path
                self._validate_s3_key_access(key)

            else:
                # Neither mode provided
                return ServiceResult.error_result(
                    message="Either file_id or both bucket and key are required",
                    error_code=ErrorCode.VALIDATION_ERROR,
                    error_details={"field": "file_id or (bucket and key)"},
                )

            # Generate presigned URL via S3 service
            url_result = self.s3_service.generate_presigned_download_url(
                key=key, bucket=bucket, expires_in=expires_in, file_name=file_name
            )

            if not url_result.success:
                return url_result

            # Build enhanced response
            response_data = {
                "download_url": url_result.data.get("url"),
                "expires_in": url_result.data.get("expires_in"),
                "key": key,
                "file_name": file_name,
            }

            # Include file_id in response if it was used
            if file_id:
                response_data["file_id"] = file_id

            return ServiceResult.success_result(response_data)

        except ValidationError as e:
            return ServiceResult.error_result(
                message=str(e),
                error_code=ErrorCode.VALIDATION_ERROR,
                error_details={"field": getattr(e, "field", None)},
            )
        except AccessDeniedError as e:
            return ServiceResult.error_result(
                message=str(e), error_code=ErrorCode.ACCESS_DENIED
            )
        except Exception as e:
            return ServiceResult.exception_result(
                exception=e,
                error_code=ErrorCode.INTERNAL_ERROR,
                context="FileSystemService.generate_download_url",
            )

    def list_files_by_directory(self, **kwargs) -> ServiceResult[List[File]]:
        """
        List files in a directory.

        Args:
            **kwargs: Flexible parameters
                # tenant_id and user_id auto-injected from self.request_context
                directory_id: Directory ID, None for root (optional)
                limit: Maximum number of results (optional, default: 50)

        Returns:
            ServiceResult with list of File models
        """
        try:
            # Extract parameters
            directory_id = kwargs.get("directory_id")
            limit = kwargs.get("limit", 50)
            ascending = kwargs.get("ascending", False)
            # Get security context from self.request_context
            user_id = self.request_context.target_user_id

            # Use GSI1 to query files by directory
            temp_file = File()
            temp_file.owner_id = user_id
            temp_file.directory_id = directory_id  # None for root files

            # Query using helper method
            query_result = self._query_by_index(
                temp_file, "gsi6", limit=limit, ascending=ascending
            )

            if not query_result.success:
                return query_result

            # Filter results
            files = []
            for file in query_result.data:
                # Filter out deleted files and apply access control
                if file.status != "deleted" and file.owner_id == user_id:
                    files.append(file)

            return ServiceResult.success_result(files)

        except Exception as e:
            return ServiceResult.exception_result(
                exception=e,
                error_code=ErrorCode.INTERNAL_ERROR,
                context="FileSystemService.list_files_by_directory",
            )

    def list_files_by_owner(self, **kwargs) -> ServiceResult[List[File]]:
        """
        List files owned by a user.

        Args:
            **kwargs: Flexible parameters
                # tenant_id, owner_id, and user_id auto-injected from self.request_context
                limit: Maximum number of results (optional, default: 50)

        Returns:
            ServiceResult with list of File models
        """
        try:
            # Extract parameters
            limit = kwargs.get("limit", 50)

            # Get security context from self.request_context
            tenant_id = self.request_context.target_tenant_id
            owner_id = self.request_context.target_user_id
            ascending = kwargs.get("ascending", False)

            # Use GSI2 to query files by owner
            temp_file = File()
            temp_file.tenant_id = tenant_id
            temp_file.owner_id = owner_id
            temp_file.category = kwargs.get("category")
            if kwargs.get("status"):
                temp_file.status = kwargs.get("status")
            # Query using helper method
            gsi= "gsi1"
            if temp_file.status and not temp_file.category:
                gsi = "gsi2"
            if temp_file.category:
                gsi = "gsi3"

            query_result = self._query_by_index(
                temp_file, gsi, limit=limit, ascending=ascending
            )

            if not query_result.success:
                return query_result

            # Filter results
            files = []
            for file in query_result.data:
                # Filter out deleted files
                if file.status != "deleted":
                    files.append(file)

            return ServiceResult.success_result(files)

        except AccessDeniedError as e:
            return ServiceResult.error_result(
                message=str(e), error_code=ErrorCode.ACCESS_DENIED
            )

    def list_by_category(
        self,
        owner_id: str,
        category: str,
        status: str = "active",
        limit: int = 100,
        ascending: bool = False,
    ) -> ServiceResult[List[File]]:
        """
        List files by category.

        Args:
            tenant_id: Tenant ID
            owner_id: Owner user ID
            category: File category
            status: File status filter
            limit: Maximum number of results

        Returns:
            ServiceResult with list of File models
        """
        try:
            # Chaos Engineering: Inject fault if configured
            if self._should_inject_chaos_fault(
                "file_system_service.list_by_category"
            ):
                return self._inject_chaos_fault(
                    "file_system_service.list_by_category"
                )

            # Use GSI4 to query files by category
            temp_file = File()
            temp_file.owner_id = owner_id
            temp_file.category = category

            # Query using helper method
            query_result = self._query_by_index(
                temp_file, "gsi4", limit=limit, ascending=ascending
            )

            if not query_result.success:
                return query_result

            # Filter results by tenant and status
            files = []
            for file in query_result.data:
                if file.tenant_id == tenant_id and file.status == status:
                    files.append(file)

            return ServiceResult.success_result(files)

        except Exception as e:
            return ServiceResult.exception_result(
                e,
                error_code=ErrorCode.DATABASE_QUERY_FAILED,
                context="FileSystemService.list_by_category",
            )

    

    def list_lineage(self, **kwargs) -> ServiceResult[List[File]]:
        """
        List files by lineage.

        Args:
            **kwargs: Flexible parameters
                # tenant_id and user_id auto-injected from self.request_context
                parent_id: Parent file ID (will recursively walk up the chain)
                root_id: Root file ID (will get all descendants)
                limit: Maximum number of results (optional, default: 50)

        Returns:
            ServiceResult with list of File models
        """
        try:
            # Extract parameters
            parent_id = kwargs.get("parent_id")
            root_id = kwargs.get("root_id")
            limit = kwargs.get("limit", 50)

            # Chaos Engineering: Inject fault if configured
            if self._should_inject_chaos_fault("file_system_service.list_lineage"):
                return self._inject_chaos_fault("file_system_service.list_lineage")

            # need at least one of parent_id or root_id
            if not parent_id and not root_id:
                return ServiceResult.error_result(
                    message="At least one of parent_id or root_id is required",
                    error_code=ErrorCode.VALIDATION_ERROR,
                )

            # Get security context from self.request_context
            user_id = self.request_context.target_user_id
            tenant_id = self.request_context.target_tenant_id

            # If parent_id is provided, walk up the parent chain
            if parent_id:
                return self._walk_parent_chain(parent_id, user_id, tenant_id, limit)

            # Otherwise, query by root_id for all descendants
            temp_file = File()
            temp_file.owner_id = user_id
            temp_file.tenant_id = tenant_id
            temp_file.root_id = root_id
            index = "gsi4"

            # Query using helper method
            query_result = self._query_by_index(
                temp_file, index, limit=limit, ascending=True
            )

            if not query_result.success:
                return query_result

            # Filter results
            files = []
            for file in query_result.data:
                # Filter out deleted files and apply access control
                if file.status != "deleted" and file.owner_id == user_id:
                    files.append(file)

            return ServiceResult.success_result(files)

        except Exception as e:
            return ServiceResult.exception_result(
                exception=e,
                error_code=ErrorCode.INTERNAL_ERROR,
                context="FileSystemService.list_lineage_files",
            )

    @service_method("archive")
    def archive(self, file_id: str) -> ServiceResult[Dict[str, Any]]:
        """
        Archive a file and all its lineage (if it's a root file).
        
        Args:
            file_id: ID of the file to archive
            
        Returns:
            ServiceResult with dict containing:
                - archived: List[File] - successfully archived files
                - failed: List[dict] - files that failed with error details
                - total_requested: int - total files attempted
                - total_archived: int - count of successful archives
                - total_failed: int - count of failures
        """
        try:
            user_id = self.request_context.authenticated_user_id
            
            # Get the file
            result = self.get_by_id(file_id=file_id)
            if not result.success:
                return result
            
            file = result.data            
            # Collect files to archive
            files_to_archive = [file]
            
            # If this is a root file, get all lineage files
            if file.id == file.root_id:
                lineage_result = self.list_lineage(root_id=file.id)
                if lineage_result.success:
                    # Verify ownership of all lineage files and exclude root (already in list)
                    for lineage_file in lineage_result.data:
                        if lineage_file.id == file.id:
                            continue  # Skip root file, already in files_to_archive
                        if lineage_file.owner_id != user_id:
                            return ServiceResult.error_result(
                                message="You can only archive your own files",
                                error_code=ErrorCode.ACCESS_DENIED,
                            )
                        files_to_archive.append(lineage_file)
            
            # Archive all files, tracking successes and failures
            archived_files = []
            failed_files = []
            
            for file in files_to_archive:
                file.status = "archived"
                save_result = self._save_model(file)
                if save_result.success:
                    archived_files.append({
                        "id": file.id,
                        "name": file.name,
                        "status": file.status
                    })
                else:
                    failed_files.append({
                        "id": file.id,
                        "name": file.name,
                        "status": file.status,
                        "error": save_result.message
                    })
            
            result_data = {
                "archived": archived_files,
                "failed": failed_files,
                "total_requested": len(files_to_archive),
                "total_archived": len(archived_files),
                "total_failed": len(failed_files)
            }
            
            return ServiceResult.success_result(result_data)
            
        except Exception as e:
            return ServiceResult.exception_result(
                exception=e,
                error_code=ErrorCode.INTERNAL_ERROR,
                context="FileSystemService.archive",
            )

    @service_method("unarchive")
    def unarchive(self, file_id: str) -> ServiceResult[Dict[str, Any]]:
        """
        Unarchive a file and ensure all parent files in its lineage chain are also unarchived.
        
        Walks the parent chain (via parent_id, not root_id) and unarchives each archived
        parent until reaching the root (parent_id is None or empty).
        
        Args:
            file_id: ID of the file to unarchive
            
        Returns:
            ServiceResult with dict containing:
                - unarchived: List[dict] - successfully unarchived files
                - failed: List[dict] - files that failed with error details
                - total_requested: int - total files attempted
                - total_unarchived: int - count of successful unarchives
                - total_failed: int - count of failures
        """
        try:
            user_id = self.request_context.authenticated_user_id
            tenant_id = self.request_context.authenticated_tenant_id
            
            # Get the target file
            result = self.get_by_id(file_id=file_id)
            if not result.success:
                return result
            
            target_file = result.data
            
            # Verify ownership
            if target_file.owner_id != user_id:
                return ServiceResult.error_result(
                    message="You can only unarchive your own files",
                    error_code=ErrorCode.ACCESS_DENIED,
                )
            
            # Walk the parent chain to collect all files that need to be checked
            # This returns files from root to target (root first, target last)
            chain_result = self._walk_parent_chain(
                start_file_id=file_id,
                user_id=user_id,
                tenant_id=tenant_id,
                limit=100,
                max_depth=50,
            )
            
            if not chain_result.success:
                return chain_result
            
            parent_chain = chain_result.data
            
            # Filter to only archived files that need unarchiving
            files_to_unarchive = [f for f in parent_chain if f.status == "archived"]
            
            # Unarchive all files, tracking successes and failures
            unarchived_files = []
            failed_files = []
            
            for file in files_to_unarchive:
                file.status = "active"
                save_result = self._save_model(file)
                if save_result.success:
                    unarchived_files.append({
                        "id": file.id,
                        "name": file.name,
                        "status": file.status
                    })
                else:
                    failed_files.append({
                        "id": file.id,
                        "name": file.name,
                        "status": file.status,
                        "error": save_result.message
                    })
            
            result_data = {
                "unarchived": unarchived_files,
                "failed": failed_files,
                "total_requested": len(files_to_unarchive),
                "total_unarchived": len(unarchived_files),
                "total_failed": len(failed_files)
            }
            
            return ServiceResult.success_result(result_data)
            
        except Exception as e:
            return ServiceResult.exception_result(
                exception=e,
                error_code=ErrorCode.INTERNAL_ERROR,
                context="FileSystemService.unarchive",
            )

    def _walk_parent_chain(
        self,
        start_file_id: str,
        user_id: str,
        tenant_id: str,
        limit: int,
        max_depth: int = 50,
    ) -> ServiceResult[List[File]]:
        """
        Walk up the direct parent chain from a starting file to the root.

        Example: E -> C -> Root (returns just the single path upward)

        Args:
            start_file_id: File ID to start walking from
            user_id: User ID for access control
            tenant_id: Tenant ID for access control
            limit: Maximum total files to return
            max_depth: Maximum depth to prevent infinite loops (default: 20)

        Returns:
            ServiceResult with list of File models in the chain (from root to start file)
        """
        try:
            files = []
            visited_ids = set()  # Prevent circular references
            current_file_id = start_file_id
            depth = 0

            # Walk up the chain
            while current_file_id and depth < max_depth:
                # Guard against circular references
                if current_file_id in visited_ids:
                    logger.warning(
                        f"Circular reference detected in file lineage at {current_file_id}"
                    )
                    break

                visited_ids.add(current_file_id)

                # Get current file
                file_result = self.get_by_id(file_id=current_file_id)
                if not file_result.success:
                    # Stop walking if we can't access the file
                    break

                current_file = file_result.data

                # Check access control
                if (
                    current_file.owner_id != user_id
                    or current_file.tenant_id != tenant_id
                ):
                    break

                # Skip deleted files
                if current_file.status != "deleted":
                    files.append(current_file)

                # Check if we've hit the limit
                if len(files) >= limit:
                    break

                # Move to parent (None or empty means we've reached the root)
                if not current_file.parent_id:
                    break

                current_file_id = current_file.parent_id
                depth += 1

            # Guard rail: warn if we hit max depth
            if depth >= max_depth:
                logger.warning(
                    f"Max depth ({max_depth}) reached while walking parent chain from {start_file_id}"
                )

            # Reverse to get root-to-leaf order (Root -> C -> E)
            files.reverse()

            return ServiceResult.success_result(files)

        except Exception as e:
            return ServiceResult.exception_result(
                exception=e,
                error_code=ErrorCode.INTERNAL_ERROR,
                context="FileSystemService._walk_parent_chain",
            )

    # ========================================
    # Validation & Helper Methods
    # ========================================

    def _validate_file_creation(self, file: File) -> None:
        """
        Validate business rules for file creation.

        Args:
            file: File model to validate

        Raises:
            ValidationError: If validation fails
        """
        # Required fields
        if not file.name:
            raise ValidationError("name is required", "name")

        # Security validation
        if not file.tenant_id:
            raise ValidationError(
                "tenant_id is required (should be auto-injected from authentication)",
                "tenant_id",
            )

        if not file.owner_id:
            raise ValidationError(
                "owner_id is required (should be auto-injected from authentication)",
                "owner_id",
            )

    def _generate_s3_key(self, file: File) -> str:
        """
        Generate organized S3 key for file using centralized S3PathService.

        Args:
            file: File model

        Returns:
            S3 key string

        Example:
            tenants/tenant-123/users/user-456/file-789/document.pdf
        """
        return S3PathService.build_path(
            tenant_id=file.tenant_id,
            user_id=file.owner_id,
            file_id=file.id,
            file_name=file.name,
        )

    def _validate_s3_key_access(self, key: str) -> None:
        """
        Validate user has access to S3 key using centralized S3PathService.

        Uses S3PathService to parse and validate key structure, ensuring:
        - Correct path format (tenants/{tenant-id}/users/{user-id}/...)
        - Tenant isolation
        - User ownership

        Future enhancements:
        - Support for shared files
        - Admin override permissions
        - Cross-tenant access with explicit grants

        Args:
            key: S3 object key to validate

        Raises:
            AccessDeniedError: If user doesn't have access to this key path
            ValidationError: If key format is invalid
        """
        # Get authenticated user's tenant and user ID from request context
        auth_tenant_id = self.request_context.authenticated_tenant_id
        auth_user_id = self.request_context.authenticated_user_id

        # Use S3PathService to validate access
        result = S3PathService.validate_user_access(
            key=key, tenant_id=auth_tenant_id, user_id=auth_user_id
        )

        # Raise appropriate errors if validation failed
        if not result.success:
            if result.error_code == ErrorCode.ACCESS_DENIED:
                raise AccessDeniedError(result.message)
            else:
                raise ValidationError(result.message, "key")

    # ========================================
    # Chaos Engineering Support
    # ========================================

    def _should_inject_chaos_fault(self, operation: str) -> bool:
        """Check if chaos fault should be injected for this operation."""
        if not isinstance(self.request_context, RequestContext):
            return False
        return self.request_context.should_inject_fault(operation)

    def _inject_chaos_fault(self, operation: str) -> ServiceResult:
        """
        Inject chaos fault for testing.

        Args:
            operation: Operation identifier

        Returns:
            ServiceResult with injected fault
        """
        if not isinstance(self.request_context, RequestContext):
            return ServiceResult.error_result(
                "Chaos injection failed: no request context"
            )

        chaos_config = self.request_context.get_chaos_config()
        if not chaos_config:
            return ServiceResult.error_result("Chaos injection failed: no config")

        logger.warning(
            f"🎭 CHAOS INJECTION: {operation}",
            extra={
                "operation": operation,
                "fault_type": chaos_config.fault_type,
                "tenant_id": self.request_context.target_tenant_id,
                "user_id": self.request_context.target_user_id,
            },
        )

        # Handle different fault types
        if chaos_config.fault_type == "exception":
            # Raise exception to trigger exception handlers
            exception_type = chaos_config.exception_type or "RuntimeError"
            exception_class = globals().get(exception_type, RuntimeError)
            raise exception_class(f"Chaos injection: {operation}")

        elif chaos_config.fault_type == "error_result":
            # Return error ServiceResult
            return ServiceResult.error_result(
                message=chaos_config.error_message
                or f"Chaos injection failure: {operation}",
                error_code=chaos_config.error_code or "CHAOS_INJECTED_ERROR",
            )

        elif chaos_config.fault_type == "delay":
            # Inject delay then continue normally
            if chaos_config.delay_ms:
                import time

                time.sleep(chaos_config.delay_ms / 1000.0)
                logger.info(f"Chaos delay injected: {chaos_config.delay_ms}ms")
            return None  # Continue with normal operation

        # Unknown fault type
        return ServiceResult.error_result(
            f"Unknown chaos fault type: {chaos_config.fault_type}"
        )

    def generate_presigned_upload_url(
        self,
        file_name: str,
        file_id: str | None = None,
        content_type: str | None = None,
        expires_in: int | None = None,
        category: str = "file",
        bucket_name: str | None = None,
    ) -> ServiceResult:

        # Get user context from authorizer claims in request context
        request_context = self.request_context
                
        tenant_id = request_context.authenticated_tenant_id
        user_id = request_context.authenticated_user_id
                
        
        if not file_name:
            return ServiceResult.error_result(
                message="file_name is required", error_code=ErrorCode.VALIDATION_ERROR
            )

        
        

        # Generate unique file ID and build S3 key using centralized path service
        file: File = File()
        file.id = file_id
        file.name = file_name
        file.tenant_id = tenant_id
        file.owner_id = user_id
        file.category = category
        file.content_type = content_type
        # called to generate unique id (if needed)
        file.prep_for_save()

        # Build organized path using S3PathService
        key = S3PathService.build_path(
            tenant_id=tenant_id, user_id=user_id, file_id=file.id, file_name=file_name
        )
        # add the new key to the file
        file.key = key

        # Add metadata for tracking
        metadata = {
            "tenant_id": tenant_id,
            "user_id": user_id,
            "original_file_name": file_name,
            "file_id": file.id,
            "category": category,
        }

        # Generate presigned URL
        signed_url_result = self.s3_service.generate_presigned_upload_url(
            key=key,
            file_name=file_name,
            expires_in=expires_in,
            content_type=content_type,
            metadata=metadata,
            bucket=bucket_name,
        )

        if not signed_url_result.success:
            return ServiceResult.error_result(message=signed_url_result.message, error_code=signed_url_result.error_code)

        # Build response with file tracking info
        presigned_data = signed_url_result.data
        response_data = {
            "file_id": file.id,
            "file_name": file_name,
            "key": presigned_data.get("key"),
            "bucket": presigned_data.get("bucket"),
            "url": presigned_data.get("url"),
            "fields": presigned_data.get("fields"),
            "expires_in": presigned_data.get("expires_in"),
            "expires_at": presigned_data.get("expires_at"),
            "method": "POST" if presigned_data.get("fields") else "PUT",
            "category": category,
        }

        
        # TODO: we may want to conditionally save the file based on settings?
        file.state = "signed-url-created"
        file.status = "pending"
        file.key = presigned_data.get("key")
        file.bucket = presigned_data.get("bucket")
        save_result =self.create(**file.to_dict())
        if not save_result.success:
            return ServiceResult.error_result(message = save_result.message, error_code = save_result.error_code)

        return ServiceResult.success_result(data=response_data)
