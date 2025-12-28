"""
Configurable S3 Upload Event Router

A lightweight, reusable handler that routes S3 upload events based on environment variables.
Deploy with different configs without changing code.

Environment Variables:
    ROUTING_STRATEGY: How to route events
        - "eventbridge" (recommended): Publish to EventBridge for fan-out
        - "sqs": Send to SQS queue for processing
        - "lambda": Direct Lambda invocation
        - "none": Skip routing (for logging/testing)
    
    EVENTBRIDGE_BUS_NAME: EventBridge bus name (if ROUTING_STRATEGY=eventbridge)
    SQS_QUEUE_URL: SQS queue URL (if ROUTING_STRATEGY=sqs)
    TARGET_LAMBDA_ARN: Lambda function ARN (if ROUTING_STRATEGY=lambda)
    
    EVENT_SOURCE: Source name for EventBridge events (default: "file-system.s3")
    EVENT_DETAIL_TYPE: Detail type for events (default: "FileUploaded")
    
    FILTER_PREFIX: Only process keys with this prefix (optional)
    FILTER_SUFFIX: Only process keys with this suffix (optional)

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

import json
import os
import boto3
from typing import Dict, Any, List, Optional
from aws_lambda_powertools import Logger

logger = Logger()

# Initialize AWS clients (cached for Lambda warm starts)
eventbridge = None
sqs = None
lambda_client = None


def get_eventbridge():
    """Get or create EventBridge client."""
    global eventbridge
    if eventbridge is None:
        eventbridge = boto3.client('events')
    return eventbridge


def get_sqs():
    """Get or create SQS client."""
    global sqs
    if sqs is None:
        sqs = boto3.client('sqs')
    return sqs


def get_lambda_client():
    """Get or create Lambda client."""
    global lambda_client
    if lambda_client is None:
        lambda_client = boto3.client('lambda')
    return lambda_client


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lightweight S3 event router.
    
    Processes S3 upload events and routes them according to ROUTING_STRATEGY.
    """
    try:
        # Get routing configuration
        routing_strategy = os.getenv('ROUTING_STRATEGY', 'eventbridge').lower()
        
        # Extract S3 records
        records = event.get('Records', [])
        if not records:
            logger.info("No S3 records in event")
            return {'statusCode': 200, 'body': json.dumps({'processed': 0})}
        
        logger.info(f"Processing {len(records)} S3 records with strategy: {routing_strategy}")
        
        # Process each record
        processed = 0
        errors = []
        
        for record in records:
            try:
                # Extract S3 event data
                s3_event = extract_s3_event(record)
                
                if s3_event is None:
                    logger.debug(f"Skipping record (filtered out)")
                    continue
                
                # Route based on strategy
                if routing_strategy == 'eventbridge':
                    route_to_eventbridge(s3_event)
                elif routing_strategy == 'sqs':
                    route_to_sqs(s3_event)
                elif routing_strategy == 'lambda':
                    route_to_lambda(s3_event)
                elif routing_strategy == 'none':
                    logger.info(f"Routing disabled - logged event: {s3_event['key']}")
                else:
                    logger.warning(f"Unknown routing strategy: {routing_strategy}")
                
                processed += 1
                logger.info(f"Routed: {s3_event['key']}")
                
            except Exception as e:
                error_msg = f"Failed to process record: {str(e)}"
                logger.exception(error_msg)
                errors.append(error_msg)
        
        # Return success response
        response = {
            'statusCode': 200,
            'body': json.dumps({
                'processed': processed,
                'total': len(records),
                'errors': errors,
                'strategy': routing_strategy
            })
        }
        
        logger.info(f"Completed: processed {processed}/{len(records)} records")
        return response
        
    except Exception as e:
        logger.exception(f"Handler failed: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def extract_s3_event(record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Extract and validate S3 event data.
    
    Returns None if event should be filtered out.
    """
    try:
        s3_data = record.get('s3', {})
        bucket_name = s3_data.get('bucket', {}).get('name')
        object_data = s3_data.get('object', {})
        key = object_data.get('key')
        size = object_data.get('size', 0)
        etag = object_data.get('eTag', '')
        
        if not bucket_name or not key:
            logger.warning("Invalid S3 record: missing bucket or key")
            return None
        
        # Apply filters if configured
        filter_prefix = os.getenv('FILTER_PREFIX')
        filter_suffix = os.getenv('FILTER_SUFFIX')
        
        if filter_prefix and not key.startswith(filter_prefix):
            logger.debug(f"Key filtered out by prefix: {key}")
            return None
        
        if filter_suffix and not key.endswith(filter_suffix):
            logger.debug(f"Key filtered out by suffix: {key}")
            return None
        
        # Build event payload
        s3_event = {
            'bucket': bucket_name,
            'key': key,
            'size': size,
            'etag': etag,
            'eventTime': record.get('eventTime'),
            'eventName': record.get('eventName'),
            'requestParameters': record.get('requestParameters', {}),
            'responseElements': record.get('responseElements', {})
        }
        
        return s3_event
        
    except Exception as e:
        logger.exception(f"Failed to extract S3 event: {e}")
        return None


def route_to_eventbridge(s3_event: Dict[str, Any]) -> None:
    """Route event to EventBridge."""
    bus_name = os.getenv('EVENTBRIDGE_BUS_NAME', 'default')
    event_source = os.getenv('EVENT_SOURCE', 'file-system.s3')
    detail_type = os.getenv('EVENT_DETAIL_TYPE', 'FileUploaded')
    
    client = get_eventbridge()
    
    response = client.put_events(
        Entries=[{
            'Source': event_source,
            'DetailType': detail_type,
            'Detail': json.dumps(s3_event),
            'EventBusName': bus_name
        }]
    )
    
    # Check for failures
    if response.get('FailedEntryCount', 0) > 0:
        failures = response.get('Entries', [])
        raise Exception(f"EventBridge put failed: {failures}")
    
    logger.debug(f"Sent to EventBridge: {s3_event['key']}")


def route_to_sqs(s3_event: Dict[str, Any]) -> None:
    """Route event to SQS queue."""
    queue_url = os.getenv('SQS_QUEUE_URL')
    
    if not queue_url:
        raise ValueError("SQS_QUEUE_URL environment variable not set")
    
    client = get_sqs()
    
    response = client.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps(s3_event),
        MessageAttributes={
            'eventType': {
                'StringValue': 'FileUploaded',
                'DataType': 'String'
            },
            'bucket': {
                'StringValue': s3_event['bucket'],
                'DataType': 'String'
            }
        }
    )
    
    logger.debug(f"Sent to SQS: {s3_event['key']} (MessageId: {response['MessageId']})")


def route_to_lambda(s3_event: Dict[str, Any]) -> None:
    """Route event to target Lambda function."""
    function_arn = os.getenv('TARGET_LAMBDA_ARN')
    
    if not function_arn:
        raise ValueError("TARGET_LAMBDA_ARN environment variable not set")
    
    client = get_lambda_client()
    
    response = client.invoke(
        FunctionName=function_arn,
        InvocationType='Event',  # Async invocation
        Payload=json.dumps(s3_event)
    )
    
    logger.debug(f"Invoked Lambda: {s3_event['key']} (StatusCode: {response['StatusCode']})")
