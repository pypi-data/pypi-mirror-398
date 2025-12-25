from enum import Enum


class WorkflowKeys:
    STEP_ID = '_step_id'
    STATUS = '_status'
    OUTCOME_ID = '_outcome_id'
    MESSAGES = '_messages'
    CONVERSATIONS = '_conversations'
    STATE_HISTORY = '_state_history'
    COLLECTOR_NODES = '_collector_nodes'
    ATTEMPT_COUNTS = '_attempt_counts'
    NODE_EXECUTION_ORDER = '_node_execution_order'
    NODE_FIELD_MAP = '_node_field_map'
    COMPUTED_FIELDS = '_computed_fields'
    ERROR = 'error'


class ActionType(Enum):
    COLLECT_INPUT_WITH_AGENT = 'collect_input_with_agent'
    CALL_FUNCTION = 'call_function'


class DataType(Enum):
    TEXT = 'text'
    NUMBER = 'number'
    DOUBLE = 'double'
    BOOLEAN = 'boolean'
    LIST = 'list'
    DICT = 'dict'
    ANY = "any"


class OutcomeType(Enum):
    SUCCESS = 'success'
    FAILURE = 'failure'


class StatusPattern:
    COLLECTING = '{step_id}_collecting'
    MAX_ATTEMPTS = '{step_id}_max_attempts'
    NEXT_STEP = '{step_id}_{next_step}'
    SUCCESS = '{step_id}_success'
    FAILED = '{step_id}_failed'
    INTENT_CHANGE = '{step_id}_{target_node}'


class TransitionPattern:
    CAPTURED = '{field}_CAPTURED:'
    FAILED = '{field}_FAILED:'
    INTENT_CHANGE = 'INTENT_CHANGE:'


DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_MODEL = 'gpt-4o-mini'
DEFAULT_TIMEOUT = 300

MAX_ATTEMPTS_MESSAGE = "I'm having trouble understanding your {field}. Please contact customer service for assistance."
WORKFLOW_COMPLETE_MESSAGE = "Workflow completed."
