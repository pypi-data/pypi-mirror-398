#!/usr/bin/env python3
"""
Test XWData Query Integration (Plan 1)

Tests the integration between XWData and XWQuery:
- as_xwnode() method
- query() convenience method
- Multiple query formats
"""

import pytest
from exonware.xwdata import XWData


@pytest.mark.xwdata_core
class TestXWDataQueryIntegration:
    """Test XWData + XWQuery integration."""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample data for testing."""
        return XWData.from_native({
            'users': [
                {'id': 1, 'name': 'Alice', 'age': 30, 'role': 'admin'},
                {'id': 2, 'name': 'Bob', 'age': 25, 'role': 'user'},
                {'id': 3, 'name': 'Charlie', 'age': 35, 'role': 'user'},
                {'id': 4, 'name': 'Diana', 'age': 28, 'role': 'admin'},
            ],
            'posts': [
                {'id': 1, 'user_id': 1, 'title': 'First Post', 'likes': 10},
                {'id': 2, 'user_id': 2, 'title': 'Second Post', 'likes': 5},
                {'id': 3, 'user_id': 1, 'title': 'Third Post', 'likes': 15},
            ]
        })
    
    def test_as_xwnode_returns_xwnode(self, sample_data):
        """Test that as_xwnode() returns an XWNode instance."""
        from exonware.xwnode import XWNode
        
        node = sample_data.as_xwnode()
        assert isinstance(node, XWNode)
        assert node is not None
    
    def test_as_xwnode_preserves_data(self, sample_data):
        """Test that as_xwnode() preserves data integrity."""
        node = sample_data.as_xwnode()
        native = node.to_native()
        
        assert 'users' in native
        assert len(native['users']) == 4
        assert native['users'][0]['name'] == 'Alice'
    
    def test_as_xwnode_error_on_empty(self):
        """Test that as_xwnode() raises error on empty data."""
        # Create XWData without proper initialization
        data = XWData.__new__(XWData)
        data._node = None
        
        with pytest.raises(ValueError, match="No XWNode available"):
            data.as_xwnode()
    
    @pytest.mark.asyncio
    async def test_query_sql_select(self, sample_data):
        """Test SQL SELECT query."""
        pytest.importorskip('exonware.xwquery')
        
        result = await sample_data.query(
            "SELECT * FROM users WHERE age > 28",
            format='sql'
        )
        
        # Result should contain filtered users
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_query_auto_detect_sql(self, sample_data):
        """Test auto-detection of SQL query."""
        pytest.importorskip('exonware.xwquery')
        
        # Query without explicit format (should auto-detect SQL)
        result = await sample_data.query("SELECT * FROM users")
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_query_jmespath(self, sample_data):
        """Test JMESPath query."""
        pytest.importorskip('exonware.xwquery')
        
        result = await sample_data.query(
            "users[?age > `28`].name",
            format='jmespath'
        )
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_query_missing_xwquery_dependency(self, sample_data, monkeypatch):
        """Test error when xwquery is not installed."""
        # Mock import error by patching the import mechanism
        import builtins
        original_import = builtins.__import__
        
        def mock_import(name, *args, **kwargs):
            if 'xwquery' in name:
                raise ImportError("No module named 'exonware.xwquery'")
            return original_import(name, *args, **kwargs)
        
        monkeypatch.setattr(builtins, '__import__', mock_import)
        
        with pytest.raises(ImportError, match="xwquery is required"):
            await sample_data.query("SELECT * FROM users")
    
    def test_query_integration_example(self, sample_data):
        """Integration example from documentation."""
        # Get XWNode for advanced operations
        node = sample_data.as_xwnode()
        
        # Can use with xwschema, xwquery, etc.
        assert node is not None
        assert hasattr(node, 'to_native')
        # XWNode instance is available for use with other libraries
        native_data = node.to_native()
        assert 'users' in native_data


@pytest.mark.xwdata_core
class TestQueryFormats:
    """Test different query formats."""
    
    @pytest.fixture
    def graph_data(self):
        """Create graph-like data for testing."""
        return XWData.from_native({
            'nodes': [
                {'id': 1, 'type': 'User', 'name': 'Alice'},
                {'id': 2, 'type': 'User', 'name': 'Bob'},
                {'id': 3, 'type': 'Post', 'title': 'Hello World'},
            ],
            'edges': [
                {'from': 1, 'to': 3, 'type': 'WROTE'},
                {'from': 2, 'to': 3, 'type': 'LIKED'},
            ]
        })
    
    @pytest.mark.asyncio
    async def test_sql_format(self, graph_data):
        """Test SQL query format."""
        pytest.importorskip('exonware.xwquery')
        
        result = await graph_data.query(
            "SELECT * FROM nodes WHERE type = 'User'",
            format='sql'
        )
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_cypher_format(self, graph_data):
        """Test Cypher query format (graph)."""
        pytest.importorskip('exonware.xwquery')
        
        result = await graph_data.query(
            "MATCH (u:User) RETURN u.name",
            format='cypher'
        )
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_graphql_format(self, graph_data):
        """Test GraphQL query format."""
        pytest.importorskip('exonware.xwquery')
        
        result = await graph_data.query(
            "{ nodes(filter: {type: 'User'}) { name } }",
            format='graphql'
        )
        assert result is not None


@pytest.mark.xwdata_core
class TestQueryChaining:
    """Test query operations with method chaining."""
    
    @pytest.mark.asyncio
    async def test_load_and_query_chain(self, tmp_path):
        """Test loading file and querying in chain."""
        pytest.importorskip('exonware.xwquery')
        
        # Create test file
        test_file = tmp_path / "test.json"
        test_file.write_text('{"items": [{"id": 1, "value": 100}, {"id": 2, "value": 200}]}')
        
        # Load and query
        data = await XWData.load(test_file)
        result = await data.query("SELECT * FROM items WHERE value > 100")
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_set_and_query_chain(self):
        """Test setting value and then querying."""
        pytest.importorskip('exonware.xwquery')
        
        data = XWData.from_native({'users': []})
        
        # Add user and query
        updated = await data.set('users', [
            {'name': 'Alice', 'age': 30},
            {'name': 'Bob', 'age': 25}
        ])
        
        result = await updated.query("SELECT * FROM users WHERE age > 26")
        assert result is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

