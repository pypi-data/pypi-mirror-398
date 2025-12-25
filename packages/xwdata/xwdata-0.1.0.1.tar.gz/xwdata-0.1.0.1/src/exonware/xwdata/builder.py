#!/usr/bin/env python3
"""
#exonware/xwdata/src/exonware/xwdata/builder.py

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: October 27, 2025

Builder pattern for XWData construction.

Provides fluent API for building complex data structures.

Priority Alignment:
1. Security - Safe data building with validation
2. Usability - Fluent, chainable API
3. Maintainability - Clean builder pattern
4. Performance - Efficient construction
5. Extensibility - Easy to extend builders
"""

from typing import Any, Optional, Union, Callable
from pathlib import Path


class XWDataBuilder:
    """
    Fluent builder for XWData construction.
    
    Enables chainable method calls for building complex data structures.
    
    Examples:
        >>> from exonware.xwdata import XWDataBuilder
        >>> data = (XWDataBuilder()
        ...     .set("name", "Alice")
        ...     .set("age", 30)
        ...     .set("address.city", "New York")
        ...     .set("tags", ["python", "data"])
        ...     .build())
        >>> 
        >>> # Or build from dict and modify
        >>> data = (XWDataBuilder({"name": "Bob"})
        ...     .set("age", 25)
        ...     .append("skills", "Python")
        ...     .append("skills", "JavaScript")
        ...     .build())
    """
    
    def __init__(self, initial_data: Optional[dict[str, Any]] = None):
        """
        Initialize builder.
        
        Args:
            initial_data: Initial data dictionary
        """
        self._data = initial_data if initial_data is not None else {}
        self._metadata = {}
        self._config = None
    
    def set(self, path: str, value: Any) -> 'XWDataBuilder':
        """
        Set value at path (supports nested paths with dots).
        
        Args:
            path: Path to set (e.g., "user.name" or "settings.api.timeout")
            value: Value to set
            
        Returns:
            Self for chaining
        """
        keys = path.split('.')
        current = self._data
        
        # Navigate to parent
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Set final value
        current[keys[-1]] = value
        return self
    
    def append(self, path: str, value: Any) -> 'XWDataBuilder':
        """
        Append value to list at path.
        
        Args:
            path: Path to list
            value: Value to append
            
        Returns:
            Self for chaining
        """
        keys = path.split('.')
        current = self._data
        
        # Navigate to parent
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Append to list (create if doesn't exist)
        final_key = keys[-1]
        if final_key not in current:
            current[final_key] = []
        
        if not isinstance(current[final_key], list):
            current[final_key] = [current[final_key]]
        
        current[final_key].append(value)
        return self
    
    def merge(self, other_data: dict[str, Any]) -> 'XWDataBuilder':
        """
        Merge another dictionary into the builder.
        
        Args:
            other_data: Data to merge
            
        Returns:
            Self for chaining
        """
        from exonware.xwsystem.operations import deep_merge, MergeStrategy
        
        self._data = deep_merge(self._data, other_data, strategy=MergeStrategy.DEEP)
        return self
    
    def set_metadata(self, key: str, value: Any) -> 'XWDataBuilder':
        """
        Set metadata value.
        
        Args:
            key: Metadata key
            value: Metadata value
            
        Returns:
            Self for chaining
        """
        self._metadata[key] = value
        return self
    
    def with_config(self, config: 'XWDataConfig') -> 'XWDataBuilder':
        """
        Set configuration for the data.
        
        Args:
            config: XWData configuration
            
        Returns:
            Self for chaining
        """
        self._config = config
        return self
    
    def delete(self, path: str) -> 'XWDataBuilder':
        """
        Delete value at path.
        
        Args:
            path: Path to delete
            
        Returns:
            Self for chaining
        """
        keys = path.split('.')
        current = self._data
        
        # Navigate to parent
        for key in keys[:-1]:
            if key not in current:
                return self  # Path doesn't exist
            current = current[key]
        
        # Delete final key
        final_key = keys[-1]
        if final_key in current:
            del current[final_key]
        
        return self
    
    def transform(self, transformer: Callable[[dict], dict]) -> 'XWDataBuilder':
        """
        Apply transformation function to data.
        
        Args:
            transformer: Function that transforms data dict
            
        Returns:
            Self for chaining
        """
        self._data = transformer(self._data)
        return self
    
    def build(self) -> 'XWData':
        """
        Build the final XWData instance.
        
        Creates XWData with applied metadata and configuration.
        
        Returns:
            XWData instance with metadata and config applied
            
        Priority Alignment:
        - Usability: Simple builder API that applies all settings
        - Maintainability: Clean separation of concerns
        - Performance: Efficient metadata/config application
        """
        from ..facade import XWData
        from ..config import XWDataConfig
        
        # Create XWData from native with metadata and config
        # XWData constructor accepts metadata and config parameters
        result = XWData.from_native(
            self._data,
            metadata=self._metadata if self._metadata else None,
            config=self._config if self._config else None
        )
        
        # If metadata was provided but not applied during construction,
        # apply it to the node directly
        if self._metadata and result._node:
            for key, value in self._metadata.items():
                result._node.set_metadata(key, value)
            # Update facade metadata
            result._metadata = result._node.metadata
        
        return result
    
    def build_dict(self) -> dict[str, Any]:
        """
        Build as plain dictionary (no XWData wrapper).
        
        Returns:
            Plain dictionary
        """
        return self._data.copy()


__all__ = ["XWDataBuilder"]

