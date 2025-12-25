from abc import ABC, abstractmethod
from typing import Dict, Any, Callable, List

from langgraph.errors import GraphInterrupt

from ..core.constants import WorkflowKeys
from ..utils.logger import logger


class ActionStrategy(ABC):
    def __init__(self, step_config: Dict[str, Any], engine_context: Any):
        self.step_config = step_config
        self.engine_context = engine_context
        self.step_id = step_config.get('id')
        self.action = step_config.get('action')

    @abstractmethod
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def pre_execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        pass

    def get_node_function(self) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
        def node_fn(state: Dict[str, Any]) -> Dict[str, Any]:
            logger.info(f"Executing node: {self.step_id} (action: {self.action})")
            try:
                self.pre_execute(state)
                result = self.execute(state)
                logger.info(f"Node {self.step_id} completed successfully")
                logger.info(f"Result: {result}")

                if state.get(WorkflowKeys.ERROR):
                    state[WorkflowKeys.OUTCOME_ID] = WorkflowKeys.ERROR
                    self._set_status(state, WorkflowKeys.ERROR)
                return result
            except GraphInterrupt:
                raise
            except Exception as e:
                logger.error(f"Node {self.step_id} failed: {e}", exc_info=True)
                self._set_status(state, WorkflowKeys.ERROR)
                state[WorkflowKeys.ERROR] = {"error": f"Unable to complete the request: {str(e)}"}
                state[WorkflowKeys.OUTCOME_ID] = WorkflowKeys.ERROR
                return state

        return node_fn

    def _get_transitions(self) -> List[Dict[str, Any]]:
        return self.step_config.get('transitions', [])

    def _get_next_step(self) -> str:
        return self.step_config.get('next')

    def _set_status(self, state: Dict[str, Any], status_suffix: str):
        from ..core.constants import WorkflowKeys
        state[WorkflowKeys.STATUS] = f'{self.step_id}_{status_suffix}'

    def _set_outcome(self, state: Dict[str, Any], outcome_id: str):
        from ..core.constants import WorkflowKeys
        state[WorkflowKeys.OUTCOME_ID] = outcome_id
