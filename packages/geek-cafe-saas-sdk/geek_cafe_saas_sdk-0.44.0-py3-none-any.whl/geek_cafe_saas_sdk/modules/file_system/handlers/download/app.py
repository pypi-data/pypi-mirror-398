"""
Lambda handler for downloading file content.

Ultra-thin handler - validation happens in service layer.

Requires authentication (secure mode).
"""

from typing import Dict, Any
from geek_cafe_saas_sdk.lambda_handlers import create_handler, LambdaEvent
from geek_cafe_saas_sdk.modules.file_system.services import FileSystemService


# Factory creates handler (defaults to secure auth)
handler_wrapper = create_handler(
    service_class=FileSystemService,
    require_body=False,
    convert_request_case=True
)


def lambda_handler(event: Dict[str, Any], context: Any, injected_service=None) -> Dict[str, Any]:
    """
    Download file content.
    
    Args:
        event: Lambda event from API Gateway
        context: Lambda context
        injected_service: Optional FileSystemService for testing
    
    Path parameters:
        fileId: File ID
    
    Returns 200 with file content (base64 encoded for binary files)
    """
    return handler_wrapper.execute(event, context, download_file, injected_service)


def download_file(
    event: LambdaEvent,
    service: FileSystemService
) -> Any:
    """
    Ultra-thin business logic - extract ID and call service.
    
    Service handles:
    - Field validation
    - Access control (from service.request_context)
    - S3 download
    - Base64 encoding
    
    Note: Service returns result with base64-encoded data for API response.
    """
    file_id = event.path("file-id")
    if not file_id:
        return ServiceResult.error_result(
            message="file-id is required in the route.", error_code=ErrorCode.VALIDATION_ERROR
        )
    # for now, we just stream the file, the download service function just downloads a local file
    return service.stream_data(file_id=file_id)
