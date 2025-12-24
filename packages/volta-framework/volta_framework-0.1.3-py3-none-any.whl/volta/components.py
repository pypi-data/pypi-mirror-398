from .element import h

def Image(**props):
    """
    Robust Image component for the Volta defined framework.
    Replaces the standard <img> tag.
    
    Features:
    - Enforces 'alt' text for accessibility.
    - Default lazy loading.
    """
    src = props.get("src")
    alt = props.get("alt")
    
    if not src:
         # Depending on strictness, we might warn or return nothing?
         # Standard img shows broken image icon, we will pass it through.
         pass

    if alt is None:
        print("\\033[93mWarning: <Image> component missing 'alt' prop. This is bad for accessibility.\\033[0m")
        props["alt"] = "" # Normalize to empty string -> decorative
    
    # robust defaults
    if "loading" not in props:
        props["loading"] = "lazy"
        
    return h("img", props)
