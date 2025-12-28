"""
Lambda handler for deleting directories.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

import json
import os
from typing import Dict, Any

from boto3_assist.dynamodb.dynamodb import DynamoDB
from geek_cafe_saas_sdk.modules.file_system.services.directory_service import DirectoryService


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Delete directory handler."""
    try:
        path_params = event.get('pathParameters', {})
        query_params = event.get('queryStringParameters', {})
        
        directory_id = path_params.get('directory_id')
        tenant_id = query_params.get('tenant_id')
        user_id = query_params.get('user_id')
        hard_delete = query_params.get('hard_delete', 'false').lower() == 'true'
        
        if not all([directory_id, tenant_id, user_id]):
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'success': False,
                    'message': 'Missing required parameters'
                })
            }
        
        table_name = os.environ.get('DYNAMODB_TABLE_NAME', 'files-table')
        db = DynamoDB()
        
        dir_service = DirectoryService(
            dynamodb=db,
            table_name=table_name
        )
        
        result = dir_service.delete(
            directory_id=directory_id,
            tenant_id=tenant_id,
            user_id=user_id,
            hard_delete=hard_delete
        )
        
        if result.success:
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': True,
                    'message': 'Directory deleted successfully'
                })
            }
        else:
            status_code = 404 if result.error_code == 'NOT_FOUND' else 403
            return {
                'statusCode': status_code,
                'body': json.dumps({
                    'success': False,
                    'message': result.message
                })
            }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'message': str(e)
            })
        }
