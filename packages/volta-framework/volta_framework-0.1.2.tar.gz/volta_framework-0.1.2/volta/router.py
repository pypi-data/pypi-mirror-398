"""
Volta Router - Client-side routing with dynamic route support
Uses a global state approach for simplicity and reliability.
"""

from .hooks import use_state
from .element import h
import re

# Global routing state (accessible across components)
_current_path = "/"
_navigation_callbacks = []
_not_found_state = {"active": False, "message": None}

def get_current_path():
    """Get the current path"""
    global _current_path
    return _current_path

def set_current_path(path):
    """Set the current path and trigger updates"""
    global _current_path
    
    # Reset not found state on navigation
    clear_not_found()
    
    _current_path = path
    # Notify all callbacks
    for callback in _navigation_callbacks:
        try:
            callback(path)
        except:
            pass

def not_found(message=None):
    """
    Programmatically trigger the Not Found (404) page.
    
    Usage:
        from volta import not_found
        
        # Basic usage
        not_found()
        
        # With custom message
        not_found("The blog post you requested does not exist.")
    
    This tells the Router to render the built-in 404 page or a user-defined
    catch-all route if one exists.
    """
    global _not_found_state
    _not_found_state["active"] = True
    _not_found_state["message"] = message
    
    # Trigger re-render by notifying callbacks with current path
    path = get_current_path()
    for callback in _navigation_callbacks:
        try:
            callback(path)
        except:
            pass

# Alias for backwards compatibility
trigger_not_found = not_found

def clear_not_found():
    """Clear the programmatically triggered not found state."""
    global _not_found_state
    if _not_found_state["active"]:
        _not_found_state["active"] = False
        _not_found_state["message"] = None

def get_not_found_state():
    """Get the current not found state (for internal use)."""
    return _not_found_state

def NotFoundPage(**props):
    """
    Built-in 404 Not Found Page component.
    This is automatically rendered by the Router when:
    1. No route matches the current path
    2. not_found() is called programmatically
    
    The component receives an optional 'error' prop with a custom message.
    """
    error = props.get("error")
    message = error if error else "The page you are looking for does not exist."
    
    return h("div", {
        "className": "volta-not-found",
        "style": {
            "minHeight": "100vh",
            "display": "flex",
            "alignItems": "center",
            "justifyContent": "center",
            "backgroundColor": "#111827",
            "padding": "1.5rem",
            "fontFamily": "system-ui, -apple-system, sans-serif"
        }
    },
        h("div", {"style": {"textAlign": "center"}},
            h("h1", {
                "style": {
                    "fontSize": "8rem",
                    "fontWeight": "bold",
                    "color": "#8b5cf6",
                    "marginBottom": "1rem",
                    "lineHeight": "1"
                }
            }, "404"),
            h("h2", {
                "style": {
                    "fontSize": "1.875rem",
                    "fontWeight": "600",
                    "color": "#ffffff",
                    "marginBottom": "1rem"
                }
            }, "Page Not Found"),
            h("p", {
                "style": {
                    "color": "rgba(255, 255, 255, 0.6)",
                    "marginBottom": "2rem",
                    "maxWidth": "28rem"
                }
            }, message),
            h("a", {
                "href": "/",
                "style": {
                    "display": "inline-block",
                    "padding": "1rem 2rem",
                    "backgroundColor": "#7c3aed",
                    "color": "#ffffff",
                    "fontWeight": "600",
                    "borderRadius": "0.75rem",
                    "textDecoration": "none",
                    "transition": "background-color 0.2s"
                }
            }, "Go Home")
        )
    )

def register_navigation_callback(callback):
    """Register a callback to be called when navigation occurs"""
    global _navigation_callbacks
    if callback not in _navigation_callbacks:
        _navigation_callbacks.append(callback)

def unregister_navigation_callback(callback):
    """Unregister a navigation callback"""
    global _navigation_callbacks
    if callback in _navigation_callbacks:
        _navigation_callbacks.remove(callback)

