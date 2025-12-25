from langgraph.checkpoint.memory import InMemorySaver
from soprano_sdk import WorkflowTool

config = {
    "model_config": {
        "base_url": "http://192.168.1.73:1234/v1",
        "model": "qwen/qwen3-coder-30b",
        "auth_callback": lambda : "test"
    }
}

checkpoint = InMemorySaver()
tool = WorkflowTool(
    yaml_path="./greeting_workflow.yaml",
    name="test",
    description="test",
    checkpointer=checkpoint,
    config=config
)

if __name__ == "__main__" :
    while True :
        query = input("Enter: ")

        result = tool.execute(
            thread_id="test_thread_1",
            user_message=query,
            initial_context={
            }
        )

        print(result)