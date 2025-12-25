"""
Workflow Tool Definitions

Manually defined workflow tools for supervisor agents to use.
Each tool wraps a specific workflow YAML file.
"""

from soprano_sdk import WorkflowTool
import os
import sys

# Add parent directory (examples) to Python path so workflows can import their functions
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Get the path to examples directory (parent of supervisors)
EXAMPLES_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Greeting Workflow Tool
greeting_tool = WorkflowTool(
    yaml_path=os.path.join(EXAMPLES_DIR, "greeting_workflow.yaml"),
    name="greeting_workflow",
    description="""
    Use this workflow when the user wants to introduce themselves or provide their personal information.
    This workflow collects the user's name and age, then provides a personalized greeting.

    Use when user says things like:
    - "What's my name?"
    - "I want to introduce myself"
    - "Can you greet me?"
    - "Tell me about myself"
    """.strip()
)

# Return Processing Workflow Tool
return_tool = WorkflowTool(
    yaml_path=os.path.join(EXAMPLES_DIR, "return_workflow.yaml"),
    name="return_workflow",
    description="""
    Use this workflow when the user wants to return an item or process a return.
    This workflow:
    1. Collects the order ID
    2. Checks if the order is eligible for return
    3. Collects the return reason
    4. Validates the return reason
    5. Processes the return

    Use when user says things like:
    - "I want to return an item"
    - "Process a return for order #123"
    - "I need to return my order"
    - "Return processing"
    - "I received a damaged item"
    """.strip()
)

# List of all available workflow tools
WORKFLOW_TOOLS = [greeting_tool, return_tool]

# Tool names for reference
TOOL_NAMES = [tool.name for tool in WORKFLOW_TOOLS]

# Global message cache for CrewAI tools (since they can't accept parameters)
_message_cache = {}

def set_user_message(thread_id: str, message: str):
    """Store user message for a workflow thread (used by CrewAI tools)"""
    _message_cache[thread_id] = message

def get_user_message(thread_id: str) -> str:
    """Retrieve user message for a workflow thread"""
    return _message_cache.get(thread_id, "")

# NOTE: LangChain and CrewAI tools are manually defined in the tools/ directory:
# - tools/langgraph_tools.py - for LangGraph supervisor
# - tools/crewai_tools.py - for CrewAI supervisor
