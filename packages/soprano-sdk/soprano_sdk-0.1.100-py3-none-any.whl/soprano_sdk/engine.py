"""
Workflow Engine - Parses YAML workflow definitions and builds LangGraph execution graphs.
"""

import yaml
import importlib
from typing import TypedDict, Optional, Dict
from langgraph.graph import StateGraph
from langgraph.types import interrupt
from langgraph.constants import START, END
from langgraph.checkpoint.memory import InMemorySaver
from agno.agent import Agent
from agno.models.openai import OpenAIChat


class WorkflowEngine:

    def __init__(self, yaml_path: str):
        self.yaml_path = yaml_path
        with open(yaml_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.workflow_name = self.config['name']
        self.workflow_description = self.config['description']
        self.data_fields = self.config['data']
        self.steps = self.config['steps']
        self.outcomes = self.config['outcomes']

        # Build state type dynamically
        self.StateType = self._build_state_type()

        # Track steps by ID
        self.step_map = {step['id']: step for step in self.steps}
        self.outcome_map = {outcome['id']: outcome for outcome in self.outcomes}

    def _build_state_type(self) -> type:
        fields = {}
        for field in self.data_fields:
            field_name = field['name']
            field_type = field['type']

            # Map YAML types to Python types
            type_mapping = {
                'text': Optional[str],
                'number': Optional[int],
                'boolean': Optional[bool]
            }

            fields[field_name] = type_mapping.get(field_type, Optional[str])

        # Add internal workflow fields
        fields['_status'] = Optional[str]
        fields['_attempt_counts'] = Optional[Dict[str, int]]
        fields['_outcome_id'] = Optional[str]
        fields['_messages'] = Optional[list]  # For message accumulation
        fields['_conversations'] = Optional[Dict[str, list]]  # Conversation histories per field

        # Create TypedDict dynamically
        print("Fields: ", fields)
        return TypedDict('WorkflowState', fields)

    def _create_collect_input_with_agent_node(self, step_config: dict):
        """Create a node that collects input using an AI agent with conversation history"""
        step_id = step_config['id']
        field = step_config['field']
        max_attempts = step_config.get('max_attempts', 5)
        agent_config = step_config['agent']
        transitions = step_config.get('transitions', [])

        def node_fn(state: dict) -> dict:
            # Initialize conversations dict if not exists
            if '_conversations' not in state or state['_conversations'] is None:
                state['_conversations'] = {}

            # Initialize messages list if not exists
            if '_messages' not in state or state['_messages'] is None:
                state['_messages'] = []

            # Check if already collected
            if state.get(field) is not None:
                # Field pre-populated by external orchestrator
                # Route using first transition (success path)
                if transitions:
                    first_transition = transitions[0]
                    next_step = first_transition['next']
                    state['_status'] = f'{step_id}_{next_step}'

                    # If next step is an outcome, set it
                    if next_step in self.outcome_map:
                        state['_outcome_id'] = next_step

                return state

            # Get conversation history for this field
            conv_key = f'{field}_conversation'
            if conv_key not in state['_conversations']:
                state['_conversations'][conv_key] = []

            conversation = state['_conversations'][conv_key]

            # Check attempt count based on user messages in conversation
            attempt_count = len([m for m in conversation if m['role'] == 'user'])

            if attempt_count >= max_attempts:
                state['_status'] = f'{step_id}_max_attempts'
                state['_messages'] = [f"I'm having trouble understanding your {field}. Please contact customer service for assistance."]
                return state

            # Create agent
            agent = Agent(
                name=agent_config.get('name', f'{field}Collector'),
                model=OpenAIChat(id=agent_config.get('model', 'gpt-4o-mini')),
                instructions=agent_config['instructions']
            )

            # Generate prompt from agent
            if len(conversation) == 0:
                # First iteration: let agent generate initial greeting
                response = agent.run(conversation)
                prompt = response.content
                conversation.append({"role": "assistant", "content": prompt})
                state['_conversations'][conv_key] = conversation
            else:
                # Use last assistant message as prompt
                prompt = conversation[-1]['content']

            # Interrupt for user input
            user_input = interrupt(prompt)

            # Add to conversation
            conversation.append({"role": "user", "content": user_input})

            # Get agent response
            response = agent.run(conversation)
            agent_response = response.content
            conversation.append({"role": "assistant", "content": agent_response})

            # Update conversation in state
            state['_conversations'][conv_key] = conversation

            # Check agent response against all transitions
            matched = False
            for transition in transitions:
                pattern = transition['pattern']
                if pattern in agent_response:
                    matched = True
                    next_step = transition['next']

                    # Try to extract value after pattern
                    value = agent_response.split(pattern)[1].strip()

                    # If there's a value, store it in the field
                    if value:
                        # Store the value (convert type if needed)
                        field_def = next((f for f in self.data_fields if f['name'] == field), None)
                        if field_def and field_def['type'] == 'number':
                            state[field] = int(value)
                        else:
                            state[field] = value

                        state['_messages'] = [f"✓ {field.replace('_', ' ').title()} collected: {value}"]
                    else:
                        # No value extracted (e.g., "ORDER_ID_FAILED:")
                        state['_messages'] = []

                    # Set status based on next step
                    state['_status'] = f'{step_id}_{next_step}'

                    # If next step is an outcome, set it
                    if next_step in self.outcome_map:
                        state['_outcome_id'] = next_step

                    break

            if not matched:
                # Continue collecting - will self-loop
                # Don't store agent_response in _messages as it will become the interrupt prompt
                state['_status'] = f'{step_id}_collecting'
                state['_messages'] = []

            return state

        return node_fn

    def _create_call_function_node(self, step_config: dict):
        step_id = step_config['id']
        function_path = step_config['function']
        inputs = step_config['inputs']
        output_field = step_config['output']
        next_step = step_config.get('next')
        transitions = step_config.get('transitions', [])

        def node_fn(state: dict) -> dict:
            # Import the function
            module_name, function_name = function_path.rsplit('.', 1)
            module = importlib.import_module(module_name)
            func = getattr(module, function_name)

            # Prepare inputs by replacing placeholders
            kwargs = {}
            for key, value in inputs.items():
                if isinstance(value, str) and value.startswith('{') and value.endswith('}'):
                    # Replace placeholder with state value
                    field_name = value[1:-1]
                    kwargs[key] = state.get(field_name)
                else:
                    kwargs[key] = value

            # Call the function silently
            result = func(**kwargs)

            # Store result
            state[output_field] = result

            # Handle transition-based routing
            if transitions:
                # Check result against all transitions
                for transition in transitions:
                    condition = transition['condition']
                    next_dest = transition['next']

                    # Match condition against result
                    if result == condition:
                        state['_status'] = f'{step_id}_{next_dest}'

                        # If next dest is an outcome, set it
                        if next_dest in self.outcome_map:
                            state['_outcome_id'] = next_dest

                        break
            else:
                # No transitions, use simple success routing
                state['_status'] = f'{step_id}_success'

                # If next step is an outcome, set it now
                if next_step and next_step in self.outcome_map:
                    state['_outcome_id'] = next_step

            return state

        return node_fn

    def _create_routing_function(self, step_config: dict):
        step_id = step_config['id']
        next_step = step_config.get('next')
        transitions = step_config.get('transitions', [])

        def route_fn(state: dict) -> str:
            status = state.get('_status', '')

            # Handle transition-based routing (both collect_input_with_agent and call_function)
            if transitions:
                # Check for self-loop (collecting) - only for collect_input_with_agent
                if status == f'{step_id}_collecting':
                    return step_id

                # Check for max_attempts - only for collect_input_with_agent
                if status == f'{step_id}_max_attempts':
                    return END

                # Extract next_step from status
                # Status format: {step_id}_{next_step}
                if status.startswith(f'{step_id}_'):
                    target = status[len(step_id) + 1:]
                    # Check if target is an outcome or a step
                    return END if target in self.outcome_map else target

            # Handle call_function with simple next step (no transitions)
            if status == f'{step_id}_success':
                if next_step:
                    # outcome_id already set in node if it's an outcome
                    return END if next_step in self.outcome_map else next_step
                else:
                    return END

            return END

        return route_fn

    def build_graph(self, checkpointer=None):
        """Build the LangGraph execution graph

        Args:
            checkpointer: Optional checkpointer for state persistence.
                         Defaults to InMemorySaver() if not provided.
        """
        builder = StateGraph(self.StateType)

        # Create nodes for each step
        node_functions = {}
        for step in self.steps:
            step_id = step['id']
            action = step['action']

            if action == 'collect_input_with_agent':
                node_fn = self._create_collect_input_with_agent_node(step)
            elif action == 'call_function':
                node_fn = self._create_call_function_node(step)
            else:
                raise ValueError(f"Unknown action type: {action}")

            node_functions[step_id] = node_fn
            builder.add_node(step_id, node_fn)

        # Set entry point (first step)
        first_step_id = self.steps[0]['id']
        builder.add_edge(START, first_step_id)

        # Add routing edges
        for step in self.steps:
            step_id = step['id']
            route_fn = self._create_routing_function(step)

            # Build routing map - include self-loops and all possible destinations
            routing_map = {}

            # Add transition-based routing (works for both collect_input_with_agent and call_function)
            transitions = step.get('transitions', [])
            if transitions:
                # Add self-loop for collect_input_with_agent
                if step['action'] == 'collect_input_with_agent':
                    routing_map[step_id] = step_id

                # Add all possible destinations from transitions
                for transition in transitions:
                    next_dest = transition['next']
                    routing_map[next_dest] = next_dest if next_dest in self.step_map else END

            # Add next step for call_function without transitions
            next_step = step.get('next')
            if next_step:
                routing_map[next_step] = next_step if next_step in self.step_map else END

            # Always include END
            routing_map[END] = END

            builder.add_conditional_edges(step_id, route_fn, routing_map)

        # Compile with checkpointer (default to InMemorySaver if not provided)
        if checkpointer is None:
            checkpointer = InMemorySaver()
        graph = builder.compile(checkpointer=checkpointer)

        return graph

    def get_outcome_message(self, state: dict) -> str:
        """Get the outcome message from final state"""
        outcome_id = state.get('_outcome_id')
        if outcome_id and outcome_id in self.outcome_map:
            outcome = self.outcome_map[outcome_id]
            message_template = outcome['message']

            # Replace placeholders in message
            message = message_template
            for field in self.data_fields:
                field_name = field['name']
                value = state.get(field_name)
                if value is not None:
                    message = message.replace(f'{{{field_name}}}', str(value))

            return message

        return "Workflow completed."


def load_workflow(yaml_path: str, checkpointer=None):
    """Load a workflow from YAML configuration

    Args:
        yaml_path: Path to the workflow YAML file
        checkpointer: Optional checkpointer for state persistence.
                     Defaults to InMemorySaver() if not provided.
                     Example: MongoDBSaver for production persistence.

    Returns:
        Tuple of (graph, engine) where graph is the compiled LangGraph
        and engine is the WorkflowEngine instance
    """
    engine = WorkflowEngine(yaml_path)
    graph = engine.build_graph(checkpointer=checkpointer)
    return graph, engine