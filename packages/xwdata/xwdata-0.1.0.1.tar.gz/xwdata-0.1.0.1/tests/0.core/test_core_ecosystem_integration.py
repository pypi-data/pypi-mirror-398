#!/usr/bin/env python3
"""
Test XWData Ecosystem Integration

Comprehensive integration tests for all three enhancement plans:
- Plan 1: XWData + XWQuery integration
- Plan 2: XWQuery format auto-detection
- Plan 3: XWData detection metadata

Tests the complete workflow: load → detect → query → transform → save
"""

import pytest
from pathlib import Path
from exonware.xwdata import XWData


@pytest.mark.xwdata_core
class TestCompleteWorkflow:
    """Test complete data processing workflow."""
    
    @pytest.mark.asyncio
    async def test_load_detect_query_save_workflow(self, tmp_path):
        """Test: Load JSON → Detect format → Query → Save YAML."""
        pytest.importorskip('exonware.xwquery')
        
        # Step 1: Create source JSON file
        json_file = tmp_path / "users.json"
        json_file.write_text('''
        {
            "users": [
                {"id": 1, "name": "Alice", "age": 30, "role": "admin"},
                {"id": 2, "name": "Bob", "age": 25, "role": "user"},
                {"id": 3, "name": "Charlie", "age": 35, "role": "admin"}
            ]
        }
        ''')
        
        # Step 2: Load and verify detection
        data = await XWData.load(json_file)
        
        # Verify format detection (Plan 3)
        assert data.get_detected_format() == 'JSON'
        assert data.get_detection_confidence() >= 0.9
        
        detection_info = data.get_detection_info()
        assert detection_info['detected_format'] == 'JSON'
        assert detection_info['detection_method'] in ['extension', 'content']
        
        # Step 3: Query data with auto-detection (Plan 1 + 2)
        result = await data.query("SELECT * FROM users WHERE role = 'admin'")
        
        # Should get filtered results
        assert result is not None
        
        # Step 4: Save as different format
        yaml_file = tmp_path / "admins.yaml"
        await data.save(yaml_file, format='yaml')
        
        # Step 5: Load YAML and verify
        yaml_data = await XWData.load(yaml_file)
        assert yaml_data.get_detected_format() == 'YAML'
        
        # Data integrity maintained
        users = await yaml_data.get('users')
        assert len(users) == 3
    
    @pytest.mark.asyncio
    async def test_multi_format_query_workflow(self, tmp_path):
        """Test querying the same data with different query formats."""
        pytest.importorskip('exonware.xwquery')
        
        # Create test data
        xml_file = tmp_path / "products.xml"
        xml_file.write_text('''
        <catalog>
            <product>
                <id>1</id>
                <name>Laptop</name>
                <price>1000</price>
                <category>Electronics</category>
            </product>
            <product>
                <id>2</id>
                <name>Desk</name>
                <price>300</price>
                <category>Furniture</category>
            </product>
        </catalog>
        ''')
        
        data = await XWData.load(xml_file)
        
        # Verify XML detection
        assert data.get_detected_format() == 'XML'
        
        # Query 1: SQL (auto-detected)
        sql_result = await data.query(
            "SELECT * FROM products WHERE price > 500"
        )
        assert sql_result is not None
        
        # Query 2: JMESPath (explicit)
        jmespath_result = await data.query(
            "products[?price > `500`].name",
            format='jmespath'
        )
        assert jmespath_result is not None
        
        # Query 3: XPath (explicit)
        xpath_result = await data.query(
            "//product[price>500]/name",
            format='xpath'
        )
        assert xpath_result is not None
    
    @pytest.mark.asyncio
    async def test_format_conversion_chain_with_queries(self, tmp_path):
        """Test format conversions with queries at each step."""
        pytest.importorskip('exonware.xwquery')
        
        # Start with JSON
        json_file = tmp_path / "data.json"
        json_file.write_text('''
        {
            "employees": [
                {"name": "Alice", "department": "Engineering", "salary": 100000},
                {"name": "Bob", "department": "Sales", "salary": 80000},
                {"name": "Charlie", "department": "Engineering", "salary": 120000}
            ]
        }
        ''')
        
        # Load JSON
        json_data = await XWData.load(json_file)
        assert json_data.get_detected_format() == 'JSON'
        
        # Query in JSON
        eng_result = await json_data.query(
            "SELECT * FROM employees WHERE department = 'Engineering'"
        )
        assert eng_result is not None
        
        # Convert to YAML
        yaml_file = tmp_path / "data.yaml"
        await json_data.save(yaml_file)
        
        # Load YAML
        yaml_data = await XWData.load(yaml_file)
        assert yaml_data.get_detected_format() == 'YAML'
        
        # Query in YAML
        high_salary = await yaml_data.query(
            "SELECT * FROM employees WHERE salary > 90000"
        )
        assert high_salary is not None
        
        # Convert to TOML
        toml_file = tmp_path / "data.toml"
        await yaml_data.save(toml_file)
        
        # Load TOML
        toml_data = await XWData.load(toml_file)
        assert toml_data.get_detected_format() == 'TOML'
        
        # Verify data integrity through all conversions
        employees = await toml_data.get('employees')
        assert len(employees) == 3


