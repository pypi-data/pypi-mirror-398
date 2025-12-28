"""Base service classes for collaborative property operations."""


import traceback
from typing import Any, Dict, List, Optional, TypeVar, Generic
from datetime import datetime

from aws_lambda_powertools import Logger

logger = Logger()


T = TypeVar('T')


class ServiceResult(Generic[T]):
    """Standard service operation result with enhanced error handling."""
    
    def __init__(self, success: bool, data: Optional[T] = None, 
                 message: Optional[str] = None, error_code: Optional[str] = None,
                 error_details: Optional[Dict[str, Any]] = None,
                 stack_trace: Optional[str] = None,
                 http_status: Optional[int] = None):
        self.success = success
        self.data = data
        self.message = message
        self.error_code = error_code
        self.error_details = error_details or {}
        self.stack_trace = stack_trace
        self.timestamp = datetime.now()
        self.version = {}
        self.diagnostics = {}
        self.count = 0
        self.http_status = http_status  # Optional override for HTTP status code        
        
    
    @classmethod
    def success_result(cls, data: T, http_status: Optional[int] = None) -> 'ServiceResult[T]':
        """Create a successful result.
        
        Args:
            data: The result data
            http_status: Optional HTTP status code override (e.g., 200 for update, 201 for create)
        """
        response = cls(success=True, data=data, http_status=http_status)
        if isinstance(data, list):
            response.count = len(data)       
        elif data is not None:
            response.count = 1
        else:
            response.count = 0
        return response
    
    @classmethod
    def created_result(cls, data: T) -> 'ServiceResult[T]':
        """Create a successful result for a CREATE operation (HTTP 201)."""
        return cls.success_result(data, http_status=201)
    
    @classmethod
    def updated_result(cls, data: T) -> 'ServiceResult[T]':
        """Create a successful result for an UPDATE operation (HTTP 200)."""
        return cls.success_result(data, http_status=200)
    
    @classmethod
    def error_result(cls, message: str, error_code: Optional[str] = None, 
                    error_details: Optional[Dict[str, Any]] = None) -> 'ServiceResult[T]':
        """Create an error result with basic error information."""
        return cls(success=False, message=message, error_code=error_code, error_details=error_details)
    
    @classmethod
    def exception_result(cls, exception: Exception, error_code: Optional[str] = None,
                        context: Optional[str] = None) -> 'ServiceResult[T]':
        """Create an error result from an exception with full stack trace logging."""
        
        # Get the full stack trace
        stack_trace = traceback.format_exc()
        
        # Extract root cause from exception chain
        root_cause = exception
        exception_chain = []
        while root_cause:
            exception_chain.append({
                'type': type(root_cause).__name__,
                'message': str(root_cause)
            })
            # Follow the exception chain
            root_cause = root_cause.__cause__ or root_cause.__context__
            # Avoid infinite loops
            if root_cause in [e for chain in exception_chain[:-1] for e in [chain]]:
                break
        
        # Use the deepest exception as the root cause
        actual_root = exception_chain[-1] if exception_chain else {
            'type': type(exception).__name__,
            'message': str(exception)
        }
        
        # Create detailed error message including root cause
        error_message = f"{type(exception).__name__}: {str(exception)}"
        if len(exception_chain) > 1:
            error_message = f"{error_message} (Root cause: {actual_root['type']}: {actual_root['message']})"
        if context:
            error_message = f"{context} - {error_message}"
        
        # Prepare error details with exception chain
        error_details = {
            'exception_type': type(exception).__name__,
            'exception_message': str(exception),
            'root_cause_type': actual_root['type'],
            'root_cause_message': actual_root['message'],
            'exception_chain': exception_chain,
            'context': context,
            'timestamp': datetime.now().isoformat()
        }
        
        # Log the full error with stack trace to CloudWatch
        logger.error(
            f"Service operation failed: {error_message}\n"
            f"Context: {context or 'None'}\n"
            f"Exception Type: {type(exception).__name__}\n"
            f"Exception Message: {str(exception)}\n"
            f"Root Cause: {actual_root['type']}: {actual_root['message']}\n"
            f"Stack Trace:\n{stack_trace}",
            extra={
                'error_code': error_code,
                'exception_type': type(exception).__name__,
                'root_cause_type': actual_root['type'],
                'root_cause_message': actual_root['message'],
                'context': context,
                'stack_trace': stack_trace
            }
        )
        
        # Also print to console for immediate visibility
        print(f"\n🚨 SERVICE ERROR: {error_message}")
        print(f"📍 Context: {context or 'None'}")
        print(f"🔍 Exception Type: {type(exception).__name__}")
        if len(exception_chain) > 1:
            print(f"🎯 Root Cause: {actual_root['type']}: {actual_root['message']}")
            chain_str = ' → '.join([e['type'] for e in exception_chain])
            print(f"🔗 Exception Chain: {chain_str}")
        print(f"📝 Stack Trace:")
        print(stack_trace)
        print("" + "="*80 + "")
        
        return cls(
            success=False, 
            message=error_message, 
            error_code=error_code or 'INTERNAL_ERROR',
            error_details=error_details,
            stack_trace=stack_trace
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for API responses."""
        result = {
            'success': self.success,
            'timestamp': self.timestamp.isoformat()
        }
        
        if self.success:
            result['data'] = self.data
        else:
            result['error'] = {
                'message': self.message,
                'code': self.error_code,
                'details': self.error_details
            }
            # Only include stack trace in development/debug mode
            # You might want to add a flag to control this
            if self.stack_trace:
                result['error']['stack_trace'] = self.stack_trace
        
        return result







