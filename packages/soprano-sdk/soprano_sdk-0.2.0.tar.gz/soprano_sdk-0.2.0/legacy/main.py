from transitions import Machine
import enum
import random
from typing import Iterator
from agno.agent import Agent
from agno.models.openai import OpenAIChat

class States(enum.Enum):
    COLLECTING_ORDER_ID = 1
    CHECKING_RETURN_ELIGIBILITY = 2
    COLLECTING_RETURN_REASON = 3
    CHECKING_REASON_VALIDITY = 4
    PROCESSING_RETURN = 5
    COMPLETED = 6

transitions = [
    {'trigger': 'order_id_collected', 'source': 'COLLECTING_ORDER_ID', 'dest': 'CHECKING_RETURN_ELIGIBILITY'},
    {'trigger': 'unable_to_get_order_id', 'source': 'COLLECTING_ORDER_ID', 'dest': 'COMPLETED'},
    {'trigger': 'eligible_for_return', 'source': 'CHECKING_RETURN_ELIGIBILITY', 'dest': 'COLLECTING_RETURN_REASON'},
    {'trigger': 'ineligible_for_return', 'source': 'CHECKING_RETURN_ELIGIBILITY', 'dest': 'COMPLETED'},
    {'trigger': 'reason_collected', 'source': 'COLLECTING_RETURN_REASON', 'dest': 'CHECKING_REASON_VALIDITY'},
    {'trigger': 'reason_valid', 'source': 'CHECKING_REASON_VALIDITY', 'dest': 'PROCESSING_RETURN'},
    {'trigger': 'return_processed', 'source': 'PROCESSING_RETURN', 'dest': 'COMPLETED'},
    {'trigger': 'unable_to_get_return_reason', 'source': 'COLLECTING_RETURN_REASON', 'dest': 'COMPLETED'},
    {'trigger': 'reason_invalid', 'source': 'CHECKING_REASON_VALIDITY', 'dest': 'COMPLETED'},    
]

