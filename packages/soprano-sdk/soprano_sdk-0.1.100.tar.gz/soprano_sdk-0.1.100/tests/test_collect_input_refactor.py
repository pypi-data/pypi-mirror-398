import pytest
from unittest.mock import MagicMock
from soprano_sdk.nodes.collect_input import CollectInputStrategy, _get_agent_response

class TestCollectInputStrategyRefactor:
    @pytest.fixture
    def strategy(self):
        step_config = {
            "field": "test_field",
            "agent": {"name": "test_agent"}
        }
        engine_context = MagicMock()
        engine_context.get_config_value.return_value = "history_based"
        return CollectInputStrategy(step_config, engine_context)

    def test_get_agent_response_success(self, strategy):
        agent = MagicMock()
        conversation = [{"role": "user", "content": "hello"}]
        
        mock_response = "response content"
        agent.invoke.return_value = mock_response
        
        response = _get_agent_response(agent, conversation)
        
        assert response == "response content"
        assert conversation[-1]["role"] == "assistant"
        assert conversation[-1]["content"] == "response content"
