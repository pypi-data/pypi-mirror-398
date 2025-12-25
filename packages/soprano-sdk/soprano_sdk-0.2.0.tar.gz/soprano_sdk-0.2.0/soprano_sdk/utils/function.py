import importlib
from typing import Callable, Dict

from ..utils.logger import logger


class FunctionRepository:
    def __init__(self):
        self._cache: Dict[str, Callable] = {}

    def load(self, function_path: str) -> Callable:
        if function_path in self._cache:
            logger.info(f"Loading function from cache: {function_path}")
            return self._cache[function_path]

        logger.info(f"Loading function: {function_path}")

        try:
            module_name, function_name = function_path.rsplit('.', 1)
            module = importlib.import_module(module_name)

            if not hasattr(module, function_name):
                raise RuntimeError(f"Module '{module_name}' has no function '{function_name}'")

            func = getattr(module, function_name)

            if not callable(func):
                raise RuntimeError(f"'{function_path}' is not callable (type: {type(func).__name__})")

            self._cache[function_path] = func
            logger.info(f"Successfully loaded and cached function: {function_path}")
            return func

        except Exception as e:
            raise RuntimeError(f"Unexpected error loading function '{function_path}': {e}")
