import os
import re
from html import escape
from html.parser import HTMLParser

TEMPLATES_DIR = os.path.join(os.getcwd(), "templates")

def _load_template(filename: str) -> str:
    path = os.path.join(TEMPLATES_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Boask TSX template not found: {filename}\n   Looked in: {TEMPLATES_DIR}")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

class _JSXParser(HTMLParser):
    """
    Minimal JSX parser that supports:
    - Nested elements
    - Self-closing tags
    - Attributes (including inline styles as strings)
    - Text nodes
    - {expression} interpolation (props.title, props['key'], children, etc.)
    Does NOT support fragments <> or spreads {...props} yet (can add later)
    """
    def __init__(self, props: dict, children: str = ""):
        super().__init__()
        self.props = props
        self.children_placeholder = children
        self.result = []
        self.stack = []  # To track open tags for proper nesting

    def eval_expr(self, expr: str) -> str:
        expr = expr.strip()
        if expr == "children":
            return self.children_placeholder
        # Support props.title, props["key"], props['key']
        if expr.startswith("props."):
            sub = expr[6:]
            if sub.startswith("[") or sub.startswith('["') or sub.startswith("['"):
                # Rough support for props["key"]
                match = re.match(r'\[(["\'])(.*?)\1\]', sub)
                if match:
                    key = match.group(2)
                    return escape(str(self.props.get(key, "")))
            else:
                keys = sub.split(".")
                value = self.props
                for k in keys:
                    value = value.get(k) if isinstance(value, dict) else None
                return escape(str(value or ""))
        # Fallback: direct key from props
        return escape(str(self.props.get(expr, "")))

    def handle_starttag(self, tag: str, attrs: list):
        attr_str = ""
        if attrs:
            attr_parts = []
            for name, value in attrs:
                if value is None:
                    attr_parts.append(name)
                else:
                    attr_parts.append(f'{name}="{escape(value)}"')
            attr_str = " " + " ".join(attr_parts)
        self.result.append(f"<{tag}{attr_str}>")
        self.stack.append(tag)

    def handle_endtag(self, tag: str):
        if self.stack and self.stack[-1] == tag:
            self.stack.pop()
            self.result.append(f"</{tag}>")

    def handle_data(self, data: str):
        # Replace {expr} in text nodes
        def repl(m):
            return self.eval_expr(m.group(1))
        rendered = re.sub(r'\{([^}]+)\}', repl, data)
        self.result.append(rendered)

    def get_html(self) -> str:
        return "".join(self.result)

class tsx_templates:
    """Real JSX/TSX parser – supports nested elements, attributes, and {props.x} / {children}"""

    @staticmethod
    def render(template_name: str, props=None, children="") -> str:
        props = props or {}
        template = _load_template(template_name)

        parser = _JSXParser(props, children)
        parser.feed(template)
        parser.close()
        return parser.get_html()