WORKFLOW_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["name", "description", "version", "data", "steps", "outcomes"],
    "properties": {
        "name": {
            "type": "string",
            "description": "Workflow name"
        },
        "description": {
            "type": "string",
            "description": "Workflow description"
        },
        "version": {
            "type": "string",
            "pattern": "^\\d+\\.\\d+(\\.\\d+)?$",
            "description": "Semantic version (e.g., 1.0.0)"
        },
        "agent_framework": {
            "type": "string",
            "enum": ["langgraph", "crewai", "agno", "pydantic-ai"],
            "default": "langgraph",
            "description": "Agent framework to use for all agents in this workflow (default: langgraph)"
        },
        "data": {
            "type": "array",
            "description": "Data fields used in the workflow",
            "items": {
                "type": "object",
                "required": ["name", "type", "description"],
                "properties": {
                    "name": {
                        "type": "string",
                        "pattern": "^[a-zA-Z_][a-zA-Z0-9_]*$",
                        "description": "Field name (must be valid Python identifier)"
                    },
                    "type": {
                        "type": "string",
                        "enum": ["text", "number", "boolean", "list", "dict", "any", "double"],
                        "description": "Field data type"
                    },
                    "description": {
                        "type": "string",
                        "description": "Field description"
                    },
                    "default": {
                        "description": "Default value for the field"
                    }
                }
            }
        },
        "inputs": {
            "type": "array",
            "description": "Input fields required to start the workflow (list of data field names)",
            "items": {
                "type": "string",
                "pattern": "^[a-zA-Z_][a-zA-Z0-9_]*$",
                "description": "Name of a field from the data array"
            }
        },
        "steps": {
            "type": "array",
            "description": "Workflow steps",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["id", "action"],
                "properties": {
                    "id": {
                        "type": "string",
                        "pattern": "^[a-zA-Z_][a-zA-Z0-9_]*$",
                        "description": "Step ID (must be unique and valid Python identifier)"
                    },
                    "action": {
                        "type": "string",
                        "enum": ["collect_input_with_agent", "call_function"],
                        "description": "Action type"
                    },
                    "field": {
                        "type": "string",
                        "description": "Field to collect (for collect_input_with_agent)"
                    },
                    "validator": {
                        "type": "string",
                        "description": "Optional data validator"
                    },
                    "max_attempts": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 20,
                        "description": "Maximum attempts (for collect_input_with_agent)"
                    },
                    "agent": {
                        "type": "object",
                        "description": "Agent configuration (for collect_input_with_agent)",
                        "required": ["name", "instructions"],
                        "properties": {
                            "name": {
                                "type": "string"
                            },
                            "model": {
                                "type": "string"
                            },
                            "description": {
                                "type": "string"
                            },
                            "instructions": {
                                "type": "string"
                            },
                            "tools": {
                                "type": "array"
                            },
                            "base_url": {
                                "type": "string",
                                "format": "uri"
                            },
                            "api_key": {
                                "type": "string"
                            },
                            "structured_output": {
                                "type": "object",
                                "description": "Structured output configuration",
                                "required": ["enabled"],
                                "properties": {
                                    "enabled": {
                                        "type": "boolean",
                                        "description": "Whether to enable structured output"
                                    },
                                    "fields": {
                                        "type": "array",
                                        "description": "Field definitions for structured output",
                                        "items": {
                                            "type": "object",
                                            "required": ["name", "type", "description"],
                                            "properties": {
                                                "name": {
                                                    "type": "string",
                                                    "pattern": "^[a-zA-Z_][a-zA-Z0-9_]*$",
                                                    "description": "Field name (must be valid Python identifier)"
                                                },
                                                "type": {
                                                    "type": "string",
                                                    "enum": ["text", "number", "boolean", "list", "dict", "double"],
                                                    "description": "Field data type"
                                                },
                                                "description": {
                                                    "type": "string",
                                                    "description": "Field description"
                                                },
                                                "required": {
                                                    "type": "boolean",
                                                    "description": "Whether the field is required",
                                                    "default": True
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "function": {
                        "type": "string",
                        "pattern": "^[a-zA-Z_][a-zA-Z0-9_.]*\\.[a-zA-Z_][a-zA-Z0-9_]*$",
                        "description": "Function path (for call_function, format: module.function)"
                    },
                    "output": {
                        "type": "string",
                        "description": "Output field name"
                    },
                    "next": {
                        "type": "string",
                        "description": "Next step ID (for simple routing)"
                    },
                    "transitions": {
                        "type": "array",
                        "description": "Conditional transitions",
                        "items": {
                            "type": "object",
                            "properties": {
                                "pattern": {
                                    "anyOf": [
                                        {"type": "string"},
                                        {"type": "array", "items": {"type": "string"}}
                                    ],
                                    "description": "Pattern(s) to match in response (for non-structured output)"
                                },
                                "match": {
                                    "description": "Value to match against a field (for structured output)"
                                },
                                "ref": {
                                    "type": "string",
                                    "description": "Field name to check when using 'match' (for structured output)"
                                },
                                "condition": {
                                    "description": "Condition to evaluate (for call_function)"
                                },
                                "next": {
                                    "type": "string",
                                    "description": "Next step or outcome ID"
                                }
                            },
                            "oneOf": [
                                {"required": ["pattern", "next"]},
                                {"required": ["match", "next", "ref"]},
                                {"required": ["condition", "next"]}
                            ]
                        }
                    },
                    "url": {
                        "type": "string",
                        "format": "uri",
                        "description": "Webhook URL (for webhook action)"
                    },
                    "method": {
                        "type": "string",
                        "enum": ["GET", "POST", "PUT", "PATCH", "DELETE"],
                        "description": "HTTP method (for webhook action)"
                    },
                    "headers": {
                        "type": "object",
                        "description": "HTTP headers (for webhook action)"
                    },
                    "timeout": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 600,
                        "description": "Timeout in seconds"
                    }
                }
            }
        },
        "outcomes": {
            "type": "array",
            "description": "Workflow outcomes",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["id", "type", "message"],
                "properties": {
                    "id": {
                        "type": "string",
                        "pattern": "^[a-zA-Z_][a-zA-Z0-9_]*$",
                        "description": "Outcome ID (must be unique)"
                    },
                    "type": {
                        "type": "string",
                        "enum": ["success", "failure"],
                        "description": "Outcome type"
                    },
                    "message": {
                        "type": "string",
                        "description": "Outcome message (supports {field} placeholders)"
                    }
                }
            }
        },
        "metadata": {
            "type": "object",
            "description": "Additional workflow metadata",
            "properties": {
                "author": {"type": "string"},
                "tags": {"type": "array", "items": {"type": "string"}},
                "documentation": {"type": "string"}
            }
        },
        "tool_config": {
            "type": "object",
            "description": "Tool configuration for the workflow",
            "properties": {
                "tools": {
                    "type": "array",
                    "description": "List of available tools",
                    "items": {
                        "type": "object",
                        "required": ["name", "description", "callable"],
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Tool name"
                            },
                            "description": {
                                "type": "string",
                                "description": "Tool description"
                            },
                            "callable": {
                                "type": "string",
                                "pattern": "^[a-zA-Z_][a-zA-Z0-9_.]*\\.[a-zA-Z_][a-zA-Z0-9_]*$",
                                "description": "Callable path (format: module.function)"
                            }
                        }
                    }
                }
            }
        }
    }
}
