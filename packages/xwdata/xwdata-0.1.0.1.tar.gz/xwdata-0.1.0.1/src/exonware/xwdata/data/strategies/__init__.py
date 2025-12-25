#!/usr/bin/env python3
"""
#exonware/xwdata/src/exonware/xwdata/data/strategies/__init__.py

Format Strategies Module

This module provides lightweight format-specific strategies that add
xwdata features (metadata extraction, reference detection) without
duplicating xwsystem's serialization logic.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 26-Oct-2025
"""

from .registry import FormatStrategyRegistry
from .json import JSONFormatStrategy
from .xml import XMLFormatStrategy
from .yaml import YAMLFormatStrategy

try:
    from .toml import TOMLFormatStrategy
    TOML_AVAILABLE = True
except ImportError:
    TOML_AVAILABLE = False
    TOMLFormatStrategy = None

try:
    from .csv import CSVFormatStrategy
    CSV_AVAILABLE = True
except ImportError:
    CSV_AVAILABLE = False
    CSVFormatStrategy = None

__all__ = [
    'FormatStrategyRegistry',
    'JSONFormatStrategy',
    'XMLFormatStrategy',
    'YAMLFormatStrategy',
]

if TOML_AVAILABLE:
    __all__.append('TOMLFormatStrategy')
if CSV_AVAILABLE:
    __all__.append('CSVFormatStrategy')

