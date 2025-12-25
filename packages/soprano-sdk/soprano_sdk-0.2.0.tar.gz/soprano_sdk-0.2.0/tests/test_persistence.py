"""
Test persistence with MongoDB checkpointer
"""

from soprano_sdk import load_workflow
from langgraph.types import Command
import uuid
import os
import sys

# Add examples directory to path
examples_dir = os.path.join(os.path.dirname(__file__), "..", "examples")
sys.path.insert(0, os.path.abspath(examples_dir))


def test_persistence_with_mongodb():
    """Test that workflow state persists across invocations"""
    try:
        from langgraph.checkpoint.mongodb import MongoDBSaver
        from pymongo import MongoClient
    except ImportError:
        print("Skipping test: langgraph-checkpoint-mongodb not installed")
        print("Install with: uv add langgraph-checkpoint-mongodb pymongo --optional persistence")
        return

    # Connect to MongoDB (assumes local MongoDB running)
    try:
        client = MongoClient("mongodb://localhost:27017", serverSelectionTimeoutMS=5000)
        client.server_info()  # Test connection
    except Exception as e:
        print(f"Skipping test: MongoDB not available ({e})")
        print("Start MongoDB with: docker run -d -p 27017:27017 mongo:latest")
        return

    # Use test database
    db_name = f"test_workflows_{uuid.uuid4().hex[:8]}"
    checkpointer = MongoDBSaver(client=client, db_name=db_name)

    try:
        # Load workflow with persistence
        yaml_path = os.path.join(examples_dir, "greeting_workflow.yaml")
        graph, engine = load_workflow(yaml_path, checkpointer=checkpointer)

        # Generate thread ID
        thread_id = f"test_{uuid.uuid4()}"
        config = {"configurable": {"thread_id": thread_id}}

        print("=" * 60)
        print("Test: Persistence with MongoDB")
        print("=" * 60)
        print(f"Database: {db_name}")
        print(f"Thread ID: {thread_id}")
        print()

        # Step 1: Start workflow
        print("Step 1: Starting workflow...")
        result1 = graph.invoke({}, config=config)

        assert "__interrupt__" in result1, "Expected workflow to interrupt for name collection"
        prompt1 = result1["__interrupt__"][0].value
        print(f"  Bot: {prompt1[:50]}...")

        # Step 2: Provide name
        print("\nStep 2: Providing name...")
        result2 = graph.invoke(Command(resume="Alice"), config=config)

        assert "__interrupt__" in result2, "Expected workflow to interrupt for age collection"
        prompt2 = result2["__interrupt__"][0].value
        print(f"  Bot: {prompt2[:50]}...")

        # Step 3: Resume in NEW invocation (simulating process restart)
        print("\nStep 3: Resuming workflow (simulating new process)...")

        # Create NEW graph and engine instances
        graph2, engine2 = load_workflow(yaml_path, checkpointer=checkpointer)

        # Resume with same thread_id - should continue from where we left off
        result3 = graph2.invoke(Command(resume="30"), config=config)

        # Should complete successfully
        assert "__interrupt__" not in result3, "Expected workflow to complete"
        outcome = engine2.get_outcome_message(result3)
        print(f"  Bot: {outcome}")

        # Verify final state
        assert result3.get("name") == "Alice", "Name should be persisted"
        assert result3.get("age") == 30, "Age should be persisted"

        print()
        print("=" * 60)
        print("✅ Test passed: Workflow state persisted and resumed successfully!")
        print("=" * 60)

    finally:
        # Cleanup - drop test database
        client.drop_database(db_name)


def test_multiple_threads():
    """Test that different thread IDs maintain separate state"""
    try:
        from langgraph.checkpoint.mongodb import MongoDBSaver
        from pymongo import MongoClient
    except ImportError:
        print("Skipping test: langgraph-checkpoint-mongodb not installed")
        return

    # Connect to MongoDB
    try:
        client = MongoClient("mongodb://localhost:27017", serverSelectionTimeoutMS=5000)
        client.server_info()
    except Exception:
        print("Skipping test: MongoDB not available")
        return

    # Use test database
    db_name = f"test_workflows_{uuid.uuid4().hex[:8]}"
    checkpointer = MongoDBSaver(client=client, db_name=db_name)

    try:
        yaml_path = os.path.join(examples_dir, "greeting_workflow.yaml")
        graph, engine = load_workflow(yaml_path, checkpointer=checkpointer)

        print("\n" + "=" * 60)
        print("Test: Multiple Thread IDs")
        print("=" * 60)

        # Start two different workflows
        thread1 = f"test_thread_1_{uuid.uuid4()}"
        thread2 = f"test_thread_2_{uuid.uuid4()}"

        config1 = {"configurable": {"thread_id": thread1}}
        config2 = {"configurable": {"thread_id": thread2}}

        # Thread 1: Provide name "Alice"
        print(f"\nThread 1 ({thread1[:20]}...): Providing name 'Alice'")
        result1 = graph.invoke({}, config=config1)
        result1 = graph.invoke(Command(resume="Alice"), config=config1)

        # Thread 2: Provide name "Bob"
        print(f"Thread 2 ({thread2[:20]}...): Providing name 'Bob'")
        result2 = graph.invoke({}, config=config2)
        result2 = graph.invoke(Command(resume="Bob"), config=config2)

        # Verify they maintain separate state
        assert result1.get("name") == "Alice", "Thread 1 should have name Alice"
        assert result2.get("name") == "Bob", "Thread 2 should have name Bob"

        print("\n✅ Both threads maintain separate state!")
        print("=" * 60)

    finally:
        # Cleanup
        client.drop_database(db_name)


if __name__ == "__main__":
    test_persistence_with_mongodb()
    test_multiple_threads()
    print("\n🎉 All persistence tests passed!")
