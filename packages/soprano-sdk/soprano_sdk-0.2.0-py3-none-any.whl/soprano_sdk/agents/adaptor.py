from abc import ABC, abstractmethod
from typing import Any, Dict, List
from langgraph.graph.state import CompiledStateGraph
from agno.agent import Agent as AgnoAgent
from pydantic import BaseModel
from pydantic_ai.agent import Agent as PydanticAIAgent
from crewai.agent import Agent as CrewAIAgent
from ..utils.logger import logger

class AgentAdapter(ABC):
    
    @abstractmethod
    def invoke(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        pass


class LangGraphAgentAdapter(AgentAdapter):
    
    def __init__(self, agent: CompiledStateGraph):
        self.agent = agent
    
    def invoke(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        logger.info("Invoking LangGraph agent with messages")
        response = self.agent.invoke({"messages": messages})
        
        if structured_response := response.get('structured_response'):
            return structured_response.model_dump()
        
        if not response or "messages" not in response:
            raise ValueError("Agent response missing 'messages'")
        
        response_messages = response.get("messages")
        if not response_messages:
            raise ValueError("Agent response 'messages' list is empty")
        
        return response_messages[-1].content


class CrewAIAgentAdapter(AgentAdapter):
    
    def __init__(self, agent: CrewAIAgent, output_schema: BaseModel):
        self.agent = agent
        self.output_schema=output_schema
    
    def invoke(self, messages: List[Dict[str, str]]) -> Any:
        try:
            logger.info("Invoking LangGraph agent with messages")
            result = self.agent.kickoff(messages, response_format=self.output_schema)

            if structured_response := getattr(result, 'pydantic', None) :
                return structured_response.model_dump()

            if agent_response := getattr(result, 'raw', None) :
                return agent_response
            
            return str(result)
        except Exception as e:
            raise RuntimeError(f"CrewAI agent invocation failed: {e}")


class AgnoAgentAdapter(AgentAdapter):
    
    def __init__(self, agent: AgnoAgent):
        self.agent = agent
    
    def invoke(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        try:
            logger.info("Invoking LangGraph agent with messages")
            response = self.agent.run(messages)
            agent_response = response.content if hasattr(response, 'content') else str(response)
            
            return agent_response
        except Exception as e:
            raise RuntimeError(f"Agno agent invocation failed: {e}")


class PydanticAIAgentAdapter(AgentAdapter):
    
    def __init__(self, agent: PydanticAIAgent):
        self.agent = agent
    
    def invoke(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        try:
            logger.info("Invoking LangGraph agent with messages")
            result = self.agent.run_sync(messages)
            agent_response = result.output if hasattr(result, 'output') else str(result)
            
            return agent_response
        except Exception as e:
            raise RuntimeError(f"Pydantic-AI agent invocation failed: {e}")