def match_route(route_pattern: str, current_path: str) -> tuple:
    """
    Match a route pattern against a path.
    Supports:
    - Static routes: /about, /contact
    - Dynamic segments: /users/:id, /posts/:slug
    - Catch-all: /docs/*
    - Nested dynamic: /users/:userId/posts/:postId
    
    Returns: (matched: bool, params: dict)
    """
    # Exact match for static routes
    if route_pattern == current_path:
        return True, {}
    
    # Handle catch-all routes
    if route_pattern.endswith("/*"):
        base_pattern = route_pattern[:-2]
        if current_path.startswith(base_pattern):
            rest = current_path[len(base_pattern):]
            return True, {"*": rest.lstrip("/")}
        return False, {}
    
    # Build regex pattern from route
    pattern_parts = route_pattern.split("/")
    path_parts = current_path.split("/")
    
    # Must have same number of segments
    if len(pattern_parts) != len(path_parts):
        return False, {}
    
    params = {}
    for pattern_part, path_part in zip(pattern_parts, path_parts):
        if pattern_part.startswith(":"):
            # Dynamic segment - extract parameter
            param_name = pattern_part[1:]
            params[param_name] = path_part
        elif pattern_part != path_part:
            # Static segment mismatch
            return False, {}
    
    return True, params

def use_router():
    """
    Hook to access current path and navigation functions.
    
    Usage:
        router = use_router()
        current = router["path"]
        router["push"]("/new-path")
    """
    path, set_path = use_state(get_current_path())
    
    def push(new_path):
        set_current_path(new_path)
        set_path(new_path)
    
    def replace(new_path):
        set_current_path(new_path)
        set_path(new_path)
    
    return {
        "path": path,
        "push": push,
        "replace": replace
    }

def Router(**props):
    """
    Router component - wraps the app and provides routing.
    
    Usage:
        <Router>
            <Route path="/" component={Home} />
            <Route path="/about" component={About} />
        </Router>
    """
    initial_path = props.get("initialPath", "/")
    current_path, set_path = use_state(initial_path)
    
    # Sync with global state
    def handle_nav(new_path):
        set_path(new_path)
    
    register_navigation_callback(handle_nav)
    
    children = props.get("children", [])
    if not isinstance(children, list):
        children = [children]
    
    # Smart Route Matching Logic
    # We want to render all matching routes, BUT if a specific route matches, 
    # we should NOT render a catch-all (path="*") or (path="/*") route.
    
    current_path = get_current_path()
    not_found_active = _not_found_state["active"]
    
    has_specific_match = False
    has_user_catch_all = False
    user_catch_all_child = None
    
    # First pass: Check for matches
    # If not_found_active is True, we pretend no specific match exists
    if not not_found_active:
        for child in children:
            if child and hasattr(child, 'props'):
                path = child.props.get("path")
                if path:
                    matched, _ = match_route(path, current_path)
                    is_catch_all = path == "*" or path.endswith("/*")
                    
                    if is_catch_all:
                        has_user_catch_all = True
                        user_catch_all_child = child
                    
                    if matched and not is_catch_all:
                        has_specific_match = True
    else:
        # When not_found is active, still need to find user catch-all
        for child in children:
            if child and hasattr(child, 'props'):
                path = child.props.get("path")
                if path:
                    is_catch_all = path == "*" or path.endswith("/*")
                    if is_catch_all:
                        has_user_catch_all = True
                        user_catch_all_child = child
    
    # Second pass: Select children to render
    rendered = []
    
    for child in children:
        if child and hasattr(child, 'props'):
            path = child.props.get("path")
            
            # If it's a Route-like element
            if path:
                matched, _ = match_route(path, current_path)
                
                # If manual 404 is active, we IGNORE the route match result 
                # unless it is a catch-all route.
                is_catch_all = path == "*" or path.endswith("/*")
                
                if matched:
                    # Should we render this?
                    
                    if not_found_active:
                        # Only render catch-alls when 404 is forced
                        if is_catch_all:
                            # Apply error message prop
                            if _not_found_state["message"]:
                                child.props["error"] = _not_found_state["message"]
                            rendered.append(child)
                    else:
                        # Normal logic
                        # Yes if it's specific.
                        # Yes if it's catch-all AND no specific match was found.
                        if not is_catch_all or (is_catch_all and not has_specific_match):
                            rendered.append(child)
            else:
                # Non-route child (e.g. Navbar), always keep
                rendered.append(child)
        else:
             # String or other child
             rendered.append(child)
    
    # If no specific match and no user-defined catch-all, render built-in 404
    # Also if not_found is active and no user-defined catch-all, render built-in 404
    should_show_builtin_404 = False
    
    if not_found_active and not has_user_catch_all:
        should_show_builtin_404 = True
    elif not has_specific_match and not has_user_catch_all:
        should_show_builtin_404 = True
    
    if should_show_builtin_404:
        error_message = _not_found_state.get("message") if not_found_active else None
        rendered.append(h(NotFoundPage, {"error": error_message}))

    return h("div", {"className": "volta-router"}, *rendered)

