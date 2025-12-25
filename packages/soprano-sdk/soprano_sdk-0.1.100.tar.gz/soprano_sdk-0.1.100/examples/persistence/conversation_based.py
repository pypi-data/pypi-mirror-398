"""
Conversation-Based Persistence Example

Uses conversation IDs to support multiple concurrent workflows per user.
This pattern is ideal for chat-based systems with external supervisors.

Use case: Multi-workflow supervisor orchestrating different conversations
Thread ID strategy: Unique conversation_id per chat session
"""

from soprano_sdk import load_workflow
from langgraph.checkpoint.mongodb import MongoDBSaver
from pymongo import MongoClient
from langgraph.types import Command
import uuid


class WorkflowConversation:
    """Manages a workflow conversation with MongoDB persistence"""

    def __init__(self, workflow_path: str, conversation_id: str = None, mongodb_uri: str = "mongodb://localhost:27017"):
        """Initialize a workflow conversation

        Args:
            workflow_path: Path to workflow YAML file
            conversation_id: Optional conversation ID (generates new UUID if not provided)
            mongodb_uri: MongoDB connection URI
        """
        self.conversation_id = conversation_id or str(uuid.uuid4())
        self.mongodb_uri = mongodb_uri

        # Setup persistence
        client = MongoClient(mongodb_uri)
        self.checkpointer = MongoDBSaver(client=client, db_name="conversations")

        # Load workflow
        self.graph, self.engine = load_workflow(workflow_path, checkpointer=self.checkpointer)

        self.config = {"configurable": {"thread_id": self.conversation_id}}

    def start_or_resume(self, initial_context: dict = None):
        """Start a new workflow or resume existing one

        Args:
            initial_context: Optional context to pre-populate (for external orchestrator)
        """
        print(f"Conversation ID: {self.conversation_id}")
        print(f"Workflow: {self.engine.workflow_name}")
        print(f"MongoDB: {self.mongodb_uri}")
        print("=" * 60)

        # Start with optional context injection
        if initial_context:
            print(f"Injecting context: {initial_context}")
            result = self.graph.invoke(initial_context, config=self.config)
        else:
            result = self.graph.invoke({}, config=self.config)

        # Interaction loop
        while True:
            if "__interrupt__" in result and result["__interrupt__"]:
                # Show completion messages
                if "_messages" in result and result["_messages"]:
                    for msg in result["_messages"]:
                        print(f"Bot: {msg}")

                # Get user input
                prompt = result["__interrupt__"][0].value
                print(f"Bot: {prompt}")
                user_input = input("You: ")

                # Resume
                result = self.graph.invoke(Command(resume=user_input), config=self.config)
            else:
                # Completed
                outcome = self.engine.get_outcome_message(result)
                print(f"\nBot: {outcome}")
                break

        print("=" * 60)
        print(f"Conversation saved to MongoDB. To resume, use conversation_id: {self.conversation_id}")

    def inject_and_complete(self, context: dict):
        """Inject full context and complete workflow automatically (supervisor pattern)

        Args:
            context: Complete context to inject

        Returns:
            Final workflow state
        """
        return self.graph.invoke(context, config=self.config)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Run workflow conversation",
        epilog="""
Examples:
  # Start new conversation
  python conversation_based.py ../greeting_workflow.yaml

  # Resume existing conversation
  python conversation_based.py ../greeting_workflow.yaml --conversation-id abc-123

  # Start with pre-populated context (supervisor pattern)
  python conversation_based.py ../return_workflow.yaml --order-id ORDER-456

  # Use MongoDB Atlas
  python conversation_based.py ../greeting_workflow.yaml --mongodb mongodb+srv://user:pass@cluster.mongodb.net
        """
    )

    parser.add_argument("workflow", help="Path to workflow YAML file")
    parser.add_argument("--conversation-id", help="Conversation ID to resume")
    parser.add_argument("--mongodb", default="mongodb://localhost:27017", help="MongoDB connection URI")
    parser.add_argument("--order-id", help="Pre-populate order_id (for return workflow demo)")

    args = parser.parse_args()

    # Create conversation
    conv = WorkflowConversation(
        args.workflow,
        conversation_id=args.conversation_id,
        mongodb_uri=args.mongodb
    )

    # Start with optional context
    initial_context = {}
    if args.order_id:
        initial_context["order_id"] = args.order_id

    conv.start_or_resume(initial_context)
