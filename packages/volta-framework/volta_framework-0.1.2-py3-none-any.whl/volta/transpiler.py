import re
import sys
from typing import Tuple, Optional

# Regex helpers
TAG_START_RE = re.compile(r"<([a-zA-Z_][\w\-\.]*)")
WS_RE = re.compile(r"\s+")
ATTR_NAME_RE = re.compile(r"([a-zA-Z_][\w\-\.]*)")
STRING_RE = re.compile(r"\"([^\"]*)\"|'([^']*)'")

def transpile(source: str) -> str:
    """
    Transpiles code containing JSX-like syntax into valid Python code using h() calls.
    Strategy: Scan for '<' that looks like a tag. Attempt to parse it as an element.
    If successful, return the transpiled string. If it's just an operator, leave it.
    """
    out = []
    i = 0
    n = len(source)
    
    while i < n:
        # Check for JSX start
        if source[i] == '<':
            # Is it a tag?
            match = TAG_START_RE.match(source, i)
            if match:
                # Potential tag. Try to parse element.
                # parsing logic returns (transpiled_str, new_index) or None if failed
                result = parse_element(source, i)
                if result:
                    transpiled, new_i = result
                    out.append(transpiled)
                    i = new_i
                    continue
        
        # Determine if we are in a string or comment to avoid false positives?
        # For this MVP, we ignore complex python tokenizing (e.g. standard strings containing <)
        # We just assume <Ident is a tag.
        
        out.append(source[i])
        i += 1
        
    return "".join(out)

def parse_element(source: str, start: int) -> Optional[Tuple[str, int]]:
    i = start + 1 # Skip <
    
    # Extract Tag Name
    m = re.match(r"([a-zA-Z_][\w\-\.]*)", source[i:])
    if not m:
        return None
    tag_name = m.group(1)
    i += len(tag_name)
    
    if tag_name in ('a', 'img'):
        # Use a premium styled warning
        print(f"\033[93m\033[1m[Volta Warning]\033[0m \033[2mUsage of raw <{tag_name}> tag detected. "
              f"Consider using the built-in <Link> or <Image> components for better integration.\033[0m")
    
    props = {}
    
    # Parse Attributes
    while i < len(source):
        # Skip whitespace
        while i < len(source) and source[i].isspace():
            i += 1
        
        if i >= len(source):
            return None
            
        char = source[i]
        
        if char == '/':
            # Self closing?
            if i+1 < len(source) and source[i+1] == '>':
                return format_h(tag_name, props, []), i+2
            return None 
            
        if char == '>':
            # End of open tag
            i += 1
            break
            
        if char == '{':
            # Spread attributes? Not supported in MVP yet (or maybe dict spread)
            # simplistic spread support: {...props}
             # TODO
             pass

        # Attribute Name
        am = ATTR_NAME_RE.match(source, i)
        if not am:
            # Malformed or unrecognized
            return None # Might be < operator
        
        attr_name = am.group(1)
        i += len(attr_name)
        
        # Check for =
        while i < len(source) and source[i].isspace(): 
            i += 1
            
        attr_val = "True" # Default boolean true
        
        if i < len(source) and source[i] == '=':
            i += 1
            while i < len(source) and source[i].isspace(): i += 1
            
            # Attribute Value: String or Expression
            if source[i] == '{':
                # Expression
                expr, new_i = parse_expression_block(source, i)
                if expr is None: return None
                attr_val = expr
                i = new_i
            elif source[i] == '"' or source[i] == "'":
                # String - handle escaped quotes
                quote = source[i]
                j = i + 1
                while j < len(source):
                    if source[j] == '\\' and j + 1 < len(source):
                        j += 2  # Skip escaped character
                        continue
                    if source[j] == quote:
                        break
                    j += 1
                if j >= len(source):
                    return None
                val = source[i+1:j]
                attr_val = repr(val)  # Quote it for python
                i = j + 1
            else:
                return None
                
        # Remap className -> class (optional, but React style uses className)
        # We can keep className or map it. Let's keep it in props, user can map it if they want.
        props[attr_name] = attr_val
        
    # Children
    children = []
    
    # Check for self-closing immediately handled earlier
    
    # Better Children Loop
    while i < len(source):
        if source.startswith(f"</{tag_name}>", i):
             return format_h(tag_name, props, children), i + len(tag_name) + 3
        
        if source[i] == '{':
            expr, new_i = parse_expression_block(source, i)
            if expr:
                children.append(expr)
                i = new_i
                continue
                
        if source[i] == '<':
            # Check child tag
             res = parse_element(source, i)
             if res:
                 c_str, new_i = res
                 children.append(c_str)
                 i = new_i
                 continue
             else:
                 # Encountered < but not a tag? (e.g. 5 < 10)
                 # Treat as text
                 pass
                 
        # Consuming text
        # Eat until < or { or end
        j = i
        text_acc = []
        while j < len(source):
            if source.startswith(f"</{tag_name}>", j): break
            if source[j] == '{': break
            if source[j] == '<' and TAG_START_RE.match(source, j): break
            text_acc.append(source[j])
            j += 1
            
        text = "".join(text_acc)
        if text:
             if text.strip():
                 # Multiline string handling
                 safe = repr(text) 
                 children.append(safe)
             
        i = j
        if i >= len(source): return None # Unexpected EOF
        
    return None

def parse_expression_block(source, start) -> Tuple[Optional[str], int]:
    """
    Parse a {...} expression block, properly handling:
    - Nested braces
    - String literals (single, double, triple quotes)
    - Comments
    """
    count = 1
    i = start + 1
    n = len(source)
    
    while i < n:
        ch = source[i]
        
        # Handle string literals - skip their contents
        if ch in ('"', "'"):
            # Check for triple quotes
            if i + 2 < n and source[i:i+3] in ('"""', "'''"):
                quote = source[i:i+3]
                i += 3
                # Find closing triple quote
                end = source.find(quote, i)
                if end == -1:
                    return None, start
                i = end + 3
                continue
            else:
                # Single/double quote string
                quote = ch
                i += 1
                while i < n:
                    if source[i] == '\\' and i + 1 < n:
                        i += 2  # Skip escaped character
                        continue
                    if source[i] == quote:
                        i += 1
                        break
                    i += 1
                continue
        
        # Handle comments
        if ch == '#':
            # Skip to end of line
            while i < n and source[i] != '\n':
                i += 1
            continue
        
        # Track braces
        if ch == '{':
            count += 1
        elif ch == '}':
            count -= 1
        
        if count == 0:
            # Found matching closing brace
            content = source[start+1:i]
            # Recursively transpile the content - it might contain JSX
            transpiled_content = transpile(content)
            return transpiled_content, i + 1
        
        i += 1
    
    return None, start

def format_h(tag, props, children):
    # Construct h calls
    # tag: if starts with uppercase, it is a variable/component -> direct code
    # if lowercase -> string
    
    if tag[0].isupper():
        tag_expr = tag
    else:
        tag_expr = f'"{tag}"'
        
    props_str = "{" + ", ".join(f'"{k}": {v}' for k, v in props.items()) + "}"
    
    if not children:
        return f'h({tag_expr}, {props_str})'
        
    children_str = ", ".join(children)
    return f'h({tag_expr}, {props_str}, {children_str})'
