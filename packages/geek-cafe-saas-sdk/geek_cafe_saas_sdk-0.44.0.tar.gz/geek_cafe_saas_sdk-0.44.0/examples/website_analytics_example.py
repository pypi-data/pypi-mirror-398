"""
Website Analytics System - Usage Examples

This script demonstrates how to use the website analytics system.
"""

import datetime as dt
from geek_cafe_saas_sdk.website_analytics_service import WebsiteAnalyticsService
from geek_cafe_saas_sdk.website_analytics_summary_service import WebsiteAnalyticsSummaryService
from geek_cafe_saas_sdk.website_analytics_tally_service import WebsiteAnalyticsTallyService


def example_track_page_views():
    """Example: Track page views for a blog post."""
    print("\n=== Example 1: Tracking Page Views ===")
    
    service = WebsiteAnalyticsService()
    
    # Track multiple page views
    routes = ["/blog/post-1", "/blog/post-2", "/products"]
    for route in routes:
        result = service.create_page_view(
            tenant_id="demo-tenant",
            user_id="user-123",
            route=route,
            duration_ms=2500,
            scroll_depth=80,
            session_id="session-abc",
            user_agent="Mozilla/5.0",
            referrer="https://google.com"
        )
        
        if result.success:
            print(f"✓ Tracked page view for {route}")
        else:
            print(f"✗ Failed to track {route}: {result.error}")


def example_log_errors():
    """Example: Log errors for debugging."""
    print("\n=== Example 2: Logging Errors ===")
    
    service = WebsiteAnalyticsService()
    
    # Log different types of errors
    errors = [
        {
            "route": "/api/users",
            "message": "Database connection timeout",
            "type": "DatabaseError"
        },
        {
            "route": "/api/products",
            "message": "Invalid JSON payload",
            "type": "ValidationError"
        }
    ]
    
    for error in errors:
        result = service.create_error_log(
            tenant_id="demo-tenant",
            user_id="user-456",
            route=error["route"],
            error_message=error["message"],
            error_type=error["type"],
            session_id="error-session"
        )
        
        if result.success:
            print(f"✓ Logged {error['type']}: {error['message']}")


def example_track_performance():
    """Example: Track performance metrics."""
    print("\n=== Example 3: Tracking Performance ===")
    
    service = WebsiteAnalyticsService()
    
    # Track performance for home page
    result = service.create_performance_log(
        tenant_id="demo-tenant",
        user_id="user-789",
        route="/",
        load_time_ms=850,
        ttfb_ms=120,
        fcp_ms=400,
        lcp_ms=750,
        session_id="perf-session"
    )
    
    if result.success:
        print("✓ Tracked performance metrics for home page")
        print(f"  - Load time: 850ms")
        print(f"  - TTFB: 120ms")
        print(f"  - FCP: 400ms")
        print(f"  - LCP: 750ms")


def example_track_custom_events():
    """Example: Track custom business events."""
    print("\n=== Example 4: Tracking Custom Events ===")
    
    service = WebsiteAnalyticsService()
    
    # Track purchase event
    result = service.create_custom_event(
        tenant_id="demo-tenant",
        user_id="user-999",
        route="/checkout",
        event_name="purchase_completed",
        amount=99.99,
        currency="USD",
        product_id="prod-123",
        session_id="checkout-session"
    )
    
    if result.success:
        print("✓ Tracked custom event: purchase_completed")
        print(f"  - Amount: $99.99")
        print(f"  - Product: prod-123")


def example_query_analytics():
    """Example: Query analytics data."""
    print("\n=== Example 5: Querying Analytics ===")
    
    service = WebsiteAnalyticsService()
    
    # Query by route
    result = service.list_by_route("/blog/post-1")
    if result.success:
        print(f"✓ Found {len(result.data)} analytics records for /blog/post-1")
    
    # Query by type
    result = service.list_by_type("error")
    if result.success:
        print(f"✓ Found {len(result.data)} error records")
    
    # Query by tenant
    result = service.list_by_tenant("demo-tenant")
    if result.success:
        print(f"✓ Found {len(result.data)} total analytics records for tenant")


def example_aggregate_data():
    """Example: Aggregate analytics into summaries."""
    print("\n=== Example 6: Aggregating Analytics ===")
    
    tally_service = WebsiteAnalyticsTallyService()
    
    # Define time period (last hour)
    current_time = dt.datetime.now(dt.UTC).timestamp()
    period_start = current_time - 3600
    
    # Aggregate specific route
    result = tally_service.aggregate_analytics_for_route(
        route="/blog/post-1",
        tenant_id="demo-tenant",
        user_id="admin",
        period_start_ts=period_start,
        period_end_ts=current_time,
        period_type="hourly"
    )
    
    if result.success:
        summary = result.data
        print(f"✓ Aggregated analytics for /blog/post-1")
        print(f"  - Total events: {summary.total_events}")
        print(f"  - Unique sessions: {summary.unique_sessions}")
        print(f"  - Unique users: {summary.unique_users}")
        print(f"  - Metrics: {summary.metrics}")


