#!/usr/bin/env python3
"""
#exonware/xwdata/src/exonware/xwdata/operations/data_merge.py

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: October 27, 2025

Data-aware merge operations using xwsystem.operations.

Provides XWData-specific merge functionality with metadata preservation.
"""

from typing import Any, Optional
from exonware.xwsystem.operations import deep_merge, MergeStrategy, MergeError


class DataMerger:
    """
    Data-aware merger that preserves XWData metadata.
    
    Integrates xwsystem.operations with XWData-specific concerns like
    metadata preservation, format conversion, and COW semantics.
    
    Priority Alignment:
    1. Security - Safe merging with validation
    2. Usability - Simple API for data merging
    3. Maintainability - Delegates to xwsystem.operations
    4. Performance - Efficient merge with COW
    5. Extensibility - Multiple strategies supported
    """
    
    def __init__(self, preserve_metadata: bool = True):
        """
        Initialize data merger.
        
        Args:
            preserve_metadata: Whether to preserve XWData metadata
        """
        self.preserve_metadata = preserve_metadata
    
    def merge(
        self,
        target: Any,
        source: Any,
        strategy: MergeStrategy = MergeStrategy.DEEP,
        preserve_types: bool = True
    ) -> Any:
        """
        Merge two data structures with XWData awareness.
        
        Args:
            target: Target data
            source: Source data to merge
            strategy: Merge strategy
            preserve_types: Preserve XWData types if present
            
        Returns:
            Merged data
            
        Examples:
            >>> merger = DataMerger()
            >>> result = merger.merge(
            ...     {"a": 1, "b": {"c": 2}},
            ...     {"b": {"d": 3}},
            ...     strategy=MergeStrategy.DEEP
            ... )
            >>> # result: {"a": 1, "b": {"c": 2, "d": 3}}
        """
        # Check if inputs are XWData instances
        from ..facade import XWData
        
        target_native = target.to_native() if isinstance(target, XWData) else target
        source_native = source.to_native() if isinstance(source, XWData) else source
        
        # Use xwsystem.operations for the merge
        result = deep_merge(target_native, source_native, strategy=strategy)
        
        # If target was XWData and we want to preserve types, return XWData
        if isinstance(target, XWData) and preserve_types:
            return XWData.from_native(result)
        
        return result


def merge_data(
    target: Any,
    source: Any,
    strategy: MergeStrategy = MergeStrategy.DEEP,
    preserve_metadata: bool = True
) -> Any:
    """
    Convenience function for merging data.
    
    Args:
        target: Target data
        source: Source data to merge
        strategy: Merge strategy
        preserve_metadata: Preserve XWData metadata
        
    Returns:
        Merged data
        
    Examples:
        >>> from exonware.xwdata import merge_data, MergeStrategy
        >>> result = merge_data(
        ...     {"a": 1},
        ...     {"b": 2},
        ...     strategy=MergeStrategy.DEEP
        ... )
    """
    merger = DataMerger(preserve_metadata=preserve_metadata)
    return merger.merge(target, source, strategy=strategy)


__all__ = ["DataMerger", "merge_data"]

