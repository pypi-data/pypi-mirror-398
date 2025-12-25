from typing import Any, Dict, List, Optional, Type
from pydantic import BaseModel, Field, create_model


TYPE_MAP = {
    "text": str,
    "number": int,
    "double": float,
    "boolean": bool,
    "list": list,
    "dict": dict,
}


def create_structured_output_model(
    fields: List[Dict[str, Any]],
    model_name: str = "StructuredOutput",
    needs_intent_change: bool = False,
) -> Type[BaseModel]:
    if not fields:
        raise ValueError("At least one field definition is required")
    
    field_definitions = {"bot_response": (Optional[str], Field(None, description="bot response for the user query, only use this for clarification or asking for more information"))}

    if needs_intent_change:
        field_definitions["intent_change"] = (Optional[str], Field(None, description="node name for handling new intent"))

    for field_def in fields:
        field_name = field_def.get("name")
        field_type = field_def.get("type")
        field_description = field_def.get("description", "")
        is_required = field_def.get("required", True)
        
        if not field_name:
            raise ValueError("Field definition missing 'name'")
        
        if not field_type:
            raise ValueError(f"Field '{field_name}' missing 'type'")
        
        python_type = TYPE_MAP.get(field_type)
        if python_type is None:
            raise ValueError(
                f"Unknown type '{field_type}' for field '{field_name}'. "
                f"Supported types: {list(TYPE_MAP.keys())}"
            )
        
        if is_required:
            field_definitions[field_name] = (
                python_type,
                Field(..., description=field_description)
            )
        else:
            python_type = Optional[python_type]
            field_definitions[field_name] = (
                python_type,
                Field(default=None, description=field_description)
            )
    
    try:
        model = create_model(model_name, **field_definitions)
        return model
    except Exception as e:
        raise ValueError(f"Failed to create model '{model_name}': {e}")


def validate_field_definitions(fields: List[Dict[str, Any]]) -> bool:
    if not isinstance(fields, list):
        raise ValueError("Field definitions must be a list")
    
    if not fields:
        raise ValueError("At least one field definition is required")
    
    field_names = set()
    
    for i, field_def in enumerate(fields):
        if not isinstance(field_def, dict):
            raise ValueError(f"Field definition at index {i} must be a dictionary")
        
        required_keys = ["name", "type", "description"]
        for key in required_keys:
            if key not in field_def:
                raise ValueError(f"Field definition at index {i} missing required key '{key}'")
        
        field_name = field_def["name"]
        
        if field_name in field_names:
            raise ValueError(f"Duplicate field name '{field_name}' found")
        field_names.add(field_name)
        
        field_type = field_def["type"]
        if field_type not in TYPE_MAP:
            raise ValueError(
                f"Invalid type '{field_type}' for field '{field_name}'. "
                f"Supported types: {list(TYPE_MAP.keys())}"
            )
    
    return True
