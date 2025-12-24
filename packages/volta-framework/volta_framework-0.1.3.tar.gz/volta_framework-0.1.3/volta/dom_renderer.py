from .renderer import BaseRenderer
from typing import Any, Dict, List

class MockNode:
    def __init__(self, tag: str, props: Dict[str, Any] = None):
        self.tag = tag
        self.props = props or {}
        self.children: List['MockNode'] = []
        self.text_content: str = ""
        self.parent = None
        
        # Simulating event listeners
        self.event_handlers = {}
        for k, v in self.props.items():
            # Support on_click (Pythonic) and onClick (React)
            if (k.startswith("on_") or k.startswith("on")) and callable(v):
                self.event_handlers[k] = v

    def __repr__(self):
        if self.tag == "TEXT":
            return f"'{self.text_content}'"
        return f"<{self.tag} {self.props}>"
        
    def to_string(self, indent=0) -> str:
        space = "  " * indent
        if self.tag == "TEXT":
            return f"{space}{self.text_content}"
        
        attrs = " ".join([f'{k}="{v}"' for k, v in self.props.items() if not k.startswith("on_")])
        if attrs:
            attrs = " " + attrs
        
        if not self.children:
            return f"{space}<{self.tag}{attrs} />"
        
        s = f"{space}<{self.tag}{attrs}>\n"
        for child in self.children:
            s += child.to_string(indent + 1) + "\n"
        s += f"{space}</{self.tag}>"
        return s

    # Helpers for testing
    def click(self):
        if "on_click" in self.event_handlers:
            self.event_handlers["on_click"]()

class InMemoryRenderer(BaseRenderer):
    """
    Renders to a tree of MockNode objects.
    Good for testing and CLI.
    """
    def create_instance(self, type_tag: str, props: dict) -> Any:
        return MockNode(type_tag, props)

    def create_text_instance(self, text: str) -> Any:
        node = MockNode("TEXT")
        node.text_content = text
        return node

    def append_child(self, parent_instance: Any, child_instance: Any):
        if child_instance in parent_instance.children:
            parent_instance.children.remove(child_instance)
        
        parent_instance.children.append(child_instance)
        child_instance.parent = parent_instance

    def remove_child(self, parent_instance: Any, child_instance: Any):
        if child_instance in parent_instance.children:
            parent_instance.children.remove(child_instance)
            child_instance.parent = None

    def insert_before(self, parent_instance: Any, child_instance: Any, before_instance: Any):
        if before_instance in parent_instance.children:
            idx = parent_instance.children.index(before_instance)
            parent_instance.children.insert(idx, child_instance)
            child_instance.parent = parent_instance
        else:
            self.append_child(parent_instance, child_instance)

    def update_instance_props(self, instance: MockNode, type_tag: str, old_props: dict, new_props: dict):
        instance.props = new_props
        # Update event handlers
        instance.event_handlers = {}
        for k, v in new_props.items():
            if (k.startswith("on_") or k.startswith("on")) and callable(v):
                instance.event_handlers[k] = v

    def update_text_instance(self, instance: MockNode, old_text: str, new_text: str):
        instance.text_content = new_text