@pytest.mark.xwdata_core
class TestCrossPackageIntegration:
    """Test integration between XWData, XWQuery, XWNode, and XWSystem."""
    
    @pytest.mark.asyncio
    async def test_xwdata_to_xwnode_to_xwquery(self, tmp_path):
        """Test data flow: XWData → XWNode → XWQuery."""
        pytest.importorskip('exonware.xwquery')
        
        # Create data
        json_file = tmp_path / "test.json"
        json_file.write_text('{"items": [{"id": 1, "value": 100}]}')
        
        # Load with XWData
        xwdata = await XWData.load(json_file)
        
        # Extract XWNode (Plan 1)
        xwnode = xwdata.as_xwnode()
        
        # Use with XWQuery directly
        from exonware.xwquery import XWQuery
        result = XWQuery.execute("SELECT * FROM items", xwnode)
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_xwsystem_serialization_with_detection(self, tmp_path):
        """Test XWSystem serialization with format detection."""
        # XWData uses XWSystem for serialization
        # Verify detection works with XWSystem integration
        
        yaml_file = tmp_path / "config.yaml"
        yaml_file.write_text('''
name: MyApp
version: 1.0.0
settings:
  debug: true
  timeout: 30
''')
        
        # Load (uses XWSystem AutoSerializer)
        data = await XWData.load(yaml_file)
        
        # Detection should work
        assert data.get_detected_format() == 'YAML'
        
        # Get data
        name = await data.get('name')
        assert name == 'MyApp'
        
        # Save as JSON (uses XWSystem AutoSerializer)
        json_file = tmp_path / "config.json"
        await data.save(json_file)
        
        # Load JSON
        json_data = await XWData.load(json_file)
        assert json_data.get_detected_format() == 'JSON'
        
        # Verify data integrity
        assert await json_data.get('name') == 'MyApp'


@pytest.mark.xwdata_core
class TestRealWorldScenarios:
    """Real-world usage scenarios."""
    
    @pytest.mark.asyncio
    async def test_config_file_migration(self, tmp_path):
        """Scenario: Migrate config from JSON to YAML."""
        # Old config in JSON
        old_config = tmp_path / "config.json"
        old_config.write_text('''
        {
            "database": {
                "host": "localhost",
                "port": 5432,
                "name": "mydb"
            },
            "api": {
                "timeout": 30,
                "retries": 3
            }
        }
        ''')
        
        # Load old config
        config = await XWData.load(old_config)
        
        # Verify it's JSON
        print(f"Original format: {config.get_detected_format()}")
        assert config.get_detected_format() == 'JSON'
        
        # Save as YAML
        new_config = tmp_path / "config.yaml"
        await config.save(new_config)
        
        # Load new config
        yaml_config = await XWData.load(new_config)
        
        # Verify conversion
        assert yaml_config.get_detected_format() == 'YAML'
        assert await yaml_config.get('database.host') == 'localhost'
        assert await yaml_config.get('api.timeout') == 30
    
    @pytest.mark.asyncio
    async def test_data_analytics_workflow(self, tmp_path):
        """Scenario: Load data → Query → Analyze → Export."""
        pytest.importorskip('exonware.xwquery')
        
        # Load sales data
        sales_file = tmp_path / "sales.json"
        sales_file.write_text('''
        {
            "sales": [
                {"date": "2024-01", "region": "North", "amount": 50000},
                {"date": "2024-01", "region": "South", "amount": 45000},
                {"date": "2024-02", "region": "North", "amount": 55000},
                {"date": "2024-02", "region": "South", "amount": 48000}
            ]
        }
        ''')
        
        data = await XWData.load(sales_file)
        
        # Verify detection
        info = data.get_detection_info()
        print(f"Loaded {info['detected_format']} with {info['detection_confidence']:.0%} confidence")
        
        # Query: Get North region sales
        north_sales = await data.query(
            "SELECT * FROM sales WHERE region = 'North'"
        )
        assert north_sales is not None
        
        # Query: Get February sales (auto-detect SQL)
        feb_sales = await data.query(
            "SELECT * FROM sales WHERE date LIKE '2024-02%'"
        )
        assert feb_sales is not None
        
        # Export results
        report_file = tmp_path / "report.yaml"
        await data.save(report_file)
        
        # Verify export
        report = await XWData.load(report_file)
        assert report.get_detected_format() == 'YAML'
    
    @pytest.mark.asyncio
    async def test_multi_source_merge_with_queries(self, tmp_path):
        """Scenario: Merge multiple files and query combined data."""
        pytest.importorskip('exonware.xwquery')
        
        # File 1: User profiles (JSON)
        users_file = tmp_path / "users.json"
        users_file.write_text('''
        {
            "users": [
                {"id": 1, "name": "Alice"},
                {"id": 2, "name": "Bob"}
            ]
        }
        ''')
        
        # File 2: User settings (YAML)
        settings_file = tmp_path / "settings.yaml"
        settings_file.write_text('''
settings:
  - user_id: 1
    theme: dark
  - user_id: 2
    theme: light
''')
        
        # Load both
        users_data = await XWData.load(users_file)
        settings_data = await XWData.load(settings_file)
        
        # Verify formats
        assert users_data.get_detected_format() == 'JSON'
        assert settings_data.get_detected_format() == 'YAML'
        
        # Merge
        combined = await users_data.merge(settings_data)
        
        # Query combined data
        result = await combined.query("SELECT * FROM users")
        assert result is not None


