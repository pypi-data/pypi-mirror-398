# # api_response_handler.py
# import re
# import os
# import json
# import time
# from typing import Any, Dict, List, Optional, Union, Callable
# from dataclasses import dataclass
# from enum import Enum
# import requests
# from requests.adapters import HTTPAdapter
# from urllib3.util.retry import Retry
# import importlib
# import operator

# class ErrorSeverity(Enum):
#     """Error severity levels"""

#     INFO = "info"
#     WARNING = "warning"
#     ERROR = "error"
#     CRITICAL = "critical"


# @dataclass
# class APIError:
#     """Structured API error"""

#     step_id: str
#     status_code: int
#     error_code: Optional[str] = None
#     message: str = ""
#     severity: ErrorSeverity = ErrorSeverity.ERROR
#     response_data: Optional[Dict] = None
#     retry_after: Optional[int] = None

#     def to_dict(self) -> Dict[str, Any]:
#         return {
#             "error": True,
#             "step_id": self.step_id,
#             "status_code": self.status_code,
#             "error_code": self.error_code,
#             "message": self.message,
#             "severity": self.severity.value,
#             "response_data": self.response_data,
#             "retry_after": self.retry_after,
#         }


# class ValueResolver:
#     """Resolves references and variables in values"""

#     @staticmethod
#     def resolve(value: Any, state: Dict[str, Any]) -> Any:
#         """Resolve a value with state context"""
#         if not isinstance(value, str):
#             return value

#         # Handle ${env.VAR_NAME}
#         value = ValueResolver._resolve_env_vars(value)

#         # Handle ${timestamp}
#         if "${timestamp}" in value:
#             value = value.replace("${timestamp}", str(int(time.time())))

#         # Handle {state.variable} or {variable.nested.path}
#         value = ValueResolver._resolve_state_references(value, state)

#         return value

#     @staticmethod
#     def _resolve_env_vars(value: str) -> str:
#         """Resolve environment variables"""
#         env_pattern = r"\$\{env\.([^}]+)\}"
#         matches = re.findall(env_pattern, value)
#         for match in matches:
#             env_value = os.environ.get(match, "")
#             value = value.replace(f"${{env.{match}}}", env_value)
#         return value

#     @staticmethod
#     def _resolve_state_references(value: str, state: Dict[str, Any]) -> str:
#         """Resolve state references like {username} or {user.profile.name}"""
#         pattern = r"\{([^}]+)\}"
#         matches = re.findall(pattern, value)

#         for match in matches:
#             resolved = ValueResolver._extract_nested_value(state, match)
#             if resolved is not None:
#                 value = value.replace(f"{{{match}}}", str(resolved))

#         return value

#     @staticmethod
#     def _extract_nested_value(data: Any, path: str) -> Any:
#         """Extract value from nested structure using dot notation"""
#         parts = path.split(".")
#         result = data

#         for part in parts:
#             if isinstance(result, dict):
#                 result = result.get(part)
#             elif isinstance(result, list) and part.isdigit():
#                 try:
#                     result = result[int(part)]
#                 except (IndexError, ValueError):
#                     return None
#             else:
#                 return None

#             if result is None:
#                 return None

#         return result


# class ConditionEvaluator:
#     OPERATORS = {
#         "==": operator.eq,
#         "!=": operator.ne,
#         ">": operator.gt,
#         "<": operator.lt,
#         ">=": operator.ge,
#         "<=": operator.le,
#         "contains": lambda a, b: b in str(a) if a is not None else False,
#         "not_contains": lambda a, b: b not in str(a) if a is not None else True,
#         "in": lambda a, b: a in b if isinstance(b, (list, tuple)) else False,
#         "not_in": lambda a, b: a not in b if isinstance(b, (list, tuple)) else True,
#         "starts_with": (
#             lambda a, b: str(a).startswith(str(b))
#             if a is not None else False
#         ),
#         "ends_with": lambda a, b: str(a).endswith(str(b)) if a is not None else False,
#         "is_null": lambda a, b: a is None,
#         "is_not_null": lambda a, b: a is not None,
#         "is_empty": lambda a, b: not a if isinstance(a, (list, dict, str)) else False,
#         "is_not_empty": (
#             lambda a, b: bool(a)
#             if isinstance(a, (list, dict, str)) else False
#         ),
#     }

