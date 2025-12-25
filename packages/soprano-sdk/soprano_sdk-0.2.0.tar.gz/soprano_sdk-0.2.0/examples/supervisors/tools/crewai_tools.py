"""
CrewAI Tool Definitions

Manually defined CrewAI tools for CrewAI supervisor.

Note: CrewAI tools cannot accept parameters due to schema generation limitations.
The UI must set the current session context before invoking the supervisor.
"""

from crewai.tools import BaseTool

# Import workflow tools - assumes this module is run from supervisors directory
# or as part of supervisors package
try:
    # Try relative import first (when imported as package)
    from ..workflow_tools import greeting_tool, return_tool, get_user_message
except ImportError:
    # Fall back to direct import (when run from supervisors directory)
    from workflow_tools import greeting_tool, return_tool, get_user_message

# Global session context (set by UI before supervisor call)
_current_session_id = None

def set_current_session(session_id: str):
    """Set the current session ID (called by UI before supervisor invocation)"""
    global _current_session_id
    _current_session_id = session_id


class GreetingWorkflowTool(BaseTool):
    name: str = "greeting_workflow"
    description: str = """Use this workflow when the user wants to introduce themselves or provide their personal information.

    This workflow collects the user's name and age, then provides a personalized greeting.

    Use when user says things like:
    - "What's my name?"
    - "I want to introduce myself"
    - "Can you greet me?"
    - "Tell me about myself"
    """

    def _run(self) -> str:
        """Execute the greeting workflow

        Returns:
            Workflow result (either interrupt prompt or completion message)
        """
        # Use global session context
        thread_id = f"workflow_{_current_session_id}" if _current_session_id else None
        user_message = get_user_message(thread_id) if thread_id else None

        return greeting_tool.execute(
            thread_id=thread_id,
            user_message=user_message,
            initial_context={}
        )


class ReturnWorkflowTool(BaseTool):
    name: str = "return_workflow"
    description: str = """Use this workflow when the user wants to return an item or process a return.

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
    """

    def _run(self) -> str:
        """Execute the return workflow

        Returns:
            Workflow result (either interrupt prompt or completion message)
        """
        # Use global session context
        thread_id = f"workflow_{_current_session_id}" if _current_session_id else None
        user_message = get_user_message(thread_id) if thread_id else None

        return return_tool.execute(
            thread_id=thread_id,
            user_message=user_message,
            initial_context={}
        )


# List of all CrewAI tools (instantiated)
CREWAI_TOOLS = [
    GreetingWorkflowTool(),
    ReturnWorkflowTool()
]
