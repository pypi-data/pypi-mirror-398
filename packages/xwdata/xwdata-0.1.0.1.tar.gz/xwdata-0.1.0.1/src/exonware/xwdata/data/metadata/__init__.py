#!/usr/bin/env python3
"""
#exonware/xwdata/src/exonware/xwdata/data/metadata/__init__.py

Metadata System Module

Universal metadata preservation for perfect roundtrips between formats.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 26-Oct-2025
"""

from .processor import MetadataProcessor
from .extractor import MetadataExtractor
from .universal import UniversalMetadata

__all__ = [
    'MetadataProcessor',
    'MetadataExtractor',
    'UniversalMetadata',
]

