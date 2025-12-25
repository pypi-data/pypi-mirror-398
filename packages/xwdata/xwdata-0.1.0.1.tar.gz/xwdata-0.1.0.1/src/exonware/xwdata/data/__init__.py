#!/usr/bin/env python3
"""
#exonware/xwdata/src/exonware/xwdata/data/__init__.py

XWData Core Data Module

This module contains the core data functionality:
- XWDataEngine: Main orchestrator
- XWDataNode: Data node with COW semantics
- NodeFactory: Node creation and pooling

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 26-Oct-2025
"""

from .engine import XWDataEngine
from .node import XWDataNode
from .factory import NodeFactory

__all__ = [
    'XWDataEngine',
    'XWDataNode',
    'NodeFactory',
]