#     @staticmethod
#     def evaluate(
#         condition: Dict[str, Any], response: Dict[str, Any], state: Dict[str, Any]) -> bool:

#         if "status_code" in condition:
#             expected = condition["status_code"]
#             actual = response.get("status")

#             if isinstance(expected, list):
#                 if actual not in expected:
#                     return False
#             elif actual != expected:
#                 return False

#         if "field" in condition:
#             field_path = condition["field"]
#             operator = condition.get("operator", "==")
#             expected_value = condition.get("value")

#             actual_value = ValueResolver._extract_nested_value(response, field_path)

#             if isinstance(expected_value, str):
#                 expected_value = ValueResolver.resolve(expected_value, state)

#             if operator not in ConditionEvaluator.OPERATORS:
#                 raise ValueError(f"Unknown operator: {operator}")

#             return ConditionEvaluator.OPERATORS[operator](actual_value, expected_value)

#         if "and" in condition:
#             return all(
#                 ConditionEvaluator.evaluate(sub_cond, response, state)
#                 for sub_cond in condition["and"]
#             )

#         if "or" in condition:
#             return any(
#                 ConditionEvaluator.evaluate(sub_cond, response, state)
#                 for sub_cond in condition["or"]
#             )

#         return True

#     @staticmethod
#     def evaluate_all(
#         conditions: List[Dict[str, Any]],
#         response: Dict[str, Any],
#         state: Dict[str, Any],
#     ) -> Optional[Dict[str, Any]]:
#         """Find first matching condition from a list"""
#         for condition in conditions:
#             # Skip default conditions for now
#             if condition.get("default"):
#                 continue

#             if ConditionEvaluator.evaluate(condition, response, state):
#                 return condition

#         # Return default if no match
#         for condition in conditions:
#             if condition.get("default"):
#                 return condition

#         return None


# class ResponseMapper:
#     """Maps response data to state variables"""

#     @staticmethod
#     def apply_mappings(
#         response: Dict[str, Any], mappings: List[Dict[str, Any]], state: Dict[str, Any]
#     ) -> None:
#         """Apply response mappings to state"""
#         for mapping in mappings:
#             from_path = mapping.get("from", "")
#             to_field = mapping.get("to", "")
#             transform = mapping.get("transform")  # Optional transformation function
#             default = mapping.get("default")  # Default value if extraction fails

#             # Extract value
#             value = ValueResolver._extract_nested_value(response, from_path)

#             # Apply default if needed
#             if value is None and default is not None:
#                 value = default

#             # Apply transformation if specified
#             if value is not None and transform:
#                 value = ResponseMapper._apply_transform(value, transform, state)

#             # Store in state
#             if to_field:
#                 state[to_field] = value

#     @staticmethod
#     def _apply_transform(
#         value: Any, transform: Union[str, Dict], state: Dict[str, Any]
#     ) -> Any:
#         """Apply transformation to a value"""
#         if isinstance(transform, str):
#             # Simple transformations
#             if transform == "lowercase":
#                 return str(value).lower()
#             elif transform == "uppercase":
#                 return str(value).upper()
#             elif transform == "trim":
#                 return str(value).strip()
#             elif transform == "int":
#                 return int(value)
#             elif transform == "float":
#                 return float(value)
#             elif transform == "bool":
#                 return bool(value)
#             elif transform == "json":
#                 return json.loads(value) if isinstance(value, str) else value

