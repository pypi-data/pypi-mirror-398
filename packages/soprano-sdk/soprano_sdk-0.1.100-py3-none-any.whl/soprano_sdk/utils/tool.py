import importlib
from typing import Dict, Any
import functools

from .logger import logger

TYPE_MAP = {
    "string": str,
    "number": float,
    "integer": int,
    "boolean": bool,
    "array": list,
    "object": dict
}

def wrap_state(state: Dict[str, Any]):
    def wrapper(func):

        @functools.wraps(func)
        def inner(*args, **kwargs):
            return func(*args, **kwargs, **state)
        return inner
    return wrapper


class ToolRepository:
    def __init__(self, tool_config):
        self._cache: Dict[str, Any] = {}
        self.tool_config = tool_config

    def load(self, tool_name, state):
        if tool_name in self._cache:
            logger.info(f"Tool '{tool_name}' found in cache")
            return self._cache[tool_name]

        tool_info = next((t for t in self.tool_config.get('tools') if t['name']==tool_name), None)
        if not tool_info:
            raise RuntimeError(f"Tool '{tool_name}' not found in tool config")

        tool_description = tool_info.get("description", "")
        function_path = tool_info.get("callable")

        module_name, function_name = function_path.rsplit('.', 1)

        try:
            module = importlib.import_module(module_name)
        except ImportError as e:
            raise RuntimeError(f"Failed to import module '{module_name}': {e}")

        if not hasattr(module, function_name):
            raise RuntimeError(f"Module '{module_name}' has no function '{function_name}'")

        func = getattr(module, function_name)

        if not callable(func):
            raise RuntimeError(f"'{function_path}' is not callable (type: {type(func).__name__})")

        self._cache[function_path] = (tool_name, tool_description, func)
        logger.info(f"Successfully loaded and cached function: {function_path}")
        return tool_name, tool_description, wrap_state(state)(func)
