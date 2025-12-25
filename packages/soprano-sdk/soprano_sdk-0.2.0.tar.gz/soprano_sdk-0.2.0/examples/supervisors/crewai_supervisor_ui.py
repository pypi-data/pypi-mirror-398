"""
CrewAI Supervisor with Gradio UI

A supervisor agent that decides which workflow to invoke based on user intent.
Uses CrewAI's agent and task delegation pattern.
"""

import sys
import os

# Add parent directory (examples) to Python path so workflows can import their functions
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from workflow_tools import WORKFLOW_TOOLS, set_user_message
from tools.crewai_tools import CREWAI_TOOLS, set_current_session
from crewai import Agent, Task, Crew
from langchain_openai import ChatOpenAI
import gradio as gr


# Create CrewAI supervisor agent
def create_supervisor():
    """Create CrewAI supervisor agent with workflow tools"""

    # Use manually defined CrewAI tools
    tools = CREWAI_TOOLS

    # Create LLM
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    # Create supervisor agent
    supervisor = Agent(
        role="Customer Service Supervisor",
        goal="Understand user requests and invoke the appropriate workflow to handle them",
        backstory="""You are an experienced customer service supervisor who routes requests
        to specialized workflow systems. You have access to multiple workflow tools that handle
        different types of customer requests like returns, greetings, and more. Your job is to
        understand what the user needs and invoke the right workflow tool.""",
        tools=tools,
        llm=llm,
        verbose=True,
        allow_delegation=False
    )

    return supervisor


# Initialize supervisor
supervisor = create_supervisor()


# Gradio chat function
def chat(message, history):
    """Handle chat messages with CrewAI supervisor

    Pass full conversation history to supervisor so it has context
    to decide which workflow to invoke. Tools are stateful and auto-resume.

    Args:
        message: User's message
        history: Chat history (managed by Gradio)

    Returns:
        Response from supervisor/workflow
    """
    # Generate session ID
    session_id = id(history)
    workflow_thread_id = f"workflow_{session_id}"

    # Set global context for CrewAI tools (they can't receive parameters)
    set_current_session(str(session_id))
    set_user_message(workflow_thread_id, message)

    print(f"[DEBUG] Session {session_id}, message: {message[:50]}...")

    try:
        # Build conversation context from history
        conversation_context = ""
        if history:
            conversation_context = "Previous conversation:\n"
            for turn in history[-5:]:  # Last 5 turns for context
                if turn.get('role') == 'user':
                    conversation_context += f"User: {turn['content']}\n"
                else:
                    conversation_context += f"Assistant: {turn['content']}\n"
            conversation_context += "\n"

        # Create task for the supervisor with full context
        task = Task(
            description=f"""
            {conversation_context}Current user message: {message}

            Analyze the conversation and invoke the appropriate workflow tool.

            IMPORTANT: If the conversation shows you previously asked a question and are waiting for a response,
            call the SAME workflow tool again - it will automatically resume and process the user's response.

            If the request is about returning an item, use the return_workflow tool.
            If the request is about greeting or personal information, use the greeting_workflow tool.

            Return the result from the workflow tool directly.
            """,
            agent=supervisor,
            expected_output="The result from executing the appropriate workflow"
        )

        # Create crew and execute
        crew = Crew(
            agents=[supervisor],
            tasks=[task],
            verbose=False
        )

        # Execute and get result
        result = crew.kickoff()
        result_str = str(result)

        print(f"[DEBUG] Result: {result_str[:200]}")

        # Parse interrupt markers
        if "__WORKFLOW_INTERRUPT__|" in result_str:
            parts = result_str.split("__WORKFLOW_INTERRUPT__|", 1)[1]
            prompt = parts.split("|", 2)[-1] if "|" in parts else result_str
            print(f"[DEBUG] Workflow interrupted, prompt: {prompt[:100]}")
            return prompt

        return result_str

    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Error: {str(e)}"


# Create Gradio interface
demo = gr.ChatInterface(
    fn=chat,
    type="messages",
    title="🚢 CrewAI Workflow Supervisor",
    description="""
    I'm a CrewAI supervisor agent that can help you with different tasks by invoking specialized workflows.

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
    theme=gr.themes.Ocean(),
)


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Starting CrewAI Supervisor with Gradio UI")
    print("=" * 60)
    print(f"Loaded {len(WORKFLOW_TOOLS)} workflow tools:")
    for tool in WORKFLOW_TOOLS:
        print(f"  - {tool.name}")
    print("=" * 60)
    print("\nLaunching Gradio interface...")

    demo.launch()
