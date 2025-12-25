#!/usr/bin/env python3
"""
#exonware/xwdata/src/exonware/xwdata/defs.py

XWData Strategy Types and Enums

This module defines all the enums and types for the XWData system:
- DataFormat: Supported data formats
- EngineMode: Engine operation modes
- CacheStrategy: Caching strategies
- ReferenceResolutionMode: Reference resolution modes
- MergeStrategy: Data merging strategies
- SerializationMode: Serialization modes

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 26-Oct-2025
"""

from enum import Enum, Flag, auto as _auto
from typing import Any, Optional


# ==============================================================================
# DATA FORMATS
# ==============================================================================

class DataFormat(Enum):
    """Supported data formats (xwsystem base + xwdata extensions)."""
    
    # Text formats (xwsystem base)
    JSON = _auto()
    YAML = _auto()
    XML = _auto()
    TOML = _auto()
    CSV = _auto()
    INI = _auto()
    CONFIGPARSER = _auto()
    
    # Binary formats (xwsystem base)
    BSON = _auto()
    MESSAGEPACK = _auto()
    CBOR = _auto()
    PICKLE = _auto()
    MARSHAL = _auto()
    
    # Database formats (xwsystem base)
    SQLITE3 = _auto()
    DBM = _auto()
    SHELVE = _auto()
    
    # Schema-based formats (xwsystem base)
    AVRO = _auto()
    PROTOBUF = _auto()
    THRIFT = _auto()
    PARQUET = _auto()
    ORC = _auto()
    CAPNPROTO = _auto()
    FLATBUFFERS = _auto()
    
    # Extended formats (xwdata exclusive)
    JSON5 = _auto()              # JSON with comments
    JSONLINES = _auto()          # JSON Lines (streaming)
    NDJSON = _auto()             # Newline-delimited JSON
    YAML_MULTI = _auto()         # Multi-document YAML
    PLIST = _auto()              # Apple Property List
    
    # Special modes
    AUTO = _auto()               # Auto-detect format


# ==============================================================================
# ENGINE MODES
# ==============================================================================

class EngineMode(Enum):
    """Engine operation modes."""
    
    STANDARD = _auto()           # Standard synchronous operations
    ASYNC = _auto()              # Async operations (default)
    STREAMING = _auto()          # Streaming for large files
    BATCH = _auto()              # Batch processing
    PARALLEL = _auto()           # Parallel processing


# ==============================================================================
# CACHE STRATEGIES
# ==============================================================================

class CacheStrategy(Enum):
    """Caching strategies for performance optimization."""
    
    NONE = _auto()               # No caching
    MEMORY = _auto()             # Memory-only caching
    DISK = _auto()               # Disk-only caching
    TWO_TIER = _auto()           # Memory + disk caching
    LRU = _auto()                # LRU eviction policy
    LFU = _auto()                # LFU eviction policy
    STRUCTURAL_HASH = _auto()    # Structural hashing for cache keys


# ==============================================================================
# REFERENCE RESOLUTION MODES
# ==============================================================================

class ReferenceResolutionMode(Enum):
    """Reference resolution modes."""
    
    DISABLED = _auto()           # No reference resolution
    DETECT_ONLY = _auto()        # Detect but don't resolve
    LAZY = _auto()               # Resolve on access
    EAGER = _auto()              # Resolve immediately
    RECURSIVE = _auto()          # Recursive resolution
    CIRCULAR_DETECT = _auto()    # Detect circular references


# ==============================================================================
# MERGE STRATEGIES
# ==============================================================================

class MergeStrategy(Enum):
    """Data merging strategies."""
    
    SHALLOW = _auto()            # Shallow merge (top-level only)
    DEEP = _auto()               # Deep recursive merge
    REPLACE = _auto()            # Replace conflicts with new value
    KEEP = _auto()               # Keep existing, skip new
    ARRAY_APPEND = _auto()       # Append arrays instead of replacing
    ARRAY_MERGE = _auto()        # Merge array elements
    CUSTOM = _auto()             # Custom merge function


# ==============================================================================
# SERIALIZATION MODES
# ==============================================================================

class SerializationMode(Enum):
    """Serialization operation modes."""
    
    STANDARD = _auto()           # Standard serialization
    PRETTY = _auto()             # Pretty-printed output
    COMPACT = _auto()            # Compact output
    STREAMING = _auto()          # Streaming serialization
    INCREMENTAL = _auto()        # Incremental serialization