def Route(**props):
    """
    Route component - renders component when path matches.
    
    Usage:
        <Route path="/users/:id" component={UserProfile} />
    """
    path_pattern = props.get("path", "/")
    component = props.get("component")
    
    if component is None:
        return None
    
    current_path = get_current_path()
    matched, params = match_route(path_pattern, current_path)
    
    if matched:
        # Pass params to component
        return h(component, {"params": params, **params})
    
    return None

def Switch(**props):
    """
    Switch component - renders only the first matching Route.
    """
    children = props.get("children", [])
    if not isinstance(children, list):
        children = [children]
    
    current_path = get_current_path()
    
    for child in children:
        if child and hasattr(child, 'props'):
            path_pattern = child.props.get("path", "/")
            matched, params = match_route(path_pattern, current_path)
            if matched:
                component = child.props.get("component")
                if component:
                    return h(component, {"params": params, **params})
    
    return None

def Link(**props):
    """
    Link component - navigates without full page reload.
    
    Usage:
        <Link to="/about">About Us</Link>
    """
    to = props.get("to", "/")
    children = props.get("children")
    
    # Extract special props to avoid passing them to the DOM element
    active_style = props.get("activeStyle")
    active_class = props.get("activeClassName")
    
    # Clean props for the anchor tag
    anchor_props = {k: v for k, v in props.items() if k not in ["to", "children", "activeClassName", "activeStyle"]}
    
    # Check if this link is active
    current = get_current_path()
    is_active = current == to
    
    # Handle Classes
    class_name = anchor_props.get("className", "")
    if is_active and active_class:
        class_name = f"{class_name} {active_class}".strip()
    anchor_props["className"] = class_name
    
    # Handle Styles
    style = anchor_props.get("style", {})
    if is_active and active_style:
         # Merge active styles
         style = {**style, **active_style}
    anchor_props["style"] = style

    # Handle Click
    user_on_click = anchor_props.get("onClick")
    
    def handle_click(e=None):
        if user_on_click:
            user_on_click(e)
            
        # If default prevented, don't navigate (if event object exists)
        # In this simple framework, e might not have preventDefault methods fully mocked yet,
        # but we follow the pattern.
        
        # Check for modifier keys or external target
        target = anchor_props.get("target")
        if target == "_blank":
            return # Let browser handle new tab
            
        # Navigate
        set_current_path(to)

        # In a real DOM, we'd prevent default here to stop browser reload
        # assuming the event system handles it or we return False
        
    anchor_props["onClick"] = handle_click
    anchor_props["href"] = to
    
    return h("a", anchor_props, children)

def NavLink(**props):
    """NavLink - Link with active state styling."""
    return Link(**props)

def Redirect(**props):
    """Redirect component - immediately redirects to target path."""
    to = props.get("to", "/")
    set_current_path(to)
    return None

def use_params():
    """Hook to access route parameters (passed to component props)."""
    # Note: params are passed directly to component props
    return {}
