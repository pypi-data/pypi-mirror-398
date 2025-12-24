import collections
from typing import Any, Dict, List, Optional, Callable, Union

from .element import VoltaElement
from .renderer import BaseRenderer
from . import hooks

# We need to expose the Fiber class to `hooks.py` technically, often done via circular import workarounds or passing references.
# For simplicity, we define Fiber here and inject the global setter into hooks or handle the global variable here.

class Fiber:
    """
    Represents a unit of work / node in the tree.
    Similar to React's Fiber node.
    """
    def __init__(self, element: VoltaElement, parent: Optional['Fiber'] = None):
        self.element = element
        self.type = element.tag if isinstance(element, VoltaElement) else None
        self.props = element.props if isinstance(element, VoltaElement) else {}
        self.parent = parent
        self.child: Optional['Fiber'] = None # First child
        self.sibling: Optional['Fiber'] = None # Next sibling
        
        # Renderer instance (DOM node)
        self.state_node: Any = None
        
        # Hooks state
        self.hooks: List[hooks.Hook] = []
        self.hook_index = 0
        
        # Setup trigger for updates
        self.schedule_update: Optional[Callable[['Fiber'], None]] = None
        
        # Effects to run
        self.effects: List[Callable] = []
        self.cleanups: List[Callable] = []

        # For diffing
        self.alternate: Optional['Fiber'] = None # The previous version of this fiber

    def __repr__(self):
        return f"Fiber({self.type})"

