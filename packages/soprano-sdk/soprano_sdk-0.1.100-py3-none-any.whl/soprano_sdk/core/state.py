import types
from typing import Annotated, Optional, Dict, List, Any

from typing_extensions import TypedDict

from .constants import DataType


def replace(_, right):
    return right


def get_state_value(state: Dict[str, Any], key: str, default: Any = None) -> Any:
    return state.get(key, default)

def set_state_value(state: Dict[str, Any], key: str, value: Any) -> None:
    state[key] = value

def create_state_model(data_fields: List[dict]):
    type_mapping = {
        DataType.TEXT.value: Optional[str],
        DataType.NUMBER.value: Optional[int],
        DataType.DOUBLE.value: Optional[float],
        DataType.BOOLEAN.value: Optional[bool],
        DataType.LIST.value: Optional[List[Any]],
        DataType.DICT.value: Optional[Dict[str, Any]],
        DataType.ANY.value: Optional[Any]
    }

    fields = {}
    for field_def in data_fields:
        field_name = field_def['name']
        field_type = field_def['type']
        python_type = type_mapping.get(field_type, Optional[str])
        fields[field_name] = Annotated[python_type, replace]

    fields['_step_id'] = Annotated[Optional[str], replace]
    fields['_status'] = Annotated[Optional[str], replace]
    fields['_outcome_id'] = Annotated[Optional[str], replace]

    fields['_messages'] = Annotated[List[str], replace]
    fields['_conversations'] = Annotated[Dict[str, List[Dict[str, str]]], replace]
    fields['_state_history'] = Annotated[List[Dict[str, Any]], replace]
    fields['_collector_nodes'] = Annotated[Dict[str, str], replace]
    fields['_attempt_counts'] = Annotated[Dict[str, int], replace]
    fields['_node_execution_order'] = Annotated[List[str], replace]
    fields['_node_field_map'] = Annotated[Dict[str, str], replace]
    fields['_computed_fields'] = Annotated[List[str], replace]
    fields['error'] = Annotated[Optional[Dict[str, str]], replace]

    return types.new_class('WorkflowState', (TypedDict,), {}, lambda ns: ns.update({'__annotations__': fields}))


def initialize_state(state: Dict[str, Any]) -> Dict[str, Any]:
    fields_to_initialize = {
        '_state_history': [],
        '_collector_nodes': {},
        '_conversations': {},
        '_messages': [],
        '_attempt_counts': {},
        '_node_execution_order': [],
        '_node_field_map': {},
        '_computed_fields': [],
        'error': None
    }

    for field_name, default_value in fields_to_initialize.items():
        if not get_state_value(state, field_name):
            set_state_value(state, field_name, default_value.copy() if isinstance(default_value, (list, dict)) else default_value)

    return state