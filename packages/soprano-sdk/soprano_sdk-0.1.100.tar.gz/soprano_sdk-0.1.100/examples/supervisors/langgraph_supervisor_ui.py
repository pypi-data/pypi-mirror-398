"""
LangGraph Supervisor with Gradio UI

A supervisor agent that decides which workflow to invoke based on user intent.
Uses LangGraph's tool calling with OpenAI models.
"""

import sys
import os

# Add parent directory (examples) to Python path so workflows can import their functions
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from workflow_tools import WORKFLOW_TOOLS
from tools.langgraph_tools import LANGCHAIN_TOOLS
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import InMemorySaver
import gradio as gr


# Create LangGraph agent with workflow tools
def create_supervisor():
    """Create LangGraph supervisor agent with static workflow tools"""

    # Use static tools from tools/langgraph_tools.py
    tools = LANGCHAIN_TOOLS

    # Create LLM
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    # System prompt for supervisor
    system_prompt = """You are a helpful customer service supervisor assistant.

Your role is to understand what the user wants and invoke the appropriate workflow tool.

Available workflows:
- greeting_workflow: For when users want to introduce themselves or provide personal information
- return_workflow: For when users want to return an item or process a return

When you decide which workflow to use, call the appropriate tool ONCE with an empty context parameter.
Do NOT call the tool multiple times.
Do NOT retry if the tool returns successfully.
The tool will handle collecting information from the user interactively.

If the user's intent is unclear, ask clarifying questions before invoking a workflow.
"""

    # Create agent with tools
    checkpointer = InMemorySaver()

    # Bind system message to LLM
    llm_with_system = llm.bind(
        system=system_prompt
    )

    agent = create_react_agent(
        llm_with_system,
        tools,
        checkpointer=checkpointer
    )

    return agent


# Initialize single supervisor instance
supervisor = create_supervisor()


# Gradio chat function
def chat(message, history):
    """Handle chat messages with LangGraph supervisor

    Tools are now stateful and automatically handle resume vs invoke.
    The supervisor just keeps calling tools with user messages.

    Args:
        message: User's message
        history: Chat history (managed by Gradio)

    Returns:
        Response from supervisor/workflow
    """
    # Generate session ID based on history object
    session_id = id(history)
    supervisor_thread_id = f"supervisor_{session_id}"

    # Config with both supervisor thread_id and session_id for tools
    config = {
        "configurable": {
            "thread_id": supervisor_thread_id,  # For agent's own state
            "session_id": str(session_id)  # For workflow tools to use
        }
    }

    # Invoke supervisor - tools will auto-detect their state
    response_text = ""

    try:
        # Stream responses from agent
        for event in supervisor.stream(
            {"messages": [{"role": "user", "content": message}]},
            config=config,
            stream_mode="updates"
        ):
            print(f"[DEBUG] Event: {event.keys()}")

            # Check tool outputs for workflow interrupts
            if "tools" in event and "messages" in event["tools"]:
                for tool_msg in event["tools"]["messages"]:
                    if hasattr(tool_msg, "content"):
                        content = tool_msg.content
                        print(f"[DEBUG] Tool output: {content[:200]}")

                        # Check if it's a workflow interrupt
                        if content.startswith("__WORKFLOW_INTERRUPT__|"):
                            parts = content.split("|", 3)
                            _, thread_id, wf_name, prompt = parts
                            print(f"[DEBUG] Workflow '{wf_name}' interrupted (thread: {thread_id})")
                            response_text = prompt
                            break

                if response_text:
                    break

            # Get agent responses if no interrupt
            if not response_text and "agent" in event and "messages" in event["agent"]:
                last_msg = event["agent"]["messages"][-1]
                if hasattr(last_msg, "content"):
                    content = last_msg.content
                    print(f"[DEBUG] Agent response: {content[:200]}")
                    response_text = content

        return response_text or "I'm processing your request..."

    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Error: {str(e)}"


# Create Gradio interface
demo = gr.ChatInterface(
    fn=chat,
    type="messages",
    title="🤖 LangGraph Workflow Supervisor",
    description="""
    I'm a supervisor agent that can help you with different tasks by invoking specialized workflows.

    **Try asking:**
    - "I want to return an item" → Invokes return workflow
    - "What's my name?" → Invokes greeting workflow
    - "Help me process a return for order #123"

    I'll automatically select and run the right workflow based on your request!
    """,
    examples=[
        "I want to return an item",
        "What's my name?",
        "Process a return for order #456",
        "Can you greet me?",
    ],
    theme=gr.themes.Soft(),
)


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Starting LangGraph Supervisor with Gradio UI")
    print("=" * 60)
    print(f"Available workflows: {len(WORKFLOW_TOOLS)}")
    for tool in WORKFLOW_TOOLS:
        print(f"  - {tool.name}")
    print("=" * 60)
    print("Note: Static tools with session_id passed via config")
    print("=" * 60)
    print("\nLaunching Gradio interface...")

    demo.launch()