class Reconciler:
    def __init__(self, renderer: BaseRenderer):
        self.renderer = renderer
        self.root_fiber: Optional[Fiber] = None
        self.output_container = None
    
    def render(self, element: VoltaElement, container: Any):
        self.output_container = container
        
        # Create a Root Fiber
        # The root fiber has no element content really, it's just a container entry
        if not self.root_fiber:
            # Initial render
            self.root_fiber = Fiber(VoltaElement("ROOT", {}, [element]))
            self.root_fiber.state_node = container
            self.root_fiber.schedule_update = self.schedule_update
            
            # Reconcile children of root
            self.update_host_component(self.root_fiber)
        else:
            # Update root? (Usually render is called once, subsequent updates are via state)
            pass 

    def schedule_update(self, fiber: Fiber):
        """
        Trigger a re-render starting from the fiber that requested it.
        In a real React, we'd walk up to root and schedule a whole tree pass or subtree pass.
        For simplicity, we'll try to re-reconcile just the subtree or the whole tree.
        Let's trigger a top-down sync update from the Modified Fiber for simplicity in this MVP.
        """
        # We need to find the nearest Component root or similar. 
        # Actually, let's just re-run the component function for this fiber and diff children.
        self.perform_unit_of_work(fiber)

    def perform_unit_of_work(self, fiber: Fiber):
        """
        Process the fiber (render component or diff host node)
        """
        is_function_component = callable(fiber.type)
        
        if is_function_component:
            self.update_function_component(fiber)
        else:
            self.update_host_component(fiber)
            
        # Post-render: commit effects?
        # In this recursive simple version, children are processed inside updates, so we are 'committed' when done.
        # However, for hooks effects, we need a committing phase.
        self.commit_effects(fiber)

    def update_function_component(self, fiber: Fiber):
        # Set global hook cursor
        hooks._current_rendering_fiber = fiber
        fiber.hook_index = 0
        
        # Execute Component
        # Children is passed as a prop in React
        func_props = fiber.props.copy()
        # If children exist in element, pass them.
        # VoltaElement separates children, but components expect them in props.
        if fiber.element.children:
             if len(fiber.element.children) == 1:
                  func_props["children"] = fiber.element.children[0]
             else:
                  func_props["children"] = fiber.element.children
        
        children_elements = fiber.type(**func_props)
        if not isinstance(children_elements, list):
             children_elements = [children_elements]
             
        # Reset hook cursor
        hooks._current_rendering_fiber = None
        
        self.reconcile_children(fiber, children_elements)

    def update_host_component(self, fiber: Fiber):
        # Create or update DOM node
        # Don't create nodes for Fragments or Root (Root manually attached)
        if fiber.type == "fragment":
             # Fragments don't have a state_node.
             # But we need to reconcile their children.
             pass
             
        elif not fiber.state_node and fiber.type != "ROOT":
             # Create
             if fiber.type == "TEXT":
                 fiber.state_node = self.renderer.create_text_instance(fiber.props.get("nodeValue", ""))
             else:
                 fiber.state_node = self.renderer.create_instance(fiber.type, fiber.props)
        
        elif fiber.state_node and fiber.type != "ROOT" and fiber.alternate:
             # Update
             if fiber.type == "TEXT":
                 if fiber.props.get("nodeValue") != fiber.alternate.props.get("nodeValue"):
                     self.renderer.update_text_instance(fiber.state_node, fiber.alternate.props.get("nodeValue"), fiber.props.get("nodeValue"))
             else:
                 self.renderer.update_instance_props(fiber.state_node, fiber.type, fiber.alternate.props, fiber.props)
        
        # Flatten children from props if present, or element structure
        children_elements = fiber.element.children if fiber.element else []
        
        self.reconcile_children(fiber, children_elements)
        
        # Append children to this node (if host)
        # Note: In a recursive flow, this might happen after children are finished.
        # But if we create nodes top-down, we append valid child state_nodes.
        # Wait, if we are reconciling, we iterate children fibers.
        
        # Since we create state_node deeply, let's attach instances in commit or post-child-process.
        # Simplified: we attach immediately but ordering matters.
        # We'll rely on reconcile_children to recursively populate.
        
        # Actually proper React does: CompleteWork -> appends to parent.

    def reconcile_children(self, fiber: Fiber, new_children_elements: List[Any]):
        """
        Keyed Diffing / Reconciliation.
        """
        
        # 1. Flatten old fibers
        old_fibers = []
        t = fiber.alternate.child if fiber.alternate else fiber.child
        while t:
            old_fibers.append(t)
            t = t.sibling
            
        # 2. Normalize new elements (flatten list, wrap text)
        normalized_elements = []
        for c in new_children_elements:
            if c is None or isinstance(c, bool):
                continue
            if isinstance(c, (str, int, float)):
                normalized_elements.append(VoltaElement("TEXT", {"nodeValue": str(c)}, []))
            elif isinstance(c, list):
                # Simple one-level flatten for now 
                for sub in c:
                     if isinstance(sub, (str, int, float)):
                        normalized_elements.append(VoltaElement("TEXT", {"nodeValue": str(sub)}, []))
                     else:
                        normalized_elements.append(sub)
            else:
                 normalized_elements.append(c)

        # 3. Map existing fibers by key or index
        old_keyed_map = {}
        old_index_map = {}
        
        for idx, old_f in enumerate(old_fibers):
            key = old_f.element.key
            if key is not None:
                old_keyed_map[key] = old_f
            else:
                old_index_map[idx] = old_f

        # 4. Iterate new elements and match
        new_fibers = []
        prev_sibling = None
        
        # Track which old fibers are reused to detect deletions
        reused_old_fibers = set()
        
        for idx, element in enumerate(normalized_elements):
            new_fiber = None
            key = element.key
            
            # Try to find match
            matched_fiber = None
            
            if key is not None:
                if key in old_keyed_map:
                    matched_fiber = old_keyed_map[key]
            else:
                # If no key, try to match by order in the unkeyed set
                # We need to find the first available unkeyed fiber at or after current index
                # Ideally we just pop from a list of unkeyed or use index if consistent
                # Simplified: try match same index if not keyed
                if idx in old_index_map:
                     matched_fiber = old_index_map[idx]
            
            if matched_fiber and matched_fiber.type == element.tag:
                # Reuse / Update
                new_fiber = Fiber(element, parent=fiber)
                new_fiber.state_node = matched_fiber.state_node
                new_fiber.alternate = matched_fiber
                new_fiber.hooks = matched_fiber.hooks
                new_fiber.schedule_update = self.schedule_update
                reused_old_fibers.add(matched_fiber)
            else:
                # Create New
                new_fiber = Fiber(element, parent=fiber)
                new_fiber.schedule_update = self.schedule_update
                
            new_fibers.append(new_fiber)
            
            # Link siblings
            if idx == 0:
                fiber.child = new_fiber
            else:
                prev_sibling.sibling = new_fiber
            prev_sibling = new_fiber
            
            # Recurse
            self.perform_unit_of_work(new_fiber)
            
        # 5. Cleanup deleted fibers
        for old_f in old_fibers:
            if old_f not in reused_old_fibers:
                if old_f.state_node:
                    self.safe_remove_child(fiber, old_f)
                    
        # 6. Commit/Reorder Host Nodes
        if fiber.type != "ROOT" and not callable(fiber.type) and fiber.state_node:
             self.commit_children_to_host(fiber, new_fibers)
        if fiber.type == "ROOT":
             self.commit_children_to_host(fiber, new_fibers)

    def commit_children_to_host(self, parent_fiber: Fiber, children: List[Fiber]):
        # We need to find the actual nearest HOST parent node.
        # If parent_fiber is a Component or Fragment, we walk up.
        
        host_parent = parent_fiber.state_node
        p = parent_fiber
        while not host_parent:
             # If p is root, break
             if not p.parent: break 
             p = p.parent
             host_parent = p.state_node
             
        if not host_parent:
             return # Should not happen unless Root is broken
             
        # parent_node = parent_fiber.state_node
        # Clear existing? No, that breaks state. Use Diffing.
        # But 'reconcile_children' logic above did not touch DOM.
        
        # We need to correctly order the DOM nodes.
        # For each child fiber:
        #   If it's a host fiber -> ensure it is attached to parent_node.
        #   If it's a function fiber -> drill down to find host nodes.
        
        for child in children:
            nodes = self.find_host_nodes(child)
            for node in nodes:
                 # In a real DOM renderer we'd check `node.parentNode == parent_node`.
                 # We rely on renderer abstract methods. Since we don't have `get_parent`, we trust our flow.
                 # We just append for now, or ensure order.
                 # A smart renderer `append_child` handles "move if already exists".
                 self.renderer.append_child(host_parent, node)


    def find_host_nodes(self, fiber: Fiber) -> List[Any]:
        if not fiber:
            return []
        if not callable(fiber.type) and fiber.type != "fragment":
             # It is a host node
             return [fiber.state_node] if fiber.state_node else []
        
        # It is a component or fragment, deeper.
        nodes = []
        child = fiber.child
        while child:
            nodes.extend(self.find_host_nodes(child))
            child = child.sibling
        return nodes

    def safe_remove_child(self, parent_fiber, child_fiber):
         # Need to find the actual host parent and host children
         parent_host_nodes = self.find_host_nodes(parent_fiber)
         # Wait, parent_fiber might be a function. We need the nearest host parent UPWARDS.
         
         host_parent = parent_fiber.state_node
         p = parent_fiber
         while not host_parent or callable(p.type):
              if p.parent:
                   p = p.parent
                   host_parent = p.state_node
              else:
                   break # Root
         
         # Now find child host nodes
         child_nodes = self.find_host_nodes(child_fiber)
         for cn in child_nodes:
              self.renderer.remove_child(host_parent, cn)

    def commit_effects(self, fiber: Fiber):
        # Run effects for this fiber
        # 1. Cleanup old
        if fiber.alternate:
            for hook in fiber.alternate.hooks:
                # This is tricky without unified hook structure.
                # Assuming simple list match.
                pass
        
        # 2. Run new
        for hook in fiber.hooks:
            if isinstance(hook.memoized_state, dict) and 'effect' in hook.memoized_state:
                eff_state = hook.memoized_state
                if eff_state['has_changed']:
                    if eff_state['cleanup']:
                        eff_state['cleanup']()
                    cleanup = eff_state['effect']()
                    eff_state['cleanup'] = cleanup
                    
def render(element: VoltaElement, container: Any, renderer: BaseRenderer):
    reconciler = Reconciler(renderer)
    reconciler.render(element, container)
    return reconciler
