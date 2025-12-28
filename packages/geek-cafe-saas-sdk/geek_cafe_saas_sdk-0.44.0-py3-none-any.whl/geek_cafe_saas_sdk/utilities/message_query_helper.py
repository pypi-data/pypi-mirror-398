"""
Geek Cafe, LLC
MIT License.  See Project Root for the license information.

MessageQueryHelper for querying messages from potentially sharded channels.

Handles:
- Single partition queries (normal channels)
- Multi-bucket queries (time-based partitioning)
- Multi-shard queries (hash-based partitioning)
- Merged sorted results (newest first)
- Stateless cursor pagination
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta, timezone
import base64
import json
from boto3_assist.dynamodb.dynamodb_key import DynamoDBKey


class MessageQueryHelper:
    """
    Helper for querying messages from potentially sharded channels.
    
    This class abstracts the complexity of querying across multiple
    DynamoDB partitions when a channel uses time-bucketing and/or sharding.
    
    For normal channels, it performs a simple single-partition query.
    For sharded channels, it queries multiple partitions in parallel,
    merges results by timestamp, and provides stateless cursor pagination.
    """
    
    def __init__(self, dynamodb, table_name: str):
        """
        Initialize the query helper.
        
        Args:
            dynamodb: DynamoDB client or resource
            table_name: DynamoDB table name
        """
        # Handle both DynamoDB resource and client
        if hasattr(dynamodb, 'client'):
            # It's a DynamoDB resource (from boto3_assist)
            self.dynamodb_client = dynamodb.client
            self.table = dynamodb.resource.Table(table_name)
        else:
            # It's a client
            self.dynamodb_client = dynamodb
            self.table = None
        
        self.table_name = table_name
    
    def query_messages(
        self,
        channel_id: str,
        sharding_config: Optional[Dict[str, Any]] = None,
        limit: int = 50,
        cursor: Optional[str] = None,
        lookback_buckets: int = 7
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """
        Query messages from channel with optional sharding support.
        
        Args:
            channel_id: Channel ID to query
            sharding_config: None for normal, config dict for sharded channels
            limit: Max messages to return
            cursor: Pagination cursor (base64 encoded)
            lookback_buckets: How many time buckets to query (default 7 for daily)
        
        Returns:
            Tuple of (messages, next_cursor)
            - messages: List of message dicts
            - next_cursor: Opaque cursor string for next page, or None
        """
        if not sharding_config or not sharding_config.get("enabled"):
            # Simple case: single partition query
            return self._query_single_partition(channel_id, limit, cursor)
        
        # Complex case: multi-bucket, multi-shard query
        return self._query_multi_partition(
            channel_id,
            sharding_config,
            limit,
            cursor,
            lookback_buckets
        )
    
    def _query_single_partition(
        self,
        channel_id: str,
        limit: int,
        cursor: Optional[str]
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """
        Query from single partition (normal channels).
        
        Args:
            channel_id: Channel ID
            limit: Max messages
            cursor: Pagination cursor
            
        Returns:
            Tuple of (messages, next_cursor)
        """
        pk_value = DynamoDBKey.build_key(("channel", channel_id))
        
        # Parse cursor if provided
        exclusive_start_key = None
        if cursor:
            try:
                cursor_data = json.loads(base64.urlsafe_b64decode(cursor))
                exclusive_start_key = cursor_data.get("key")
            except Exception:
                # Invalid cursor, ignore
                pass
        
        # Query GSI1
        from boto3.dynamodb.conditions import Key
        
        kwargs = {
            "IndexName": "gsi1",
            "KeyConditionExpression": Key("gsi1_pk").eq(pk_value),
            "ScanIndexForward": False,  # Newest first
            "Limit": limit
        }
        
        if exclusive_start_key:
            kwargs["ExclusiveStartKey"] = exclusive_start_key
        
        # Use table if available, otherwise use client
        if self.table:
            response = self.table.query(**kwargs)
        else:
            # Convert to client format
            kwargs_client = {
                "TableName": self.table_name,
                "IndexName": kwargs["IndexName"],
                "KeyConditionExpression": "gsi1_pk = :pk",
                "ExpressionAttributeValues": {":pk": pk_value},
                "ScanIndexForward": kwargs["ScanIndexForward"],
                "Limit": kwargs["Limit"]
            }
            if exclusive_start_key:
                kwargs_client["ExclusiveStartKey"] = exclusive_start_key
            
            response = self.dynamodb_client.query(**kwargs_client)
        
        items = response.get("Items", [])
        
        # Build next cursor
        next_cursor = None
        if response.get("LastEvaluatedKey"):
            next_cursor = base64.urlsafe_b64encode(
                json.dumps({"key": response["LastEvaluatedKey"]}, default=str).encode()
            ).decode()
        
        return items, next_cursor
    
    def _query_multi_partition(
        self,
        channel_id: str,
        sharding_config: Dict[str, Any],
        limit: int,
        cursor: Optional[str],
        lookback_buckets: int
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """
        Query from multiple partitions (sharded channels).
        
        Strategy:
        1. Generate list of partition keys (buckets × shards)
        2. Query each partition
        3. Merge results by timestamp (newest first)
        4. Apply limit
        5. Generate cursor from last emitted message
        
        Args:
            channel_id: Channel ID
            sharding_config: Sharding configuration
            limit: Max messages
            cursor: Pagination cursor
            lookback_buckets: Number of time buckets to query
            
        Returns:
            Tuple of (messages, next_cursor)
        """
        bucket_span = sharding_config.get("bucket_span", "day")
        shard_count = sharding_config.get("shard_count", 1)
        
        # Generate time buckets (newest to oldest)
        now = datetime.now(timezone.utc)
        buckets = self._generate_buckets(now, bucket_span, lookback_buckets)
        
        # Parse cursor for guard SK (to avoid duplicates)
        guard_sk = None
        if cursor:
            try:
                cursor_data = json.loads(base64.urlsafe_b64decode(cursor))
                guard_sk = cursor_data.get("last_sk")
            except Exception:
                # Invalid cursor, ignore
                pass
        
        # Query all partitions and collect items
        all_items = []
        for bucket in buckets:
            for shard_idx in range(shard_count):
                pk = self._build_sharded_pk(channel_id, bucket, shard_idx)
                items = self._query_partition(pk, guard_sk, limit * 2)  # Query extra for better merge
                all_items.extend(items)
        
        # Sort by timestamp descending (newest first)
        # Handle both dict and object formats
        def get_timestamp(item):
            if isinstance(item, dict):
                return item.get("created_utc_ts", 0)
            return getattr(item, "created_utc_ts", 0)
        
        all_items.sort(key=get_timestamp, reverse=True)
        
        # Apply limit
        result_items = all_items[:limit]
        
        # Generate cursor from last item
        next_cursor = None
        if result_items and len(all_items) > limit:
            last_item = result_items[-1]
            # Get SK from last item
            if isinstance(last_item, dict):
                last_sk = last_item.get("gsi1_sk")
            else:
                last_sk = getattr(last_item, "gsi1_sk", None)
            
            if last_sk:
                next_cursor = base64.urlsafe_b64encode(
                    json.dumps({"last_sk": last_sk}).encode()
                ).decode()
        
        return result_items, next_cursor
    
    def _query_partition(
        self,
        pk: str,
        guard_sk: Optional[str],
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        Query single partition with optional SK guard.
        
        Args:
            pk: Partition key value
            guard_sk: Optional SK guard (for pagination)
            limit: Max items to retrieve
            
        Returns:
            List of items from partition
        """
        from boto3.dynamodb.conditions import Key
        
        kwargs = {
            "IndexName": "gsi1",
            "KeyConditionExpression": Key("gsi1_pk").eq(pk),
            "ScanIndexForward": False,  # Newest first
            "Limit": limit
        }
        
        # Add SK filter if guard provided
        if guard_sk:
            kwargs["KeyConditionExpression"] &= Key("gsi1_sk").lt(guard_sk)
        
        # Query
        if self.table:
            response = self.table.query(**kwargs)
        else:
            # Convert to client format
            kwargs_client = {
                "TableName": self.table_name,
                "IndexName": kwargs["IndexName"],
                "KeyConditionExpression": "gsi1_pk = :pk",
                "ExpressionAttributeValues": {":pk": pk},
                "ScanIndexForward": kwargs["ScanIndexForward"],
                "Limit": kwargs["Limit"]
            }
            
            if guard_sk:
                kwargs_client["KeyConditionExpression"] += " AND gsi1_sk < :guard"
                kwargs_client["ExpressionAttributeValues"][":guard"] = guard_sk
            
            response = self.dynamodb_client.query(**kwargs_client)
        
        return response.get("Items", [])
    
    def _build_sharded_pk(self, channel_id: str, bucket: str, shard_idx: int) -> str:
        """
        Build partition key for sharded channel.
        
        Args:
            channel_id: Channel ID
            bucket: Time bucket string (yyyyMMdd or yyyyMMddHH)
            shard_idx: Shard index
            
        Returns:
            Partition key string
        """
        return DynamoDBKey.build_key(
            ("channel", channel_id),
            ("bucket", bucket),
            ("shard", str(shard_idx))
        )
    
    @staticmethod
    def _generate_buckets(
        start_time: datetime,
        span: str,
        count: int
    ) -> List[str]:
        """
        Generate list of time bucket strings (newest to oldest).
        
        Args:
            start_time: Starting datetime (typically now)
            span: "day" or "hour"
            count: Number of buckets to generate
            
        Returns:
            List of bucket strings (e.g., ["20251014", "20251013", ...])
        """
        buckets = []
        delta = timedelta(days=1) if span == "day" else timedelta(hours=1)
        
        for i in range(count):
            bucket_time = start_time - (i * delta)
            bucket_str = bucket_time.strftime(
                "%Y%m%d" if span == "day" else "%Y%m%d%H"
            )
            buckets.append(bucket_str)
        
        return buckets