class ReturnProcessor(object):
    def __init__(self):
        self.machine = Machine(model=self, states=States, transitions=transitions, initial=States.COLLECTING_ORDER_ID)
        self.machine.on_enter_CHECKING_RETURN_ELIGIBILITY('check_return_eligibility')

    def process_message(self, user_message="", history=[]) -> Iterator[str]:
        """Route message to appropriate method based on current state, yielding multiple messages"""
        if self.state == States.COLLECTING_ORDER_ID:
            yield from self.collect_order_id(user_message, history)
        elif self.state == States.CHECKING_RETURN_ELIGIBILITY:
            yield from self.check_return_eligibility(user_message, history)
        elif self.state == States.COLLECTING_RETURN_REASON:
            yield from self.collect_return_reason(user_message, history)
        elif self.state == States.CHECKING_REASON_VALIDITY:
            yield from self.check_reason_validity(user_message, history)
        elif self.state == States.PROCESSING_RETURN:
            yield from self.process_return(user_message, history)
        elif self.state == States.COMPLETED:
            yield from self.handle_completed_state(user_message, history)
        else:
            yield "I'm sorry, I'm in an unknown state. Please start over."

    def collect_order_id(self, user_message="", history=[]) -> Iterator[str]:
        if not hasattr(self, 'order_agent'):
            self.order_agent = Agent(
                name="ValueCatcher",
                model=OpenAIChat(id="gpt-4o-mini"),
                instructions=(
                    "Goal: capture a single order id from the user. "
                    "Ask concise follow-ups if ambiguous. "
                    "Once you have a clear order ID, respond with: 'ORDER_ID_CAPTURED: [order_id]' "
                    "If you cannot get the order ID after multiple attempts, respond with: 'ORDER_ID_FAILED: Unable to collect order ID' "
                    "Be helpful and guide the user to provide their order information. "
                    "Use the conversation history to understand the context and avoid repeating questions."
                ),
            )

        if not user_message:
            user_message = "Hello! I need to help you with a return. Could you please provide your order ID?"

        # Add current user message to history and pass to agent
        messages = history + [{"role": "user", "content": user_message}]
        resp = self.order_agent.run(messages)

        # Analyze agent output to determine state transition
        agent_response = resp.content

        if "ORDER_ID_CAPTURED:" in agent_response:
            # Extract order ID and trigger successful transition
            order_id = agent_response.split("ORDER_ID_CAPTURED:")[1].strip()
            self.order_id = order_id
            yield f"✓ Order ID collected: {order_id}"

            self.order_id_collected()  # Transition to CHECKING_RETURN_ELIGIBILITY
            yield "Checking if this order is eligible for return..."

            # Auto-continue to next state
            yield from self.check_return_eligibility()
        elif "ORDER_ID_FAILED:" in agent_response:
            # Trigger failed transition
            self.unable_to_get_order_id()  # Transition to COMPLETED
            yield "I'm sorry, I wasn't able to collect your order ID. Please contact customer service for further assistance."
        else:
            # Continue collecting - stay in current state
            yield resp.content
    
    def check_return_eligibility(self, user_message="", history=[]) -> Iterator[str]:
        yield "Validating order details and return policy..."

        num = random.randint(1, 100)
        print("Am here checking return eligibility")
        eligible = num % 2 == 0

        if eligible:
            self.eligible_for_return()
            yield "✓ Your order is eligible for return!"
            yield "Please provide the reason for your return."

            # Don't auto-continue for states that need user input
            # yield from self.collect_return_reason()
        else:
            self.ineligible_for_return()
            yield "❌ I'm sorry, your order is not eligible for return based on our return policy."

    def collect_return_reason(self, user_message="", history=[]) -> Iterator[str]:
        if not hasattr(self, 'reason_agent'):
            self.reason_agent = Agent(
                name="ReasonCollector",
                model=OpenAIChat(id="gpt-4o-mini"),
                instructions=(
                    "Goal: capture the reason why the user wants to return their order. "
                    "Ask concise follow-ups if the reason is unclear or incomplete. "
                    "Once you have a clear return reason, respond with: 'REASON_CAPTURED: [reason]' "
                    "If you cannot get a valid reason after multiple attempts, respond with: 'REASON_FAILED: Unable to collect return reason' "
                    "Be helpful and guide the user to provide valid return reasons like: damaged item, wrong size, wrong color, defective, not as described, etc. "
                    "Use the conversation history to understand the context and avoid repeating questions."
                ),
            )

        if not user_message:
            user_message = "Could you please tell me the reason for your return?"

        # Add current user message to history and pass to agent
        messages = history + [{"role": "user", "content": user_message}]
        resp = self.reason_agent.run(messages)

        # Analyze agent output to determine state transition
        agent_response = resp.content

        if "REASON_CAPTURED:" in agent_response:
            # Extract return reason and trigger successful transition
            return_reason = agent_response.split("REASON_CAPTURED:")[1].strip()
            self.return_reason = return_reason
            yield f"✓ Return reason captured: {return_reason}"

            self.reason_collected()  # Transition to CHECKING_REASON_VALIDITY
            yield "Validating the return reason..."

            # Auto-continue to next state
            yield from self.check_reason_validity()
        elif "REASON_FAILED:" in agent_response:
            # Trigger failed transition
            self.unable_to_get_return_reason()  # Transition to COMPLETED
            yield "I'm sorry, I wasn't able to collect a valid return reason. Please contact customer service for further assistance."
        else:
            # Continue collecting - stay in current state
            yield resp.content

    def check_reason_validity(self, user_message="", history=[]) -> Iterator[str]:
        # This is an automatic validation step - validate the stored return reason
        if hasattr(self, 'return_reason') and self.return_reason:
            # Simple validation logic - you can make this more sophisticated
            invalid_reasons = ["no reason", "just because", "don't want it"]
            reason_lower = self.return_reason.lower()

            valid = not any(invalid in reason_lower for invalid in invalid_reasons)

            if valid:
                self.reason_valid()  # Transition to PROCESSING_RETURN
                yield f"✓ Return reason '{self.return_reason}' is valid."
                yield "Processing your return now..."

                # Auto-continue to next state
                yield from self.process_return()
            else:
                self.reason_invalid()  # Transition to COMPLETED
                yield f"❌ I'm sorry, the reason '{self.return_reason}' is not a valid return reason. Please contact customer service."
        else:
            # No reason stored - this shouldn't happen, but handle gracefully
            self.reason_invalid()
            yield "No return reason found. Please start the return process again."

    def process_return(self, user_message="", history=[]) -> Iterator[str]:
        # This is an automatic processing step - process the return
        order_id = getattr(self, 'order_id', 'Unknown')
        return_reason = getattr(self, 'return_reason', 'Unknown')

        print(f"Processing return for order {order_id} with reason: {return_reason}")
        yield "Creating return record..."
        yield "Generating return shipping label..."
        yield "Sending confirmation email..."

        # Simulate return processing (could integrate with actual return system)
        try:
            # Here you would typically:
            # 1. Create return record in database
            # 2. Generate return shipping label
            # 3. Send confirmation email
            # 4. Update inventory

            self.return_processed()  # Transition to COMPLETED
            yield "✅ Return processed successfully!"
            yield f"Your order {order_id} return request has been approved."
            yield "You will receive further instructions via email."
        except Exception as e:
            # If processing fails, could stay in current state or go to completed with error
            print(f"Return processing failed: {e}")
            yield "❌ There was an error processing your return. Please contact customer service for assistance."

    def handle_completed_state(self, user_message="", history=[]) -> Iterator[str]:
        # Return process is complete - can handle follow-up questions or start new process
        if user_message and user_message.lower().strip():
            # Check if user wants to start a new return
            if any(keyword in user_message.lower() for keyword in ["new return", "another return", "different order", "start over"]):
                # Reset state machine for new return process
                self.reset_for_new_return()
                yield "Starting a new return process..."
                yield "Could you please provide the order ID for the new return?"

                # Auto-continue to collecting order ID
                yield from self.collect_order_id()
            else:
                # General help or questions
                yield "Your return process is complete. If you need to start a new return, just say 'new return'. Otherwise, is there anything else I can help you with?"
        else:
            yield "Your return process is complete. Is there anything else I can help you with?"

    def reset_for_new_return(self):
        """Reset the state machine for a new return process"""
        # Clear stored data
        if hasattr(self, 'order_id'):
            delattr(self, 'order_id')
        if hasattr(self, 'return_reason'):
            delattr(self, 'return_reason')

        # Reset to initial state
        self.state = States.COLLECTING_ORDER_ID

        

# return_processor = ReturnProcessor()
# print(return_processor.state)
# return_processor.collect_order_id()