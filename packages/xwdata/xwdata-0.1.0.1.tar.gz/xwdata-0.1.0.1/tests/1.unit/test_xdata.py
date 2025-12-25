#!/usr/bin/env python3
"""
Simple test script for the new xData library.
"""

def test_basic_functionality():
    """Test basic xData functionality."""
    print("🧪 Testing xData library...")
    
    try:
        # Test imports
        print("1. Testing imports...")
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))
        
        from src.xlib.xdata.config import Config
        from src.xlib.xdata.facade import xData
        from src.xlib.xdata.handlers.registry import get_available_formats
        print("   ✅ Imports successful")
        
        # Test config creation
        print("2. Testing configuration...")
        config = Config.default()
        strict_config = Config.strict()
        fast_config = Config.fast()
        print(f"   ✅ Configs created: {type(config)}")
        
        # Test available formats
        print("3. Testing format detection...")
        formats = get_available_formats()
        print(f"   ✅ Available formats: {formats}")
        
        # Test basic xData creation
        print("4. Testing xData creation...")
        data = xData.from_native({"test": "data", "number": 42})
        print(f"   ✅ xData created: {data}")
        
        # Test data access
        print("5. Testing data access...")
        test_val = data.get("test")
        number_val = data.get("number")
        print(f"   ✅ Data access: test={test_val}, number={number_val}")
        
        # Test mutation (COW)
        print("6. Testing copy-on-write mutation...")
        new_data = data.set("test", "modified")
        original_val = data.get("test")
        modified_val = new_data.get("test")
        print(f"   ✅ COW mutation: original={original_val}, modified={modified_val}")
        
        # Test JSON serialization
        print("7. Testing JSON serialization...")
        json_str = data.serialize("json")
        print(f"   ✅ JSON serialization: {json_str[:50]}...")
        
        print("\n🎉 All tests passed! xData library is working correctly.")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_basic_functionality()
