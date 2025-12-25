from typing import TypedDict, Optional
from langgraph.graph import StateGraph
from langgraph.types import interrupt
from langgraph.constants import START, END
from langgraph.checkpoint.memory import InMemorySaver
import random
from agno.agent import Agent
from agno.models.openai import OpenAIChat


class State(TypedDict):
    order_id: Optional[str]
    return_reason: Optional[str]
    is_eligible: Optional[bool]
    is_reason_valid: Optional[bool]
    messages: list[str]  # Store messages to show to user
    status: str  # Track workflow status
    conversation_history: list[dict]  # Order ID conversation context
    reason_conversation: list[dict]  # Return reason conversation context


def collect_order_id(state: State) -> State:
    """Collect order ID from user using AI agent with interrupt for user input"""

    # Initialize state fields
    if "messages" not in state:
        state["messages"] = []
    if "conversation_history" not in state:
        state["conversation_history"] = []

    # Only collect if we don't already have an order ID
    if "order_id" not in state or state["order_id"] is None:
        # Check attempt limit
        attempt_count = len([m for m in state["conversation_history"] if m["role"] == "user"])
        if attempt_count >= 5:
            state["status"] = "failed"
            state["messages"] = ["I'm having trouble understanding your order ID. Please contact customer service for assistance."]
            return state

        # Create agent
        agent = Agent(
            name="OrderIdCollector",
            model=OpenAIChat(id="gpt-4o-mini"),
            instructions=(
                "Goal: capture a single order id from the user. "
                "Be concise and direct. If the user provides what looks like an order ID, accept it immediately. "
                "If they confirm 'yes' or 'correct' or 'yes correct' to your clarification, accept the order ID you asked about. "
                "Once you have a clear order ID (including confirmations), respond with ONLY: 'ORDER_ID_CAPTURED: [order_id]' "
                "Examples: "
                "- User says '1234' -> respond: 'ORDER_ID_CAPTURED: 1234' "
                "- User says 'yes correct' after you asked 'Is your order ID #1234?' -> respond: 'ORDER_ID_CAPTURED: 1234' "
                "- User says 'my order is #1234' -> respond: 'ORDER_ID_CAPTURED: #1234' "
            ),
        )

        # Determine prompt
        if len(state["conversation_history"]) == 0:
            prompt = "Hello! I need to help you with a return. Could you please provide your order ID?"
        else:
            # Use last assistant message as prompt
            prompt = state["conversation_history"][-1]["content"]

        # Single interrupt per execution - self-loop handles iteration
        user_input = interrupt(prompt)

        # Add to conversation
        state["conversation_history"].append({"role": "user", "content": user_input})

        # Get agent response
        response = agent.run(state["conversation_history"])
        agent_response = response.content
        state["conversation_history"].append({"role": "assistant", "content": agent_response})

        # Check if order ID was captured
        if "ORDER_ID_CAPTURED:" in agent_response:
            order_id = agent_response.split("ORDER_ID_CAPTURED:")[1].strip()
            state["order_id"] = order_id
            state["messages"] = [f"✓ Order ID collected: {order_id}"]
            state["status"] = "order_id_collected"
        elif "ORDER_ID_FAILED:" in agent_response:
            state["status"] = "failed"
            state["messages"] = ["I'm sorry, I wasn't able to collect your order ID. Please contact customer service."]
        else:
            # Continue collecting - will self-loop
            state["status"] = "collecting_order_id"
            state["messages"] = [agent_response]

    return state

def check_return_eligibility(state: State) -> State:
    """Check if the order is eligible for return"""
    state["messages"] = [
        "Checking if this order is eligible for return...",
        "Validating order details and return policy..."
    ]

    # Simulate eligibility check (random for now, similar to main.py)
    num = random.randint(1, 100)
    is_eligible = num % 2 == 0

    state["is_eligible"] = is_eligible

    if is_eligible:
        state["messages"].append("✓ Your order is eligible for return!")
        state["status"] = "eligible"
    else:
        state["messages"].append("❌ I'm sorry, your order is not eligible for return based on our return policy.")
        state["status"] = "ineligible"

    return state


