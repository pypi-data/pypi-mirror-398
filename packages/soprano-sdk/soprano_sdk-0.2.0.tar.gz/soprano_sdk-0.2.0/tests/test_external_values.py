"""
Test external value injection into workflows
"""

from soprano_sdk import load_workflow
import uuid
import os
import sys

# Add examples directory to path so workflow can import function modules
examples_dir = os.path.join(os.path.dirname(__file__), "..", "examples")
sys.path.insert(0, os.path.abspath(examples_dir))

# Load return workflow
yaml_path = os.path.join(examples_dir, "return_workflow.yaml")
graph, engine = load_workflow(yaml_path)
thread_id = str(uuid.uuid4())
config = {"configurable": {"thread_id": thread_id}}

print("=" * 60)
print("Test 1: Inject order_id only")
print("=" * 60)

result = graph.invoke({
    "order_id": "TEST-123"
}, config=config)

print("\nResult state:")
print(f"  order_id: {result.get('order_id')}")
print(f"  is_eligible: {result.get('is_eligible')}")
print(f"  _status: {result.get('_status')}")
print(f"  _outcome_id: {result.get('_outcome_id')}")

if "__interrupt__" in result and result["__interrupt__"]:
    interrupt_info = result["__interrupt__"][0]
    print("\nWorkflow interrupted (waiting for input):")
    print(f"  Prompt: {interrupt_info.value[:100]}...")
else:
    print("\nWorkflow completed")
    print(f"  Outcome: {engine.get_outcome_message(result)}")

print("\n" + "=" * 60)
print("Test 2: Inject both order_id and return_reason")
print("=" * 60)

# New thread for fresh test
thread_id2 = str(uuid.uuid4())
config2 = {"configurable": {"thread_id": thread_id2}}

result2 = graph.invoke({
    "order_id": "TEST-456",
    "return_reason": "damaged item"
}, config=config2)

print("\nResult state:")
print(f"  order_id: {result2.get('order_id')}")
print(f"  return_reason: {result2.get('return_reason')}")
print(f"  is_eligible: {result2.get('is_eligible')}")
print(f"  is_reason_valid: {result2.get('is_reason_valid')}")
print(f"  return_processed: {result2.get('return_processed')}")
print(f"  _status: {result2.get('_status')}")
print(f"  _outcome_id: {result2.get('_outcome_id')}")

if "__interrupt__" in result2 and result2["__interrupt__"]:
    interrupt_info = result2["__interrupt__"][0]
    print("\nWorkflow interrupted (waiting for input):")
    print(f"  Prompt: {interrupt_info.value[:100]}...")
else:
    print("\nWorkflow completed")
    print(f"  Outcome: {engine.get_outcome_message(result2)}")
