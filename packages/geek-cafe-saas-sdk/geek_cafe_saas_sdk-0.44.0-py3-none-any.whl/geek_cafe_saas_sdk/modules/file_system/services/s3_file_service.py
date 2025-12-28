"""
S3 file operations service using boto3-assist.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from boto3_assist.s3.s3_object import S3Object
from boto3_assist.s3.s3_bucket import S3Bucket
from boto3_assist.s3.s3_connection import S3Connection
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.core.error_codes import ErrorCode
import os


class S3FileService:
    """
    S3 file operations using boto3-assist.
    
    Handles all S3 operations including upload, download, delete,
    presigned URLs, and versioning. Supports dependency injection
    for testing with Moto.
    
    Bucket Configuration (Resolution Order):
    Each method follows this fallback chain for bucket selection:
    1. Explicit parameter: bucket="my-bucket" in method call
    2. Handler config: handler_wrapper.config["upload_bucket"] (via event.config())
    3. Instance default: S3FileService(default_bucket="...")
    4. Environment variables: S3_UPLOAD_BUCKET_NAME, UPLOAD_BUCKET, etc.
    
    Example Config Injection:
        # From consumer (e.g., Aplos layer)
        handler_wrapper.config["upload_bucket"] = os.getenv("UPLOAD_BUCKET")
        
    Environment Variables:
    - FILE_UPLOAD_MAX_SIZE: Maximum file size in bytes (default: 104857600 = 100MB)
    - FILE_PRESIGNED_URL_EXPIRY: Presigned URL expiration in seconds (default: 300)
    - S3_UPLOAD_BUCKET_NAME: Default upload bucket
    - S3_DOWNLOAD_BUCKET_NAME: Default download bucket
    - UPLOAD_BUCKET: Consumer fallback for uploads
    - DOWNLOAD_BUCKET: Consumer fallback for downloads
    - COPY_SOURCE_BUCKET: Source bucket for copy operations
    - COPY_DEST_BUCKET: Destination bucket for copy operations
    """
    
    def __init__(
        self, 
        s3_object: Optional[S3Object] = None,
        s3_bucket: Optional[S3Bucket] = None,
        default_bucket: Optional[str] = None,
        request_context: Optional[Any] = None,
        signature_version: str | None= "s3v4",
        aws_profile: str | None = None,
        aws_region: str | None = None,
        aws_end_point_url: str | None = None,
        aws_access_key_id: str | None = None,
        aws_secret_access_key: str | None = None
    ):
        """
        Initialize S3 service.
        
        Args:
            s3_object: S3Object instance (inject for testing with Moto)
            s3_bucket: S3Bucket instance (inject for testing)
            default_bucket: Default bucket name (from env or parameter)
            request_context: RequestContext instance (optional, for base handler compatibility)
        """
        self.signature_version= signature_version
        self.aws_profile = aws_profile
        self.aws_region = aws_region
        self.aws_end_point_url = aws_end_point_url
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key

        if s3_object is None:
            # Create connection and S3Object if not provided
            self.connection = self._generate_s3_connection()
            self.s3_object = S3Object(connection=self.connection)
            self.bucket = s3_bucket or S3Bucket(connection=self.connection)
        else:
            self.s3_object = s3_object
            # If bucket not provided, need to create connection
            if s3_bucket is None:
                self.connection = self._generate_s3_connection()
                self.bucket = S3Bucket(connection=self.connection)
            else:
                self.bucket = s3_bucket
                # Try to get connection from s3_object
                self.connection = getattr(s3_object, 'connection', self._generate_s3_connection())
            
        self.default_bucket = default_bucket or os.getenv("S3_FILE_BUCKET")
        
        # Configuration
        self.max_file_size = int(os.getenv("FILE_UPLOAD_MAX_SIZE", "104857600"))  # 100MB
        self.presigned_url_expiry = int(os.getenv("FILE_PRESIGNED_URL_EXPIRY", "300"))  # 5 minutes
    
    def _generate_s3_connection(self):
        connection = S3Connection(
            signature_version=self.signature_version,
            aws_profile=self.aws_profile,
            aws_region=self.aws_region,
            aws_end_point_url=self.aws_end_point_url,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key
        )
        return connection

    def upload_file(
        self,
        file_data: bytes,
        key: str,
        bucket: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
        content_type: Optional[str] = None
    ) -> ServiceResult:
        """
        Upload file to S3.
        
        Args:
            file_data: File content as bytes
            key: S3 object key
            bucket: Bucket name (uses default if not provided)
            metadata: Custom metadata
            content_type: MIME type
            
        Returns:
            ServiceResult with upload details
        """
        try:
            bucket_name = bucket or self.default_bucket
            
            if not bucket_name:
                return ServiceResult.error_result(
                    message="S3 bucket name is required",
                    error_code=ErrorCode.VALIDATION_ERROR
                )
            
            # Validate file size
            if len(file_data) > self.max_file_size:
                return ServiceResult.error_result(
                    message=f"File size exceeds maximum allowed size of {self.max_file_size} bytes",
                    error_code=ErrorCode.VALIDATION_ERROR
                )
            
            # Upload to S3
            self.s3_object.put(
                bucket=bucket_name,
                key=key,
                data=file_data
            )
            
            # Note: boto3-assist S3Object.put doesn't support metadata/content_type directly
            # For production, you may need to use boto3 client directly or extend S3Object
            
            return ServiceResult.success_result({
                "bucket": bucket_name,
                "key": key,
                "size": len(file_data),
                "s3_uri": f"s3://{bucket_name}/{key}"
            })
            
        except Exception as e:
            return ServiceResult.error_result(
                message=f"Failed to upload file to S3: {str(e)}",
                error_code=ErrorCode.INTERNAL_ERROR
            )
    
    def stream_data(self, *, key:str, bucket: str | None = None)->ServiceResult:
        """
        Stream file data from S3.
        
        Args:
            key: S3 object key
            bucket: Bucket name, if not supplied attempts to use default bucket
            
        Returns:
            ServiceResult with file data
        """
        try:
            bucket_name = bucket or self.default_bucket
            
            if not bucket_name:
                return ServiceResult.error_result(
                    message="S3 bucket name is required",
                    error_code=ErrorCode.VALIDATION_ERROR
                )
            
            response = self.s3_object.get_object(
                bucket_name=bucket_name,
                key=key
            )
            
            file_data = response['Body'].read()
            
            return ServiceResult.success_result({
                "data": file_data,
                "content_type": response.get('ContentType'),
                "size": response.get('ContentLength'),
                "metadata": response.get('Metadata', {}),
                "last_modified": response.get('LastModified'),
                "etag": response.get('ETag')
            })
            
        except Exception as e:
            # Check if it's a NoSuchKey error
            if 'NoSuchKey' in str(e) or 'Not Found' in str(e) or '404' in str(e):
                return ServiceResult.error_result(
                    message=f"File not found: {key}",
                    error_code=ErrorCode.NOT_FOUND
                )
            return ServiceResult.error_result(
                message=f"Failed to download file from S3: {str(e)}",
                error_code=ErrorCode.INTERNAL_ERROR
            )


    def download_file(
        self,
        *,        
        key: str,
        bucket: str | None = None,
        local_directory: str | None = None,
        local_file_path: str | None = None,
        retry_attempts: int = 3,
    ) -> ServiceResult:
        """
        Download file from S3.
        
        Args:
            bucket: Bucket name
            key: S3 object key
            local_directory: Local directory to save file. 
                If not supplied, will use a tmp directory
            local_file_path: Local file path to save file, 
            if not supplied, will use a tmp directory and the file name from the S3 object
            
        Returns:
            ServiceResult with file data
        """
        try:
            bucket_name = bucket or self.default_bucket
            
            if not bucket_name:
                return ServiceResult.error_result(
                    message="S3 bucket name is required",
                    error_code=ErrorCode.VALIDATION_ERROR
                )
            
            path = self.s3_object.download_file(
                bucket=bucket_name,
                key=key,
                local_directory=local_directory,
                local_file_path=local_file_path,
                retry_attempts=retry_attempts
            )
            
            
            
            return ServiceResult.success_result({
                "path": path,
                "bucket": bucket_name,
                "key": key
            })
            
        except Exception as e:
            # Check if it's a NoSuchKey error
            if 'NoSuchKey' in str(e) or 'Not Found' in str(e) or '404' in str(e):
                return ServiceResult.error_result(
                    message=f"File not found: {key}",
                    error_code=ErrorCode.NOT_FOUND
                )
            return ServiceResult.error_result(
                message=f"Failed to download file from S3: {str(e)}",
                error_code=ErrorCode.INTERNAL_ERROR
            )
    
    def delete_file(
        self,        
        key: str,
        bucket: str | None = None
    ) -> ServiceResult:
        """
        Delete file from S3.
        
        Args:
            key: S3 object key
            bucket: Bucket name
            
        Returns:
            ServiceResult with deletion details
        """
        try:
            bucket_name = bucket or self.default_bucket
            
            if not bucket_name:
                return ServiceResult.error_result(
                    message="S3 bucket name is required",
                    error_code=ErrorCode.VALIDATION_ERROR
                )
            
            self.s3_object.delete(
                bucket_name=bucket_name,
                key=key
            )
            
            return ServiceResult.success_result({
                "deleted": key,
                "bucket": bucket_name
            })
            
        except Exception as e:
            return ServiceResult.error_result(
                message=f"Failed to delete file from S3: {str(e)}",
                error_code=ErrorCode.INTERNAL_ERROR
            )
    
    def generate_presigned_upload_url(
        self,
        key: str,
        file_name: str,
        bucket: Optional[str] = None,
        expires_in: Optional[int] = None,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> ServiceResult:
        """
        Generate presigned URL for file upload.
        
        Args:
            key: S3 object key
            file_name: Original file name
            bucket: Bucket name
            expires_in: Expiration time in seconds
            content_type: MIME type
            metadata: Custom metadata
            
        Returns:
            ServiceResult with presigned URL
        """
        try:
            bucket_name = bucket or self.default_bucket or os.getenv("S3_UPLOAD_BUCKET_NAME") or os.getenv("UPLOAD_BUCKET")
            expiry = expires_in or self.presigned_url_expiry
            
            if not bucket_name:
                return ServiceResult.error_result(
                    message="S3 bucket name is required",
                    error_code=ErrorCode.VALIDATION_ERROR
                )
            
            url_data = self.s3_object.generate_presigned_url(
                bucket_name=bucket_name,
                key_path=key,
                file_name=file_name,
                meta_data=metadata,
                expiration=expiry,
                method_type='POST'
            )
            signed_url = url_data.get("signed_url")
            if not signed_url:
                return ServiceResult.error_result(
                    message="Failed to generate presigned upload URL",
                    error_code=ErrorCode.INTERNAL_ERROR
                )
            
            expires_at = (datetime.utcnow() + timedelta(seconds=expiry)).strftime('%Y-%m-%d %H:%M:%S UTC')
            return ServiceResult.success_result({
                "url": signed_url.get('url'),
                "fields": signed_url.get('fields', {}),
                "signed_url": signed_url,
                "expires_in": expiry,
                "expires_at": expires_at,
                "key": key,
                "bucket": bucket_name
            })
            
        except Exception as e:
            return ServiceResult.error_result(
                message=f"Failed to generate presigned upload URL: {str(e)}",
                error_code=ErrorCode.INTERNAL_ERROR
            )
    
    def generate_presigned_download_url(
        self,
        key: str,
        bucket: Optional[str] = None,
        expires_in: Optional[int] = None,
        file_name: Optional[str] = None
    ) -> ServiceResult:
        """
        Generate presigned URL for file download.
        
        Args:
            key: S3 object key
            bucket: Bucket name
            expires_in: Expiration time in seconds
            file_name: Optional filename for download
            
        Returns:
            ServiceResult with presigned URL
        """
        try:
            bucket_name = bucket or self.default_bucket or os.getenv("S3_DOWNLOAD_BUCKET_NAME") or os.getenv("DOWNLOAD_BUCKET")
            expiry = expires_in or self.presigned_url_expiry
            
            if not bucket_name:
                return ServiceResult.error_result(
                    message="S3 bucket name is required",
                    error_code=ErrorCode.VALIDATION_ERROR
                )
            
            # Use file_name or extract from key
            download_name = file_name or key.split('/')[-1]
            
            url_data = self.s3_object.generate_presigned_url(
                bucket_name=bucket_name,
                key_path=key,
                file_name=download_name,
                expiration=expiry,
                method_type='GET'
            )
            
            signed_url = url_data.get('signed_url')
            if not signed_url:
                return ServiceResult.error_result(
                    message="Failed to generate presigned download URL",
                    error_code=ErrorCode.INTERNAL_ERROR
                )
            return ServiceResult.success_result({
                "url": signed_url,
                "expires_in": expiry,
                "key": key,
                "bucket": bucket_name,                
                "signed_url": signed_url,
                "expires_at": url_data.get('expires_at'),
                "method": "GET"
            })
            
        except Exception as e:
            return ServiceResult.error_result(
                message=f"Failed to generate presigned download URL: {str(e)}",
                error_code=ErrorCode.INTERNAL_ERROR
            )
    
    def list_object_versions(
        self,
        key: str,
        bucket: Optional[str] = None
    ) -> ServiceResult:
        """
        List all versions of an object (for S3 native versioning).
        
        Args:
            key: S3 object key
            bucket: Bucket name
            
        Returns:
            ServiceResult with versions list
        """
        try:
            bucket_name = bucket or self.default_bucket or os.getenv("S3_DOWNLOAD_BUCKET_NAME") or os.getenv("DOWNLOAD_BUCKET")
            
            if not bucket_name:
                return ServiceResult.error_result(
                    message="S3 bucket name is required",
                    error_code=ErrorCode.VALIDATION_ERROR
                )
            
            versions = self.s3_object.list_versions(
                bucket=bucket_name,
                prefix=key
            )
            
            return ServiceResult.success_result({
                "versions": versions,
                "key": key,
                "bucket": bucket_name
            })
            
        except Exception as e:
            return ServiceResult.error_result(
                message=f"Failed to list object versions: {str(e)}",
                error_code=ErrorCode.INTERNAL_ERROR
            )
    
    def copy_object(
        self,
        source_key: str,
        dest_key: str,
        source_bucket: Optional[str] = None,
        dest_bucket: Optional[str] = None
    ) -> ServiceResult:
        """
        Copy object within S3.
        
        Args:
            source_key: Source S3 key
            dest_key: Destination S3 key
            source_bucket: Source bucket (default bucket if not provided)
            dest_bucket: Destination bucket (default bucket if not provided)
            
        Returns:
            ServiceResult with copy details
        """
        try:
            src_bucket = source_bucket or self.default_bucket or os.getenv("COPY_SOURCE_BUCKET")
            dst_bucket = dest_bucket or self.default_bucket or os.getenv("COPY_DEST_BUCKET")
            
            if not src_bucket or not dst_bucket:
                return ServiceResult.error_result(
                    message="S3 bucket names are required",
                    error_code=ErrorCode.VALIDATION_ERROR
                )
            
            self.s3_object.copy(
                source_bucket=src_bucket,
                source_key=source_key,
                destination_bucket=dst_bucket,
                destination_key=dest_key
            )
            
            return ServiceResult.success_result({
                "source": f"s3://{src_bucket}/{source_key}",
                "destination": f"s3://{dst_bucket}/{dest_key}"
            })
            
        except Exception as e:
            return ServiceResult.error_result(
                message=f"Failed to copy object: {str(e)}",
                error_code=ErrorCode.INTERNAL_ERROR
            )
    
    def enable_bucket_versioning(
        self,
        bucket: Optional[str] = None
    ) -> ServiceResult:
        """
        Enable versioning on S3 bucket.
        
        Args:
            bucket: Bucket name
            
        Returns:
            ServiceResult with status
        """
        try:
            bucket_name = bucket or self.default_bucket
            
            if not bucket_name:
                return ServiceResult.error_result(
                    message="S3 bucket name is required",
                    error_code=ErrorCode.VALIDATION_ERROR
                )
            
            self.bucket.enable_versioning(
                bucket_name=bucket_name
            )
            
            return ServiceResult.success_result({
                "versioning_enabled": True,
                "bucket": bucket_name
            })
            
        except Exception as e:
            return ServiceResult.error_result(
                message=f"Failed to enable bucket versioning: {str(e)}",
                error_code=ErrorCode.INTERNAL_ERROR
            )
    
    def get_object_metadata(
        self,
        key: str,
        bucket: Optional[str] = None
    ) -> ServiceResult:
        """
        Get S3 object metadata without downloading file.
        
        Args:
            key: S3 object key
            bucket: Bucket name
            
        Returns:
            ServiceResult with metadata
        """
        try:
            bucket_name = bucket or self.default_bucket
            
            if not bucket_name:
                return ServiceResult.error_result(
                    message="S3 bucket name is required",
                    error_code=ErrorCode.VALIDATION_ERROR
                )
            
            # Use head_object to get metadata without downloading
            response = self.connection.client.head_object(
                Bucket=bucket_name,
                Key=key
            )
            
            return ServiceResult.success_result({
                "content_type": response.get('ContentType'),
                "size": response.get('ContentLength'),
                "metadata": response.get('Metadata', {}),
                "last_modified": response.get('LastModified'),
                "etag": response.get('ETag'),
                "version_id": response.get('VersionId'),
                "storage_class": response.get('StorageClass')
            })
            
        except Exception as e:
            # Check if it's a NoSuchKey error
            if '404' in str(e) or 'NoSuchKey' in str(e) or 'Not Found' in str(e):
                return ServiceResult.error_result(
                    message=f"File not found: {key}",
                    error_code=ErrorCode.NOT_FOUND
                )
            return ServiceResult.error_result(
                message=f"Failed to get object metadata: {str(e)}",
                error_code=ErrorCode.INTERNAL_ERROR
            )