#         elif isinstance(transform, dict):
#             # Function-based transformation
#             if "function" in transform:
#                 func_path = transform["function"]
#                 func_args = transform.get("args", {})

#                 # Resolve arguments
#                 resolved_args = {
#                     k: ValueResolver.resolve(v, state) for k, v in func_args.items()
#                 }
#                 resolved_args["value"] = value

#                 # Execute transformation function
#                 return FunctionExecutor.execute_transform(func_path, resolved_args)

#         return value


# class ErrorHandler:
#     """Handles API errors with configurable responses"""

#     @staticmethod
#     def handle_error(
#         step_id: str,
#         response: Dict[str, Any],
#         error_config: Dict[str, Any],
#         state: Dict[str, Any],
#     ) -> APIError:
#         """Handle an error based on configuration"""
#         status_code = response.get("status", 0)

#         message = error_config.get("message", "An error occurred")
#         message = ValueResolver.resolve(message, {**state, "response": response})

#         error_code_path = error_config.get("error_code_field", "error_code")
#         error_code = ValueResolver._extract_nested_value(
#             response, f"data.{error_code_path}"
#         )

#         severity_str = error_config.get("severity", "error")
#         severity = ErrorSeverity(severity_str)

#         retry_after = error_config.get("retry_after")
#         if retry_after:
#             retry_after = ValueResolver.resolve(retry_after, state)

#         return APIError(
#             step_id=step_id,
#             status_code=status_code,
#             error_code=error_code,
#             message=message,
#             severity=severity,
#             response_data=response.get("data"),
#             retry_after=retry_after,
#         )


# class PostProcessor:
#     """Handles post-processing of API responses"""

#     @staticmethod
#     def process(
#         response: Dict[str, Any], post_config: Dict[str, Any], state: Dict[str, Any]
#     ) -> Any:
#         """Execute post-processing on response"""
#         function_path = post_config.get("function")
#         inputs = post_config.get("inputs", {})
#         output_field = post_config.get("output")

#         resolved_inputs = {"response": response}
#         for key, value in inputs.items():
#             resolved_inputs[key] = ValueResolver.resolve(value, state)

#         result = FunctionExecutor.execute(function_path, resolved_inputs)

#         if output_field:
#             state[output_field] = result

#         return result


# class FunctionExecutor:
#     """Executes functions from module paths"""

#     @staticmethod
#     def execute(function_path: str, inputs: Dict[str, Any]) -> Any:
#         """Execute a function given its module path"""
#         try:
#             # Parse module and function name
#             parts = function_path.rsplit(".", 1)
#             if len(parts) != 2:
#                 raise ValueError(f"Invalid function path: {function_path}")

#             module_name, function_name = parts

#             module = importlib.import_module(module_name)
#             function = getattr(module, function_name)

#             return function(**inputs)

#         except Exception as e:
#             raise Exception(f"Failed to execute function {function_path}: {str(e)}")

#     @staticmethod
#     def execute_transform(function_path: str, inputs: Dict[str, Any]) -> Any:
#         """Execute a transformation function"""
#         return FunctionExecutor.execute(function_path, inputs)


# class APIClient:
#     """Handles API requests with comprehensive error handling"""

#     def __init__(self, config: Dict[str, Any]):
#         self.name = config.get("name")
#         self.base_url = ValueResolver._resolve_env_vars(config.get("base_url", ""))
#         self.headers = self._resolve_headers(config.get("headers", {}))
#         self.timeout = config.get("timeout", 30)
#         self.retry_config = config.get("retry", {})

#         self.session = self._create_session()

#     def _resolve_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
#         """Resolve all header values"""
#         return {k: ValueResolver._resolve_env_vars(v) for k, v in headers.items()}

#     def _create_session(self) -> requests.Session:
#         """Create requests session with retry logic"""
#         session = requests.Session()

