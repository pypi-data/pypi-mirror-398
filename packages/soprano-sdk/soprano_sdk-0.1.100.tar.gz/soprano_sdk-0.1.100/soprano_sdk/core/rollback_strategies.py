import copy
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, List

from soprano_sdk.core.constants import WorkflowKeys, ActionType
from ..utils.logger import logger

class RollbackStrategy(ABC):
    @abstractmethod
    def rollback_to_node(
        self,
        state: Dict[str, Any],
        target_node: str,
        node_execution_order: List[str],
        node_field_map: Dict[str, str],
        workflow_steps: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    def should_save_snapshot(self) -> bool:
        pass

    @abstractmethod
    def save_snapshot(self, state: Dict[str, Any], node_id: str, execution_index: int) -> None:
        pass

    @abstractmethod
    def get_strategy_name(self) -> str:
        pass


def _restore_from_snapshot(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    return copy.deepcopy(snapshot['state'])


def _clear_future_executions(
        state: Dict[str, Any],
    target_node: str,
    workflow_steps: List[Dict[str, Any]]
) -> Dict[str, Any]:
    target_step_index = next(
        (i for i, step in enumerate(workflow_steps) if step['id'] == target_node),
        None
    )

    if target_step_index is None:
        logger.warning(f"Target node {target_node} not found in workflow steps")
        return state

    future_steps = workflow_steps[target_step_index:]

    logger.info(f"Future steps to clear: {[s['id'] for s in future_steps]}")

    for step in future_steps:
        action = step.get('action')

        if action == ActionType.COLLECT_INPUT_WITH_AGENT.value:
            field_name = step.get('field')
            if field_name:
                state[field_name] = None

                conv_key = f"{field_name}_conversation"
                conversations = state.get(WorkflowKeys.CONVERSATIONS, {})
                if conv_key in conversations:
                    del conversations[conv_key]
                    logger.info(f"Cleared conversation: {conv_key}")

        elif action == ActionType.CALL_FUNCTION.value:
            output_field = step.get('output')
            if output_field:
                state[output_field] = None
                logger.info(f"Cleared computed field: {output_field}")

    return state


class HistoryBasedRollback(RollbackStrategy):
    def get_strategy_name(self) -> str:
        return "history_based"

    def should_save_snapshot(self) -> bool:
        return True

    def save_snapshot(self, state: Dict[str, Any], node_id: str, execution_index: int) -> None:
        state_history = state.get(WorkflowKeys.STATE_HISTORY, [])

        snapshot = {
            'snapshot_id': str(uuid.uuid4()),
            'node_about_to_execute': node_id,
            'execution_index': execution_index,
            'timestamp': datetime.now().isoformat(),
            'state': copy.deepcopy(state),
        }

        state_history.append(snapshot)
        state[WorkflowKeys.STATE_HISTORY] = state_history

        logger.info(f"Saved snapshot #{len(state_history)-1} before executing {node_id}")

    def rollback_to_node(
        self,
        state: Dict[str, Any],
        target_node: str,
        node_execution_order: List[str],
        node_field_map: Dict[str, str],
        workflow_steps: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        state_history = state.get(WorkflowKeys.STATE_HISTORY, [])

        if not state_history:
            logger.warning("No state history available for rollback")
            return {}

        logger.info(f"Looking for snapshot before node '{target_node}'")

        target_snapshot = None
        target_index = None

        for i, snapshot in enumerate(state_history):
            if snapshot.get('node_about_to_execute') == target_node:
                target_snapshot = snapshot
                target_index = i
                break

        if target_snapshot is None:
            logger.warning(f"No snapshot found before node '{target_node}'")
            return {}

        logger.info(f"Found snapshot at index {target_index}")
        restored_state = _restore_from_snapshot(target_snapshot)

        restored_state = _clear_future_executions(
            restored_state,
            target_node,
            workflow_steps
        )

        restored_state[WorkflowKeys.STATE_HISTORY] = state_history[:target_index + 1]

        logger.info(f"Successfully rolled back to {target_node}")

        return restored_state


def _build_dependency_graph(
    workflow_steps: List[Dict[str, Any]]
) -> Dict[str, List[str]]:
    graph = {}

    for step in workflow_steps:
        field = step.get('field') or step.get('output')

        if not field:
            continue

        depends_on = step.get('depends_on')

        if depends_on:
            if isinstance(depends_on, str):
                depends_on_list = [depends_on]
            elif isinstance(depends_on, list):
                depends_on_list = depends_on
            else:
                logger.warning(f"Invalid depends_on type for field '{field}': {type(depends_on)}")
                depends_on_list = []

            for parent_field in depends_on_list:
                if parent_field not in graph:
                    graph[parent_field] = []
                if field not in graph[parent_field]:
                    graph[parent_field].append(field)

        if field not in graph:
            graph[field] = []

    return graph


def _find_all_dependents(
    field: str,
    dependency_graph: Dict[str, List[str]]
) -> set:
    all_dependents = set()
    visited = set()

    def _recurse(current_field: str):
        if current_field in visited:
            return
        visited.add(current_field)

        direct_dependents = dependency_graph.get(current_field, [])

        for dependent in direct_dependents:
            all_dependents.add(dependent)
            _recurse(dependent)

    _recurse(field)

    return all_dependents


def _clear_field_conversation(state: Dict[str, Any], field: str) -> None:
    conv_key = f"{field}_conversation"
    conversations = state.get(WorkflowKeys.CONVERSATIONS, {})

    if conv_key in conversations:
        del conversations[conv_key]
        logger.info(f"Cleared conversation: {conv_key}")


class DependencyBasedRollback(RollbackStrategy):
    def get_strategy_name(self) -> str:
        return "dependency_based"

    def should_save_snapshot(self) -> bool:
        return False

    def save_snapshot(self, state: Dict[str, Any], node_id: str, execution_index: int) -> None:
        return None

    def rollback_to_node(
        self,
        state: Dict[str, Any],
        target_node: str,
        node_execution_order: List[str],
        node_field_map: Dict[str, str],
        workflow_steps: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        target_field = node_field_map.get(target_node)

        if not target_field:
            logger.warning(f"No field found for target node '{target_node}'")
            return state

        logger.info(f"Rolling back to node '{target_node}' (field: '{target_field}')")

        dependency_graph = _build_dependency_graph(workflow_steps)

        logger.info(f"Dependency graph: {dependency_graph}")

        dependent_fields = _find_all_dependents(target_field, dependency_graph)

        logger.info(f"Fields dependent on '{target_field}': {dependent_fields}")

        state[target_field] = None
        _clear_field_conversation(state, target_field)

        for field in dependent_fields:
            state[field] = None
            _clear_field_conversation(state, field)
            logger.info(f"Cleared dependent field: {field}")

        logger.info(f"Successfully rolled back to {target_node} using dependency graph")

        return state
