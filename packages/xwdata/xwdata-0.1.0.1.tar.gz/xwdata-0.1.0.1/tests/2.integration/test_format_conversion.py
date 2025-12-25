#!/usr/bin/env python3
"""
#exonware/xwdata/tests/2.integration/test_format_conversion.py

Integration tests for format conversion.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.0.1.3
Generation Date: 26-Oct-2025
"""

import pytest


@pytest.mark.xwdata_integration
class TestFormatConversion:
    """Integration tests for cross-format operations."""
    
    @pytest.mark.asyncio
    async def test_json_to_native_roundtrip(self, tmp_path):
        """Test JSON save and load roundtrip."""
        from exonware.xwdata import XWData
        
        # Create data
        original_data = {'name': 'Test', 'value': 42}
        data = XWData.from_native(original_data)
        
        # Save as JSON
        json_file = tmp_path / "test.json"
        await data.save(json_file, format='json')
        
        # Load back
        loaded = await XWData.load(json_file)
        loaded_native = loaded.to_native()
        
        assert loaded_native == original_data

