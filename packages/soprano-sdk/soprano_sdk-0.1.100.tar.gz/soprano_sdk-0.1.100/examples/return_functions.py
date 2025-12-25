"""
Business logic functions for return processing workflow
"""

import random


def check_eligibility(state: dict) -> bool:
    """
    Check if an order is eligible for return.

    Args:
        state: The workflow state containing order information

    Returns:
        True if eligible, False otherwise
    """

    # Simulate eligibility check (random for demo purposes)
    # In production, this would check against order database, return policy, etc.
    num = random.randint(1, 100)
    return num % 2 == 0


def validate_reason(state: dict) -> bool:
    """
    Validate if a return reason is acceptable.

    Args:
        state: The workflow state containing return reason

    Returns:
        True if valid, False otherwise
    """
    reason = state.get('return_reason', '')

    # Invalid reasons that are not acceptable
    invalid_reasons = ["no reason", "just because", "don't want it"]

    reason_lower = reason.lower()

    # Check if any invalid reason is in the provided reason
    is_invalid = any(invalid in reason_lower for invalid in invalid_reasons)

    return not is_invalid


def process_return(state: dict) -> bool:
    """
    Process the return request.

    Args:
        state: The workflow state containing order and return information

    Returns:
        True if processing succeeded
    """
    order_id = state.get('order_id')
    reason = state.get('return_reason')

    # In production, this would:
    # 1. Create return record in database
    # 2. Generate return shipping label
    # 3. Send confirmation email
    # 4. Update inventory

    print(f"Processing return for order {order_id} with reason: {reason}")
    return True
