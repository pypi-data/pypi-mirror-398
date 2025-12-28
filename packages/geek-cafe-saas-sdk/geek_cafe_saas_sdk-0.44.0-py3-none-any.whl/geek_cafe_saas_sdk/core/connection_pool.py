"""
Connection pool manager for database connections.

Maintains a pool of database connections at the module level to avoid
recreating connections on every Lambda invocation (cold start optimization).
"""

import threading
from typing import Dict, Any, Optional, Callable
from aws_lambda_powertools import Logger

logger = Logger()


class ConnectionPool:
    """
    Thread-safe connection pool for Lambda functions.
    
    Maintains connections at module level so they persist across
    Lambda warm invocations. New containers can reuse existing connections.
    """
    
    def __init__(self):
        """Initialize empty connection pool."""
        self._connections: Dict[str, Any] = {}
        self._lock = threading.Lock()
        self._factories: Dict[str, Callable] = {}
    
    def register_factory(self, connection_type: str, factory: Callable) -> None:
        """
        Register a factory function for creating connections.
        
        Args:
            connection_type: Type of connection (e.g., "dynamodb", "redis")
            factory: Factory function that creates the connection
        """
        with self._lock:
            self._factories[connection_type] = factory
            logger.debug(f"Registered connection factory for: {connection_type}")
    
    def get_connection(self, connection_type: str, force_new: bool = False) -> Any:
        """
        Get a connection from the pool.
        
        If connection doesn't exist, creates it using registered factory.
        If force_new is True, creates a new connection even if one exists.
        
        Args:
            connection_type: Type of connection to get
            force_new: Force creation of new connection
            
        Returns:
            Connection object
            
        Raises:
            ValueError: If no factory registered for connection type
        """
        with self._lock:
            # Check if we need to create new connection
            if force_new or connection_type not in self._connections:
                if connection_type not in self._factories:
                    raise ValueError(
                        f"No factory registered for connection type: {connection_type}. "
                        f"Call register_factory() first."
                    )
                
                logger.debug(f"Creating new connection: {connection_type}")
                factory = self._factories[connection_type]
                connection = factory()
                self._connections[connection_type] = connection
            else:
                logger.debug(f"Reusing existing connection: {connection_type}")
            
            return self._connections[connection_type]
    
    def close_connection(self, connection_type: str) -> None:
        """
        Close and remove a connection from pool.
        
        Args:
            connection_type: Type of connection to close
        """
        with self._lock:
            if connection_type in self._connections:
                logger.debug(f"Closing connection: {connection_type}")
                connection = self._connections[connection_type]
                
                # Try to close gracefully if connection has close method
                if hasattr(connection, 'close'):
                    try:
                        connection.close()
                    except Exception as e:
                        logger.warning(f"Error closing connection {connection_type}: {e}")
                
                del self._connections[connection_type]
    
    def close_all(self) -> None:
        """Close all connections in pool."""
        with self._lock:
            for connection_type in list(self._connections.keys()):
                self.close_connection(connection_type)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about connection pool.
        
        Returns:
            Dict with pool statistics
        """
        with self._lock:
            return {
                "active_connections": len(self._connections),
                "connection_types": list(self._connections.keys()),
                "registered_factories": list(self._factories.keys())
            }


# Module-level singleton instance
# This persists across Lambda invocations in warm containers
_connection_pool = ConnectionPool()


def get_connection_pool() -> ConnectionPool:
    """
    Get the module-level connection pool singleton.
    
    Returns:
        ConnectionPool instance
    """
    return _connection_pool


def register_connection_factory(connection_type: str, factory: Callable) -> None:
    """
    Register a connection factory with the global pool.
    
    Args:
        connection_type: Type of connection (e.g., "dynamodb")
        factory: Factory function
    """
    _connection_pool.register_factory(connection_type, factory)


def get_pooled_connection(connection_type: str, force_new: bool = False) -> Any:
    """
    Get a connection from the global pool.
    
    Args:
        connection_type: Type of connection
        force_new: Force new connection
        
    Returns:
        Connection object
    """
    return _connection_pool.get_connection(connection_type, force_new)
