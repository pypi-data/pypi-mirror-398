# Workflow Supervisors

This directory contains supervisor agents that orchestrate multiple workflows based on user intent. The supervisor acts as an intelligent router that understands what the user wants and invokes the appropriate workflow.

## Architecture

```
User → Supervisor Agent → [Workflow Tools] → Selected Workflow → Result → User
                              ↓
                    [greeting_tool, return_tool]
```

**Supervisor Pattern**:
1. User sends a message to supervisor
2. Supervisor analyzes intent using LLM
3. Supervisor selects and invokes appropriate workflow tool
4. Workflow executes and returns result
5. Supervisor returns result to user

## Available Implementations

### 1. LangGraph Supervisor (`langgraph_supervisor_ui.py`)

Uses LangGraph's ReAct agent pattern with tool calling.

**Features**:
- Built on LangGraph's create_react_agent
- Native tool calling with OpenAI
- Stateful conversations with checkpointing
- Stream-based responses

**Run**:
```bash
cd examples/supervisors
python langgraph_supervisor_ui.py
```

---

### 2. CrewAI Supervisor (`crewai_supervisor_ui.py`)

Uses CrewAI's agent and task delegation pattern.

**Features**:
- Built on CrewAI's Agent/Task/Crew pattern
- Role-based agent design
- Task-oriented execution
- CrewAI's orchestration layer

**Run**:
```bash
cd examples/supervisors
python crewai_supervisor_ui.py
```

---

## Workflow Tools

Workflows are wrapped as tools that agents can invoke. See `workflow_tools.py` for definitions.

### Greeting Workflow Tool
- **Name**: `greeting_workflow`
- **Purpose**: Collects user's name and age, provides personalized greeting
- **Trigger phrases**: "What's my name?", "Greet me", "Introduce myself"

### Return Workflow Tool
- **Name**: `return_workflow`
- **Purpose**: Process customer returns (order ID → eligibility → reason → process)
- **Trigger phrases**: "Return an item", "Process return", "I received damaged item"

---

## Usage Examples

### Example 1: Return Processing

```
User: "I want to return an item"
Supervisor: [Analyzes intent] → Invokes return_workflow
Workflow: "Hello! I hope you're doing well today. Could you please provide me with your order ID?"
User: "ORDER-123"
Workflow: [Checks eligibility] → [Collects reason] → [Processes return]
Result: "✅ Return processed successfully!"
```

### Example 2: Greeting

```
User: "What's my name?"
Supervisor: [Analyzes intent] → Invokes greeting_workflow
Workflow: "Hello! What's your name?"
User: "Alice"
Workflow: "How old are you?"
User: "30"
Result: "Hello Alice! You are 30 years old."
```

### Example 3: Context Injection

```
User: "Process return for order #456, it was damaged"
Supervisor: [Extracts context] → Invokes return_workflow with context
Workflow: [Uses pre-populated order_id="456", return_reason="damaged"]
Result: [Skips collection, validates, processes]
```

---

## How Workflow Tools Work

The `WorkflowTool` class (see `soprano_sdk/tools.py`) wraps a workflow YAML file:

```python
greeting_tool = WorkflowTool(
    yaml_path="examples/greeting_workflow.yaml",
    name="greeting_workflow",
    description="Collects user's name and age..."
)

# Convert to framework-specific tool
langchain_tool = greeting_tool.to_langchain_tool()
crewai_tool = greeting_tool.to_crewai_tool()
```

When invoked:
1. Loads workflow from YAML
2. Executes with LangGraph engine
3. Returns final outcome message

---

## Comparing LangGraph vs CrewAI

| Feature | LangGraph | CrewAI |
|---------|-----------|---------|
| **Pattern** | ReAct agent | Agent/Task/Crew |
| **Tool Calling** | Native OpenAI | LangChain tools |
| **State Management** | Built-in checkpointing | Task-based |
| **Streaming** | Yes | Limited |
| **Learning Curve** | Medium | Easy |
| **Best For** | Complex workflows | Role-based agents |

---

## Adding New Workflows

To add a new workflow to the supervisor:

1. **Create workflow YAML** in `examples/`
```yaml
name: "Support Ticket Workflow"
description: "Handle customer support tickets"
# ... workflow definition
```

2. **Add tool definition** in `workflow_tools.py`
```python
support_tool = WorkflowTool(
    yaml_path=os.path.join(EXAMPLES_DIR, "support_workflow.yaml"),
    name="support_workflow",
    description="Handle customer support tickets and issues..."
)

WORKFLOW_TOOLS = [greeting_tool, return_tool, support_tool]
```

3. **Restart supervisor** - Tools are loaded at startup

That's it! The supervisor will automatically have access to the new workflow.

---

## Prerequisites

Install required dependencies:

```bash
# Install all supervisor dependencies
uv add langchain-openai crewai --optional supervisors

# Or sync with dev dependencies
uv sync --dev --extra supervisors

# Or if using pip
pip install conversational-sop-framework[supervisors,dev]
```

**Note**: CrewAI agents can use LangChain tools directly, so no separate CrewAI tool library is needed.

Set OpenAI API key:
```bash
export OPENAI_API_KEY="sk-..."
```

---

## Advanced: Interactive Workflows

Currently, workflows run non-interactively (context injection only). For truly interactive multi-turn workflows, you would need to:

1. Maintain workflow thread_id in supervisor state
2. Resume workflow with user input on each turn
3. Handle interrupts and pass messages back to supervisor

This is a future enhancement that would enable workflows to pause/resume through the supervisor.

---

## Troubleshooting

### "Module not found" errors
```bash
# Make sure you're running from supervisors directory
cd examples/supervisors
python langgraph_supervisor_ui.py
```

### "Tool not working" errors
- Check that workflow YAML files exist in examples/
- Verify OpenAI API key is set
- Check console output for specific errors

### Supervisor not selecting right workflow
- Improve tool descriptions in `workflow_tools.py`
- Add more examples of trigger phrases
- Try different LLM models (gpt-4 instead of gpt-4o-mini)

---

## Architecture Benefits

1. **Separation of Concerns**
   - Supervisor: Intent recognition and routing
   - Workflows: Domain-specific business logic

2. **Scalability**
   - Add new workflows without changing supervisor code
   - Each workflow is independently testable

3. **Flexibility**
   - Switch between LangGraph/CrewAI without changing workflows
   - Workflows can be used standalone or via supervisor

4. **Composability**
   - Workflows are reusable tools
   - Can be used in any agent framework

---

## Next Steps

- **Add MongoDB persistence** to supervisor for multi-session conversations
- **Implement interactive workflow mode** for true multi-turn dialogs
- **Add context extraction** to parse entities (order IDs, names) from user messages
- **Create more workflows** for different business processes
- **Add workflow discovery** to auto-load workflows from directory

---

## Links

- [Main README](../../README.md)
- [Workflow Engine Documentation](../../soprano_sdk/engine.py)
- [Persistence Examples](../persistence/)
