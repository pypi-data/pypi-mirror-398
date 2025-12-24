
# Global Registry to map string IDs to callables (handlers) across the render usage
_handler_registry = {}

def register_handler(handler) -> str:
    """Registers a handler and returns a unique ID"""
    import uuid
    uid = str(uuid.uuid4())
    _handler_registry[uid] = handler
    return uid

def get_handler(uid):
    return _handler_registry.get(uid)

def clear_handlers():
    _handler_registry.clear()
