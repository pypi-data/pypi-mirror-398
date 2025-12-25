from typing import Any
from jinja2 import Template, TemplateError, UndefinedError
import ast


def get_nested_value(data: Any, path: str) -> Any:
    if not path:
        return data

    template_str = f"{{{{ {path} }}}}"

    try:
        template = Template(template_str)
        if isinstance(data, dict):
            result = template.render(**data)
        else:
            result = template.render(data)
        
        if not result or result == '':
            return None
            
        try:
            return ast.literal_eval(result)
        except (ValueError, SyntaxError):
            return result
    except (TemplateError, UndefinedError):
        return None