# Conversational SOP Framework

A YAML-driven workflow engine with AI agent integration for building conversational Standard Operating Procedures (SOPs).

## Features

- **YAML Configuration**: Define workflows declaratively using YAML
- **AI Agent Integration**: Built-in support for conversational data collection using OpenAI models
- **State Management**: Powered by LangGraph for robust workflow execution
- **External Context Injection**: Support for pre-populated fields from external orchestrators
- **Pattern Matching**: Flexible transition logic based on patterns and conditions
- **Visualization**: Generate workflow graphs as images or Mermaid diagrams

## Installation

```bash
pip install conversational-sop-framework
```

Or using uv:

```bash
uv add conversational-sop-framework
```

## Quick Start

### 1. Define a Workflow in YAML

```yaml
name: "User Greeting Workflow"
description: "Collects user information and provides a personalized greeting"
version: "1.0"

data:
  - name: name
    type: text
    description: "User's name"
  - name: age
    type: number
    description: "User's age in years"

steps:
  - id: get_name
    action: collect_input_with_agent
    field: name
    max_attempts: 3
    agent:
      name: "NameCollector"
      model: "gpt-4o-mini"
      instructions: |
        Your goal is to capture the user's name.
        Start with a friendly greeting and ask for their name.
        Once you have a clear name, respond with: 'NAME_CAPTURED: [name]'
    transitions:
      - pattern: "NAME_CAPTURED:"
        next: get_age
      - pattern: "NAME_FAILED:"
        next: end_failed

  - id: get_age
    action: collect_input_with_agent
    field: age
    max_attempts: 3
    agent:
      name: "AgeCollector"
      model: "gpt-4o-mini"
      instructions: |
        Ask for the user's age.
        Once you have a valid age, respond with: 'AGE_CAPTURED: [age]'
    transitions:
      - pattern: "AGE_CAPTURED:"
        next: end_success
      - pattern: "AGE_FAILED:"
        next: end_failed

outcomes:
  - id: end_success
    type: success
    message: "Hello {name}! You are {age} years old."

  - id: end_failed
    type: failure
    message: "Sorry, I couldn't complete the workflow."
```

### 2. Load and Execute the Workflow

```python
from soprano_sdk import load_workflow
from langgraph.types import Command
import uuid

# Load workflow
graph, engine = load_workflow("greeting_workflow.yaml")

# Setup execution
thread_id = str(uuid.uuid4())
config = {"configurable": {"thread_id": thread_id}}

# Start workflow
result = graph.invoke({}, config=config)

# Interaction loop
while True:
    if "__interrupt__" in result and result["__interrupt__"]:
        # Get prompt from workflow
        prompt = result["__interrupt__"][0].value
        print(f"Bot: {prompt}")

        # Get user input
        user_input = input("You: ")

        # Resume workflow with user input
        result = graph.invoke(Command(resume=user_input), config=config)
    else:
        # Workflow completed
        message = engine.get_outcome_message(result)
        print(f"Bot: {message}")
        break
```

### 3. External Context Injection

You can inject external context into workflows:

```python
# Pre-populate fields from external orchestrator
result = graph.invoke({
    "name": "Alice",
    "age": 30
}, config=config)

# Workflow will automatically skip collection steps
# and proceed to validation/processing
```

### 4. Persistence

The library supports pluggable persistence through LangGraph's checkpointer system.

#### In-Memory (Default)

```python
# No persistence - state lost when process ends
graph, engine = load_workflow("workflow.yaml")
```

#### MongoDB Persistence

```python
from soprano_sdk import load_workflow
from langgraph.checkpoint.mongodb import MongoDBSaver
from pymongo import MongoClient

# Setup MongoDB persistence (local)
client = MongoClient("mongodb://localhost:27017")
checkpointer = MongoDBSaver(client=client, db_name="workflows")

# Or MongoDB Atlas (cloud)
client = MongoClient("mongodb+srv://user:pass@cluster.mongodb.net")
checkpointer = MongoDBSaver(client=client, db_name="workflows")

# Load workflow with persistence
graph, engine = load_workflow("workflow.yaml", checkpointer=checkpointer)

# Execute with thread_id for state tracking
config = {"configurable": {"thread_id": "user-123-return"}}
result = graph.invoke({}, config=config)

# Later, resume using same thread_id
result = graph.invoke(Command(resume="continue"), config=config)
```

#### Thread ID Strategies

Choose a thread_id strategy based on your use case:

| Strategy | Thread ID Pattern | Best For |
|----------|-------------------|----------|
| **Entity-Based** | `f"return_{order_id}"` | One workflow per business entity |
| **Conversation** | `str(uuid.uuid4())` | Multiple concurrent workflows |
| **User+Workflow** | `f"{user_id}_{workflow_type}"` | One workflow type per user |
| **Session-Based** | `session_id` | Web apps with sessions |

**Examples**: See `examples/persistence/` for detailed examples of each strategy.