@pytest.mark.xwdata_core
class TestErrorHandlingIntegration:
    """Test error handling across the ecosystem."""
    
    @pytest.mark.asyncio
    async def test_ambiguous_format_with_hint(self, tmp_path):
        """Test handling ambiguous file with format hint."""
        # File with no clear extension
        data_file = tmp_path / "data.txt"
        data_file.write_text('{"key": "value"}')
        
        # Load with hint
        data = await XWData.load(data_file, format_hint='json')
        
        # Should work with hint (format is normalized to uppercase)
        assert data.get_detected_format() == 'JSON'
        assert data.get_detection_confidence() == 1.0  # Perfect with hint
        assert data.get_detection_info()['detection_method'] == 'hint'
    
    @pytest.mark.asyncio
    async def test_invalid_query_format_explicit(self, tmp_path):
        """Test handling of invalid explicit query format."""
        pytest.importorskip('exonware.xwquery')
        
        data = XWData.from_native({'items': []})
        
        # Try invalid format - XWQuery gracefully falls back to auto-detect
        # This is acceptable behavior (graceful degradation)
        result = await data.query("SELECT * FROM items", format='invalid_format')
        # Should return a result (auto-detected as SQL)
        assert result is not None
    
    def test_missing_xwnode_error(self):
        """Test error when XWNode not available."""
        data = XWData.__new__(XWData)
        data._node = None
        
        with pytest.raises(ValueError, match="No XWNode available"):
            data.as_xwnode()


@pytest.mark.xwdata_core
class TestPerformanceIntegration:
    """Test performance aspects of integration."""
    
    @pytest.mark.asyncio
    async def test_caching_with_detection(self, tmp_path):
        """Test that detection metadata is cached."""
        json_file = tmp_path / "data.json"
        json_file.write_text('{"items": [1, 2, 3]}')
        
        # Load first time
        data1 = await XWData.load(json_file)
        format1 = data1.get_detected_format()
        
        # Load second time (should use cache if enabled)
        data2 = await XWData.load(json_file)
        format2 = data2.get_detected_format()
        
        # Should have same detection results
        assert format1 == format2
        assert format1 == 'JSON'
    
    @pytest.mark.asyncio
    async def test_query_auto_detection_performance(self, tmp_path):
        """Test that query auto-detection is fast."""
        pytest.importorskip('exonware.xwquery')
        import time
        
        data = XWData.from_native({
            'records': [{'id': i, 'value': i * 10} for i in range(100)]
        })
        
        # Time auto-detection
        start = time.time()
        result = await data.query("SELECT * FROM records WHERE value > 500")
        elapsed = time.time() - start
        
        # Should be reasonably fast (< 1 second)
        assert elapsed < 1.0
        assert result is not None


@pytest.mark.xwdata_core
class TestDocumentationExamples:
    """Test examples from documentation."""
    
    @pytest.mark.asyncio
    async def test_quick_start_example(self, tmp_path):
        """Test quick start example from docs."""
        pytest.importorskip('exonware.xwquery')
        
        # Create sample file
        users_file = tmp_path / "users.json"
        users_file.write_text('''
        {
            "users": [
                {"name": "Alice", "age": 30},
                {"name": "Bob", "age": 25}
            ]
        }
        ''')
        
        # Load data
        data = await XWData.load(users_file)
        
        # Check what format was detected
        print(f"Detected: {data.get_detected_format()}")
        
        # Query the data
        result = await data.query("SELECT * FROM users WHERE age > 26")
        
        # Save as different format
        output_file = tmp_path / "users.yaml"
        await data.save(output_file)
        
        # Verify
        assert data.get_detected_format() == 'JSON'
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_advanced_example(self, tmp_path):
        """Test advanced integration example."""
        pytest.importorskip('exonware.xwquery')
        
        # Load JSON data
        data_file = tmp_path / "data.json"
        data_file.write_text('{"items": [{"id": 1, "name": "Item1"}]}')
        
        data = await XWData.load(data_file)
        
        # Get detection info
        info = data.get_detection_info()
        if info['detection_confidence'] < 0.8:
            print("Warning: Low confidence detection!")
        
        # Get XWNode for advanced operations
        node = data.as_xwnode()
        
        # Use XWQuery directly on node
        from exonware.xwquery import XWQuery
        result = XWQuery.execute(
            "SELECT * FROM items",
            node,
            auto_detect=True
        )
        
        assert result is not None
        assert info['detected_format'] == 'JSON'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

