from .core import route, use, run_server, protect
from .templates.html import html_templates
from .templates.tsx import tsx_templates
from .error import error_page, error_path
from .auth.login import login
from .auth.register import register
from .middleware.logging import logging_middleware
from .middleware.cors import cors
from .middleware.rate_limit import rate_limit
from .middleware.auth import auth_middleware

__version__ = "1.1.5"

__all__ = [
    "route",
    "use",
    "protect",
    "run_server",
    "html_templates",
    "tsx_templates",
    "error_page",
    "error_path",
    "login",
    "register",
    "logging_middleware",
    "cors",
    "rate_limit",
    "auth_middleware"
]
