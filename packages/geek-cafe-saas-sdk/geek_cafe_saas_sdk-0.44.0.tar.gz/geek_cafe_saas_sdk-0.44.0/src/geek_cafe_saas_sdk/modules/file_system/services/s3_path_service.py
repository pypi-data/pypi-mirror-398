"""
S3 Path Service - Centralized S3 key/path management.

Provides standardized methods for building and parsing S3 file paths.
Ensures consistent path structure across all file operations.

Path Pattern:
    tenants/{tenant_id}/users/{user_id}/{file_id}/{file_name}

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

from typing import Dict, Any
from dataclasses import dataclass
from geek_cafe_saas_sdk.core.error_codes import ErrorCode
from geek_cafe_saas_sdk.core.service_result import ServiceResult


@dataclass
class S3PathComponents:
    """Components extracted from an S3 path."""
    tenant_id: str
    user_id: str
    file_id: str
    file_name: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "file_id": self.file_id,
            "file_name": self.file_name
        }

    @staticmethod
    def to_object(data: Dict[str, Any]) -> "S3PathComponents":
        """Convert to object."""
        components: S3PathComponents = S3PathComponents(
            tenant_id=data.get("tenant_id"),
            user_id=data.get("user_id"),
            file_id=data.get("file_id"),
            file_name=data.get("file_name")
        )
        return components


class S3PathService:
    """
    Centralized S3 path management service.
    
    Handles building and parsing S3 keys/paths for file operations.
    Ensures consistent path structure and provides easy component extraction.
    
    Path Pattern:
        tenants/{tenant_id}/users/{user_id}/{file_id}/{file_name}
    
    Usage:
        # Build file path
        path = S3PathService.build_path(
            tenant_id="tenant-123",
            user_id="user-456",
            file_id="file-789",
            file_name="document.pdf"
        )
        # Result: tenants/tenant-123/users/user-456/file-789/document.pdf
        
        # Parse path
        components = S3PathService.parse_path(path)
        print(components.tenant_id)  # "tenant-123"
        print(components.file_id)  # "file-789"
    """
    
    @staticmethod
    def build_path(
        tenant_id: str,
        user_id: str,
        file_id: str,
        file_name: str
    ) -> str:
        """
        Build S3 path for file storage.
        
        Pattern: tenants/{tenant_id}/users/{user_id}/{file_id}/{file_name}
        
        Args:
            tenant_id: Tenant identifier
            user_id: User identifier
            file_id: Unique file identifier
            file_name: Original file name
            
        Returns:
            S3 key path string
            
        Example:
            >>> build_path("tenant-123", "user-456", "file-789", "doc.pdf")
            'tenants/tenant-123/users/user-456/file-789/doc.pdf'
        """
        key_parts = [
            "tenants",
            tenant_id,
            "users",
            user_id,
            "files",            
            file_id,
            "path",
            file_name
        ]
        return "/".join(key_parts)
    
    @staticmethod
    def parse_path(key: str) -> ServiceResult:
        """
        Parse S3 path and extract components.
        
        Path pattern: tenants/{tenant_id}/users/{user_id}/files/{file_id}/path/{file_name}
        
        Args:
            key: S3 object key/path
            
        Returns:
            ServiceResult with S3PathComponents data or error
            
        Example:
            >>> result = parse_path("tenants/t123/users/u456/files/f789/path/doc.pdf")
            >>> result.data.tenant_id  # "t123"
            >>> result.data.file_id  # "f789"
        """
        if not key:
            return ServiceResult.error_result(
                message="S3 key is required",
                error_code=ErrorCode.VALIDATION_ERROR
            )
        
        parts = key.split('/')
        
        # Minimum parts: tenants/{tid}/users/{uid}/files/{file_id}/path/{file_name}
        if len(parts) < 8:
            return ServiceResult.error_result(
                message=f"Invalid S3 key format. Expected at least 8 parts, got {len(parts)}: {key}",
                error_code=ErrorCode.VALIDATION_ERROR
            )
        
        # Validate structure
        if parts[0].lower() not in ['tenant', 'tenants']:
            return ServiceResult.error_result(
                message=f"Invalid S3 key format. Expected to start with 'tenants/', got: {parts[0]}/",
                error_code=ErrorCode.VALIDATION_ERROR
            )
        
        if parts[2].lower() != 'users':
            return ServiceResult.error_result(
                message=f"Invalid S3 key format. Expected 'users' at position 2, got: {parts[2]}",
                error_code=ErrorCode.VALIDATION_ERROR
            )
        
        if parts[4].lower() != 'files':
            return ServiceResult.error_result(
                message=f"Invalid S3 key format. Expected 'files' at position 4, got: {parts[4]}",
                error_code=ErrorCode.VALIDATION_ERROR
            )
        
        if parts[6].lower() != 'path':
            return ServiceResult.error_result(
                message=f"Invalid S3 key format. Expected 'path' at position 6, got: {parts[6]}",
                error_code=ErrorCode.VALIDATION_ERROR
            )
        
        tenant_id = parts[1]
        user_id = parts[3]
        file_id = parts[5]
        file_name = "/".join(parts[7:])  # Handle filenames with slashes
        
        components = S3PathComponents(
            tenant_id=tenant_id,
            user_id=user_id,
            file_id=file_id,
            file_name=file_name
        )
        
        return ServiceResult.success_result(data=components)
    
    @staticmethod
    def validate_tenant_access(key: str, tenant_id: str) -> ServiceResult:
        """
        Validate that the key belongs to the specified tenant.
        
        Args:
            key: S3 object key/path
            tenant_id: Expected tenant identifier
            
        Returns:
            ServiceResult with success=True if valid, error otherwise
        """
        parse_result = S3PathService.parse_path(key)
        
        if not parse_result.success:
            return parse_result
        
        components: S3PathComponents =parse_result.data
        
        if components.tenant_id != tenant_id:
            return ServiceResult.error_result(
                message=f"Access denied: File belongs to different tenant. "
                        f"Expected: {tenant_id}, Found: {components.tenant_id}",
                error_code=ErrorCode.ACCESS_DENIED
            )
        
        return ServiceResult.success_result(data=components)
    
    @staticmethod
    def validate_user_access(key: str, tenant_id: str, user_id: str) -> ServiceResult:
        """
        Validate that the key belongs to the specified tenant and user.
        
        Args:
            key: S3 object key/path
            tenant_id: Expected tenant identifier
            user_id: Expected user identifier
            
        Returns:
            ServiceResult with success=True if valid, error otherwise
        """
        # First validate tenant
        tenant_result = S3PathService.validate_tenant_access(key, tenant_id)
        
        if not tenant_result.success:
            return tenant_result
        
        components: S3PathComponents = tenant_result.data
        
        if components.user_id != user_id:
            return ServiceResult.error_result(
                message=f"Access denied: File belongs to different user. "
                        f"Expected: {user_id}, Found: {components.user_id}",
                error_code=ErrorCode.ACCESS_DENIED
            )
        
        return ServiceResult.success_result(data=components)
