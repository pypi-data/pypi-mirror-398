#!/usr/bin/env python3
"""
#exonware/xwdata/src/exonware/xwdata/errors.py

XWData Error Classes

This module defines all error classes for the xwdata library,
providing rich error context and actionable error messages.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 26-Oct-2025
"""

from typing import Any, Optional


# ==============================================================================
# BASE ERROR
# ==============================================================================

class XWDataError(Exception):
    """
    Base exception for all xwdata errors.
    
    Provides rich error context with actionable suggestions.
    """
    
    def __init__(
        self,
        message: str,
        *,
        operation: Optional[str] = None,
        path: Optional[str] = None,
        format: Optional[str] = None,
        context: Optional[dict[str, Any]] = None,
        suggestion: Optional[str] = None
    ):
        """
        Initialize xwdata error with rich context.
        
        Args:
            message: Error message
            operation: Operation being performed
            path: File path (if applicable)
            format: Data format (if applicable)
            context: Additional context
            suggestion: Actionable suggestion for fixing
        """
        self.message = message
        self.operation = operation
        self.path = path
        self.format = format
        self.context = context or {}
        self.suggestion = suggestion
        
        # Build detailed error message
        parts = [message]
        
        if operation:
            parts.append(f"Operation: {operation}")
        if path:
            parts.append(f"Path: {path}")
        if format:
            parts.append(f"Format: {format}")
        if context:
            context_str = ", ".join(f"{k}={v}" for k, v in context.items())
            parts.append(f"Context: {context_str}")
        if suggestion:
            parts.append(f"Suggestion: {suggestion}")
        
        full_message = " | ".join(parts)
        super().__init__(full_message)


# ==============================================================================
# SECURITY ERRORS
# ==============================================================================

class XWDataSecurityError(XWDataError):
    """Raised for security violations."""
    
    def __init__(self, message: str, **kwargs):
        if 'suggestion' not in kwargs:
            kwargs['suggestion'] = "Check security configuration and validate input data"
        super().__init__(message, operation='security_check', **kwargs)


class XWDataPathSecurityError(XWDataSecurityError):
    """Raised for path security violations."""
    
    def __init__(self, message: str, path: str, **kwargs):
        super().__init__(
            message,
            path=path,
            suggestion="Ensure path is within allowed directories and doesn't contain traversal patterns",
            **kwargs
        )


class XWDataSizeLimitError(XWDataSecurityError):
    """Raised when file size exceeds limits."""
    
    def __init__(self, message: str, size: int, limit: int, **kwargs):
        super().__init__(
            message,
            context={'size_bytes': size, 'limit_bytes': limit},
            suggestion=f"File size {size} exceeds limit {limit}. Increase limit or use streaming.",
            **kwargs
        )


# ==============================================================================
# PARSE/SERIALIZE ERRORS
# ==============================================================================

class XWDataParseError(XWDataError):
    """Raised when parsing fails."""
    
    def __init__(
        self,
        message: str,
        format: Optional[str] = None,
        line: Optional[int] = None,
        column: Optional[int] = None,
        snippet: Optional[str] = None,
        **kwargs
    ):
        context = kwargs.get('context', {})
        if line:
            context['line'] = line
        if column:
            context['column'] = column
        if snippet:
            context['snippet'] = snippet
        
        kwargs['context'] = context
        kwargs['suggestion'] = f"Check {format or 'data'} syntax and ensure valid format"
        
        super().__init__(message, operation='parse', format=format, **kwargs)


class XWDataSerializeError(XWDataError):
    """Raised when serialization fails."""
    
    def __init__(
        self,
        message: str,
        format: Optional[str] = None,
        data_type: Optional[str] = None,
        **kwargs
    ):
        if data_type:
            kwargs['context'] = kwargs.get('context', {})
            kwargs['context']['data_type'] = data_type
        
        kwargs['suggestion'] = f"Ensure data is compatible with {format or 'target'} format"
        
        super().__init__(message, operation='serialize', format=format, **kwargs)


# ==============================================================================
# I/O ERRORS
# ==============================================================================

class XWDataIOError(XWDataError):
    """Raised for I/O operation failures."""
    
    def __init__(self, message: str, path: Optional[str] = None, **kwargs):
        kwargs['suggestion'] = "Check file permissions and ensure path exists"
        super().__init__(message, operation='io', path=path, **kwargs)


class XWDataFileNotFoundError(XWDataIOError):
    """Raised when file is not found."""
    
    def __init__(self, path: str, **kwargs):
        super().__init__(
            f"File not found: {path}",
            path=path,
            suggestion="Ensure file exists and path is correct",
            **kwargs
        )


# ==============================================================================
# ENGINE ERRORS
# ==============================================================================

class XWDataEngineError(XWDataError):
    """Raised for engine operation failures."""
    
    def __init__(self, message: str, **kwargs):
        # Set operation if not already provided
        if 'operation' not in kwargs:
            kwargs['operation'] = 'engine'
        super().__init__(message, **kwargs)


