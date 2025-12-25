from typing import TypedDict, Optional
from langgraph.graph import StateGraph
from langgraph.types import interrupt
from langgraph.constants import START, END
from langgraph.checkpoint.memory import InMemorySaver


class State(TypedDict):
    name: Optional[str]
    greeting_message: Optional[str]


def collect_name(state: State) -> State:
    """Collect user's name using interrupt"""

    # Only collect if we don't already have a name
    if "name" not in state or state["name"] is None:
        # Ask for user's name
        print("hi")
        user_input = interrupt("Hello! What is your name?")
        print("hi 2")

        # Store the name in state
        state["name"] = user_input.strip()

    return state


def greet_user(state: State) -> State:
    """Greet the user by their name"""

    name = state.get("name", "Guest")
    greeting = f"Nice to meet you, {name}! Welcome to the LangGraph demo."

    state["greeting_message"] = greeting

    return state


def get_demo_graph():
    """Build and return the simple demo graph"""
    builder = StateGraph(State)

    # Add nodes
    builder.add_node("collect_name", collect_name)
    builder.add_node("greet_user", greet_user)

    # Set entry point and edges
    builder.add_edge(START, "collect_name")
    builder.add_edge("collect_name", "greet_user")
    builder.add_edge("greet_user", END)

    # Compile with checkpointer for state persistence
    checkpointer = InMemorySaver()
    graph = builder.compile(checkpointer=checkpointer)

    return graph


if __name__ == "__main__":
    """Test the graph with a simple command-line interface"""
    from langgraph.types import Command
    import uuid

    graph = get_demo_graph()
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    print("Starting LangGraph Demo...")
    print("-" * 50)

    # Initial invoke
    result = graph.invoke({}, config=config)

    # Handle interrupt
    if "__interrupt__" in result and result["__interrupt__"]:
        interrupt_info = result["__interrupt__"][0]
        prompt = interrupt_info.value
        print(f"Bot: {prompt}")

        # Get user input
        user_name = input("You: ")

        # Resume with user input
        result = graph.invoke(Command(resume=user_name), config=config)

    # Display final greeting
    if "greeting_message" in result:
        print(f"Bot: {result['greeting_message']}")

    print("-" * 50)
    print("Demo completed!")
