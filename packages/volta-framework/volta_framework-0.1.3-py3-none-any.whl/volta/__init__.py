"""
Volta: A Python UI framework mimicking React.
With built-in security features.
"""

from .element import h, fragment, VoltaElement
from .hooks import use_state, use_effect, use_ref, use_memo, use_callback, use_reducer, create_context, use_context
from .reconciler import render
from .renderer import BaseRenderer
from .html_renderer import HTMLRenderer
from .router import Router, Route, Switch, Link, NavLink, Redirect, use_router, use_params, not_found, NotFoundPage
from .components import Image

# Security exports
from .security import (
    escape, escape_attr, escape_url, is_safe,
    CSRFProtection, XSSProtection, InputValidator,
    SecurityConfig
)

__all__ = [
    # Core
    "h", "fragment", "VoltaElement", 
    # Hooks
    "use_state", "use_effect", "use_ref", "use_memo", "use_callback", "use_reducer",
    "create_context", "use_context", 
    # Rendering
    "render", "BaseRenderer", "HTMLRenderer",
    # Router
    "Router", "Route", "Switch", "Link", "NavLink", "Redirect", "use_router", "use_params",
    # Error Handling
    "not_found", "NotFoundPage",
    # Components
    "Image",
    # Security
    "escape", "escape_attr", "escape_url", "is_safe",
    "CSRFProtection", "XSSProtection", "InputValidator", "SecurityConfig"
]

