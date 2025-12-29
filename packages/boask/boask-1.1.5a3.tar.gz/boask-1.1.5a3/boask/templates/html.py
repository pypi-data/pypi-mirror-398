import os
import re
from html import escape

# Templates are loaded from a "templates" folder in your project root
TEMPLATES_DIR = os.path.join(os.getcwd(), "templates")

def _load_template(filename: str) -> str:
    path = os.path.join(TEMPLATES_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Boask template not found: {filename}\n   Looked in: {TEMPLATES_DIR}")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

class html_templates:
    """Simple {{ variable }} templating with automatic HTML escaping"""
    
    @staticmethod
    def render(template_name: str, **context) -> str:
        template = _load_template(template_name)
        
        def repl(match):
            key = match.group(1).strip()
            value = context.get(key, "")
            return escape(str(value))
        
        return re.sub(r'{{([^}]+)}}', repl, template)