#!/usr/bin/env python3
"""
#exonware/xwdata/tests/1.unit/references_tests/conftest.py

Fixtures for reference resolution tests.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.0.1
Generation Date: 28-Oct-2025
"""

import pytest
from pathlib import Path
import json
import tempfile


@pytest.fixture
def temp_ref_dir(tmp_path):
    """Create temporary directory for reference test files."""
    ref_dir = tmp_path / "ref_test"
    ref_dir.mkdir()
    return ref_dir


@pytest.fixture
def simple_json_ref_data():
    """Simple JSON data with $ref."""
    return {
        "name": "Main Document",
        "reference": {
            "$ref": "external.json"
        }
    }


@pytest.fixture
def external_json_data():
    """External JSON file content."""
    return {
        "externalName": "External Document",
        "value": 42
    }


@pytest.fixture
def json_pointer_data():
    """Data for JSON Pointer testing."""
    return {
        "definitions": {
            "Pet": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "age": {"type": "integer"}
                }
            },
            "Person": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "pet": {"$ref": "#/definitions/Pet"}
                }
            }
        },
        "schema": {
            "$ref": "#/definitions/Person"
        }
    }


@pytest.fixture
def circular_ref_data_a():
    """Circular reference data - file A."""
    return {
        "name": "File A",
        "reference": {"$ref": "file_b.json"}
    }


@pytest.fixture
def circular_ref_data_b():
    """Circular reference data - file B."""
    return {
        "name": "File B",
        "reference": {"$ref": "file_a.json"}
    }


@pytest.fixture
def nested_ref_data():
    """Nested references for multi-level testing."""
    return {
        "level1": {
            "$ref": "level2.json"
        }
    }


@pytest.fixture
def ref_test_files(temp_ref_dir, external_json_data, json_pointer_data):
    """Create test files with references."""
    # Create external.json
    external_file = temp_ref_dir / "external.json"
    external_file.write_text(json.dumps(external_json_data, indent=2))
    
    # Create definitions.json (for JSON Pointer tests)
    definitions_file = temp_ref_dir / "definitions.json"
    definitions_file.write_text(json.dumps(json_pointer_data, indent=2))
    
    # Create main.json with $ref to external
    main_data = {
        "name": "Main Document",
        "external": {"$ref": "external.json"}
    }
    main_file = temp_ref_dir / "main.json"
    main_file.write_text(json.dumps(main_data, indent=2))
    
    # Create JSON Pointer reference file
    pointer_ref_data = {
        "name": "Pointer Test",
        "petDefinition": {"$ref": "definitions.json#/definitions/Pet"}
    }
    pointer_file = temp_ref_dir / "pointer_ref.json"
    pointer_file.write_text(json.dumps(pointer_ref_data, indent=2))
    
    return {
        'dir': temp_ref_dir,
        'external': external_file,
        'definitions': definitions_file,
        'main': main_file,
        'pointer_ref': pointer_file
    }


@pytest.fixture
def circular_ref_files(temp_ref_dir, circular_ref_data_a, circular_ref_data_b):
    """Create files with circular references."""
    file_a = temp_ref_dir / "file_a.json"
    file_b = temp_ref_dir / "file_b.json"
    
    file_a.write_text(json.dumps(circular_ref_data_a, indent=2))
    file_b.write_text(json.dumps(circular_ref_data_b, indent=2))
    
    return {
        'file_a': file_a,
        'file_b': file_b,
        'dir': temp_ref_dir
    }


@pytest.fixture
def invalid_ref_data():
    """Data with invalid reference."""
    return {
        "name": "Invalid Ref",
        "bad": {"$ref": "nonexistent.json"}
    }


@pytest.fixture
def malicious_ref_data():
    """Data with malicious path traversal reference."""
    return {
        "name": "Malicious",
        "dangerous": {"$ref": "../../../etc/passwd"}
    }

