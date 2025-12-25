"""
MongoDB Persistence Demo

Demonstrates basic MongoDB persistence with resume capability.
Shows how to save and restore workflow state across process restarts.
"""

from soprano_sdk import load_workflow
from langgraph.checkpoint.mongodb import MongoDBSaver
from pymongo import MongoClient
from langgraph.types import Command
import uuid


def run_with_persistence(workflow_path: str, thread_id: str = None, mongodb_uri: str = "mongodb://localhost:27017"):
    """Run workflow with MongoDB persistence

    Args:
        workflow_path: Path to workflow YAML file
        thread_id: Thread ID (generates new if not provided)
        mongodb_uri: MongoDB connection URI
    """
    print("=" * 60)
    print("MongoDB Persistence Demo")
    print("=" * 60)

    # Setup MongoDB persistence
    client = MongoClient(mongodb_uri)
    checkpointer = MongoDBSaver(client=client, db_name="demo_workflows")

    # Load workflow with checkpointer
    graph, engine = load_workflow(workflow_path, checkpointer=checkpointer)

    # Generate or use provided thread_id
    if thread_id is None:
        thread_id = str(uuid.uuid4())
        print(f"Generated new thread ID: {thread_id}")
        print("Save this ID to resume later!")
    else:
        print(f"Resuming workflow with thread ID: {thread_id}")

    print(f"MongoDB: {mongodb_uri}")
    print("Database: demo_workflows")
    print(f"Workflow: {engine.workflow_name}")
    print("=" * 60 + "\n")

    config = {"configurable": {"thread_id": thread_id}}

    # Start or resume workflow
    result = graph.invoke({}, config=config)

    # Interaction loop
    while True:
        if "__interrupt__" in result and result["__interrupt__"]:
            # Show completion messages
            if "_messages" in result and result["_messages"]:
                for msg in result["_messages"]:
                    print(f"Bot: {msg}")

            # Get prompt
            prompt = result["__interrupt__"][0].value
            print(f"Bot: {prompt}")

            # Check if user wants to pause
            print("\n(Type 'PAUSE' to save and exit, or provide your response)")
            user_input = input("You: ")

            if user_input.strip().upper() == "PAUSE":
                print("\n" + "=" * 60)
                print("Workflow paused and saved to MongoDB!")
                print(f"Thread ID: {thread_id}")
                print(f"MongoDB: {mongodb_uri}")
                print("\nTo resume, run:")
                print(f"  python mongodb_demo.py --thread-id {thread_id}")
                if mongodb_uri != "mongodb://localhost:27017":
                    print(f"  --mongodb {mongodb_uri}")
                print("=" * 60)
                return

            # Resume
            result = graph.invoke(Command(resume=user_input), config=config)
        else:
            # Completed
            outcome = engine.get_outcome_message(result)
            print(f"\nBot: {outcome}")
            print("\n" + "=" * 60)
            print("Workflow completed successfully!")
            print("=" * 60)
            break


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="MongoDB Persistence Demo",
        epilog="""
Examples:
  # Start new workflow (local MongoDB)
  python mongodb_demo.py

  # Resume existing workflow
  python mongodb_demo.py --thread-id abc-123-def-456

  # Use different workflow
  python mongodb_demo.py --workflow ../return_workflow.yaml

  # Use MongoDB Atlas
  python mongodb_demo.py --mongodb mongodb+srv://user:pass@cluster.mongodb.net
        """
    )

    parser.add_argument(
        "--workflow",
        default="../greeting_workflow.yaml",
        help="Path to workflow YAML file"
    )
    parser.add_argument(
        "--thread-id",
        help="Thread ID to resume existing workflow"
    )
    parser.add_argument(
        "--mongodb",
        default="mongodb://localhost:27017",
        help="MongoDB connection URI"
    )

    args = parser.parse_args()

    try:
        run_with_persistence(args.workflow, args.thread_id, args.mongodb)
    except KeyboardInterrupt:
        print("\n\nWorkflow interrupted by user.")
        print("State has been saved. Use the same thread ID to resume.")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
