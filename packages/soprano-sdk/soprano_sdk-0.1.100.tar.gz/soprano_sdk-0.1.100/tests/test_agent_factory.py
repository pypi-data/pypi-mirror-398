"""Tests for the agent factory module."""

import pytest
from unittest.mock import MagicMock
from soprano_sdk.agents.factory import (
    AgentFactory,
    AgentAdapter,
    LangGraphAgentCreator,
    LangGraphAgentAdapter,
    CrewAIAgentCreator,
    CrewAIAgentAdapter,
    AgnoAgentCreator,
    AgnoAgentAdapter,
    PydanticAIAgentCreator,
)


class TestAgentFactory:
    """Test suite for AgentFactory."""
    
    def test_get_creator_langgraph(self):
        """Test that factory returns LangGraph creator for 'langgraph'."""
        creator = AgentFactory.get_creator("langgraph")
        assert isinstance(creator, LangGraphAgentCreator)
    
    def test_get_creator_langgraph_case_insensitive(self):
        """Test that framework names are case-insensitive."""
        creator = AgentFactory.get_creator("LangGraph")
        assert isinstance(creator, LangGraphAgentCreator)
    
    def test_get_creator_crewai(self):
        """Test that factory returns CrewAI creator for 'crewai'."""
        creator = AgentFactory.get_creator("crewai")
        assert isinstance(creator, CrewAIAgentCreator)
    
    def test_get_creator_agno(self):
        """Test that factory returns Agno creator for 'agno'."""
        creator = AgentFactory.get_creator("agno")
        assert isinstance(creator, AgnoAgentCreator)
    
    def test_get_creator_pydantic_ai(self):
        """Test that factory returns Pydantic-AI creator for 'pydantic-ai'."""
        creator = AgentFactory.get_creator("pydantic-ai")
        assert isinstance(creator, PydanticAIAgentCreator)
    
    def test_get_creator_invalid_framework(self):
        """Test that factory raises ValueError for invalid framework."""
        with pytest.raises(ValueError) as exc_info:
            AgentFactory.get_creator("invalid_framework")
        
        assert "Unsupported agent framework" in str(exc_info.value)
        assert "invalid_framework" in str(exc_info.value)
        assert "langgraph" in str(exc_info.value)  # Should list supported frameworks
    
    def test_create_agent_langgraph_returns_adapter(self):
        """Test that factory returns an adapter when creating LangGraph agent."""
        adapter = AgentFactory.create_agent(
            framework="langgraph",
            name="TestAgent",
            model_config={"model_name": "gpt-4", "api_key": "key", "base_url": "url"},
            tools=[],
            system_prompt="Test prompt",
            structured_output_model=None
        )
        
        # Should return an adapter, not raw agent
        assert isinstance(adapter, AgentAdapter)
        assert isinstance(adapter, LangGraphAgentAdapter)
        assert hasattr(adapter, 'invoke')


class TestLangGraphAgentAdapter:
    """Test suite for LangGraphAgentAdapter."""
    
    def test_adapter_has_invoke_method(self):
        """Test that adapter has invoke method."""
        creator = LangGraphAgentCreator()        
        adapter = creator.create_agent(
            name="TestAgent",
            model_config={"model_name": "gpt-4", "api_key": "key", "base_url": "url"},
            tools=[],
            system_prompt="Test prompt"
        )
        
        assert isinstance(adapter, LangGraphAgentAdapter)
        assert hasattr(adapter, 'invoke')
        assert callable(adapter.invoke)
    
    def test_adapter_invoke_returns_standardized_format(self):
        """Test that adapter invoke returns standardized response format."""
        # Create a mock agent
        mock_agent = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "Test response"
        mock_agent.invoke.return_value = {"messages": [mock_message]}
        
        adapter = LangGraphAgentAdapter(mock_agent)
        
        result = adapter.invoke([{"role": "user", "content": "Hello"}])
        
        # Check standardized format
        # Check standardized format
        assert isinstance(result, str)
        assert result == "Test response"
    
    def test_adapter_invoke_raises_on_missing_messages(self):
        """Test that adapter raises ValueError when response missing messages."""
        mock_agent = MagicMock()
        mock_agent.invoke.return_value = {}
        
        adapter = LangGraphAgentAdapter(mock_agent)
        
        with pytest.raises(ValueError, match="Agent response missing 'messages'"):
            adapter.invoke([{"role": "user", "content": "Hello"}])


class TestPlaceholderAgentAdapters:
    """Test suite for placeholder agent adapters (CrewAI, Agno, Pydantic-AI)."""
    
    def test_crewai_adapter_raises_import_error(self):
        """Test that CrewAI creator raises ImportError if crewai not installed."""
        creator = CrewAIAgentCreator()        
        # Should raise ImportError if crewai package is not installed
        try:
            adapter = creator.create_agent(
                name="TestAgent",
                model_config={"model_name": "gpt-4", "api_key": "key", "base_url": "url"},
                tools=[],
                system_prompt="Test"
            )
            # If we get here, crewai is installed - test the adapter
            assert isinstance(adapter, CrewAIAgentAdapter)
        except ImportError as e:
            assert "crewai" in str(e).lower()
    
    def test_agno_adapter_raises_import_error(self):
        """Test that Agno creator raises ImportError if agno not installed."""
        creator = AgnoAgentCreator()        
        # Should raise ImportError if agno package is not installed
        try:
            adapter = creator.create_agent(
                name="TestAgent",
                model_config={"model_name": "gpt-4", "api_key": "key", "base_url": "url"},
                tools=[],
                system_prompt="Test",
            )
            # If we get here, agno is installed - test the adapter
            assert isinstance(adapter, AgnoAgentAdapter)
        except ImportError as e:
            assert "agno" in str(e).lower()
    