#         if self.retry_config:
#             retry_strategy = Retry(
#                 total=self.retry_config.get("max_attempts", 3),
#                 backoff_factor=1 if self.retry_config.get("backoff") == "exponential" else 0,
#                 status_forcelist=self.retry_config.get("for_status_codes", [429, 500, 502, 503, 504]),
#             )
#             adapter = HTTPAdapter(max_retries=retry_strategy)
#             session.mount("http://", adapter)
#             session.mount("https://", adapter)

#         return session

#     def execute(
#         self,
#         request_config: Dict[str, Any],
#         state: Dict[str, Any],
#         step_id: str = "api_call",
#     ) -> Dict[str, Any]:
#         """Execute API request with full error handling"""

#         method = request_config.get("method", "GET").upper()
#         path = self._prepare_path(request_config, state)
#         url = f"{self.base_url}{path}"

#         query_params = self._prepare_params(
#             request_config.get("query_params", {}), state
#         )
#         headers = self._prepare_headers(request_config, state)
#         body = self._prepare_body(request_config, state)

#         try:
#             response = self.session.request(
#                 method=method,
#                 url=url,
#                 headers=headers,
#                 params=query_params,
#                 json=body if request_config.get("body_type", "json") == "json" else None,
#                 data=body if request_config.get("body_type") != "json" else None,
#                 timeout=self.timeout,
#             )

#             try:
#                 response_data = response.json()
#             except:
#                 response_data = {"raw": response.text}

#             return {
#                 "status": response.status_code,
#                 "data": response_data,
#                 "headers": dict(response.headers),
#                 "success": response.ok,
#                 "url": url,
#                 "method": method,
#             }

#         except requests.exceptions.Timeout:
#             return {
#                 "status": 0,
#                 "error": "Request timeout",
#                 "error_type": "timeout",
#                 "success": False,
#             }
#         except requests.exceptions.ConnectionError:
#             return {
#                 "status": 0,
#                 "error": "Connection error",
#                 "error_type": "connection",
#                 "success": False,
#             }
#         except requests.exceptions.RequestException as e:
#             return {
#                 "status": 0,
#                 "error": str(e),
#                 "error_type": "request",
#                 "success": False,
#             }

#     def _prepare_path(
#         self, request_config: Dict[str, Any], state: Dict[str, Any]
#     ) -> str:
#         """Prepare URL path with variable substitution"""
#         path = request_config.get("path", "")
#         path_params = request_config.get("path_params", {})

#         for key, value in path_params.items():
#             resolved_value = ValueResolver.resolve(value, state)
#             path = path.replace(f"{{{key}}}", str(resolved_value))

#         return path

#     def _prepare_params(
#         self, params: Dict[str, Any], state: Dict[str, Any]
#     ) -> Dict[str, Any]:
#         """Prepare query parameters"""
#         return {k: ValueResolver.resolve(v, state) for k, v in params.items()}

#     def _prepare_headers(
#         self, request_config: Dict[str, Any], state: Dict[str, Any]
#     ) -> Dict[str, str]:
#         """Prepare request headers"""
#         headers = {**self.headers}

#         if "headers" in request_config:
#             for key, value in request_config["headers"].items():
#                 headers[key] = ValueResolver.resolve(value, state)

#         return headers

#     def _prepare_body(
#         self, request_config: Dict[str, Any], state: Dict[str, Any]
#     ) -> Optional[Dict[str, Any]]:
#         """Prepare request body"""
#         if "body" not in request_config:
#             return None

#         body = request_config["body"]
#         return self._resolve_dict(body, state)

#     def _resolve_dict(
#         self, data: Dict[str, Any], state: Dict[str, Any]
#     ) -> Dict[str, Any]:
#         """Recursively resolve dictionary values"""
#         result = {}
#         for key, value in data.items():
#             if isinstance(value, dict):
#                 result[key] = self._resolve_dict(value, state)
#             elif isinstance(value, list):
#                 result[key] = [
#                     self._resolve_dict(item, state)
#                     if isinstance(item, dict)
#                     else ValueResolver.resolve(item, state)
#                     for item in value
#                 ]
#             else:
#                 result[key] = ValueResolver.resolve(value, state)
#         return result


