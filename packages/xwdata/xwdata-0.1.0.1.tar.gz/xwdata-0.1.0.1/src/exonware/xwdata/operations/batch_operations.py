#!/usr/bin/env python3
"""
#exonware/xwdata/src/exonware/xwdata/operations/batch_operations.py

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: October 27, 2025

Batch operations for efficient data processing.
"""

import asyncio
from typing import Any, Callable, Optional
from concurrent.futures import ThreadPoolExecutor


class BatchOperations:
    """
    Batch operations for efficient data processing.
    
    Priority Alignment:
    1. Security - Safe batch processing
    2. Usability - Simple batch API
    3. Maintainability - Clean implementation
    4. Performance - Concurrent processing
    5. Extensibility - Multiple batch modes
    """
    
    def __init__(self, max_workers: int = 4):
        """
        Initialize batch operations.
        
        Args:
            max_workers: Maximum concurrent workers
        """
        self.max_workers = max_workers
    
    async def batch_convert_async(
        self,
        items: list[Any],
        target_format: str,
        **kwargs
    ) -> list[Any]:
        """
        Convert multiple items to target format concurrently.
        
        Args:
            items: Items to convert
            target_format: Target format
            **kwargs: Conversion options
            
        Returns:
            List of converted items
        """
        from ..facade import XWData
        
        async def convert_one(item):
            if not isinstance(item, XWData):
                item = XWData.from_native(item)
            # Return serialized data in target format
            return await item.serialize_async(target_format, **kwargs)
        
        tasks = [convert_one(item) for item in items]
        return await asyncio.gather(*tasks)
    
    def batch_convert(
        self,
        items: list[Any],
        target_format: str,
        **kwargs
    ) -> list[Any]:
        """
        Convert multiple items to target format (sync).
        
        Args:
            items: Items to convert
            target_format: Target format
            **kwargs: Conversion options
            
        Returns:
            List of converted items
        """
        from ..facade import XWData
        
        results = []
        for item in items:
            if not isinstance(item, XWData):
                item = XWData.from_native(item)
            results.append(item.serialize(target_format, **kwargs))
        
        return results
    
    async def batch_validate_async(
        self,
        items: list[Any],
        validator: Callable[[Any], bool]
    ) -> list[bool]:
        """
        Validate multiple items concurrently.
        
        Args:
            items: Items to validate
            validator: Validation function
            
        Returns:
            List of validation results
        """
        async def validate_one(item):
            return validator(item)
        
        tasks = [validate_one(item) for item in items]
        return await asyncio.gather(*tasks)
    
    async def batch_transform_async(
        self,
        items: list[Any],
        transformer: Callable[[Any], Any]
    ) -> list[Any]:
        """
        Transform multiple items concurrently.
        
        Args:
            items: Items to transform
            transformer: Transformation function
            
        Returns:
            List of transformed items
        """
        async def transform_one(item):
            result = transformer(item)
            # If transformer returns coroutine, await it
            if asyncio.iscoroutine(result):
                return await result
            return result
        
        tasks = [transform_one(item) for item in items]
        return await asyncio.gather(*tasks)


# Convenience functions
def batch_convert(
    items: list[Any],
    target_format: str,
    **kwargs
) -> list[Any]:
    """
    Batch convert items to target format.
    
    Examples:
        >>> from exonware.xwdata import batch_convert
        >>> items = [{"a": 1}, {"b": 2}]
        >>> results = batch_convert(items, "json")
    """
    batch_ops = BatchOperations()
    return batch_ops.batch_convert(items, target_format, **kwargs)


def batch_validate(
    items: list[Any],
    validator: Callable[[Any], bool]
) -> list[bool]:
    """
    Batch validate items.
    
    Examples:
        >>> from exonware.xwdata import batch_validate
        >>> items = [1, 2, "invalid", 4]
        >>> results = batch_validate(items, lambda x: isinstance(x, int))
        >>> # [True, True, False, True]
    """
    batch_ops = BatchOperations()
    return asyncio.run(batch_ops.batch_validate_async(items, validator))


def batch_transform(
    items: list[Any],
    transformer: Callable[[Any], Any]
) -> list[Any]:
    """
    Batch transform items.
    
    Examples:
        >>> from exonware.xwdata import batch_transform
        >>> items = [1, 2, 3]
        >>> results = batch_transform(items, lambda x: x * 2)
        >>> # [2, 4, 6]
    """
    batch_ops = BatchOperations()
    return asyncio.run(batch_ops.batch_transform_async(items, transformer))


__all__ = ["BatchOperations", "batch_convert", "batch_validate", "batch_transform"]

