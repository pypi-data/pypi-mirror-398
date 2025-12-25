#!/usr/bin/env python3
from jinja2 import Template
import ast

data = {'items': [{'id': 123}, {'id': 456}]}

# Test different path syntaxes
paths = [
    'result.items[0].id',
    'result.items.0.id',
    'result["items"][0]["id"]',
    'result.items[0]',
    'result.items',
]

for path in paths:
    template_str = f'{{{{ {path} }}}}'
    print(f"\nPath: {path}")
    print(f"Template: {template_str}")
    try:
        template = Template(template_str)
        result = template.render(result=data)
        print(f"Rendered: '{result}' (type: {type(result).__name__})")
        try:
            evaled = ast.literal_eval(result)
            print(f"Evaluated: {evaled} (type: {type(evaled).__name__})")
        except Exception as e:
            print(f"literal_eval failed: {e}")
    except Exception as e:
        print(f"ERROR: {e}")
