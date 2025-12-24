
"""
Simple HTML String Renderer (Server-Side Rendering)
With built-in XSS protection
"""
from .renderer import BaseRenderer
from .security import XSSProtection, escape, escape_attr, escape_url

class HTMLRenderer(BaseRenderer):
    def __init__(self):
        self.root = None

    def create_instance(self, type_tag: str, props: dict) -> 'HTMLElement':
        return HTMLElement(type_tag, props)

    def create_text_instance(self, text: str) -> 'HTMLText':
        return HTMLText(text)

    def append_child(self, parent_instance, child_instance):
        # Avoid duplicates - only append if not already a child
        if child_instance not in parent_instance.children:
            parent_instance.children.append(child_instance)

    def remove_child(self, parent_instance, child_instance):
        if child_instance in parent_instance.children:
            parent_instance.children.remove(child_instance)

    def insert_before(self, parent_instance, child_instance, before_instance):
        if before_instance in parent_instance.children:
            idx = parent_instance.children.index(before_instance)
            parent_instance.children.insert(idx, child_instance)
        else:
            self.append_child(parent_instance, child_instance)

    def update_instance_props(self, instance, type_tag, old_props, new_props):
        instance.props = new_props

    def update_text_instance(self, instance, old_text, new_text):
        instance.text = new_text

class HTMLElement:
    # Tags that can have unsafe content (like script, style, svg)
    # These require special handling but are allowed in framework components
    UNSAFE_CONTENT_TAGS = {'script', 'style'}
    
    # Attributes that should be URL-escaped
    URL_ATTRIBUTES = {'href', 'src', 'action', 'formaction', 'poster', 'data'}
    
    # Attributes that should never be rendered (potential XSS vectors)
    BLOCKED_ATTRIBUTES = {'srcdoc'}
    
    def __init__(self, tag, props):
        self.tag = tag
        self.props = props
        self.children = []

    def __str__(self):
        from .events import register_handler
        attrs = []
        
        for k, v in self.props.items():
            if k == "children": 
                continue
            
            # Block dangerous attributes
            if k.lower() in self.BLOCKED_ATTRIBUTES:
                continue
                
            if k == "className": 
                k = "class"
            
            # Handle Events
            if (k.startswith("on") or k.startswith("on_")) and callable(v):
                # Use secure handler registration
                from .security import SecureHandlerRegistry
                uid = SecureHandlerRegistry.register_handler(v)
                # Map standard 'onClick' -> 'click', 'oninput' -> 'input'
                event_name = k.lower().replace("on_", "").replace("on", "")
                # We attach a special attribute that our client JS will read
                attrs.append(f'data-v-on-{escape_attr(event_name)}="{escape_attr(uid)}"')
                continue
            
            if k == "style" and isinstance(v, dict):
                # Convert dict to css string
                # Convert camelCase keys to kebab-case (e.g. backgroundColor -> background-color)
                def camel_to_kebab(name):
                    import re
                    # Insert hyphen before uppercase letters and convert to lowercase
                    return re.sub(r'([a-z])([A-Z])', r'\\1-\\2', name).lower()
                
                # Escape style values to prevent CSS injection
                style_parts = []
                for sk, sv in v.items():
                    safe_key = camel_to_kebab(sk)
                    safe_value = escape_attr(str(sv))
                    style_parts.append(f"{safe_key}: {safe_value}")
                style_str = "; ".join(style_parts)
                attrs.append(f'{k}="{style_str}"')
            elif k.lower() in self.URL_ATTRIBUTES:
                # URL attributes get special sanitization
                safe_url = escape_url(str(v))
                attrs.append(f'{escape_attr(k)}="{escape_attr(safe_url)}"')
            else:
                # Regular attributes - escape both key and value
                safe_key = escape_attr(k)
                safe_value = escape_attr(str(v))
                attrs.append(f'{safe_key}="{safe_value}"')
        
        attr_str = " " + " ".join(attrs) if attrs else ""
        
        # Self closing?
        if not self.children and self.tag in ["input", "img", "br", "hr", "meta", "link"]:
             return f"<{self.tag}{attr_str} />"
             
        inner = "".join(str(c) for c in self.children)
        return f"<{self.tag}{attr_str}>{inner}</{self.tag}>"

class HTMLText:
    def __init__(self, text):
        self.text = text
    
    def __str__(self):
        # Escape text content to prevent XSS
        # Convert to string and escape HTML special characters
        return escape(str(self.text) if self.text is not None else '')

