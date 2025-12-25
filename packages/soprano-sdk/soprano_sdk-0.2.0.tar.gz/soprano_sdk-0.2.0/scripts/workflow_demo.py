"""
Workflow Demo - CLI interface for YAML-configured workflows
"""

from soprano_sdk import load_workflow
from langgraph.types import Command
import uuid
import sys
import argparse


def run_workflow(yaml_path: str, thread_id: str = None, mongodb_uri: str = None):
    """Run a workflow from YAML configuration

    Args:
        yaml_path: Path to workflow YAML file
        thread_id: Optional thread ID for resuming workflows (generates new UUID if not provided)
        mongodb_uri: Optional MongoDB URI for persistence (e.g., "mongodb://localhost:27017")
    """
    print("\n" + "="*60)
    print("YAML Workflow Demo")
    print("="*60)

    # Setup checkpointer if MongoDB URI provided
    checkpointer = None
    if mongodb_uri:
        try:
            from langgraph.checkpoint.mongodb import MongoDBSaver
            from pymongo import MongoClient

            client = MongoClient(mongodb_uri)
            checkpointer = MongoDBSaver(client=client, db_name="workflows")
            print(f"Using MongoDB persistence: {mongodb_uri}")
        except ImportError:
            print("Warning: langgraph-checkpoint-mongodb not installed. Using in-memory persistence.")
            print("Install with: uv add langgraph-checkpoint-mongodb --optional persistence")

    # Load workflow
    print(f"Loading workflow from: {yaml_path}")
    graph, engine = load_workflow(yaml_path, checkpointer=checkpointer)

    print(f"Workflow: {engine.workflow_name}")
    print(f"Description: {engine.workflow_description}")

    # Setup execution
    if thread_id is None:
        thread_id = str(uuid.uuid4())
        print(f"Generated thread ID: {thread_id}")
    else:
        print(f"Using thread ID: {thread_id}")

    print("="*60 + "\n")

    config = {"configurable": {"thread_id": thread_id}}

    # Start workflow
    result = graph.invoke({}, config=config)

    # Main interaction loop
    while True:
        # Check for interrupt
        if "__interrupt__" in result and result["__interrupt__"]:
            prompt = result["__interrupt__"][0].value
            print(f"Bot: {prompt}")
            user_input = input("You: ")

            # Resume with user input
            result = graph.invoke(Command(resume=user_input), config=config)
        else:
            # No more interrupts - workflow complete
            break

    # Display outcome
    print("\n" + "="*60)
    outcome_message = engine.get_outcome_message(result)
    print(f"Bot: {outcome_message}")
    print("="*60 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run a workflow from YAML configuration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with in-memory persistence (new UUID)
  python workflow_demo.py examples/greeting_workflow.yaml

  # Run with MongoDB persistence (new UUID)
  python workflow_demo.py examples/greeting_workflow.yaml --mongodb mongodb://localhost:27017

  # Resume existing workflow
  python workflow_demo.py examples/greeting_workflow.yaml --mongodb mongodb://localhost:27017 --thread-id abc-123

  # Use MongoDB Atlas
  python workflow_demo.py examples/return_workflow.yaml --mongodb mongodb+srv://user:pass@cluster.mongodb.net

  # Use custom thread ID
  python workflow_demo.py examples/return_workflow.yaml --thread-id order_12345
        """
    )

    parser.add_argument("workflow", help="Path to workflow YAML file")
    parser.add_argument(
        "--thread-id",
        help="Thread ID for workflow execution (generates new UUID if not provided)"
    )
    parser.add_argument(
        "--mongodb",
        metavar="URI",
        help="MongoDB connection URI for persistence (uses in-memory if not provided)"
    )

    args = parser.parse_args()

    try:
        run_workflow(args.workflow, thread_id=args.thread_id, mongodb_uri=args.mongodb)
    except FileNotFoundError:
        print(f"Error: Workflow file '{args.workflow}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
