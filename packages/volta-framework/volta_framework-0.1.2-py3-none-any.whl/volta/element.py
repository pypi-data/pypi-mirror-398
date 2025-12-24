from typing import Any, Dict, List, Union, Callable, Optional 

class VoltaElement:
    """
    Represents a Virtual DOM element.
    Conceptually similar to React.createElement objects.
    """
    def __init__(self, tag: Union[str, Callable], props: Dict[str, Any], children: List[Any], key: Optional[Any] = None):
        self.tag = tag
        self.props = props
        self.children = children
        self.key = key

    def __repr__(self):
        tag_name = self.tag if isinstance(self.tag, str) else self.tag.__name__
        return f"<{tag_name} props={self.props} children={len(self.children)}>"

def h(tag: Union[str, Callable], props: Optional[Dict[str, Any]] = None, *children: Any) -> VoltaElement:
    """
    Helper function to create VoltaElements.
    Similar to React.createElement or hyperscript 'h'.
    """
    if props is None:
        props = {}
    
    # Extract key if present
    key = props.pop("key", None)
    
    # Flatten children mostly for convenience, though strict React doesn't auto-flatten arrays usually.
    # We will accept variable args as children.
    flat_children = []
    for c in children:
        if isinstance(c, list):
            flat_children.extend(c)
        else:
            flat_children.append(c)

    return VoltaElement(tag, props, flat_children, key)

def fragment(props: Optional[Dict[str, Any]] = None, *children: Any) -> VoltaElement:
    """
    A Fragment component.
    """
    return h("fragment", props, *children)
