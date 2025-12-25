from typing import Dict, Any, Type, Callable

from .base import ActionStrategy
from .call_function import CallFunctionStrategy
from .collect_input import CollectInputStrategy
from ..core.constants import ActionType
from ..utils.logger import logger


class NodeFactory:
    _strategies: Dict[str, Type[ActionStrategy]] = {}

    @classmethod
    def register(cls, action_type: str, strategy_class: Type[ActionStrategy]):
        if not issubclass(strategy_class, ActionStrategy):
            raise RuntimeError(f"Strategy class {strategy_class.__name__} must inherit from NodeStrategy")

        logger.info(f"Registering node strategy: {action_type} -> {strategy_class.__name__}")
        cls._strategies[action_type] = strategy_class

    @classmethod
    def create(
        cls,
        step_config: Dict[str, Any],
        engine_context: Any
    ) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
        action = step_config.get('action')

        if not action:
            raise RuntimeError(f"Step '{step_config.get('id', 'unknown')}' is missing 'action' property")

        if action not in cls._strategies:
            raise RuntimeError(f"Unknown action type: '{action}'.")

        strategy_class = cls._strategies[action]
        strategy = strategy_class(step_config, engine_context)

        return strategy.get_node_function()

    @classmethod
    def is_registered(cls, action_type: str) -> bool:
        return action_type in cls._strategies


NodeFactory.register(ActionType.COLLECT_INPUT_WITH_AGENT.value, CollectInputStrategy)
NodeFactory.register(ActionType.CALL_FUNCTION.value, CallFunctionStrategy)
