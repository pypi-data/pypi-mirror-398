import abc
from typing import Any, Callable

class BaseRenderer(abc.ABC):
    """
    Abstract base class for Renderers.
    Defines the interface for host environment manipulation.
    """

    @abc.abstractmethod
    def create_instance(self, type_tag: str, props: dict) -> Any:
        """Create a native instance (e.g. DOM element)"""
        pass

    @abc.abstractmethod
    def create_text_instance(self, text: str) -> Any:
        """Create a native text instance"""
        pass

    @abc.abstractmethod
    def append_child(self, parent_instance: Any, child_instance: Any):
        """Append a child to a parent"""
        pass

    @abc.abstractmethod
    def remove_child(self, parent_instance: Any, child_instance: Any):
        """Remove a child from a parent"""
        pass

    @abc.abstractmethod
    def insert_before(self, parent_instance: Any, child_instance: Any, before_instance: Any):
        """Insert a child before another child"""
        pass

    @abc.abstractmethod
    def update_instance_props(self, instance: Any, type_tag: str, old_props: dict, new_props: dict):
        """Update properties of an instance"""
        pass
        
    @abc.abstractmethod
    def update_text_instance(self, instance: Any, old_text: str, new_text: str):
        """Update text content"""
        pass