# class APIResponseHandler:
#     """Main handler for API responses with error handling and post-processing"""

#     def __init__(self, step_id: str, api_client: APIClient):
#         self.step_id = step_id
#         self.api_client = api_client

#     def execute_with_handling(
#         self,
#         request_config: Dict[str, Any],
#         response_config: Dict[str, Any],
#         state: Dict[str, Any],
#     ) -> Dict[str, Any]:
#         """Execute API call with full response handling"""

#         response = self.api_client.execute(request_config, state, self.step_id)

#         error_handlers = response_config.get("error_handlers", [])
#         error = self._check_errors(response, error_handlers, state)

#         if error:
#             return error.to_dict()

#         mappings = response_config.get("mappings", [])
#         if mappings:
#             ResponseMapper.apply_mappings(response, mappings, state)

#         if "post_process" in response_config:
#             post_result = PostProcessor.process(
#                 response, response_config["post_process"], state
#             )

#         conditions = response_config.get("conditions", [])
#         if conditions:
#             matching_condition = ConditionEvaluator.evaluate_all(
#                 conditions, response, state
#             )

#             if matching_condition:
#                 if "mappings" in matching_condition:
#                     ResponseMapper.apply_mappings(
#                         response, matching_condition["mappings"], state
#                     )

#                 if "next" in matching_condition:
#                     state["_next_step"] = matching_condition["next"]

#                 if "action" in matching_condition:
#                     state["_action"] = matching_condition["action"]

#         return {"success": True, "response": response, "state": state}

#     def _check_errors(
#         self,
#         response: Dict[str, Any],
#         error_handlers: List[Dict[str, Any]],
#         state: Dict[str, Any],
#     ) -> Optional[APIError]:
#         for error_config in error_handlers:
#             # Evaluate error condition
#             if ConditionEvaluator.evaluate(error_config, response, state):
#                 return ErrorHandler.handle_error(
#                     self.step_id, response, error_config, state
#                 )

#         return None


# # Example usage
# if __name__ == "__main__":
#     # Example configuration
#     api_config = {
#         "name": "user_service",
#         "base_url": "https://api.example.com",
#         "headers": {
#             "Authorization": "Bearer ${env.API_TOKEN}",
#             "Content-Type": "application/json",
#         },
#         "timeout": 30,
#     }

#     request_config = {
#         "method": "GET",
#         "path": "/users/{user_id}",
#         "path_params": {"user_id": "{user_id}"},
#     }

#     response_config = {
#         "mappings": [
#             {"from": "data.name", "to": "user_name"},
#             {"from": "data.email", "to": "user_email"},
#         ],
#         "error_handlers": [
#             {
#                 "status_code": 404,
#                 "field": "data.error_code",
#                 "operator": "==",
#                 "value": "ERR_NOT_FOUND",
#                 "message": "Sorry, we could not find the user you requested",
#                 "severity": "error",
#             },
#             {
#                 "status_code": 200,
#                 "field": "data.error_data",
#                 "operator": "==",
#                 "value": "ERR_NOT_FOUND",
#                 "message": "Sorry, we could not find the request",
#                 "severity": "warning",
#             },
#         ],
#         "post_process": {
#             "function": "response_processors.format_user_data",
#             "inputs": {"user_id": "{user_id}"},
#             "output": "formatted_user",
#         },
#     }

#     # Initialize
#     state = {"user_id": "12345"}
#     api_client = APIClient(api_config)
#     handler = APIResponseHandler("fetch_user", api_client)

#     # Execute
#     result = handler.execute_with_handling(request_config, response_config, state)

#     print(json.dumps(result, indent=2))
