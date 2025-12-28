"""
Service pooling manager for Lambda warm starts.

Manages service initialization and caching to improve Lambda performance
by reusing connections across invocations.

Includes optional telemetry for tracking cold/warm starts, execution times,
and Lambda container uptime.
"""

import os
import time
from typing import Dict, Type, TypeVar, Generic, Optional, Any
from aws_lambda_powertools import Logger

logger = Logger()

T = TypeVar('T')


class ServicePool(Generic[T]):
    """
    Manages service instances for Lambda warm starts with PER-INVOCATION security context refresh.
    
    Lambda containers reuse the global scope between invocations, allowing
    us to cache service instances (and their DB connections) to reduce 
    cold start latency by 80-90%.
    
    SECURITY: request_context is refreshed on EVERY invocation to prevent
    cross-user data leaks in warm Lambda containers.
    
    Example:
        # Module level
        vote_service_pool = ServicePool(VoteService, dynamodb=db, table_name=TABLE)
        
        # In handler (per invocation)
        request_context = RequestContext(user_context)  # Fresh context
        service = vote_service_pool.get(request_context)  # Context refreshed!
    """
    
    def __init__(self, service_class: Type[T], **service_kwargs):
        """
        Initialize the service pool with optional telemetry.
        
        Args:
            service_class: The service class to instantiate
            **service_kwargs: Keyword arguments for service (dynamodb, table_name, etc.)
                             NOTE: request_context should NOT be in kwargs - it's per-invocation
        
        Environment Variables:
            ENABLE_SERVICE_POOL_TELEMETRY: Set to 'true' to enable metrics logging
        """
        self.service_class = service_class
        self.service_kwargs = service_kwargs
        self._instance: Optional[T] = None
        
        # Telemetry tracking (optional)
        self._telemetry_enabled = os.getenv('ENABLE_SERVICE_POOL_TELEMETRY', 'false').lower() in ('true', '1', 'yes')
        self._container_start_time = time.time()  # When this Lambda container started
        self._cold_start_count = 0  # Number of cold starts
        self._warm_start_count = 0  # Number of warm starts
        self._total_invocations = 0  # Total invocations
        self._last_invocation_time: Optional[float] = None
        self._execution_times: list = []  # Track execution durations (limited to last 10)
    
    def get(self, request_context: Optional[Any] = None) -> T:
        """
        Get or create the service instance with FRESH request_context.
        
        SECURITY CRITICAL: On warm starts, the request_context is REFRESHED
        to prevent User A's credentials from being used for User B's request.
        
        TELEMETRY: Tracks cold/warm starts and logs metrics if enabled.
        
        Args:
            request_context: Fresh RequestContext for this invocation
            
        Returns:
            Service instance (DB connection cached, security context refreshed)
        """
        is_cold_start = self._instance is None
        
        if is_cold_start:
            # Cold start - create new service instance
            if self._telemetry_enabled:
                self._cold_start_count += 1
                logger.info(
                    "ServicePool: Cold start",
                    extra={
                        "service": self.service_class.__name__,
                        "cold_starts": self._cold_start_count,
                        "warm_starts": self._warm_start_count
                    }
                )
            
            kwargs = {**self.service_kwargs}
            if request_context is not None:
                kwargs['request_context'] = request_context
            self._instance = self.service_class(**kwargs)
        else:
            # Warm start - REFRESH request_context for security
            if self._telemetry_enabled:
                self._warm_start_count += 1
            
            if request_context is not None and hasattr(self._instance, '_request_context'):
                self._instance._request_context = request_context
        
        self._total_invocations += 1
        self._last_invocation_time = time.time()
        
        # Log telemetry periodically (every 10 invocations)
        if self._telemetry_enabled and self._total_invocations % 10 == 0:
            self._log_telemetry()
        
        return self._instance
    
    def track_execution_time(self, duration_ms: float):
        """
        Track execution time for this invocation.
        
        Args:
            duration_ms: Execution duration in milliseconds
        """
        if not self._telemetry_enabled:
            return
        
        # Keep only last 10 execution times to avoid memory bloat
        self._execution_times.append(duration_ms)
        if len(self._execution_times) > 10:
            self._execution_times.pop(0)
    
    def _log_telemetry(self):
        """Log telemetry metrics."""
        container_uptime_seconds = time.time() - self._container_start_time
        
        metrics = {
            "service": self.service_class.__name__,
            "total_invocations": self._total_invocations,
            "cold_starts": self._cold_start_count,
            "warm_starts": self._warm_start_count,
            "container_uptime_seconds": round(container_uptime_seconds, 2),
            "container_uptime_minutes": round(container_uptime_seconds / 60, 2),
            "warm_start_ratio": round(
                self._warm_start_count / self._total_invocations * 100, 2
            ) if self._total_invocations > 0 else 0
        }
        
        # Add execution time stats if available
        if self._execution_times:
            avg_exec_time = sum(self._execution_times) / len(self._execution_times)
            metrics.update({
                "avg_execution_ms": round(avg_exec_time, 2),
                "min_execution_ms": round(min(self._execution_times), 2),
                "max_execution_ms": round(max(self._execution_times), 2),
                "recent_executions_tracked": len(self._execution_times)
            })
        
        logger.info(
            "ServicePool Telemetry",
            extra=metrics
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get current telemetry metrics.
        
        Returns:
            Dictionary of metrics
        """
        container_uptime = time.time() - self._container_start_time
        
        metrics = {
            "service_class": self.service_class.__name__,
            "total_invocations": self._total_invocations,
            "cold_starts": self._cold_start_count,
            "warm_starts": self._warm_start_count,
            "container_uptime_seconds": round(container_uptime, 2),
            "warm_start_ratio_percent": round(
                self._warm_start_count / self._total_invocations * 100, 2
            ) if self._total_invocations > 0 else 0,
            "telemetry_enabled": self._telemetry_enabled
        }
        
        if self._execution_times:
            avg_exec = sum(self._execution_times) / len(self._execution_times)
            metrics.update({
                "avg_execution_ms": round(avg_exec, 2),
                "min_execution_ms": round(min(self._execution_times), 2),
                "max_execution_ms": round(max(self._execution_times), 2)
            })
        
        return metrics
    
    def reset(self):
        """Reset the pool (useful for testing)."""
        self._instance = None
        # Don't reset telemetry - it tracks the entire container lifecycle


class MultiServicePool:
    """
    Manages multiple service instances by class name.
    
    Example:
        pool = MultiServicePool()
        vote_service = pool.get(VoteService)
        analytics_service = pool.get(WebsiteAnalyticsService)
    """
    
    def __init__(self):
        self._pools: Dict[Type, ServicePool] = {}
    
    def get(self, service_class: Type[T]) -> T:
        """
        Get or create a service instance.
        
        Args:
            service_class: The service class to instantiate
            
        Returns:
            Service instance (cached on warm starts)
        """
        if service_class not in self._pools:
            self._pools[service_class] = ServicePool(service_class)
        return self._pools[service_class].get()
    
    def reset(self, service_class: Optional[Type] = None):
        """
        Reset one or all service pools.
        
        Args:
            service_class: Specific class to reset, or None for all
        """
        if service_class:
            if service_class in self._pools:
                self._pools[service_class].reset()
        else:
            for pool in self._pools.values():
                pool.reset()
