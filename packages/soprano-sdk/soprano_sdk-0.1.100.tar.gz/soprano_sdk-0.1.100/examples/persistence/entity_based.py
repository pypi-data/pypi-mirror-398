"""
Entity-Based Persistence Example

Uses business entity IDs (e.g., order_id, ticket_id) as the thread_id.
This pattern allows workflows to be naturally resumed using the business identifier.

Use case: Processing returns for specific orders
Thread ID strategy: f"return_{order_id}"
"""

from soprano_sdk import load_workflow
from langgraph.checkpoint.mongodb import MongoDBSaver
from pymongo import MongoClient
from langgraph.types import Command
import sys


def process_return(order_id: str, mongodb_uri: str = "mongodb://localhost:27017"):
    """Process a return for a specific order

    Args:
        order_id: The order identifier (e.g., "ORDER-123")
        mongodb_uri: MongoDB connection URI
    """
    # Use order_id as the thread identifier
    thread_id = f"return_{order_id}"

    # Setup persistence
    client = MongoClient(mongodb_uri)
    checkpointer = MongoDBSaver(client=client, db_name="workflows")

    # Load workflow
    graph, engine = load_workflow("../return_workflow.yaml", checkpointer=checkpointer)

    config = {"configurable": {"thread_id": thread_id}}

    print(f"Processing return for order: {order_id}")
    print(f"Thread ID: {thread_id}")
    print(f"MongoDB: {mongodb_uri}")
    print("=" * 60)

    # Start or resume workflow
    result = graph.invoke({}, config=config)

    # Interaction loop
    while True:
        if "__interrupt__" in result and result["__interrupt__"]:
            # Show any completion messages
            if "_messages" in result and result["_messages"]:
                for msg in result["_messages"]:
                    print(f"Bot: {msg}")

            # Get user input
            prompt = result["__interrupt__"][0].value
            print(f"Bot: {prompt}")
            user_input = input("You: ")

            # Resume workflow
            result = graph.invoke(Command(resume=user_input), config=config)
        else:
            # Workflow completed
            outcome = engine.get_outcome_message(result)
            print(f"\nBot: {outcome}")
            break

    print("=" * 60)
    print(f"Workflow state saved to MongoDB with thread_id: {thread_id}")
    print(f"To resume this workflow, run: python entity_based.py {order_id}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python entity_based.py <order_id> [mongodb_uri]")
        print("\nExample:")
        print("  python entity_based.py ORDER-123")
        print("  python entity_based.py ORDER-123 mongodb://localhost:27017")
        print("  python entity_based.py ORDER-123 mongodb+srv://user:pass@cluster.mongodb.net")
        sys.exit(1)

    order_id = sys.argv[1]
    mongodb_uri = sys.argv[2] if len(sys.argv) > 2 else "mongodb://localhost:27017"

    process_return(order_id, mongodb_uri)
