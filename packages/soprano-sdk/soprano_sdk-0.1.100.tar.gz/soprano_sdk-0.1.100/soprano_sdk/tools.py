"""
Workflow Tools - Wraps workflows as callable tools for agent frameworks
"""

import uuid
from typing import Optional, Dict, Any


from .utils.logger import logger

from langfuse.langchain import CallbackHandler

from .core.engine import load_workflow


class WorkflowTool:
    """Wraps a conversational workflow as a tool for agent orchestration

    This allows workflows to be used as tools in LangGraph, CrewAI, or other
    agent frameworks. The supervisor agent can decide which workflow to invoke
    based on user intent.
    """

    def __init__(
        self,
        yaml_path: str,
        name: str,
        description: str,
        checkpointer=None,
        config: Optional[Dict]=None
    ):
        """Initialize workflow tool

        Args:
            yaml_path: Path to workflow YAML file
            name: Tool name (used by agents to reference this tool)
            description: Tool description (helps agent decide when to use it)
            checkpointer: Optional checkpointer for persistence
        """
        self.yaml_path = yaml_path
        self.name = name
        self.description = description
        self.checkpointer = checkpointer

        # Load workflow
        self.graph, self.engine = load_workflow(yaml_path, checkpointer=checkpointer, config=config)

    def execute(
        self,
        thread_id: Optional[str] = None,
        user_message: Optional[str] = None,
        initial_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Execute the workflow with automatic state detection

        Checks workflow state and automatically resumes if interrupted,
        or starts fresh if not started/completed.

        Args:
            thread_id: Thread ID for state tracking
            user_message: User's message (used for resume if workflow is interrupted)
            initial_context: Context to inject for fresh starts (e.g., {"order_id": "123"})

        Returns:
            Final outcome message or interrupt prompt
        """
        from langgraph.types import Command
        from soprano_sdk.utils.tracing import trace_workflow_execution
        
        if thread_id is None:
            thread_id = str(uuid.uuid4())
        
        with trace_workflow_execution(
            workflow_name=self.engine.workflow_name,
            thread_id=thread_id,
            has_initial_context=initial_context is not None
        ) as span:
            callback_handler = CallbackHandler()
            config = {"configurable": {"thread_id": thread_id}, "callbacks": [callback_handler]}

            self.engine.update_context(initial_context)
            span.add_event("context.updated", {"fields": list(initial_context.keys())})

            state = self.graph.get_state(config)

            if state.next:
                span.set_attribute("workflow.resumed", True)
                logger.info(f"[WorkflowTool] Resuming interrupted workflow {self.name} (thread: {thread_id})")
                result = self.graph.invoke(
                    Command(resume=user_message or "", update=initial_context),
                    config=config
                )
            else:
                span.set_attribute("workflow.resumed", False)
                logger.info(f"[WorkflowTool] Starting fresh workflow {self.name} (thread: {thread_id})")
                result = self.graph.invoke(initial_context, config=config)
            
            final_state = self.graph.get_state(config)
            if not final_state.next and self.checkpointer:
                self.checkpointer.delete_thread(thread_id)

            # If workflow needs user input, return structured interrupt data
            if "__interrupt__" in result and result["__interrupt__"]:
                span.set_attribute("workflow.status", "interrupted")
                prompt = result["__interrupt__"][0].value
                return f"__WORKFLOW_INTERRUPT__|{thread_id}|{self.name}|{prompt}"

            # Workflow completed without interrupting
            span.set_attribute("workflow.status", "completed")
            return self.engine.get_outcome_message(result)

    def resume(self, thread_id: str, user_message: str) -> str:
        """Resume an interrupted workflow with user input

        Args:
            thread_id: Thread ID of the interrupted workflow
            user_message: User's response to the interrupt prompt

        Returns:
            Either another interrupt prompt or final outcome message
        """
        from langgraph.types import Command

        config = {"configurable": {"thread_id": thread_id}}
        result = self.graph.invoke(Command(resume=user_message), config=config)

        # Check if workflow needs more input
        if "__interrupt__" in result and result["__interrupt__"]:
            prompt = result["__interrupt__"][0].value
            return f"__WORKFLOW_INTERRUPT__|{thread_id}|{self.name}|{prompt}"

        # Workflow completed
        return self.engine.get_outcome_message(result)

    def to_langchain_tool(self):
        """Convert to LangChain tool format

        Returns:
            LangChain Tool that can be used by LangGraph agents
        """
        from langchain_core.tools import tool

        # Create function with proper name and docstring
        def workflow_tool(context: str = "") -> str:
            """Execute workflow with optional context"""
            # Parse context if provided (simple key=value format)
            initial_context = {}
            if context:
                for pair in context.split(","):
                    if "=" in pair:
                        key, value = pair.split("=", 1)
                        initial_context[key.strip()] = value.strip()

            return self.execute(initial_context=initial_context)

        # Set function name and docstring from tool definition
        workflow_tool.__name__ = self.name
        workflow_tool.__doc__ = self.description

        # Decorate and return
        return tool(workflow_tool)

    def to_crewai_tool(self):
        """Convert to CrewAI tool format

        Returns:
            CrewAI BaseTool that can be used by CrewAI agents
        """
        from crewai.tools import BaseTool

        # Capture self in closure
        workflow_tool = self

        # Create a custom CrewAI tool class
        class WorkflowCrewAITool(BaseTool):
            name: str = workflow_tool.name
            description: str = workflow_tool.description

            def _run(self, context: str = "") -> str:
                """Execute workflow with optional context"""
                # Parse context if provided (simple key=value format)
                initial_context = {}
                if context:
                    for pair in context.split(","):
                        if "=" in pair:
                            key, value = pair.split("=", 1)
                            initial_context[key.strip()] = value.strip()

                return workflow_tool.execute(initial_context=initial_context)

        # Return an instance of the tool
        return WorkflowCrewAITool()

    def get_mermaid_diagram(self) -> str:
        return self.graph.get_graph().draw_mermaid()

    def __call__(self, **kwargs) -> str:
        """Allow tool to be called directly

        Args:
            **kwargs: Context to pass to workflow

        Returns:
            Workflow result
        """
        return self.execute(initial_context=kwargs)
