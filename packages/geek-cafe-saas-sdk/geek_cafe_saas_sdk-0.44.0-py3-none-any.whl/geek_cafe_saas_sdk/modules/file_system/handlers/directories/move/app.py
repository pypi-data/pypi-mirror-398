"""
Lambda handler for moving directories.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

import json
import os
from typing import Dict, Any

from boto3_assist.dynamodb.dynamodb import DynamoDB
from geek_cafe_saas_sdk.modules.file_system.services.directory_service import DirectoryService


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Move directory handler."""
    try:
        path_params = event.get('pathParameters', {})
        
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})
        
        directory_id = path_params.get('directory_id')
        tenant_id = body.get('tenant_id')
        user_id = body.get('user_id')
        new_parent_id = body.get('new_parent_id')
        
        if not all([directory_id, tenant_id, user_id, new_parent_id]):
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
        
        result = dir_service.move(
            directory_id=directory_id,
            tenant_id=tenant_id,
            user_id=user_id,
            new_parent_id=new_parent_id
        )
        
        if result.success:
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': True,
                    'data': result.data.to_dictionary()
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
