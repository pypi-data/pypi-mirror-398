"""
Lambda handler for preparing lineage bundle.

Requires authentication (secure mode).
"""

from typing import Dict, Any
from geek_cafe_saas_sdk.lambda_handlers import create_handler, LambdaEvent
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.modules.file_system.services import FileSystemService


# Factory creates handler (defaults to secure auth)
handler_wrapper = create_handler(
    service_class=FileSystemService,
    require_body=False,
    convert_request_case=True
)


def lambda_handler(event: Dict[str, Any], context: Any, injected_service=None) -> Dict[str, Any]:
    """
    Prepare lineage bundle for a file (metadata only, no file content).
    
    Args:
        event: Lambda event from API Gateway
        context: Lambda context
        injected_service: Optional FileSystemService for testing
    
    Path parameters:
        fileId: File ID to bundle
    
    Returns 200 with bundle information:
    {
        "selectedFile": {file object},
        "mainFile": {file object or null},
        "originalFile": {file object or null},
        "metadata": {
            "selectedFileId": "...",
            "selectedFileName": "...",
            "transformationChain": [
                {"step": 1, "type": "original", "fileId": "...", "fileName": "..."},
                {"step": 2, "type": "convert", "fileId": "...", "fileName": "...", "operation": "..."},
                {"step": 3, "type": "clean", "fileId": "...", "fileName": "...", "operation": "..."}
            ]
        }
    }
    """
    return handler_wrapper.execute(event, context, prepare_bundle, injected_service)


def prepare_bundle(event: LambdaEvent, service: FileSystemService) -> ServiceResult:
    """
    Business logic for preparing lineage bundle.
    """
    tenant_id = user_context.get("tenant_id")
    user_id = user_context.get("user_id")
    
    # Get file ID from path parameters
    path_params = event.get("pathParameters", {})
    file_id = path_params.get("fileId") or path_params.get("id")
    
    if not file_id:
        raise ValueError("fileId path parameter is required")
    
    # Prepare bundle
    result = service.prepare_lineage_bundle(
        selected_file_id=file_id,
        tenant_id=tenant_id,
        user_id=user_id
    )
    
    return result
