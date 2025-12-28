# Website Analytics Tally Service

from typing import Dict, Any, Optional, List
from boto3_assist.dynamodb.dynamodb import DynamoDB
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.lambda_handlers._base.decorators import service_method
from geek_cafe_saas_sdk.core.error_codes import ErrorCode
from geek_cafe_saas_sdk.core.request_context import RequestContext
from .website_analytics_service import WebsiteAnalyticsService
from .website_analytics_summary_service import WebsiteAnalyticsSummaryService
from geek_cafe_saas_sdk.modules.analytics.models import WebsiteAnalytics, WebsiteAnalyticsSummary
from aws_lambda_powertools import Logger
import os
import datetime as dt
import time

logger = Logger()


class WebsiteAnalyticsTallyService:
    """
    Service for aggregating analytics data into summaries.
    
    Designed to be called by EventBridge scheduled jobs (e.g., hourly).
    Aggregates raw analytics events into summary records for efficient querying.
    """
    
    def __init__(self, *, dynamodb: DynamoDB = None, table_name: str = None,
                 request_context: RequestContext):
        """
        Initialize tally service with child services.
        
        NOTE: This service keeps custom __init__ because it creates child services.
        Simple services inherit DatabaseService.__init__ directly.
        """
        self.request_context = request_context
        self.analytics_service = WebsiteAnalyticsService(
            dynamodb=dynamodb, table_name=table_name, request_context=request_context
        )
        self.summary_service = WebsiteAnalyticsSummaryService(
            dynamodb=dynamodb, table_name=table_name, request_context=request_context
        )
        self.page_size = 100  # Configurable page size for pagination
        
        # Pagination monitoring configuration from environment variables
        self.max_pagination_iterations = int(os.getenv('TALLY_MAX_PAGINATION_ITERATIONS', '50'))
        self.max_pagination_time_seconds = int(os.getenv('TALLY_MAX_PAGINATION_TIME_SECONDS', '30'))
        self.halt_on_pagination_limit = os.getenv('TALLY_HALT_ON_PAGINATION_LIMIT', 'false').lower() == 'true'
    
    @service_method("aggregate_analytics_for_route")

    
    def aggregate_analytics_for_route(self, route: str,
                                     period_start_ts: float, period_end_ts: float,
                                     period_type: str = "hourly") -> ServiceResult[WebsiteAnalyticsSummary]:
        """
        Aggregate all analytics for a specific route within a time period.
        
        Args:
            route: The route/slug to aggregate analytics for
            tenant_id: Tenant ID for access control
            user_id: User ID for audit trail
            period_start_ts: Start of aggregation period (UTC timestamp)
            period_end_ts: End of aggregation period (UTC timestamp)
            period_type: Type of period (hourly, daily, weekly, monthly)
            
        Returns:
            ServiceResult containing the created/updated WebsiteAnalyticsSummary
        """
        self.request_context.require_authentication()
        tenant_id = self.request_context.target_tenant_id
        user_id = self.request_context.target_user_id
        
        try:
            logger.info(f"Starting analytics aggregation for route: {route}, period: {period_start_ts} to {period_end_ts}")
            
            # Get all analytics for this route with pagination support
            all_analytics = []
            start_key = None
            pagination_iterations = 0
            pagination_start_time = time.time()
            
            while True:
                pagination_iterations += 1
                pagination_elapsed = time.time() - pagination_start_time
                
                # Check pagination limits
                if pagination_iterations > self.max_pagination_iterations:
                    logger.warning(
                        "Analytics pagination iteration limit exceeded",
                        extra={
                            "metric_name": "AnalyticsPaginationIterationsExceeded",
                            "metric_value": pagination_iterations,
                            "route": route,
                            "analytics_collected": len(all_analytics),
                            "max_iterations": self.max_pagination_iterations
                        }
                    )
                    if self.halt_on_pagination_limit:
                        logger.error(f"Halting pagination after {pagination_iterations} iterations")
                        break
                
                if pagination_elapsed > self.max_pagination_time_seconds:
                    logger.warning(
                        "Analytics pagination time limit exceeded",
                        extra={
                            "metric_name": "AnalyticsPaginationTimeExceeded",
                            "metric_value": pagination_elapsed,
                            "route": route,
                            "analytics_collected": len(all_analytics),
                            "max_time_seconds": self.max_pagination_time_seconds
                        }
                    )
                    if self.halt_on_pagination_limit:
                        logger.error(f"Halting pagination after {pagination_elapsed:.2f} seconds")
                        break
                
                analytics_result = self.analytics_service.list_by_route(route, start_key=start_key)
                
                if not analytics_result.success:
                    logger.error(f"Failed to retrieve analytics for route {route}: {analytics_result.message}")
                    return ServiceResult.error_result(
                        message=f"Failed to retrieve analytics: {analytics_result.message}",
                        error_code=analytics_result.error_code
                    )
                
                # Add this page of results
                if analytics_result.data:
                    all_analytics.extend(analytics_result.data)
                
                # Check if there are more pages via error_details
                if (analytics_result.error_details and 
                    'last_evaluated_key' in analytics_result.error_details):
                    start_key = analytics_result.error_details['last_evaluated_key']
                    logger.debug(f"Fetching next page of analytics, total so far: {len(all_analytics)}")
                else:
                    # No more pages
                    break
            
            # Log pagination metrics
            logger.info(
                "Pagination completed for analytics aggregation",
                extra={
                    "metric_name": "AnalyticsPaginationCompleted",
                    "iterations": pagination_iterations,
                    "elapsed_seconds": pagination_elapsed,
                    "analytics_collected": len(all_analytics),
                    "route": route
                }
            )
            
            # Filter analytics by time period
            analytics_in_period = [
                a for a in all_analytics
                if period_start_ts <= a.created_utc_ts <= period_end_ts
            ]
            
            if not analytics_in_period:
                # No analytics - create empty summary
                return self._create_empty_summary(route, tenant_id, user_id, 
                                                 period_start_ts, period_end_ts, period_type)
            
            # Group by analytics type
            analytics_by_type = {}
            for analytics in analytics_in_period:
                analytics_type = analytics.analytics_type
                if analytics_type not in analytics_by_type:
                    analytics_by_type[analytics_type] = []
                analytics_by_type[analytics_type].append(analytics)
            
            # Create summaries for each type
            summaries = []
            for analytics_type, analytics_list in analytics_by_type.items():
                summary_data = self._aggregate_by_type(analytics_type, analytics_list)
                
                summary_result = self._create_or_update_summary(
                    route, tenant_id, user_id, analytics_type,
                    period_start_ts, period_end_ts, period_type,
                    summary_data
                )
                
                if summary_result.success:
                    summaries.append(summary_result.data)
                    logger.info(f"Summary created for route {route}, type {analytics_type}: {len(analytics_list)} events")
            
            # Return the first summary (or general if available)
            if summaries:
                general_summaries = [s for s in summaries if s.analytics_type == "general"]
                return ServiceResult.success_result(general_summaries[0] if general_summaries else summaries[0])
            
            return self._create_empty_summary(route, tenant_id, user_id, 
                                            period_start_ts, period_end_ts, period_type)
            
        except Exception as e:
            logger.error(f"Error aggregating analytics for route {route}: {str(e)}")
            return ServiceResult.exception_result(
                e,
                error_code=ErrorCode.OPERATION_FAILED,
                context=f"Failed to aggregate analytics for route {route}"
            )
    
    def _aggregate_by_type(self, analytics_type: str, analytics_list: List[WebsiteAnalytics]) -> Dict[str, Any]:
        """Aggregate analytics data based on type."""
        if analytics_type == "general":
            return self._aggregate_general_analytics(analytics_list)
        elif analytics_type == "error":
            return self._aggregate_error_analytics(analytics_list)
        elif analytics_type == "performance":
            return self._aggregate_performance_analytics(analytics_list)
        elif analytics_type == "custom":
            return self._aggregate_custom_analytics(analytics_list)
        else:
            return self._aggregate_general_analytics(analytics_list)
    
    def _aggregate_general_analytics(self, analytics_list: List[WebsiteAnalytics]) -> Dict[str, Any]:
        """Aggregate general analytics (page views, sessions)."""
        total_events = len(analytics_list)
        
        # Count unique sessions and users
        unique_sessions: Set[str] = set()
        unique_users: Set[str] = set()
        
        # Collect metrics
        durations = []
        scroll_depths = []
        
        for analytics in analytics_list:
            if analytics.session_id:
                unique_sessions.add(analytics.session_id)
            if analytics.user_id:
                unique_users.add(analytics.user_id)
            
            # Extract metrics from data dict
            if analytics.data:
                duration = analytics.data.get('duration_ms')
                if duration is not None:
                    durations.append(duration)
                
                scroll = analytics.data.get('scroll_depth')
                if scroll is not None:
                    scroll_depths.append(scroll)
        
        metrics = {
            "page_views": total_events,
        }
        
        # Calculate averages
        if durations:
            metrics["avg_duration_ms"] = sum(durations) / len(durations)
            metrics["max_duration_ms"] = max(durations)
            metrics["min_duration_ms"] = min(durations)
        
        if scroll_depths:
            metrics["avg_scroll_depth"] = sum(scroll_depths) / len(scroll_depths)
        
        return {
            "total_events": total_events,
            "unique_sessions": len(unique_sessions),
            "unique_users": len(unique_users),
            "metrics": metrics
        }
    
    def _aggregate_error_analytics(self, analytics_list: List[WebsiteAnalytics]) -> Dict[str, Any]:
        """Aggregate error analytics."""
        total_events = len(analytics_list)
        
        # Count unique sessions and users
        unique_sessions: Set[str] = set()
        unique_users: Set[str] = set()
        
        # Count errors by type
        error_counts = {}
        error_messages = []
        
        for analytics in analytics_list:
            if analytics.session_id:
                unique_sessions.add(analytics.session_id)
            if analytics.user_id:
                unique_users.add(analytics.user_id)
            
            if analytics.data:
                error_type = analytics.data.get('error_type', 'unknown')
                error_counts[error_type] = error_counts.get(error_type, 0) + 1
                
                error_msg = analytics.data.get('error_message')
                if error_msg:
                    error_messages.append(error_msg)
        
        metrics = {
            "total_errors": total_events,
            "errors_by_type": error_counts,
            "unique_error_messages": len(set(error_messages))
        }
        
        return {
            "total_events": total_events,
            "unique_sessions": len(unique_sessions),
            "unique_users": len(unique_users),
            "metrics": metrics
        }
    
    def _aggregate_performance_analytics(self, analytics_list: List[WebsiteAnalytics]) -> Dict[str, Any]:
        """Aggregate performance analytics."""
        total_events = len(analytics_list)
        
        # Count unique sessions and users
        unique_sessions: Set[str] = set()
        unique_users: Set[str] = set()
        
        # Collect performance metrics
        load_times = []
        ttfb_times = []
        fcp_times = []
        lcp_times = []
        
        for analytics in analytics_list:
            if analytics.session_id:
                unique_sessions.add(analytics.session_id)
            if analytics.user_id:
                unique_users.add(analytics.user_id)
            
            if analytics.data:
                load_time = analytics.data.get('load_time_ms')
                if load_time is not None:
                    load_times.append(load_time)
                
                ttfb = analytics.data.get('ttfb_ms')
                if ttfb is not None:
                    ttfb_times.append(ttfb)
                
                fcp = analytics.data.get('fcp_ms')
                if fcp is not None:
                    fcp_times.append(fcp)
                
                lcp = analytics.data.get('lcp_ms')
                if lcp is not None:
                    lcp_times.append(lcp)
        
        metrics = {}
        
        if load_times:
            metrics["avg_load_time_ms"] = sum(load_times) / len(load_times)
            metrics["p95_load_time_ms"] = self._calculate_percentile(load_times, 95)
        
        if ttfb_times:
            metrics["avg_ttfb_ms"] = sum(ttfb_times) / len(ttfb_times)
        
        if fcp_times:
            metrics["avg_fcp_ms"] = sum(fcp_times) / len(fcp_times)
        
        if lcp_times:
            metrics["avg_lcp_ms"] = sum(lcp_times) / len(lcp_times)
        
        return {
            "total_events": total_events,
            "unique_sessions": len(unique_sessions),
            "unique_users": len(unique_users),
            "metrics": metrics
        }
    
    def _aggregate_custom_analytics(self, analytics_list: List[WebsiteAnalytics]) -> Dict[str, Any]:
        """Aggregate custom analytics."""
        total_events = len(analytics_list)
        
        # Count unique sessions and users
        unique_sessions: Set[str] = set()
        unique_users: Set[str] = set()
        
        # Count events by name
        event_counts = {}
        
        for analytics in analytics_list:
            if analytics.session_id:
                unique_sessions.add(analytics.session_id)
            if analytics.user_id:
                unique_users.add(analytics.user_id)
            
            if analytics.data:
                event_name = analytics.data.get('event', 'unknown')
                event_counts[event_name] = event_counts.get(event_name, 0) + 1
        
        metrics = {
            "total_events": total_events,
            "events_by_name": event_counts
        }
        
        return {
            "total_events": total_events,
            "unique_sessions": len(unique_sessions),
            "unique_users": len(unique_users),
            "metrics": metrics
        }
    
    def _calculate_percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile of a list of values."""
        if not values:
            return 0.0
        sorted_values = sorted(values)
        index = int((percentile / 100) * len(sorted_values))
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    def _create_empty_summary(self, route: str, tenant_id: str, user_id: str,
                             period_start_ts: float, period_end_ts: float,
                             period_type: str) -> ServiceResult[WebsiteAnalyticsSummary]:
        """Create an empty summary for routes with no analytics."""
        return self.summary_service.create(
            tenant_id=tenant_id,
            user_id=user_id,
            route=route,
            analytics_type="general",
            period_start_ts=period_start_ts,
            period_end_ts=period_end_ts,
            period_type=period_type,
            total_events=0,
            unique_sessions=0,
            unique_users=0,
            metrics={},
            content={
                "last_tallied_utc_ts": self._get_current_timestamp(),
                "event_count": 0
            }
        )
    
    def _create_or_update_summary(self, route: str, tenant_id: str, user_id: str,
                                 analytics_type: str, period_start_ts: float,
                                 period_end_ts: float, period_type: str,
                                 summary_data: Dict[str, Any]) -> ServiceResult[WebsiteAnalyticsSummary]:
        """Create or update analytics summary."""
        return self.summary_service.create(
            tenant_id=tenant_id,
            user_id=user_id,
            route=route,
            analytics_type=analytics_type,
            period_start_ts=period_start_ts,
            period_end_ts=period_end_ts,
            period_type=period_type,
            total_events=summary_data["total_events"],
            unique_sessions=summary_data["unique_sessions"],
            unique_users=summary_data["unique_users"],
            metrics=summary_data["metrics"],
            content={
                "last_tallied_utc_ts": self._get_current_timestamp(),
                "event_count": summary_data["total_events"]
            }
        )
    
    @service_method("aggregate_multiple_routes")

    
    def aggregate_multiple_routes(self, routes: List[str],
                                 period_start_ts: float, period_end_ts: float,
                                 period_type: str = "hourly") -> ServiceResult[List[WebsiteAnalyticsSummary]]:
        """
        Aggregate analytics for multiple routes efficiently.
        
        This is useful for batch processing or scheduled jobs.
        
        Args:
            routes: List of routes to process
            tenant_id: Tenant ID for access control
            user_id: User ID for audit trail
            period_start_ts: Start of aggregation period
            period_end_ts: End of aggregation period
            period_type: Type of period (hourly, daily, etc.)
            
        Returns:
            ServiceResult containing list of created summaries
        """
        self.request_context.require_authentication()
        tenant_id = self.request_context.target_tenant_id
        user_id = self.request_context.target_user_id
        
        try:
            logger.info(f"Starting batch aggregation for {len(routes)} routes")
            
            summaries = []
            failed_routes = []
            
            for route in routes:
                result = self.aggregate_analytics_for_route(
                    route, period_start_ts, period_end_ts, period_type
                )
                
                if result.success:
                    summaries.append(result.data)
                else:
                    failed_routes.append({
                        'route': route,
                        'message': result.message,
                        'error_code': result.error_code
                    })
                    logger.warning(f"Failed to aggregate route {route}: {result.message}")
            
            if failed_routes:
                logger.warning(f"Batch aggregation completed with {len(failed_routes)} failures out of {len(routes)} routes")
                return ServiceResult.error_result(
                    message=f"Batch aggregation completed with failures: {len(failed_routes)}/{len(routes)} failed",
                    error_code=ErrorCode.PARTIAL_FAILURE,
                    error_details={
                        'successful_count': len(summaries),
                        'failed_count': len(failed_routes),
                        'failed_routes': failed_routes,
                        'successful_summaries': summaries
                    }
                )
            else:
                logger.info(f"Batch aggregation completed successfully for all {len(routes)} routes")
                return ServiceResult.success_result(summaries)
                
        except Exception as e:
            logger.error(f"Error in batch aggregation operation: {str(e)}")
            return ServiceResult.exception_result(
                e,
                error_code=ErrorCode.BATCH_OPERATION_FAILED,
                context="Failed to process batch aggregation operation"
            )
    
    @service_method("aggregate_hourly")

    
    def aggregate_hourly(self, 
                        hours_ago: int = 1) -> ServiceResult[List[WebsiteAnalyticsSummary]]:
        """
        Aggregate analytics for the last N hours.
        
        This is the main method to be called by EventBridge scheduled jobs.
        
        Args:
            tenant_id: Tenant ID for access control
            user_id: User ID for audit trail
            hours_ago: How many hours ago to start aggregation from
            
        Returns:
            ServiceResult containing list of created summaries
        """
        self.request_context.require_authentication()
        tenant_id = self.request_context.target_tenant_id
        user_id = self.request_context.target_user_id
        
        try:
            current_time = self._get_current_timestamp()
            period_end_ts = current_time
            period_start_ts = current_time - (hours_ago * 3600)  # Convert hours to seconds
            
            logger.info(f"Starting hourly aggregation for period: {period_start_ts} to {period_end_ts}")
            
            # Get all analytics in the time period with pagination support
            all_analytics = []
            start_key = None
            pagination_iterations = 0
            pagination_start_time = time.time()
            
            while True:
                pagination_iterations += 1
                pagination_elapsed = time.time() - pagination_start_time
                
                # Check pagination limits
                if pagination_iterations > self.max_pagination_iterations:
                    logger.warning(
                        "Hourly analytics pagination iteration limit exceeded",
                        extra={
                            "metric_name": "HourlyAnalyticsPaginationIterationsExceeded",
                            "metric_value": pagination_iterations,
                            "tenant_id": tenant_id,
                            "analytics_collected": len(all_analytics),
                            "max_iterations": self.max_pagination_iterations
                        }
                    )
                    if self.halt_on_pagination_limit:
                        logger.error(f"Halting pagination after {pagination_iterations} iterations")
                        break
                
                if pagination_elapsed > self.max_pagination_time_seconds:
                    logger.warning(
                        "Hourly analytics pagination time limit exceeded",
                        extra={
                            "metric_name": "HourlyAnalyticsPaginationTimeExceeded",
                            "metric_value": pagination_elapsed,
                            "tenant_id": tenant_id,
                            "analytics_collected": len(all_analytics),
                            "max_time_seconds": self.max_pagination_time_seconds
                        }
                    )
                    if self.halt_on_pagination_limit:
                        logger.error(f"Halting pagination after {pagination_elapsed:.2f} seconds")
                        break
                
                analytics_result = self.analytics_service.list_by_tenant(start_key=start_key)
                
                if not analytics_result.success:
                    return analytics_result
                
                # Add this page of results
                if analytics_result.data:
                    all_analytics.extend(analytics_result.data)
                
                # Check if there are more pages via error_details
                if (analytics_result.error_details and 
                    'last_evaluated_key' in analytics_result.error_details):
                    start_key = analytics_result.error_details['last_evaluated_key']
                    logger.debug(f"Fetching next page of tenant analytics, total so far: {len(all_analytics)}")
                else:
                    # No more pages
                    break
            
            # Log pagination metrics
            logger.info(
                "Pagination completed for hourly aggregation",
                extra={
                    "metric_name": "HourlyAnalyticsPaginationCompleted",
                    "iterations": pagination_iterations,
                    "elapsed_seconds": pagination_elapsed,
                    "analytics_collected": len(all_analytics),
                    "tenant_id": tenant_id
                }
            )
            
            # Filter by time period and group by route
            routes_with_data: Set[str] = set()
            for analytics in all_analytics:
                if period_start_ts <= analytics.created_utc_ts <= period_end_ts:
                    if analytics.route:
                        routes_with_data.add(analytics.route)
            
            if not routes_with_data:
                logger.info("No routes with analytics data in the specified period")
                return ServiceResult.success_result([])
            
            # Aggregate each route
            return self.aggregate_multiple_routes(
                list(routes_with_data),
                period_start_ts, period_end_ts, "hourly"
            )
            
        except Exception as e:
            logger.error(f"Error in hourly aggregation: {str(e)}")
            return ServiceResult.exception_result(
                e,
                error_code=ErrorCode.OPERATION_FAILED,
                context="Failed to process hourly aggregation"
            )
    
    def _get_current_timestamp(self) -> float:
        """Get current UTC timestamp."""
        return dt.datetime.now(dt.UTC).timestamp()
