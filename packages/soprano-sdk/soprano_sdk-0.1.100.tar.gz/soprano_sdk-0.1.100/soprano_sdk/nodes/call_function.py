from typing import Dict, Any

from .base import ActionStrategy
from ..core.state import set_state_value, get_state_value
from ..utils.logger import logger
from ..utils.template import get_nested_value


class CallFunctionStrategy(ActionStrategy):
    def __init__(self, step_config: Dict[str, Any], engine_context: Any):
        super().__init__(step_config, engine_context)
        self.function_path = step_config.get('function')
        self.output_field = step_config.get('output')
        self.inputs = step_config.get('inputs', {})
        self.transitions = self._get_transitions()
        self.next_step = self._get_next_step()

        if not self.function_path:
            raise RuntimeError(f"Step '{self.step_id}' missing required 'function' property")

        if not self.output_field:
            raise RuntimeError(f"Step '{self.step_id}' missing required 'output' property")

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        from ..utils.tracing import trace_node_execution
        
        with trace_node_execution(
            node_id=self.step_id,
            node_type="call_function",
            function=self.function_path,
            output_field=self.output_field
        ) as span:
            try:
                logger.info(f"Loading function: {self.function_path}")
                func = self.engine_context.function_repository.load(self.function_path)
            except Exception as e:
                span.set_attribute("error", True)
                span.set_attribute("error.type", "LoadError")
                span.set_attribute("error.message", str(e))
                raise RuntimeError(
                    f"Failed to load function '{self.function_path}' in step '{self.step_id}': {e}"
                )

            try:
                logger.info(f"Calling function: {self.function_path}")
                result = func(state)
                logger.info(f"Function {self.function_path} returned: {result}")
                
                span.add_event("function.executed", {
                    "result_type": type(result).__name__,
                    "result": str(result)
                })
            except Exception as e:
                span.set_attribute("error", True)
                span.set_attribute("error.type", type(e).__name__)
                span.set_attribute("error.message", str(e))
                raise RuntimeError(f"Function '{self.function_path}' failed in step '{self.step_id}': {e}")

            if self.output_field:
                set_state_value(state, self.output_field, result)

                from ..core.constants import WorkflowKeys
                computed_fields = get_state_value(state, WorkflowKeys.COMPUTED_FIELDS, [])
                if self.output_field not in computed_fields:
                    computed_fields.append(self.output_field)
                set_state_value(state, WorkflowKeys.COMPUTED_FIELDS, computed_fields)

            if self.transitions:
                return self._handle_transition_routing(state, result)

            return self._handle_simple_routing(state)

    def _handle_transition_routing(
        self,
        state: Dict[str, Any],
        result: Any
    ) -> Dict[str, Any]:
        for transition in self.transitions:
            check_value = result
            if 'ref' in transition:
                check_value = get_nested_value(result, transition['ref'])

            condition = transition['condition']
            if isinstance(condition, list):
                if check_value not in condition:
                    continue
            elif check_value != condition:
                continue

            next_dest = transition['next']
            logger.info(f"Found matching transition, transitioning to {next_dest}")
            self._set_status(state, next_dest)

            if next_dest in self.engine_context.outcome_map:
                self._set_outcome(state, next_dest)
            return state

        logger.warning(
            f"No matching transition for result '{result}' in step '{self.step_id}'"
        )
        self._set_status(state, 'failed')
        return state

    def _handle_simple_routing(self, state: Dict[str, Any]) -> Dict[str, Any]:
        self._set_status(state, 'success')

        if self.next_step:
            self._set_status(state, self.next_step)

            if self.next_step in self.engine_context.outcome_map:
                self._set_outcome(state, self.next_step)
        return state
