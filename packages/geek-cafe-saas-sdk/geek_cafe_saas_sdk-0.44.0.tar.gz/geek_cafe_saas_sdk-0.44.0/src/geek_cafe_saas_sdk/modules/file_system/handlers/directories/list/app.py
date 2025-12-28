"""
Lambda handler for listing directories.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

import json
import os
from typing import Dict, Any

from boto3_assist.dynamodb.dynamodb import DynamoDB
from geek_cafe_saas_sdk.modules.file_system.services.directory_service import DirectoryService


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """List directories handler."""
    try:
        query_params = event.get('queryStringParameters', {})
        
        tenant_id = query_params.get('tenant_id')
        user_id = query_params.get('user_id')
        parent_directory_id = query_params.get('parent_directory_id')
        limit = int(query_params.get('limit', '100'))
        
        if not all([tenant_id, user_id]):
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
        
        result = dir_service.list_by_parent(
            tenant_id=tenant_id,
            parent_directory_id=parent_directory_id,
            user_id=user_id,
            limit=limit
        )
        
        if result.success:
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': True,
                    'data': [d.to_dictionary() for d in result.data],
                    'count': len(result.data)
                })
            }
        else:
            return {
                'statusCode': 400,
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
