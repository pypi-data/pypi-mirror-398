from typing import Dict, Any, List, Optional

from langgraph.constants import END

from ..core.constants import WorkflowKeys
from ..utils.logger import logger


class WorkflowRouter:
    def __init__(self, step_config: Dict[str, Any], step_map: Dict[str, Any], outcome_map: Dict[str, Any]):
        self.step_id = step_config['id']
        self.action = step_config['action']
        self.step_map = step_map
        self.outcome_map = outcome_map
        self.transitions = step_config.get('transitions', [])
        self.next_step = step_config.get('next')

    def create_route_function(self):
        def route_fn(state: Dict[str, Any]) -> str:
            try:
                return self._route(state)
            except Exception as e:
                logger.error(f"Routing error in step '{self.step_id}': {e}")
                raise RuntimeError(f"Failed to route from step '{self.step_id}': {e}")

        return route_fn

    def _route(self, state: Dict[str, Any]) -> str:
        status = state.get(WorkflowKeys.STATUS, '')

        if status == f'{self.step_id}_collecting':
            logger.info(f"Self-loop: {self.step_id} (collecting)")
            return self.step_id

        if status == f'{self.step_id}_error' :
            logger.info(f"Error encountered in {self.step_id}, ending workflow")
            return END

        if status == f'{self.step_id}_max_attempts':
            logger.info(f"Max attempts reached in {self.step_id}, ending workflow")
            return END

        if self.transitions or status.startswith(f'{self.step_id}_'):
            next_node = self._route_with_transitions(state, status)
            if next_node:
                return next_node

        if self.next_step:
            is_outcome = self.next_step in self.outcome_map
            logger.info(f"Simple routing: {self.step_id} -> {self.next_step}")
            return END if is_outcome else self.next_step

        logger.info(f"No routing match for status '{status}', ending workflow")
        return END

    def _route_with_transitions(self, state: Dict[str, Any], status: str) -> Optional[str]:
        if not status.startswith(f'{self.step_id}_'):
            return None

        target = status[len(self.step_id) + 1:]

        if target in self.outcome_map:
            logger.info(f"Routing to outcome: {self.step_id} -> {target}")
            return END

        if target in self.step_map:
            logger.info(f"Routing to step: {self.step_id} -> {target}")
            return target

        logger.warning(f"Unknown routing target '{target}' from step '{self.step_id}'")
        return END

    def get_routing_map(self, collector_nodes: List[str]) -> Dict[str, str]:
        routing_map = {}

        if self.action == 'collect_input_with_agent':
            routing_map[self.step_id] = self.step_id

        for transition in self.transitions:
            next_dest = transition['next']
            if next_dest in self.step_map:
                routing_map[next_dest] = next_dest
            else:
                routing_map[next_dest] = END

        if self.next_step:
            if self.next_step in self.step_map:
                routing_map[self.next_step] = self.next_step
            else:
                routing_map[self.next_step] = END

        for collector_node in collector_nodes:
            routing_map[collector_node] = collector_node

        routing_map[END] = END

        return routing_map
