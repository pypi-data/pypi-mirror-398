#!/usr/bin/env python3
"""
Direct test for get_nested_value function with Jinja2
"""
from typing import Any
from jinja2 import Template, TemplateError, UndefinedError
import ast

def get_nested_value(data: Any, path: str) -> Any:
    """
    Retrieve a value from a nested dictionary or list using Jinja2 template syntax.
    """
    if not path:
        return data

    # Wrap in Jinja2 template syntax if not already wrapped
    if not path.strip().startswith('{{'):
        template_str = f'{{{{ {path} }}}}'
    else:
        template_str = path

    try:
        template = Template(template_str)
        result = template.render(result=data)
        
        # If result is empty or undefined, return None
        if not result or result == '':
            return None
            
        # Try to use ast.literal_eval to safely convert string representations to Python types
        # This handles: int, float, bool, None, strings, lists, dicts, tuples
        try:
            return ast.literal_eval(result)
        except (ValueError, SyntaxError):
            # If literal_eval fails, it's likely a plain string - return as-is
            return result
    except (TemplateError, UndefinedError):
        return None

def test_nested_dict():
    data = {'meta': {'status': 'success'}, 'data': 'ok'}
    result = get_nested_value(data, 'result.meta.status')
    assert result == 'success', f"Expected 'success', got {result}"
    print("✓ Nested dict test passed")

def test_list_index():
    data = {'items': [{'id': 123}, {'id': 456}]}
    result = get_nested_value(data, 'result["items"][0]["id"]')
    assert result == 123, f"Expected 123, got {result}"
    print("✓ List index test passed")

def test_list_with_safe_key():
    # Test with a key that doesn't conflict with dict methods
    data = {'products': [{'id': 999}]}
    result = get_nested_value(data, 'result.products[0].id')
    assert result == 999, f"Expected 999, got {result}"
    print("✓ List with safe key test passed")

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
    data = {'products': [1, 2, 3, 4, 5]}
    result = get_nested_value(data, 'result.products | length')
    assert result == 5, f"Expected 5, got {result}"
    print("✓ Jinja filter test passed")

def test_boolean_value():
    data = {'active': True}
    result = get_nested_value(data, 'result.active')
    assert result is True, f"Expected True, got {result}"
    print("✓ Boolean value test passed")

if __name__ == '__main__':
    print("Running standalone tests for get_nested_value with Jinja2...\n")
    try:
        test_nested_dict()
        test_list_index()
        test_list_with_safe_key()
        test_direct_value()
        test_missing_path()
        test_with_jinja_filters()
        test_boolean_value()
        print("\n✅ All tests passed!")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        import sys
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        import sys
        sys.exit(1)
