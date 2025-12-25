"""
Test script to verify structured output functionality.
"""
from soprano_sdk.agents.structured_output import (
    create_structured_output_model,
    validate_field_definitions
)


def test_field_validation():
    """Test field definition validation."""
    print("Testing field validation...")
    
    # Valid fields
    valid_fields = [
        {"name": "username", "type": "text", "description": "User's name", "required": True},
        {"name": "age", "type": "number", "description": "User's age", "required": False}
    ]
    
    try:
        validate_field_definitions(valid_fields)
        print("✓ Valid field definitions passed")
    except Exception as e:
        print(f"✗ Valid field definitions failed: {e}")
        return False
    
    # Invalid fields - missing required key
    invalid_fields = [
        {"name": "username", "description": "User's name"}  # missing type
    ]
    
    try:
        validate_field_definitions(invalid_fields)
        print("✗ Invalid field definitions should have raised error")
        return False
    except ValueError as e:
        print(f"✓ Invalid field definitions correctly raised error: {e}")
    
    return True


def test_model_creation():
    """Test dynamic model creation."""
    print("\nTesting model creation...")
    
    fields = [
        {"name": "name", "type": "text", "description": "User's full name", "required": True},
        {"name": "age", "type": "number", "description": "User's age", "required": True},
        {"name": "email", "type": "text", "description": "User's email", "required": True}
    ]
    
    try:
        UserModel = create_structured_output_model(fields, "UserProfile")
        print(f"✓ Model created: {UserModel.__name__}")
        
        # Test model instantiation
        user = UserModel(name="John Doe", age=30, email="john@example.com")
        print(f"✓ Model instance created: {user}")
        
        # Test model_dump
        user_dict = user.model_dump()
        print(f"✓ Model dump: {user_dict}")
        
        # Verify fields
        assert user.name == "John Doe"
        assert user.age == 30
        assert user.email == "john@example.com"
        print("✓ All field values correct")
        
        return True
    except Exception as e:
        print(f"✗ Model creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_optional_fields():
    """Test optional field handling."""
    print("\nTesting optional fields...")
    
    fields = [
        {"name": "username", "type": "text", "description": "Username", "required": True},
        {"name": "bio", "type": "text", "description": "User bio", "required": False}
    ]
    
    try:
        UserModel = create_structured_output_model(fields, "UserWithOptional")
        
        # Create with required field only
        user1 = UserModel(username="john_doe")
        print(f"✓ Created with required field only: {user1}")
        assert user1.bio is None
        
        # Create with both fields
        user2 = UserModel(username="jane_doe", bio="Software engineer")
        print(f"✓ Created with optional field: {user2}")
        assert user2.bio == "Software engineer"
        
        return True
    except Exception as e:
        print(f"✗ Optional fields test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_type_mapping():
    """Test all type mappings."""
    print("\nTesting type mappings...")
    
    fields = [
        {"name": "text_field", "type": "text", "description": "Text field", "required": True},
        {"name": "number_field", "type": "number", "description": "Number field", "required": True},
        {"name": "boolean_field", "type": "boolean", "description": "Boolean field", "required": True},
        {"name": "list_field", "type": "list", "description": "List field", "required": True},
        {"name": "dict_field", "type": "dict", "description": "Dict field", "required": True}
    ]
    
    try:
        TestModel = create_structured_output_model(fields, "TypeTestModel")
        
        instance = TestModel(
            text_field="hello",
            number_field=42,
            boolean_field=True,
            list_field=[1, 2, 3],
            dict_field={"key": "value"}
        )
        
        print(f"✓ All types mapped correctly: {instance}")
        return True
    except Exception as e:
        print(f"✗ Type mapping test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Structured Output Validation Tests")
    print("=" * 60)
    
    results = []
    results.append(("Field Validation", test_field_validation()))
    results.append(("Model Creation", test_model_creation()))
    results.append(("Optional Fields", test_optional_fields()))
    results.append(("Type Mapping", test_type_mapping()))
    
    print("\n" + "=" * 60)
    print("Test Results:")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(result for _, result in results)
    print("\n" + "=" * 60)
    if all_passed:
        print("All tests passed! ✓")
    else:
        print("Some tests failed! ✗")
    print("=" * 60)
