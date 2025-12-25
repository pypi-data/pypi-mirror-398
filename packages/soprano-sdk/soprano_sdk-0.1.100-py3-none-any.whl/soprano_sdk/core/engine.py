from typing import Optional, Dict, Any, Tuple

import yaml
from jinja2 import Environment
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.constants import START
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph

from .constants import WorkflowKeys
from .state import create_state_model
from ..nodes.factory import NodeFactory
from ..routing.router import WorkflowRouter
from ..utils.function import FunctionRepository
from ..utils.logger import logger
from ..utils.tool import ToolRepository
from ..validation import validate_workflow


class WorkflowEngine:
    def __init__(self, yaml_path: str, configs: dict):
        self.yaml_path = yaml_path
        self.configs = configs or {}
        logger.info(f"Loading workflow from: {yaml_path}")

        try:
            with open(yaml_path, 'r') as f:
                self.config = yaml.safe_load(f)

            logger.info("Validating workflow configuration")
            validate_workflow(self.config)

            self.workflow_name = self.config['name']
            self.workflow_description = self.config['description']
            self.workflow_version = self.config['version']
            self.data_fields = self.config['data']
            self.steps = self.config['steps']
            self.outcomes = self.config['outcomes']
            self.metadata = self.config.get('metadata', {})

            self.StateType = create_state_model(self.data_fields)

            self.step_map = {step['id']: step for step in self.steps}
            self.outcome_map = {outcome['id']: outcome for outcome in self.outcomes}

            self.function_repository = FunctionRepository()
            self.tool_repository = None
            if tool_config := self.config.get("tool_config"):
                self.tool_repository = ToolRepository(tool_config)

            self.context_store = {}
            self.collect_input_fields = self._get_collect_input_fields()

            logger.info(
                f"Workflow loaded: {self.workflow_name} v{self.workflow_version} "
                f"({len(self.steps)} steps, {len(self.outcomes)} outcomes)"
            )

        except Exception as e:
            raise e

    def get_config_value(self, key, default_value: Optional[Any]=None):
        if value := self.configs.get(key) :
            return value

        if value := self.config.get(key) :
            return value

        return default_value

    def _get_collect_input_fields(self) -> set:
        fields = set()
        for step in self.steps:
            if step.get('action') == 'collect_input_with_agent' and (field := step.get('field')):
                fields.add(field)
        return fields

    def update_context(self, context: Dict[str, Any]):
        self.context_store.update(context)
        logger.info(f"Context updated: {context}")

    def remove_context_field(self, field_name: str):
        if field_name in self.context_store:
            del self.context_store[field_name]
            logger.info(f"Removed context field: {field_name}")
    
    def get_context_value(self, field_name: str):
        value = self.context_store.get(field_name, None)
        if value is not None:
            logger.info(f"Retrieved context value for '{field_name}': {value}")
        return value

    def build_graph(self, checkpointer=None):
        logger.info("Building workflow graph")

        try:
            builder = StateGraph(self.StateType)

            collector_nodes = []

            logger.info("Adding nodes to graph")
            for step in self.steps:
                step_id = step['id']
                action = step['action']

                if action == 'collect_input_with_agent':
                    collector_nodes.append(step_id)

                node_fn = NodeFactory.create(step, engine_context=self)
                builder.add_node(step_id, node_fn)

                logger.info(f"Added node: {step_id} (action: {action})")

            first_step_id = self.steps[0]['id']
            builder.add_edge(START, first_step_id)
            logger.info(f"Set entry point: {first_step_id}")

            logger.info("Adding routing edges")
            for step in self.steps:
                step_id = step['id']

                router = WorkflowRouter(step, self.step_map, self.outcome_map)
                route_fn = router.create_route_function()
                routing_map = router.get_routing_map(collector_nodes)

                builder.add_conditional_edges(step_id, route_fn, routing_map)

                logger.info(
                    f"Added routing for {step_id}: {len(routing_map)} destinations"
                )

            if checkpointer is None:
                checkpointer = InMemorySaver()
                logger.info("Using InMemorySaver for state persistence")
            else:
                logger.info(f"Using custom checkpointer: {type(checkpointer).__name__}")

            graph = builder.compile(checkpointer=checkpointer)

            logger.info("Workflow graph built successfully")
            return graph

        except Exception as e:
            raise RuntimeError(f"Failed to build workflow graph: {e}")

    def get_outcome_message(self, state: Dict[str, Any]) -> str:
        outcome_id = state.get(WorkflowKeys.OUTCOME_ID)
        step_id = state.get(WorkflowKeys.STEP_ID)

        outcome = self.outcome_map.get(outcome_id)
        if outcome and 'message' in outcome:
            message = outcome['message']
            template_loader = self.get_config_value("template_loader", Environment())
            message = template_loader.from_string(message).render(state)
            logger.info(f"Outcome message generated in step {step_id}: {message}")
            return message

        if error := state.get("error"):
            logger.info(f"Outcome error found in step {step_id}: {error}")
            return f"{error}"

        if message := state.get(WorkflowKeys.MESSAGES):
            logger.info(f"Outcome message found in step {step_id}: {message}")
            return f"{message}"

        logger.error(f"No outcome message found in step {step_id}")
        return "{'error': 'Unable to complete the request'}"

    def get_step_info(self, step_id: str) -> Optional[Dict[str, Any]]:
        return self.step_map.get(step_id)

    def get_outcome_info(self, outcome_id: str) -> Optional[Dict[str, Any]]:
        return self.outcome_map.get(outcome_id)

    def list_steps(self) -> list:
        return [step['id'] for step in self.steps]

    def list_outcomes(self) -> list:
        return [outcome['id'] for outcome in self.outcomes]

    def get_workflow_info(self) -> Dict[str, Any]:
        return {
            'name': self.workflow_name,
            'description': self.workflow_description,
            'version': self.workflow_version,
            'steps': len(self.steps),
            'outcomes': len(self.outcomes),
            'data_fields': [f['name'] for f in self.data_fields],
            'metadata': self.metadata
        }

    def get_tool_policy(self) -> str:
        tool_config = self.config.get('tool_config')
        if not tool_config:
            raise ValueError("Tool config is not provided in the YAML")
        return tool_config.get('usage_policy')


def load_workflow(yaml_path: str, checkpointer=None, config=None) -> Tuple[CompiledStateGraph, WorkflowEngine]:
    """
    Load a workflow from YAML configuration.

    This is the main entry point for using the framework.

    Args:
        yaml_path: Path to the workflow YAML file
        checkpointer: Optional checkpointer for state persistence.
                     Defaults to InMemorySaver() if not provided.
                     Example: MongoDBSaver for production persistence.

    Returns:
        Tuple of (compiled_graph, engine) where:
        - compiled_graph: LangGraph ready for execution
        - engine: WorkflowEngine instance for introspection

    Example:
        ```python
        graph, engine = load_workflow("workflow.yaml")
        result = graph.invoke({}, config={"configurable": {"thread_id": "123"}})
        message = engine.get_outcome_message(result)
        ```
    """
    engine = WorkflowEngine(yaml_path, configs=config)
    graph = engine.build_graph(checkpointer=checkpointer)
    return graph, engine
