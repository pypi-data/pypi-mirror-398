#!/usr/bin/env python3
"""
#exonware/xwdata/src/exonware/xwdata/data/factory.py

NodeFactory Implementation

This module provides NodeFactory for creating XWDataNode instances
with optional object pooling and configuration.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 26-Oct-2025
"""

import copy
from typing import Any, Optional
from exonware.xwsystem import get_logger

from ..base import ANodeFactory
from ..config import XWDataConfig
from .node import XWDataNode

logger = get_logger(__name__)


class NodeFactory(ANodeFactory):
    """
    Factory for creating XWDataNode instances.
    
    Features:
    - Object pooling for performance
    - Configurable COW behavior
    - Metadata and format info injection
    """
    
    def __init__(self, config: Optional[XWDataConfig] = None):
        """
        Initialize node factory.
        
        Args:
            config: Optional configuration
        """
        super().__init__()
        self._config = config or XWDataConfig.default()
        self._pool: list[XWDataNode] = []
        self._pool_enabled = self._config.performance.enable_pooling
        self._pool_max_size = self._config.performance.pool_size
        
        # Pre-populate pool if enabled
        if self._pool_enabled:
            self._initialize_pool()
    
    def _initialize_pool(self) -> None:
        """Initialize object pool."""
        # Pre-create nodes for pooling
        for _ in range(min(10, self._pool_max_size)):
            node = XWDataNode()
            self._pool.append(node)
        
        logger.debug(f"Initialized node pool with {len(self._pool)} nodes")
    
    async def create_node(
        self,
        data: Any,
        metadata: Optional[dict] = None,
        format_info: Optional[dict] = None,
        references: Optional[list] = None,
        **opts
    ) -> XWDataNode:
        """
        Create data node with all features.
        
        Args:
            data: Node data
            metadata: Optional metadata
            format_info: Format information
            references: Reference list
            **opts: Additional options
            
        Returns:
            XWDataNode instance
        """
        # Try to get from pool
        if self._pool_enabled and self._pool:
            node = self._pool.pop()
            # Reinitialize pooled node
            node._data = data
            node._metadata = metadata or {}
            node._format_info = format_info or {}
            node._references = references or []
            node._frozen = False
            node._hash_cache = None
            node._config = self._config  # Update config
            node._nav_cache = {}  # Clear navigation cache
            
            # Recreate XWNode wrapper (immutable for COW)
            if data is not None:
                try:
                    from exonware.xwnode import XWNode
                    node._xwnode = XWNode.from_native(data, immutable=True)
                except Exception as e:
                    logger.debug(f"Could not wrap in XWNode: {e}")
                    node._xwnode = None
            
            return node
        
        # Create new node
        return XWDataNode(
            data=data,
            metadata=metadata,
            format_info=format_info,
            references=references,
            config=self._config
        )
    
    async def create_from_native(self, data: Any, **opts) -> XWDataNode:
        """
        Create node from native Python data.
        
        XWNode now handles COW internally with HAMT structural sharing,
        so no deep copy needed here - XWNode manages immutability.
        
        Args:
            data: Native Python data
            **opts: Additional options
            
        Returns:
            XWDataNode instance
        """
        # No deep copy needed - XWNode (immutable=True) handles COW
        
        # Initialize metadata (handle None case, remove from opts to avoid duplicate)
        metadata = opts.pop('metadata', None) or {}
        metadata = metadata.copy() if metadata else {}
        metadata.update({
            'source': 'native',
            'original_type': type(data).__name__
        })
        
        return await self.create_node(
            data=data,  # XWNode COW handles immutability
            metadata=metadata,
            **opts
        )
    
    def return_to_pool(self, node: XWDataNode) -> None:
        """Return node to pool for reuse."""
        if self._pool_enabled and len(self._pool) < self._pool_max_size:
            # Clear node data before pooling
            node._data = None
            node._metadata.clear()
            node._format_info.clear()
            node._references.clear()
            node._frozen = False
            node._hash_cache = None
            node._xwnode = None
            
            self._pool.append(node)
    
    def clear_pool(self) -> None:
        """Clear object pool."""
        self._pool.clear()
    
    def get_pool_stats(self) -> dict[str, Any]:
        """Get pool statistics."""
        return {
            'enabled': self._pool_enabled,
            'size': len(self._pool),
            'max_size': self._pool_max_size
        }


__all__ = ['NodeFactory']

