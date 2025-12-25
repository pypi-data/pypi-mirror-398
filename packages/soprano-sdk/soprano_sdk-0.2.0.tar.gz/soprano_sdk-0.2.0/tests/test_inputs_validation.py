#!/usr/bin/env python3
"""
Test to verify the simplified inputs field validation
"""
import sys
sys.path.insert(0, '/Users/rrk/Dev/Projects/soprano_sdk')

from soprano_sdk.validation.validator import WorkflowValidator

# Test 1: Valid inputs referencing data fields
valid_config = {
    "name": "Test Workflow",
    "description": "Test",
    "version": "1.0.0",
    "data": [
        {"name": "user_name", "type": "text", "description": "User's name"},
        {"name": "user_age", "type": "number", "description": "User's age"}
    ],
    "inputs": ["user_name", "user_age"],  # List of strings
    "steps": [
        {
            "id": "step1",
            "action": "call_function",
            "function": "module.func",
            "output": "user_name"
        }
    ],
    "outcomes": [
        {"id": "success", "type": "success", "message": "Done"}
    ]
}

# Test 2: Invalid inputs referencing non-existent fields
invalid_config = {
    "name": "Test Workflow",
    "description": "Test",
    "version": "1.0.0",
    "data": [
        {"name": "user_name", "type": "text", "description": "User's name"}
    ],
    "inputs": ["user_name", "invalid_field"],  # invalid_field doesn't exist
    "steps": [
        {
            "id": "step1",
            "action": "call_function",
            "function": "module.func",
            "output": "user_name"
        }
    ],
    "outcomes": [
        {"id": "success", "type": "success", "message": "Done"}
    ]
}

print("Test 1: Valid inputs referencing data fields")
validator1 = WorkflowValidator(valid_config)
result1 = validator1.validate()
if result1.is_valid:
    print("✅ PASSED - Valid config accepted")
else:
    print(f"❌ FAILED - Valid config rejected: {result1.errors}")

print("\nTest 2: Invalid inputs with non-existent field")
validator2 = WorkflowValidator(invalid_config)
result2 = validator2.validate()
if not result2.is_valid and any("invalid_field" in err for err in result2.errors):
    print("✅ PASSED - Invalid field caught")
    print(f"   Error: {[e for e in result2.errors if 'invalid_field' in e][0]}")
else:
    print(f"❌ FAILED - Invalid field not caught. Errors: {result2.errors}")

print("\n" + "="*50)
if result1.is_valid and not result2.is_valid:
    print("✅ All tests passed!")
else:
    print("❌ Some tests failed")
    sys.exit(1)
