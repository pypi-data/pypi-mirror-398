#!/usr/bin/env python3
"""
#exonware/xwdata/tests/1.unit/conftest.py

Unit test fixtures.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.0.1.3
Generation Date: 26-Oct-2025
"""

import pytest


@pytest.fixture
def xwdata_config():
    """Get default XWData configuration."""
    from exonware.xwdata import XWDataConfig
    return XWDataConfig.default()

