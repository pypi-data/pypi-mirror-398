from typing import Any, Callable, List, Optional, Tuple, Dict, TypeVar

# Global state to track the current rendering fiber/component
_current_rendering_fiber: Optional[Any] = None

class Hook:
    def __init__(self):
        self.memoized_state = None
        self.queue = []

def get_current_fiber() -> Any:
    global _current_rendering_fiber
    if _current_rendering_fiber is None:
        raise RuntimeError("Hooks can only be called inside the body of a functional component.")
    return _current_rendering_fiber

def use_state(initial_value: Any) -> Tuple[Any, Callable[[Any], None]]:
    """
    Returns a stateful value and a function to update it.
    
    Usage:
        count, set_count = use_state(0)
        set_count(count + 1)  # Set directly
        set_count(lambda prev: prev + 1)  # Functional update
    """
    fiber = get_current_fiber()
    hook_index = fiber.hook_index
    
    if hook_index < len(fiber.hooks):
        hook = fiber.hooks[hook_index]
    else:
        hook = Hook()
        # Handle lazy initialization
        if callable(initial_value):
            hook.memoized_state = initial_value()
        else:
            hook.memoized_state = initial_value
        fiber.hooks.append(hook)
    
    fiber.hook_index += 1
    
    # Create a stable reference to the hook for the setter closure
    current_hook = hook
    current_fiber = fiber
    
    def set_state(action):
        new_value = action(current_hook.memoized_state) if callable(action) else action
        if new_value != current_hook.memoized_state:
            current_hook.memoized_state = new_value
            if current_fiber.schedule_update:
                current_fiber.schedule_update(current_fiber)

    return current_hook.memoized_state, set_state

def use_effect(effect: Callable[[], Optional[Callable[[], None]]], deps: Optional[List[Any]] = None):
    """
    Accepts a function that contains imperative, possibly effectful code.
    Effects run after render. Cleanup functions run before the next effect.
    
    Usage:
        def my_effect():
            print("Effect ran!")
            return lambda: print("Cleanup!")
        
        use_effect(my_effect, [some_dep])
    """
    fiber = get_current_fiber()
    hook_index = fiber.hook_index
    
    if hook_index < len(fiber.hooks):
        hook = fiber.hooks[hook_index]
        prev_deps = hook.memoized_state.get('deps') if hook.memoized_state else None
        has_changed = deps_changed(deps, prev_deps)
        
        hook.memoized_state = {
            'effect': effect,
            'deps': deps,
            'has_changed': has_changed,
            'cleanup': hook.memoized_state.get('cleanup') if hook.memoized_state else None
        }
    else:
        hook = Hook()
        hook.memoized_state = {
            'effect': effect,
            'deps': deps,
            'has_changed': True,
            'cleanup': None
        }
        fiber.hooks.append(hook)
    
    fiber.hook_index += 1

def use_ref(initial_value: Any = None) -> Dict[str, Any]:
    """
    Returns a mutable ref object whose .current property is initialized to the argument.
    The returned object will persist for the full lifetime of the component.
    
    Usage:
        my_ref = use_ref(0)
        my_ref["current"] = 5  # Mutate without triggering re-render
    """
    fiber = get_current_fiber()
    hook_index = fiber.hook_index
    
    if hook_index < len(fiber.hooks):
        hook = fiber.hooks[hook_index]
    else:
        hook = Hook()
        hook.memoized_state = {"current": initial_value}
        fiber.hooks.append(hook)
        
    fiber.hook_index += 1
    return hook.memoized_state

def use_memo(factory: Callable[[], Any], deps: Optional[List[Any]]) -> Any:
    """
    Returns a memoized value. Only recomputes when dependencies change.
    
    Usage:
        expensive_value = use_memo(lambda: compute_expensive(a, b), [a, b])
    """
    fiber = get_current_fiber()
    hook_index = fiber.hook_index
    
    if hook_index < len(fiber.hooks):
        hook = fiber.hooks[hook_index]
        prev_deps = hook.memoized_state[1] if hook.memoized_state else None
        
        if deps_changed(deps, prev_deps):
            new_value = factory()
            hook.memoized_state = (new_value, deps)
        fiber.hook_index += 1
        return hook.memoized_state[0]
    else:
        value = factory()
        hook = Hook()
        hook.memoized_state = (value, deps)
        fiber.hooks.append(hook)
        
    fiber.hook_index += 1
    return hook.memoized_state[0]

def use_callback(callback: Callable, deps: Optional[List[Any]]) -> Callable:
    """
    Returns a memoized callback. Only changes when dependencies change.
    
    Usage:
        handle_click = use_callback(lambda: do_something(a), [a])
    """
    return use_memo(lambda: callback, deps)

def use_reducer(reducer: Callable[[Any, Any], Any], initial_state: Any) -> Tuple[Any, Callable[[Any], None]]:
    """
    An alternative to use_state for complex state logic.
    
    Usage:
        def reducer(state, action):
            if action["type"] == "increment":
                return state + 1
            elif action["type"] == "decrement":
                return state - 1
            return state
        
        count, dispatch = use_reducer(reducer, 0)
        dispatch({"type": "increment"})
    """
    fiber = get_current_fiber()
    hook_index = fiber.hook_index
    
    if hook_index < len(fiber.hooks):
        hook = fiber.hooks[hook_index]
    else:
        hook = Hook()
        hook.memoized_state = initial_state
        fiber.hooks.append(hook)
    
    fiber.hook_index += 1
    
    current_hook = hook
    current_fiber = fiber
    current_reducer = reducer
    
    def dispatch(action):
        new_state = current_reducer(current_hook.memoized_state, action)
        if new_state != current_hook.memoized_state:
            current_hook.memoized_state = new_state
            if current_fiber.schedule_update:
                current_fiber.schedule_update(current_fiber)
    
    return current_hook.memoized_state, dispatch

def deps_changed(new_deps: Optional[List[Any]], old_deps: Optional[List[Any]]) -> bool:
    """Check if dependencies have changed."""
    if new_deps is None or old_deps is None:
        return True
    if len(new_deps) != len(old_deps):
        return True
    for d1, d2 in zip(new_deps, old_deps):
        if d1 != d2:
            return True
    return False

# --- Context API ---

class Context:
    """Context object for sharing data across the component tree."""
    def __init__(self, default_value: Any):
        self.default_value = default_value
        self.Provider = self._create_provider()

    def _create_provider(self):
        context = self
        def Provider(value=None, children=None, **kwargs):
            # If value not explicitly passed, use default
            if value is None:
                value = context.default_value
            return children
        Provider._context_object = context
        return Provider

def create_context(default_value: Any) -> Context:
    """
    Creates a Context object for sharing data across the component tree.
    
    Usage:
        ThemeContext = create_context("light")
        
        # In a component:
        theme = use_context(ThemeContext)
    """
    return Context(default_value)

def use_context(context: Context) -> Any:
    """
    Accepts a context object and returns the current context value.
    
    Usage:
        theme = use_context(ThemeContext)
    """
    fiber = get_current_fiber()
    parent = fiber.parent
    
    while parent:
        if callable(parent.type) and getattr(parent.type, "_context_object", None) == context:
            return parent.props.get("value", context.default_value)
        parent = parent.parent
    
    return context.default_value
