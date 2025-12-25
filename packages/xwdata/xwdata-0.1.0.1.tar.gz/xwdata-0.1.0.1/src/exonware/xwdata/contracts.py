#!/usr/bin/env python3
"""
#exonware/xwdata/src/exonware/xwdata/contracts.py

XWData Interfaces and Contracts

This module defines all interfaces for the xwdata library following
GUIDELINES_DEV.md standards. All interfaces use 'I' prefix.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 26-Oct-2025
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Union, AsyncIterator
from pathlib import Path

# Import enums from defs
from .defs import DataFormat, MergeStrategy, SerializationMode, COWMode


# ==============================================================================
# CORE DATA INTERFACE
# ==============================================================================

class IData(ABC):
    """
    Core interface for all XWData instances.
    
    This interface defines the fundamental operations that all XWData
    implementations must support. Follows GUIDELINES_DEV.md naming:
    IData (interface) → AData (abstract) → XWData (concrete).
    """
    
    @abstractmethod
    async def get(self, path: str, default: Any = None) -> Any:
        """Get value at path with optional default."""
        pass
    
    @abstractmethod
    async def set(self, path: str, value: Any) -> 'IData':
        """Set value at path (returns new instance with COW)."""
        pass
    
    @abstractmethod
    async def delete(self, path: str) -> 'IData':
        """Delete value at path (returns new instance with COW)."""
        pass
    
    @abstractmethod
    async def exists(self, path: str) -> bool:
        """Check if path exists."""
        pass
    
    @abstractmethod
    def to_native(self) -> Any:
        """Get native Python object."""
        pass
    
    @abstractmethod
    async def serialize(self, format: Union[str, DataFormat], **opts) -> Union[str, bytes]:
        """Serialize to specified format."""
        pass
    
    @abstractmethod
    def to_format(self, format: Union[str, DataFormat], **opts) -> Union[str, bytes]:
        """Synchronously serialize to specified format."""
        pass
    
    @abstractmethod
    async def save(self, path: Union[str, Path], format: Optional[Union[str, DataFormat]] = None, **opts) -> 'IData':
        """Save to file (returns self for chaining)."""
        pass
    
    @abstractmethod
    def to_file(self, path: Union[str, Path], format: Optional[Union[str, DataFormat]] = None, **opts) -> 'IData':
        """Synchronously save to file (returns self for chaining)."""
        pass
    
    @abstractmethod
    async def merge(self, other: 'IData', strategy: Union[str, MergeStrategy] = 'deep') -> 'IData':
        """Merge with another IData instance."""
        pass
    
    @abstractmethod
    async def transform(self, transformer: callable) -> 'IData':
        """Transform data using function."""
        pass
    
    @abstractmethod
    def get_metadata(self) -> dict[str, Any]:
        """Get metadata dictionary."""
        pass
    
    @abstractmethod
    def get_format(self) -> Optional[str]:
        """Get format information."""
        pass


# ==============================================================================
# DATA ENGINE INTERFACE
# ==============================================================================

class IDataEngine(ABC):
    """
    Interface for data processing engine.
    
    The engine orchestrates all data operations, composing:
    - XWSerializer (xwsystem) for format I/O
    - FormatStrategyRegistry for format-specific logic
    - MetadataProcessor for universal metadata
    - ReferenceResolver for reference handling
    - CacheManager for performance
    - NodeFactory for node creation
    """
    
    @abstractmethod
    async def load(
        self,
        path: Union[str, Path],
        format_hint: Optional[Union[str, DataFormat]] = None,
        **opts
    ) -> 'IDataNode':
        """Load data from file."""
        pass
    
    @abstractmethod
    async def save(
        self,
        node: 'IDataNode',
        path: Union[str, Path],
        format: Optional[Union[str, DataFormat]] = None,
        **opts
    ) -> None:
        """Save node to file."""
        pass
    
    @abstractmethod
    async def parse(
        self,
        content: Union[str, bytes],
        format: Union[str, DataFormat],
        **opts
    ) -> 'IDataNode':
        """Parse content with specified format."""
        pass
    
    @abstractmethod
    async def create_node_from_native(
        self,
        data: Any,
        metadata: Optional[dict] = None,
        **opts
    ) -> 'IDataNode':
        """Create node from native Python data."""
        pass
    
    @abstractmethod
    async def merge_nodes(
        self,
        nodes: list['IDataNode'],
        strategy: Union[str, MergeStrategy] = 'deep'
    ) -> 'IDataNode':
        """Merge multiple nodes into one."""
        pass
    
    @abstractmethod
    async def stream_load(
        self,
        path: Union[str, Path],
        chunk_size: int = 8192,
        **opts
    ) -> AsyncIterator['IDataNode']:
        """Stream load large files."""
        pass


# ==============================================================================
# DATA NODE INTERFACE
# ==============================================================================

class IDataNode(ABC):
    """
    Interface for data nodes.
    
    Data nodes extend XWNode with:
    - Copy-on-write semantics
    - Format-specific metadata
    - Reference tracking
    - Structural hashing
    """
    
    @abstractmethod
    def to_native(self) -> Any:
        """Convert node to native Python object."""
        pass
    
    @abstractmethod
    def get_value_at_path(self, path: str, default: Any = None) -> Any:
        """Get value at path."""
        pass
    
    @abstractmethod
    def set_value_at_path(self, path: str, value: Any) -> 'IDataNode':
        """Set value at path (returns new node with COW)."""
        pass
    
    @abstractmethod
    def delete_at_path(self, path: str) -> 'IDataNode':
        """Delete value at path (returns new node with COW)."""
        pass
    
    @abstractmethod
    def path_exists(self, path: str) -> bool:
        """Check if path exists."""
        pass
    
    @abstractmethod
    def copy(self) -> 'IDataNode':
        """Create copy of node."""
        pass
    
    @property
    @abstractmethod
    def is_frozen(self) -> bool:
        """Check if node is frozen (COW active)."""
        pass
    
    @property
    @abstractmethod
    def metadata(self) -> dict[str, Any]:
        """Get metadata dictionary."""
        pass
    
    @property
    @abstractmethod
    def format_info(self) -> dict[str, Any]:
        """Get format information."""
        pass


# ==============================================================================
# FORMAT STRATEGY INTERFACE
# ==============================================================================

class IFormatStrategy(ABC):
    """
    Interface for format-specific strategies.
    
    Format strategies provide format-specific logic:
    - Metadata extraction (format-specific semantics)
    - Reference detection (format-specific patterns)
    - Type mapping (format ↔ native ↔ universal)
    
    They do NOT handle serialization (that's xwsystem's job).
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Strategy name (format identifier)."""
        pass
    
    @property
    @abstractmethod
    def extensions(self) -> list[str]:
        """Supported file extensions."""
        pass
    
    @abstractmethod
    async def extract_metadata(self, data: Any, **opts) -> dict[str, Any]:
        """Extract format-specific metadata."""
        pass
    
    @abstractmethod
    async def detect_references(self, data: Any, **opts) -> list[dict[str, Any]]:
        """Detect format-specific references."""
        pass
    
    @abstractmethod
    def get_reference_patterns(self) -> dict[str, Any]:
        """Get reference detection patterns for this format."""
        pass
    
    @abstractmethod
    def get_type_mapping(self) -> dict[str, str]:
        """Get type mapping (format types → universal types)."""
        pass


# ==============================================================================
# METADATA PROCESSOR INTERFACE
# ==============================================================================

class IMetadataProcessor(ABC):
    """Interface for metadata processing."""
    
    @abstractmethod
    async def extract(
        self,
        data: Any,
        strategy: IFormatStrategy,
        **opts
    ) -> dict[str, Any]:
        """Extract metadata using format strategy."""
        pass
    
    @abstractmethod
    async def apply(
        self,
        data: Any,
        metadata: dict[str, Any],
        target_format: str,
        **opts
    ) -> Any:
        """Apply metadata for target format."""
        pass


# ==============================================================================
# REFERENCE RESOLVER INTERFACE
# ==============================================================================

class IReferenceDetector(ABC):
    """Interface for reference detection."""
    
    @abstractmethod
    async def detect(
        self,
        data: Any,
        strategy: IFormatStrategy,
        **opts
    ) -> list[dict[str, Any]]:
        """Detect references in data."""
        pass


class IReferenceResolver(ABC):
    """Interface for reference resolution."""
    
    @abstractmethod
    async def resolve(
        self,
        data: Any,
        strategy: IFormatStrategy,
        base_path: Optional[Path] = None,
        **opts
    ) -> Any:
        """Resolve all references in data."""
        pass
    
    @abstractmethod
    async def resolve_reference(
        self,
        reference: dict[str, Any],
        base_path: Optional[Path] = None,
        **opts
    ) -> Any:
        """Resolve single reference."""
        pass


# ==============================================================================
# CACHE MANAGER INTERFACE
# ==============================================================================

class ICacheManager(ABC):
    """Interface for cache management."""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get cached value."""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set cached value."""
        pass
    
    @abstractmethod
    async def invalidate(self, key: str) -> None:
        """Invalidate cached value."""
        pass
    
    @abstractmethod
    async def clear(self) -> None:
        """Clear all cached values."""
        pass
    
    @abstractmethod
    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        pass


# ==============================================================================
# NODE FACTORY INTERFACE
# ==============================================================================

class INodeFactory(ABC):
    """Interface for node creation."""
    
    @abstractmethod
    async def create_node(
        self,
        data: Any,
        metadata: Optional[dict] = None,
        format_info: Optional[dict] = None,
        **opts
    ) -> IDataNode:
        """Create data node."""
        pass
    
    @abstractmethod
    async def create_from_native(self, data: Any, **opts) -> IDataNode:
        """Create node from native Python data."""
        pass


# ==============================================================================
# SERIALIZER INTERFACE (EXTENDS XWSYSTEM)
# ==============================================================================

class IXWDataSerializer(ABC):
    """
    Interface for xwdata-specific serializers.
    
    Extends xwsystem's ISerialization with xwdata features.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Serializer name."""
        pass
    
    @property
    @abstractmethod
    def extensions(self) -> list[str]:
        """Supported extensions."""
        pass
    
    @abstractmethod
    async def serialize(self, data: Any, **opts) -> Union[str, bytes]:
        """Serialize data."""
        pass
    
    @abstractmethod
    async def deserialize(self, content: Union[str, bytes], **opts) -> Any:
        """Deserialize content."""
        pass
    
    @abstractmethod
    def detect(self, content: Union[str, bytes]) -> float:
        """Detect if content matches this format (0.0-1.0 confidence)."""
        pass


# ==============================================================================
# EXPORTS
# ==============================================================================

__all__ = [
    # Core interfaces
    'IData',
    'IDataEngine',
    'IDataNode',
    
    # Strategy interfaces
    'IFormatStrategy',
    
    # Service interfaces
    'IMetadataProcessor',
    'IReferenceDetector',
    'IReferenceResolver',
    'ICacheManager',
    'INodeFactory',
    
    # Serializer interface
    'IXWDataSerializer',
]