## Workflow Actions

### collect_input_with_agent

Collects user input using an AI agent with conversation history.

```yaml
- id: collect_field
  action: collect_input_with_agent
  field: field_name
  max_attempts: 5
  agent:
    name: "CollectorAgent"
    model: "gpt-4o-mini"
    instructions: |
      Instructions for the agent...
  transitions:
    - pattern: "SUCCESS:"
      next: next_step
    - pattern: "FAILED:"
      next: failure_outcome
```

### call_function

Calls a Python function with workflow state.

```yaml
- id: process_data
  action: call_function
  function: "my_module.my_function"
  inputs:
    field1: "{field_name}"
    field2: "static_value"
  output: result_field
  transitions:
    - condition: true
      next: success_step
    - condition: false
      next: failure_step
```

## Examples

See the `examples/` directory for complete workflow examples:

- `greeting_workflow.yaml` - Simple user greeting workflow
- `return_workflow.yaml` - Customer return processing workflow
- Function modules with business logic (`greeting_functions.py`, `return_functions.py`)
- `persistence/` - Persistence strategy examples (entity-based, conversation-based, SQLite demo)

## Running Workflows

### CLI Demo

```bash
# Basic usage (in-memory)
python scripts/workflow_demo.py examples/greeting_workflow.yaml

# With MongoDB persistence (local)
python scripts/workflow_demo.py examples/greeting_workflow.yaml --mongodb mongodb://localhost:27017

# Resume existing workflow
python scripts/workflow_demo.py examples/greeting_workflow.yaml --mongodb mongodb://localhost:27017 --thread-id abc-123

# With MongoDB Atlas
python scripts/workflow_demo.py examples/greeting_workflow.yaml --mongodb mongodb+srv://user:pass@cluster.mongodb.net
```

### Gradio UI

```bash
# Basic usage (in-memory)
python scripts/workflow_demo_ui.py examples/greeting_workflow.yaml

# With MongoDB persistence
python scripts/workflow_demo_ui.py examples/greeting_workflow.yaml --mongodb mongodb://localhost:27017

# With MongoDB Atlas
python scripts/workflow_demo_ui.py examples/greeting_workflow.yaml --mongodb mongodb+srv://user:pass@cluster.mongodb.net
```

### Persistence Examples

```bash
cd examples/persistence

# Entity-based (order ID as thread ID)
python entity_based.py ORDER-123

# Conversation-based (UUID with supervisor pattern)
python conversation_based.py ../return_workflow.yaml --order-id ORDER-456

# MongoDB demo with pause/resume
python mongodb_demo.py

# Use MongoDB Atlas
python mongodb_demo.py --mongodb mongodb+srv://user:pass@cluster.mongodb.net
```

### Visualize Workflow

```bash
python scripts/visualize_workflow.py examples/greeting_workflow.yaml
```

## Development

### Setup

```bash
git clone https://github.com/dnivra26/soprano_sdk_framework.git
cd soprano_sdk_framework
uv sync --dev
```

### Run Tests

```bash
python tests/test_external_values.py
```

## Architecture

- **soprano_sdk/**: Core library package
  - `engine.py`: Workflow engine implementation
  - `__init__.py`: Public API exports

- **examples/**: Example workflows and persistence patterns
  - Workflow YAML definitions
  - Function modules with business logic
  - `persistence/`: Different persistence strategy examples

- **scripts/**: Utility tools for running and visualizing workflows
  - `workflow_demo.py`: CLI runner with persistence support
  - `workflow_demo_ui.py`: Gradio UI with thread management
  - `visualize_workflow.py`: Workflow graph generator

- **tests/**: Test suite
- **legacy/**: Previous implementations (FSM, direct LangGraph)

## Requirements

### Core Dependencies

- Python >= 3.12
- agno >= 2.0.7
- langgraph >= 0.6.8
- openai >= 1.108.1
- pyyaml >= 6.0

### Optional Dependencies

For MongoDB persistence:
```bash
# Using pip
pip install langgraph-checkpoint-mongodb pymongo

# Using uv (recommended)
uv add langgraph-checkpoint-mongodb pymongo --optional persistence

# Or install library with persistence support
pip install conversational-sop-framework[persistence]
```

For development (includes Gradio UI and tests):
```bash
pip install conversational-sop-framework[dev]
# or
uv sync --dev
```

## License

MIT

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## To Do

- ✅ Database persistence (SqliteSaver, PostgresSaver supported)
- ✅ Pluggable checkpointer system
- ✅ Thread ID strategies and examples
- Additional action types (webhook, conditional branching, parallel execution)
- More workflow examples (customer onboarding, support ticketing, approval flows)
- Workflow testing utilities
- Metrics and monitoring hooks

## Links

- [GitHub Repository](https://github.com/dnivra26/soprano_sdk_framework)
- [Issues](https://github.com/dnivra26/soprano_sdk_framework/issues)
