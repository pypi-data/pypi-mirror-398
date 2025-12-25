"""
Workflow Demo UI - Gradio interface for YAML-configured workflows
"""

from soprano_sdk import load_workflow
from langgraph.types import Command
import uuid
import gradio as gr
import argparse

# Parse command line arguments
parser = argparse.ArgumentParser(description="Run workflow with Gradio UI")
parser.add_argument("workflow", nargs="?", default="greeting_workflow.yaml", help="Path to workflow YAML file")
parser.add_argument("--mongodb", metavar="URI", help="MongoDB connection URI for persistence (e.g., mongodb://localhost:27017)")
args = parser.parse_args()

# Setup checkpointer if MongoDB URI provided
checkpointer = None
if args.mongodb:
    try:
        from langgraph.checkpoint.mongodb import MongoDBSaver
        from pymongo import MongoClient

        client = MongoClient(args.mongodb)
        checkpointer = MongoDBSaver(client=client, db_name="workflows")
        print(f"Using MongoDB persistence: {args.mongodb}")
    except ImportError:
        print("Warning: langgraph-checkpoint-mongodb not installed. Using in-memory persistence.")
        print("Install with: uv add langgraph-checkpoint-mongodb --optional persistence")

# Load workflow
graph, engine = load_workflow(args.workflow, checkpointer=checkpointer)

# Store thread_id per session (Gradio manages this via state)
session_threads = {}


def run(message, history, thread_id_input):
    """Handle user messages and return responses from the workflow

    Args:
        message: User's input message
        history: Chat history (managed by Gradio)
        thread_id_input: Optional thread ID from user input
    """
    # Determine thread_id: use input if provided, otherwise generate per-session
    # Use history length as a simple session identifier
    session_key = str(id(history))  # Unique per Gradio session

    if thread_id_input and thread_id_input.strip():
        # User provided explicit thread ID (for resuming)
        thread_id = thread_id_input.strip()
    elif session_key in session_threads:
        # Reuse existing thread for this session
        thread_id = session_threads[session_key]
    else:
        # Generate new thread for this session
        thread_id = str(uuid.uuid4())
        session_threads[session_key] = thread_id

    config = {"configurable": {"thread_id": thread_id}}

    # Resume with user message or start fresh
    if message and message.strip():
        result = graph.invoke(Command(resume=message), config=config)
    else:
        result = graph.invoke({}, config=config)

    # Check if graph is waiting for user input (interrupt)
    if "__interrupt__" in result and result["__interrupt__"]:
        interrupt_info = result["__interrupt__"][0]
        prompt = interrupt_info.value

        # Show any completion messages from previous step
        response_parts = []
        if "_messages" in result and result["_messages"]:
            response_parts.extend(result["_messages"])

        # Add the interrupt prompt
        response_parts.append(prompt)
        return "\n\n".join(response_parts)

    # Workflow completed - get outcome message
    outcome_message = engine.get_outcome_message(result)
    return outcome_message


# Create Gradio interface with thread ID input
with gr.Blocks() as demo:
    gr.Markdown(f"# {engine.workflow_name}")
    gr.Markdown(f"{engine.workflow_description}")

    with gr.Row():
        thread_id_box = gr.Textbox(
            label="Thread ID (optional)",
            placeholder="Leave empty for auto-generated ID, or enter ID to resume existing workflow",
            scale=4
        )

    chatbot = gr.ChatInterface(
        fn=run,
        type="messages",
        additional_inputs=[thread_id_box]
    )

    if args.mongodb:
        gr.Markdown(f"💾 **Persistence enabled**: MongoDB ({args.mongodb})")
        gr.Markdown("Workflows are saved to MongoDB. You can close and reopen the browser to resume using the same Thread ID.")
    else:
        gr.Markdown("⚠️ **In-memory mode**: Workflows will be lost if you refresh the page.")

demo.launch()