def collect_return_reason(state: State) -> State:
    """Collect return reason from user using AI agent"""

    # Initialize conversation history for reason collection
    if "reason_conversation" not in state:
        state["reason_conversation"] = []

    # Only collect if we don't already have a return reason
    if "return_reason" not in state or state["return_reason"] is None:
        # Check attempt limit
        attempt_count = len([m for m in state["reason_conversation"] if m["role"] == "user"])
        if attempt_count >= 5:
            state["status"] = "failed"
            state["messages"] = ["I'm having trouble understanding your return reason. Please contact customer service for assistance."]
            return state

        # Create agent
        agent = Agent(
            name="ReasonCollector",
            model=OpenAIChat(id="gpt-4o-mini"),
            instructions=(
                "Goal: capture the reason why the user wants to return their order. "
                "Be concise and direct. Accept clear reasons immediately. "
                "Once you have a clear return reason, respond with ONLY: 'REASON_CAPTURED: [reason]' "
                "Valid return reasons include: damaged item, wrong size, wrong color, defective, not as described, changed mind, etc. "
                "Examples: "
                "- User says 'it was damaged' -> respond: 'REASON_CAPTURED: damaged item' "
                "- User says 'wrong size' -> respond: 'REASON_CAPTURED: wrong size' "
            ),
        )

        # Determine prompt
        if len(state["reason_conversation"]) == 0:
            prompt = "Please provide the reason for your return."
        else:
            # Use last assistant message as prompt
            prompt = state["reason_conversation"][-1]["content"]

        # Single interrupt per execution - self-loop handles iteration
        user_input = interrupt(prompt)

        # Add to conversation
        state["reason_conversation"].append({"role": "user", "content": user_input})

        # Get agent response
        response = agent.run(state["reason_conversation"])
        agent_response = response.content
        state["reason_conversation"].append({"role": "assistant", "content": agent_response})

        # Check if reason was captured
        if "REASON_CAPTURED:" in agent_response:
            return_reason = agent_response.split("REASON_CAPTURED:")[1].strip()
            state["return_reason"] = return_reason
            state["messages"] = [f"✓ Return reason captured: {return_reason}"]
            state["status"] = "reason_collected"
        elif "REASON_FAILED:" in agent_response:
            state["status"] = "failed"
            state["messages"] = ["I'm sorry, I wasn't able to collect a valid return reason. Please contact customer service."]
        else:
            # Continue collecting - will self-loop
            state["status"] = "collecting_reason"
            state["messages"] = [agent_response]

    return state


def check_reason_validity(state: State) -> State:
    """Validate the return reason against business rules"""
    state["messages"] = ["Validating the return reason..."]

    return_reason = state.get("return_reason", "")

    # Simple validation logic - similar to main.py
    invalid_reasons = ["no reason", "just because", "don't want it"]
    reason_lower = return_reason.lower()

    is_valid = not any(invalid in reason_lower for invalid in invalid_reasons)

    state["is_reason_valid"] = is_valid

    if is_valid:
        state["messages"].append(f"✓ Return reason '{return_reason}' is valid.")
        state["status"] = "reason_valid"
    else:
        state["messages"].append(f"❌ I'm sorry, the reason '{return_reason}' is not a valid return reason. Please contact customer service.")
        state["status"] = "reason_invalid"

    return state


def process_return(state: State) -> State:
    """Process the approved return"""
    order_id = state.get("order_id", "Unknown")

    state["messages"] = [
        "Processing your return now...",
        "Creating return record...",
        "Generating return shipping label...",
        "Sending confirmation email...",
        "✅ Return processed successfully!",
        f"Your order {order_id} return request has been approved.",
        "You will receive further instructions via email."
    ]

    state["status"] = "completed"

    return state


def route_after_order_id(state: State) -> str:
    """Route after order ID collection based on status"""
    status = state.get("status", "")
    if status == "order_id_collected":
        return "check_eligibility"
    elif status == "collecting_order_id":
        return "collect_order_id"  # Self-loop for multi-turn conversation
    else:
        return END


def route_after_eligibility(state: State) -> str:
    """Route after eligibility check based on result"""
    if state.get("is_eligible", False):
        return "collect_reason"
    else:
        return END


def route_after_reason(state: State) -> str:
    """Route after reason collection based on status"""
    status = state.get("status", "")
    if status == "reason_collected":
        return "check_validity"
    elif status == "collecting_reason":
        return "collect_reason"  # Self-loop for multi-turn conversation
    else:
        return END


def route_after_validity(state: State) -> str:
    """Route after validity check based on result"""
    if state.get("is_reason_valid", False):
        return "process"
    else:
        return END


def get_graph():
    """Build and return the complete return processing state graph"""
    builder = StateGraph(State)

    # Add all nodes
    builder.add_node("collect_order_id", collect_order_id)
    builder.add_node("check_eligibility", check_return_eligibility)
    builder.add_node("collect_reason", collect_return_reason)
    builder.add_node("check_validity", check_reason_validity)
    builder.add_node("process", process_return)

    # Set entry point
    builder.add_edge(START, "collect_order_id")

    # Add conditional edges for routing (including self-loops)
    builder.add_conditional_edges(
        "collect_order_id",
        route_after_order_id,
        {
            "check_eligibility": "check_eligibility",
            "collect_order_id": "collect_order_id",  # Self-loop
            END: END
        }
    )

    builder.add_conditional_edges(
        "check_eligibility",
        route_after_eligibility,
        {
            "collect_reason": "collect_reason",
            END: END
        }
    )

    builder.add_conditional_edges(
        "collect_reason",
        route_after_reason,
        {
            "check_validity": "check_validity",
            "collect_reason": "collect_reason",  # Self-loop
            END: END
        }
    )

    builder.add_conditional_edges(
        "check_validity",
        route_after_validity,
        {
            "process": "process",
            END: END
        }
    )

    # Process always goes to END
    builder.add_edge("process", END)

    # Compile with checkpointer for state persistence
    checkpointer = InMemorySaver()
    graph = builder.compile(checkpointer=checkpointer)
    return graph
