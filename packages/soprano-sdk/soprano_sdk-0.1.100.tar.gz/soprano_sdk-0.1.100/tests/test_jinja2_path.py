#!/usr/bin/env python3
"""
Standalone test for get_nested_value function with Jinja2
"""
import sys
sys.path.insert(0, '/Users/rrk/Dev/Projects/soprano_sdk')

from soprano_sdk.utils.template import get_nested_value

def test_nested_dict():
    data = {'meta': {'status': 'success'}, 'data': 'ok'}
    result = get_nested_value(data, 'meta.status')
    assert result == 'success', f"Expected 'success', got {result}"
    print("✓ Nested dict test passed")

def test_list_index():
    data = {'items': [{'id': 123}, {'id': 456}]}
    result = get_nested_value(data, 'items[0].id')
    assert result == 123, f"Expected 123, got {result}"
    print("✓ List index test passed")

def test_direct_value():
    data = 'direct_hit'
    result = get_nested_value(data, '')
    assert result == 'direct_hit', f"Expected 'direct_hit', got {result}"
    print("✓ Direct value test passed")

def test_missing_path():
    data = {'meta': {'status': 'success'}}
    result = get_nested_value(data, 'result.meta.nonexistent')
    assert result is None, f"Expected None, got {result}"
    print("✓ Missing path test passed")

def test_with_jinja_filters():
    data = {'items': [1, 2, 3, 4, 5]}
    result = get_nested_value(data, 'items | length')
    assert result == 5, f"Expected 5, got {result}"
    print("✓ Jinja filter test passed")

def test_boolean_value():
    data = {'active': True}
    result = get_nested_value(data, 'active')
    assert result is True, f"Expected True, got {result}"
    print("✓ Boolean value test passed")

if __name__ == '__main__':
    print("Running standalone tests for get_nested_value with Jinja2...\n")
    try:
        test_nested_dict()
        test_list_index()
        test_direct_value()
        test_missing_path()
        test_with_jinja_filters()
        test_boolean_value()
        print("\n✅ All tests passed!")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
