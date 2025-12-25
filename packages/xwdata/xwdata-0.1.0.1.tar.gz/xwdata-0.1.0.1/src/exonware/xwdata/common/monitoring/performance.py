#!/usr/bin/env python3
"""
#exonware/xwdata/src/exonware/xwdata/common/monitoring/performance.py

Performance Monitor

Performance monitoring with context managers for operation tracking.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 26-Oct-2025
"""

import time
from typing import Any, Optional
from contextlib import asynccontextmanager
from exonware.xwsystem import get_logger

logger = get_logger(__name__)


class PerformanceMonitor:
    """
    Performance monitor with operation tracking.
    
    Provides context managers for tracking operation performance.
    """
    
    def __init__(self):
        """Initialize performance monitor."""
        self._timings: dict[str, list] = {}
    
    @asynccontextmanager
    async def track(self, operation: str):
        """
        Track operation performance.
        
        Usage:
            async with monitor.track('load'):
                result = await engine.load(path)
        
        Args:
            operation: Operation name
        """
        start_time = time.time()
        
        try:
            yield
        finally:
            elapsed = time.time() - start_time
            
            if operation not in self._timings:
                self._timings[operation] = []
            
            self._timings[operation].append(elapsed)
            
            logger.debug(f"Operation '{operation}' took {elapsed:.3f}s")
    
    def get_stats(self) -> dict[str, Any]:
        """Get performance statistics."""
        stats = {}
        
        for operation, timings in self._timings.items():
            if timings:
                stats[operation] = {
                    'count': len(timings),
                    'total': sum(timings),
                    'average': sum(timings) / len(timings),
                    'min': min(timings),
                    'max': max(timings)
                }
        
        return stats
    
    def reset(self) -> None:
        """Reset all timings."""
        self._timings.clear()


__all__ = ['PerformanceMonitor']