def example_batch_aggregation():
    """Example: Batch aggregation for multiple routes."""
    print("\n=== Example 7: Batch Aggregation ===")
    
    tally_service = WebsiteAnalyticsTallyService()
    
    current_time = dt.datetime.now(dt.UTC).timestamp()
    period_start = current_time - 3600
    
    # Aggregate multiple routes
    routes = ["/blog/post-1", "/blog/post-2", "/products"]
    result = tally_service.aggregate_multiple_routes(
        routes=routes,
        tenant_id="demo-tenant",
        user_id="admin",
        period_start_ts=period_start,
        period_end_ts=current_time,
        period_type="hourly"
    )
    
    if result.success:
        print(f"✓ Batch aggregated {len(result.data)} route summaries")
        for summary in result.data:
            print(f"  - {summary.route}: {summary.total_events} events")


def example_hourly_aggregation():
    """Example: Hourly aggregation (for EventBridge)."""
    print("\n=== Example 8: Hourly Aggregation (EventBridge) ===")
    
    tally_service = WebsiteAnalyticsTallyService()
    
    # This is what EventBridge would call
    result = tally_service.aggregate_hourly(
        tenant_id="demo-tenant",
        user_id="system",
        hours_ago=1
    )
    
    if result.success:
        print(f"✓ Hourly aggregation completed")
        print(f"  - Processed {len(result.data)} routes")
        print(f"  - Ready for dashboard queries")
    else:
        print(f"✗ Aggregation failed: {result.error}")


def example_query_summaries():
    """Example: Query aggregated summaries."""
    print("\n=== Example 9: Querying Summaries ===")
    
    summary_service = WebsiteAnalyticsSummaryService()
    
    # Query summaries by route
    result = summary_service.list_by_route("/blog/post-1")
    if result.success:
        print(f"✓ Found {len(result.data)} summaries for /blog/post-1")
        for summary in result.data[:3]:  # Show first 3
            print(f"  - Period: {summary.period_type}, Events: {summary.total_events}")
    
    # Query summaries by type
    result = summary_service.list_by_type("error")
    if result.success:
        print(f"✓ Found {len(result.data)} error summaries")


def lambda_handler_example(event, context):
    """
    Example Lambda handler for EventBridge scheduled aggregation.
    
    EventBridge Rule Configuration:
    {
      "schedule": "rate(1 hour)",
      "description": "Hourly website analytics aggregation"
    }
    """
    print("\n=== Example 10: Lambda Handler ===")
    
    from geek_cafe_saas_sdk.website_analytics_tally_service import WebsiteAnalyticsTallyService
    
    tally_service = WebsiteAnalyticsTallyService()
    
    # Get tenant_id from event or environment
    tenant_id = event.get('tenant_id', 'default-tenant')
    
    # Aggregate analytics from the past hour
    result = tally_service.aggregate_hourly(
        tenant_id=tenant_id,
        user_id="system",
        hours_ago=1
    )
    
    if result.success:
        print(f"✓ Lambda: Successfully aggregated {len(result.data)} summaries")
        return {
            'statusCode': 200,
            'body': {
                'message': 'Aggregation successful',
                'summaries_created': len(result.data)
            }
        }
    else:
        print(f"✗ Lambda: Aggregation failed: {result.error}")
        return {
            'statusCode': 500,
            'body': {
                'message': 'Aggregation failed',
                'error': result.error
            }
        }


def main():
    """Run all examples."""
    print("=" * 60)
    print("Website Analytics System - Usage Examples")
    print("=" * 60)
    
    # Note: These examples assume you have a DynamoDB instance
    # For demo purposes, you can use moto for mocking:
    
    print("\nNote: Connect to DynamoDB before running these examples.")
    print("For testing, use moto with the test fixtures from test_website_analytics.py")
    
    print("\nAvailable examples:")
    print("1. Track page views")
    print("2. Log errors")
    print("3. Track performance")
    print("4. Track custom events")
    print("5. Query analytics")
    print("6. Aggregate data")
    print("7. Batch aggregation")
    print("8. Hourly aggregation")
    print("9. Query summaries")
    print("10. Lambda handler")
    
    # Uncomment to run examples with actual database connection:
    # example_track_page_views()
    # example_log_errors()
    # example_track_performance()
    # example_track_custom_events()
    # example_query_analytics()
    # example_aggregate_data()
    # example_batch_aggregation()
    # example_hourly_aggregation()
    # example_query_summaries()


if __name__ == "__main__":
    main()