# ==============================================================================
# COW (COPY-ON-WRITE) MODES
# ==============================================================================

class COWMode(Enum):
    """Copy-on-write operation modes."""
    
    DISABLED = _auto()           # No COW (in-place mutations)
    ENABLED = _auto()            # COW enabled (immutable)
    SHALLOW_COPY = _auto()       # Shallow copy on write
    DEEP_COPY = _auto()          # Deep copy on write
    STRUCTURAL_SHARING = _auto() # Structural sharing (persistent data structures)


# ==============================================================================
# METADATA PRESERVATION MODES
# ==============================================================================

class MetadataMode(Enum):
    """Metadata preservation modes."""
    
    NONE = _auto()               # No metadata preservation
    BASIC = _auto()              # Basic metadata only
    FULL = _auto()               # Full metadata preservation
    UNIVERSAL = _auto()          # Universal metadata for perfect roundtrips


# ==============================================================================
# VALIDATION MODES
# ==============================================================================

class ValidationMode(Enum):
    """Data validation modes."""
    
    DISABLED = _auto()           # No validation
    BASIC = _auto()              # Basic type validation
    STRICT = _auto()             # Strict validation
    SCHEMA = _auto()             # Schema-based validation (with xwschema)


# ==============================================================================
# PERFORMANCE TRAITS
# ==============================================================================

class PerformanceTrait(Flag):
    """Performance optimization traits (can be combined)."""
    
    NONE = 0
    CACHING = _auto()            # Enable caching
    POOLING = _auto()            # Object pooling
    STRUCTURAL_HASH = _auto()    # Structural hashing
    LAZY_LOADING = _auto()       # Lazy loading
    STREAMING = _auto()          # Streaming support
    PARALLEL = _auto()           # Parallel processing


# ==============================================================================
# SECURITY TRAITS
# ==============================================================================

class SecurityTrait(Flag):
    """Security features (can be combined)."""
    
    NONE = 0
    PATH_VALIDATION = _auto()    # Path validation
    SIZE_LIMITS = _auto()        # File size limits
    DEPTH_LIMITS = _auto()       # Nesting depth limits
    SANITIZATION = _auto()       # Input sanitization
    ENCRYPTION = _auto()         # Encryption support


# ==============================================================================
# CONSTANTS
# ==============================================================================

# Default values
DEFAULT_CACHE_SIZE = 1000
DEFAULT_MAX_FILE_SIZE_MB = 100
DEFAULT_MAX_NESTING_DEPTH = 50
DEFAULT_TIMEOUT_SECONDS = 30
DEFAULT_MERGE_STRATEGY = 'deep'

# Format extensions mapping
FORMAT_EXTENSIONS = {
    'json': ['.json', '.js'],
    'yaml': ['.yaml', '.yml'],
    'xml': ['.xml', '.xhtml'],
    'toml': ['.toml'],
    'csv': ['.csv', '.tsv'],
    'json5': ['.json5'],
    'jsonlines': ['.jsonl', '.ndjson'],
}

# MIME types mapping
FORMAT_MIME_TYPES = {
    'json': ['application/json', 'text/json'],
    'yaml': ['application/yaml', 'text/yaml'],
    'xml': ['application/xml', 'text/xml'],
    'toml': ['application/toml'],
    'csv': ['text/csv'],
}


# ==============================================================================
# EXPORTS
# ==============================================================================

__all__ = [
    # Enums
    'DataFormat',
    'EngineMode',
    'CacheStrategy',
    'ReferenceResolutionMode',
    'MergeStrategy',
    'SerializationMode',
    'COWMode',
    'MetadataMode',
    'ValidationMode',
    
    # Flags
    'PerformanceTrait',
    'SecurityTrait',
    
    # Constants
    'DEFAULT_CACHE_SIZE',
    'DEFAULT_MAX_FILE_SIZE_MB',
    'DEFAULT_MAX_NESTING_DEPTH',
    'DEFAULT_TIMEOUT_SECONDS',
    'DEFAULT_MERGE_STRATEGY',
    'FORMAT_EXTENSIONS',
    'FORMAT_MIME_TYPES',
]