class XWDataStrategyError(XWDataEngineError):
    """Raised for format strategy errors."""
    
    def __init__(self, message: str, strategy: Optional[str] = None, **kwargs):
        if strategy:
            kwargs['context'] = kwargs.get('context', {})
            kwargs['context']['strategy'] = strategy
        
        kwargs['suggestion'] = "Check format strategy configuration and ensure strategy is registered"
        super().__init__(message, **kwargs)


# ==============================================================================
# METADATA ERRORS
# ==============================================================================

class XWDataMetadataError(XWDataError):
    """Raised for metadata operation failures."""
    
    def __init__(self, message: str, **kwargs):
        kwargs['suggestion'] = "Check metadata configuration and ensure valid metadata structure"
        super().__init__(message, operation='metadata', **kwargs)


# ==============================================================================
# REFERENCE ERRORS
# ==============================================================================

class XWDataReferenceError(XWDataError):
    """Raised for reference resolution failures."""
    
    def __init__(self, message: str, reference: Optional[str] = None, **kwargs):
        if reference:
            kwargs['context'] = kwargs.get('context', {})
            kwargs['context']['reference'] = reference
        
        kwargs['suggestion'] = "Check reference path and ensure referenced file exists"
        super().__init__(message, operation='reference_resolution', **kwargs)


class XWDataCircularReferenceError(XWDataReferenceError):
    """Raised when circular references are detected."""
    
    def __init__(self, message: str, cycle: Optional[list[str]] = None, **kwargs):
        if cycle:
            kwargs['context'] = kwargs.get('context', {})
            kwargs['context']['cycle'] = ' → '.join(cycle)
        
        kwargs['suggestion'] = "Break circular reference chain or enable circular reference handling"
        super().__init__(message, **kwargs)


# ==============================================================================
# CACHE ERRORS
# ==============================================================================

class XWDataCacheError(XWDataError):
    """Raised for cache operation failures."""
    
    def __init__(self, message: str, **kwargs):
        kwargs['suggestion'] = "Check cache configuration and available memory"
        super().__init__(message, operation='cache', **kwargs)


# ==============================================================================
# NODE ERRORS
# ==============================================================================

class XWDataNodeError(XWDataError):
    """Raised for node operation failures."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, operation='node', **kwargs)


class XWDataPathError(XWDataNodeError):
    """Raised for invalid path operations."""
    
    def __init__(self, message: str, path: Optional[str] = None, **kwargs):
        kwargs['suggestion'] = "Check path syntax (dot-separated or bracket notation)"
        super().__init__(message, path=path, **kwargs)


class XWDataTypeError(XWDataNodeError):
    """Raised for type-related errors."""
    
    def __init__(self, message: str, expected_type: Optional[str] = None, actual_type: Optional[str] = None, **kwargs):
        if expected_type or actual_type:
            kwargs['context'] = kwargs.get('context', {})
            if expected_type:
                kwargs['context']['expected_type'] = expected_type
            if actual_type:
                kwargs['context']['actual_type'] = actual_type
        
        kwargs['suggestion'] = "Ensure data type matches expected type for operation"
        super().__init__(message, **kwargs)


# ==============================================================================
# VALIDATION ERRORS
# ==============================================================================

class XWDataValidationError(XWDataError):
    """Raised for validation failures."""
    
    def __init__(self, message: str, field: Optional[str] = None, **kwargs):
        if field:
            kwargs['context'] = kwargs.get('context', {})
            kwargs['context']['field'] = field
        
        kwargs['suggestion'] = "Check data against validation rules and schema"
        super().__init__(message, operation='validation', **kwargs)


# ==============================================================================
# CONFIGURATION ERRORS
# ==============================================================================

class XWDataConfigError(XWDataError):
    """Raised for configuration errors."""
    
    def __init__(self, message: str, config_key: Optional[str] = None, **kwargs):
        if config_key:
            kwargs['context'] = kwargs.get('context', {})
            kwargs['context']['config_key'] = config_key
        
        kwargs['suggestion'] = "Check configuration values and ensure valid settings"
        super().__init__(message, operation='configuration', **kwargs)


# ==============================================================================
# EXPORTS
# ==============================================================================

__all__ = [
    # Base
    'XWDataError',
    
    # Security
    'XWDataSecurityError',
    'XWDataPathSecurityError',
    'XWDataSizeLimitError',
    
    # Parse/Serialize
    'XWDataParseError',
    'XWDataSerializeError',
    
    # I/O
    'XWDataIOError',
    'XWDataFileNotFoundError',
    
    # Engine
    'XWDataEngineError',
    'XWDataStrategyError',
    
    # Metadata
    'XWDataMetadataError',
    
    # References
    'XWDataReferenceError',
    'XWDataCircularReferenceError',
    
    # Cache
    'XWDataCacheError',
    
    # Node
    'XWDataNodeError',
    'XWDataPathError',
    'XWDataTypeError',
    
    # Validation
    'XWDataValidationError',
    
    # Configuration
    'XWDataConfigError',
]

