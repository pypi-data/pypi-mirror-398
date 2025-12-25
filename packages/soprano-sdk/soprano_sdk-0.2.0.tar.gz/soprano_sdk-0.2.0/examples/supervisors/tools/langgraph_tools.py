"""
LangGraph Tool Definitions

Manually defined LangChain tools for LangGraph supervisor.
"""

from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
import uuid

# Import workflow tools - assumes this module is run from supervisors directory
# or as part of supervisors package
try:
    # Try relative import first (when imported as package)
    from ..workflow_tools import greeting_tool, return_tool
except ImportError:
    # Fall back to direct import (when run from supervisors directory)
    from workflow_tools import greeting_tool, return_tool


@tool
def greeting_workflow(context: str = "", config: RunnableConfig = None) -> str:
    """Use this workflow when the user wants to introduce themselves or provide their personal information.

    This workflow collects the user's name and age, then provides a personalized greeting.

    Use when user says things like:
    - "What's my name?"
    - "I want to introduce myself"
    - "Can you greet me?"
    - "Tell me about myself"

    Args:
        context: User message for workflow (passed as context parameter)
        config: Configuration passed by LangGraph framework (contains session_id)

    Returns:
        Workflow result (either interrupt prompt or completion message)
    """
    # Extract session_id from config to use as workflow thread_id
    session_id = config.get("configurable", {}).get("session_id") if config else None
    workflow_thread_id = f"workflow_{session_id}" if session_id else str(uuid.uuid4())

    # Tool automatically detects state and resumes if needed
    return greeting_tool.execute(
        thread_id=workflow_thread_id,
        user_message=context,  # Pass user message for resume
        initial_context={}
    )


@tool
def return_workflow(context: str = "", config: RunnableConfig = None) -> str:
    """Use this workflow when the user wants to return an item or process a return.

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

    Args:
        context: User message for workflow (passed as context parameter)
        config: Configuration passed by LangGraph framework (contains session_id)

    Returns:
        Workflow result (either interrupt prompt or completion message)
    """
    # Extract session_id from config to use as workflow thread_id
    session_id = config.get("configurable", {}).get("session_id") if config else None
    workflow_thread_id = f"workflow_{session_id}" if session_id else str(uuid.uuid4())

    # Tool automatically detects state and resumes if needed
    return return_tool.execute(
        thread_id=workflow_thread_id,
        user_message=context,  # Pass user message for resume
        initial_context={}
    )


# List of all LangChain tools
LANGCHAIN_TOOLS = [greeting_workflow, return_workflow]
