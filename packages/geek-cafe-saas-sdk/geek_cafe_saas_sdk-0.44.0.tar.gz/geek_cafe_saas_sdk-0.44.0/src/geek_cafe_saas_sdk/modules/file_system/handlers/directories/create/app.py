"""
Lambda handler for creating directories.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

import json
import os
from typing import Dict, Any

from boto3_assist.dynamodb.dynamodb import DynamoDB
from geek_cafe_saas_sdk.modules.file_system.services.directory_service import DirectoryService


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Create directory handler."""
    try:
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})
        
        tenant_id = body.get('tenant_id')
        user_id = body.get('user_id')
        directory_name = body.get('directory_name')
        parent_directory_id = body.get('parent_directory_id')
        description = body.get('description')
        
        if not all([tenant_id, user_id, directory_name]):
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'success': False,
                    'message': 'Missing required fields'
                })
            }
        
        table_name = os.environ.get('DYNAMODB_TABLE_NAME', 'files-table')
        db = DynamoDB()
        
        dir_service = DirectoryService(
            dynamodb=db,
            table_name=table_name
        )
        
        result = dir_service.create(
            tenant_id=tenant_id,
            user_id=user_id,
            directory_name=directory_name,
            parent_directory_id=parent_directory_id,
            description=description
        )
        
        if result.success:
            return {
                'statusCode': 201,
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
