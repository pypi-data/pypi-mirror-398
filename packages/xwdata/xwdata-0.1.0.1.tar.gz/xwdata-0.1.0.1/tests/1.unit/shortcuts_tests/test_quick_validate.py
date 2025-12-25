#!/usr/bin/env python3
"""
#exonware/xwdata/tests/1.unit/shortcuts_tests/test_quick_validate.py

Unit tests for quick_validate shortcut function.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.0.1.5
Generation Date: 26-Oct-2025
"""

import pytest
from exonware.xwdata.shortcuts import quick_validate, _basic_validate
from exonware.xwdata import XWData


@pytest.mark.xwdata_unit
class TestQuickValidate:
    """Test quick_validate function."""
    
    def test_validate_with_valid_data_returns_true(self):
        """Test validation with valid data returns True."""
        schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        data = {"name": "Alice"}
        
        result = quick_validate(data, schema)
        
        assert result is True
    
    def test_validate_with_invalid_type_returns_false(self):
        """Test validation with invalid type returns False."""
        schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        data = {"name": 123}  # Should be string
        
        result = quick_validate(data, schema)
        
        assert result is False
    
    def test_validate_with_missing_required_field_returns_false(self):
        """Test validation with missing required field returns False."""
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}, "age": {"type": "integer"}},
            "required": ["name", "age"]
        }
        data = {"name": "Alice"}  # Missing age
        
        result = quick_validate(data, schema)
        
        assert result is False
    
    def test_validate_with_xwdata_instance(self):
        """Test validation works with XWData instance."""
        schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        data = XWData.from_native({"name": "Alice"})
        
        result = quick_validate(data, schema)
        
        assert result is True
    
    def test_validate_with_array_schema(self):
        """Test validation with array schema."""
        schema = {"type": "array", "items": {"type": "string"}}
        data = ["item1", "item2", "item3"]
        
        result = quick_validate(data, schema)
        
        assert result is True
    
    def test_validate_with_invalid_array_items_returns_false(self):
        """Test validation with invalid array items returns False."""
        schema = {"type": "array", "items": {"type": "string"}}
        data = ["item1", 123, "item3"]  # Invalid item type
        
        result = quick_validate(data, schema)
        
        assert result is False
    
    def test_validate_with_nested_object_schema(self):
        """Test validation with nested object schema."""
        schema = {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {"name": {"type": "string"}}
                }
            }
        }
        data = {"user": {"name": "Alice"}}
        
        result = quick_validate(data, schema)
        
        assert result is True
    
    def test_validate_falls_back_to_basic_when_xwschema_unavailable(self):
        """Test that validation falls back to basic when xwschema unavailable."""
        schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        data = {"name": "Alice"}
        
        # Should work even if xwschema is not available
        result = quick_validate(data, schema)
        
        # Should return a boolean (either True or False based on basic validation)
        assert isinstance(result, bool)


@pytest.mark.xwdata_unit
class TestBasicValidate:
    """Test _basic_validate helper function."""
    
    def test_basic_validate_string_type(self):
        """Test basic validation with string type."""
        schema = {"type": "string"}
        data = "hello"
        
        result = _basic_validate(data, schema)
        
        assert result is True
    
    def test_basic_validate_invalid_string_type(self):
        """Test basic validation rejects invalid string type."""
        schema = {"type": "string"}
        data = 123  # Should be string
        
        result = _basic_validate(data, schema)
        
        assert result is False
    
    def test_basic_validate_integer_type(self):
        """Test basic validation with integer type."""
        schema = {"type": "integer"}
        data = 42
        
        result = _basic_validate(data, schema)
        
        assert result is True
    
    def test_basic_validate_number_type(self):
        """Test basic validation with number type."""
        schema = {"type": "number"}
        data = 3.14
        
        result = _basic_validate(data, schema)
        
        assert result is True
    
    def test_basic_validate_boolean_type(self):
        """Test basic validation with boolean type."""
        schema = {"type": "boolean"}
        data = True
        
        result = _basic_validate(data, schema)
        
        assert result is True
    
    def test_basic_validate_array_type(self):
        """Test basic validation with array type."""
        schema = {"type": "array"}
        data = [1, 2, 3]
        
        result = _basic_validate(data, schema)
        
        assert result is True
    
    def test_basic_validate_object_type(self):
        """Test basic validation with object type."""
        schema = {"type": "object"}
        data = {"key": "value"}
        
        result = _basic_validate(data, schema)
        
        assert result is True
    
    def test_basic_validate_null_type(self):
        """Test basic validation with null type."""
        schema = {"type": "null"}
        data = None
        
        result = _basic_validate(data, schema)
        
        assert result is True
    
    def test_basic_validate_required_fields(self):
        """Test basic validation checks required fields."""
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}, "age": {"type": "integer"}},
            "required": ["name"]
        }
        data = {"age": 30}  # Missing required "name"
        
        result = _basic_validate(data, schema)
        
        assert result is False
    
    def test_basic_validate_nested_properties(self):
        """Test basic validation with nested properties."""
        schema = {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {"name": {"type": "string"}}
                }
            }
        }
        data = {"user": {"name": "Alice"}}
        
        result = _basic_validate(data, schema)
        
        assert result is True
    
    def test_basic_validate_array_items(self):
        """Test basic validation with array items schema."""
        schema = {
            "type": "array",
            "items": {"type": "string"}
        }
        data = ["item1", "item2"]
        
        result = _basic_validate(data, schema)
        
        assert result is True
    
    def test_basic_validate_invalid_array_items(self):
        """Test basic validation rejects invalid array items."""
        schema = {
            "type": "array",
            "items": {"type": "string"}
        }
        data = ["item1", 123]  # Invalid item type
        
        result = _basic_validate(data, schema)
        
        assert result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

