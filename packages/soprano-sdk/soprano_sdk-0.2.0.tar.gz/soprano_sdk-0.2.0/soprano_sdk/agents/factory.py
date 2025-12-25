from abc import ABC, abstractmethod
from typing import Any, Dict, List, Literal, Tuple, Callable

from agno.models.openai import OpenAIChat
from crewai import LLM
from langchain_openai import ChatOpenAI
from pydantic import SecretStr, BaseModel
from typing import Optional

from .adaptor import (
    AgentAdapter,
    LangGraphAgentAdapter,
    CrewAIAgentAdapter,
    AgnoAgentAdapter,
    PydanticAIAgentAdapter
)


def get_model(config: Dict[str, Any], framework: Literal['langgraph', 'crewai', 'agno', 'pydantic-ai'] = "langgraph", output_schema: Optional[BaseModel] = None, tools: Optional[List] = None):
    errors = []
    
    model_name: str = config.get("model_name", "")
    if not model_name:
        errors.append("Model name is required in model_config")
    
    base_url = config.get("base_url")
    if not base_url:
        errors.append("Base url for model is required in model_config")
    
    api_key = config.get("api_key", "")
    if not api_key:
        if auth_callback := config.get("auth_callback"):
            api_key = auth_callback()
        if not api_key:
            errors.append("API key/Auth callback for model is required in model_config")
    
    if errors:
        raise ValueError("; ".join(errors))
    
    if framework == "agno" :
        return OpenAIChat(
            id=model_name,
            api_key=api_key,
            base_url=base_url
        )

    if framework == "crewai" :
        return LLM(
            api_key=api_key,
            model=f"openai/{model_name}",
            base_url=base_url,
            temperature=0.1,
            top_p=0.7
        )

    llm = ChatOpenAI(
        model=model_name,
        api_key=SecretStr(api_key),
        base_url=base_url,
    )
    
    if output_schema:
        return llm.with_structured_output(output_schema)

    if tools:
        llm = llm.bind_tools(tools)

    return llm


class AgentCreator(ABC):
    @abstractmethod
    def create_agent(
        self,
        name: str,
        model_config: Dict[str, Any],
        tools: List[Any],
        system_prompt: str,
        structured_output_model: Any = None
    ) -> AgentAdapter:
        pass


class LangGraphAgentCreator(AgentCreator):
    def create_agent(
        self,
        name: str,
        model_config: Dict[str, Any],
        tools: List[Any],
        system_prompt: str,
        structured_output_model: Any = None,
    ) -> LangGraphAgentAdapter:
        from langchain.agents import create_agent
        from langchain.tools import tool
        from langchain.agents.structured_output import ProviderStrategy

        tools = [tool(tool_name, description=description)(tool_callable) for tool_name, description, tool_callable in tools]

        output_parser = None
        if structured_output_model:
            output_parser = ProviderStrategy(structured_output_model)

        agent = create_agent(
            name=name,
            model=get_model(model_config, 'langgraph', tools=tools),
            tools=tools,
            system_prompt=system_prompt,
            response_format=output_parser
        )
        return LangGraphAgentAdapter(agent)


class CrewAIAgentCreator(AgentCreator):
    def create_agent(
        self,
        name: str,
        model_config: Dict[str, Any],
        tools: List[Any],
        system_prompt: str,
        structured_output_model: Any = None
    ) -> CrewAIAgentAdapter:
        from crewai.agent import Agent
        from crewai.tools import tool

        def create_crewai_tool(tool_name: str, description: str, tool_callable: Callable) -> Any:
            tool_callable.__doc__ = description
            return tool(tool_name)(tool_callable)
        
        tools = [create_crewai_tool(tn, desc, tc) for tn, desc, tc in tools]

        agent = Agent(
            role=name,
            backstory=system_prompt,
            goal="Collect the required data from user messages using the available tools.",
            tools=tools,
            llm=get_model(model_config, 'crewai'),
            max_retry_limit=2
        )
        
        return CrewAIAgentAdapter(agent, output_schema=structured_output_model)


class AgnoAgentCreator(AgentCreator):
    def create_agent(
        self,
        name: str,
        model_config: Dict[str, Any],
        tools: List[Any],
        system_prompt: str,
        structured_output_model: Any = None
    ) -> AgnoAgentAdapter:
        from agno.agent import Agent
        from agno.tools import tool

        tools = [tool(name=tool_name, description=description)(tool_callable) for tool_name, description, tool_callable in tools]

        agent = Agent(
            name=name,
            model=get_model(model_config, 'agno'),
            tools=tools,
            instructions=[system_prompt]
        )
        
        return AgnoAgentAdapter(agent)


class PydanticAIAgentCreator(AgentCreator):
    def create_agent(
        self,
        name: str,
        model_config: Dict[str, Any],
        tools: List[Tuple[str, str, Callable]],
        system_prompt: str,
        structured_output_model: Any = None
    ) -> PydanticAIAgentAdapter:
        from pydantic_ai import Agent

        agent = Agent(
            model=get_model(model_config, 'pydantic-ai'),
            system_prompt=system_prompt,
        )

        for tool_name, description, tool_callable in tools:
            agent.tool(name=tool_name, description=description)(tool_callable)

        return PydanticAIAgentAdapter(agent)


class AgentFactory:
    _CREATORS = {
        "langgraph": LangGraphAgentCreator,
        "crewai": CrewAIAgentCreator,
        "agno": AgnoAgentCreator,
        "pydantic-ai": PydanticAIAgentCreator,
    }
    
    @classmethod
    def get_creator(cls, framework: str) -> AgentCreator:
        framework_lower = framework.lower()
        
        if framework_lower not in cls._CREATORS:
            supported = ", ".join(cls._CREATORS.keys())
            raise ValueError(
                f"Unsupported agent framework: '{framework}'. "
                f"Supported frameworks: {supported}"
            )
        
        creator_class = cls._CREATORS[framework_lower]
        return creator_class()
    
    @classmethod
    def create_agent(
        cls,
        framework: str,
        name: str,
        model_config: Dict[str, Any],
        tools: List[Any],
        system_prompt: str,
        structured_output_model: Any
    ) -> Any:
        creator = cls.get_creator(framework)
        return creator.create_agent(
            name=name,
            model_config=model_config,
            tools=tools,
            system_prompt=system_prompt,
            structured_output_model=structured_output_model
        )
