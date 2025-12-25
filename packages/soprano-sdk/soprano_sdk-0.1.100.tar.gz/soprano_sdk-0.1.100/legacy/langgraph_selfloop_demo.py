"""
Demonstrates the self-loop pattern in LangGraph for multi-turn conversations.
This shows how a node can loop back to itself using conditional routing instead of while loops.
"""

from typing import TypedDict, Optional
from langgraph.graph import StateGraph
from langgraph.types import interrupt
from langgraph.constants import START, END
from langgraph.checkpoint.memory import InMemorySaver


class State(TypedDict):
    name: Optional[str]
    age: Optional[int]
    greeting_message: Optional[str]
    status: str  # Track collection status


def collect_name(state: State) -> State:
    """Collect user's name - single interrupt per execution, self-loops if needed"""

    # Check if name is already collected
    if state.get("name"):
        return state

    # Check attempt count
    attempt_count = state.get("attempt_count", 0)
    if attempt_count >= 3:
        state["status"] = "failed"
        return state

    # Determine prompt
    if attempt_count == 0:
        prompt = "Hello! What is your name?"
    else:
        prompt = f"I didn't get that. Please tell me your name (attempt {attempt_count + 1}/3):"

    # Single interrupt - self-loop handles multiple turns
    user_input = interrupt(prompt)

    # Increment attempt count
    state["attempt_count"] = attempt_count + 1

    # Validate input
    if user_input and len(user_input.strip()) > 0:
        state["name"] = user_input.strip()
        state["status"] = "name_collected"
    else:
        # Invalid input - will self-loop
        state["status"] = "collecting_name"

    return state


def collect_age(state: State) -> State:
    """Collect user's age - single interrupt per execution, self-loops if needed"""

    # Check if age is already collected
    if state.get("age"):
        return state

    # Check attempt count
    age_attempts = state.get("age_attempts", 0)
    if age_attempts >= 3:
        state["status"] = "failed"
        return state

    # Determine prompt
    if age_attempts == 0:
        prompt = "How old are you?"
    else:
        prompt = f"Please enter a valid age as a number (attempt {age_attempts + 1}/3):"

    # Single interrupt - self-loop handles multiple turns
    user_input = interrupt(prompt)

    # Increment attempt count
    state["age_attempts"] = age_attempts + 1

    # Validate input
    try:
        age = int(user_input)
        if age > 0 and age < 150:
            state["age"] = age
            state["status"] = "age_collected"
        else:
            # Invalid range - will self-loop
            state["status"] = "collecting_age"
    except ValueError:
        # Invalid input - will self-loop
        state["status"] = "collecting_age"

    return state


def greet_user(state: State) -> State:
    """Generate final greeting"""
    name = state.get("name", "Guest")
    age = state.get("age", "unknown")
    greeting = f"Nice to meet you, {name}! You are {age} years old. Welcome!"
    state["greeting_message"] = greeting
    state["status"] = "completed"
    return state


def route_after_name(state: State) -> str:
    """Route after name collection - implements self-loop"""
    status = state.get("status", "")
    if status == "name_collected":
        return "collect_age"
    elif status == "collecting_name":
        return "collect_name"  # SELF-LOOP!
    else:
        return END


def route_after_age(state: State) -> str:
    """Route after age collection - implements self-loop"""
    status = state.get("status", "")
    if status == "age_collected":
        return "greet"
    elif status == "collecting_age":
        return "collect_age"  # SELF-LOOP!
    else:
        return END


def get_demo_graph():
    """Build the demo graph with self-loops"""
    builder = StateGraph(State)

    # Add nodes
    builder.add_node("collect_name", collect_name)
    builder.add_node("collect_age", collect_age)
    builder.add_node("greet", greet_user)

    # Entry point
    builder.add_edge(START, "collect_name")

    # Conditional edges with self-loops
    builder.add_conditional_edges(
        "collect_name",
        route_after_name,
        {
            "collect_age": "collect_age",
            "collect_name": "collect_name",  # Self-loop for multi-turn
            END: END
        }
    )

    builder.add_conditional_edges(
        "collect_age",
        route_after_age,
        {
            "greet": "greet",
            "collect_age": "collect_age",  # Self-loop for multi-turn
            END: END
        }
    )

    builder.add_edge("greet", END)

    # Compile with checkpointer
    checkpointer = InMemorySaver()
    graph = builder.compile(checkpointer=checkpointer)
    return graph
