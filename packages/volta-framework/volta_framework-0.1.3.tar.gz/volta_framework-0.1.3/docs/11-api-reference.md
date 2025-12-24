# API Reference

## Overview

Complete API reference for all Volta exports, functions, components, and hooks.

---

## Core

### h(tag, props, *children)

Creates a VoltaElement (virtual DOM node).

```python
from volta import h

# Create element
element = h("div", {"className": "container"}, "Hello World")

# With component
element = h(MyComponent, {"title": "Hello"})

# With children
element = h("div", {},
    h("h1", {}, "Title"),
    h("p", {}, "Content")
)
```

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `tag` | str \| function | HTML tag name or component function |
| `props` | dict | Properties/attributes |
| `*children` | any | Child elements |

**Returns:** `VoltaElement`

---

### fragment(*children)

Creates a fragment to group elements without a wrapper.

```python
from volta import fragment

def TableRow():
    return fragment(
        h("td", {}, "Cell 1"),
        h("td", {}, "Cell 2"),
        h("td", {}, "Cell 3")
    )
```

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `*children` | any | Child elements |

**Returns:** `VoltaElement`

---

### VoltaElement

The virtual DOM node class.

```python
from volta import VoltaElement

# Properties
element.tag      # str | function
element.props    # dict
element.children # list
element.key      # str | None
```

---

## Hooks

### use_state(initial_value)

Manages local component state.

```python
from volta import use_state

def Counter():
    count, set_count = use_state(0)
    
    def increment():
        set_count(count + 1)
    
    return h("button", {"onClick": increment}, f"Count: {count}")
```

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `initial_value` | any | Initial state value |

**Returns:** `tuple[value, setter_function]`

---

### use_effect(effect_fn, dependencies)

Performs side effects.

```python
from volta import use_effect

def DataFetcher():
    data, set_data = use_state(None)
    
    def fetch_data():
        set_data({"name": "John"})
        
        def cleanup():
            pass  # Optional cleanup
        return cleanup
    
    use_effect(fetch_data, [])  # Empty deps = run once
    
    return h("div", {}, data and data["name"])
```

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `effect_fn` | callable | Effect function (may return cleanup) |
| `dependencies` | list \| None | Deps array, None = every render |

**Returns:** None

---

### use_ref(initial_value)

Creates a mutable ref that persists across renders.

```python
from volta import use_ref

def Component():
    render_count = use_ref(0)
    render_count.current += 1
    
    return h("p", {}, f"Rendered {render_count.current} times")
```

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `initial_value` | any | Initial ref value |

**Returns:** Object with `.current` property

---

### use_memo(factory, dependencies)

Memoizes expensive computations.

```python
from volta import use_memo

def ExpensiveComponent(**props):
    items = props.get("items", [])
    
    sorted_items = use_memo(
        lambda: sorted(items, key=lambda x: x["name"]),
        [items]
    )
    
    return h("ul", {}, *[h("li", {}, i["name"]) for i in sorted_items])
```

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `factory` | callable | Function that computes the value |
| `dependencies` | list | Deps array |

**Returns:** Memoized value

---

### use_callback(callback, dependencies)

Memoizes callback functions.

```python
from volta import use_callback

def Parent():
    count, set_count = use_state(0)
    
    increment = use_callback(
        lambda: set_count(count + 1),
        [count]
    )
    
    return h(Child, {"onClick": increment})
```

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `callback` | callable | Callback function |
| `dependencies` | list | Deps array |

**Returns:** Memoized callback

---

### use_reducer(reducer, initial_state)

Manages complex state with a reducer.

```python
from volta import use_reducer

def reducer(state, action):
    if action["type"] == "INCREMENT":
        return {"count": state["count"] + 1}
    return state

def Counter():
    state, dispatch = use_reducer(reducer, {"count": 0})
    
    return h("button", 
        {"onClick": lambda: dispatch({"type": "INCREMENT"})},
        f"Count: {state['count']}"
    )
```

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `reducer` | callable | (state, action) → new_state |
| `initial_state` | any | Initial state value |

**Returns:** `tuple[state, dispatch_function]`

---

## Context

### create_context(default_value)

Creates a context object.

```python
from volta import create_context

ThemeContext = create_context("light")
UserContext = create_context(None)
```

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `default_value` | any | Default context value |

**Returns:** Context object with `.Provider` component

---

### use_context(context)

Consumes a context value.

```python
from volta import use_context

def ThemedButton():
    theme = use_context(ThemeContext)
    return h("button", {"className": f"btn-{theme}"}, "Click")
```

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `context` | Context | Context object from create_context |

**Returns:** Current context value

---

## Routing

### Router

Container component for routing.

```python
from volta import Router, Route

def App():
    return (
        <Router>
            <Route path="/" component={Home} />
            <Route path="/about" component={About} />
        </Router>
    )
```

**Props:**
| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `initialPath` | str | `"/"` | Initial route path |
| `children` | elements | - | Route definitions |

---

### Route

Defines a route mapping.

```python
<Route path="/users/:id" component={UserProfile} />
```

**Props:**
| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `path` | str | *required* | URL pattern |
| `component` | function | *required* | Component to render |

**Path Patterns:**
| Pattern | Example | Matches |
|---------|---------|---------|
| `/about` | Static | `/about` |
| `/users/:id` | Dynamic | `/users/123`, `/users/abc` |
| `/docs/*` | Catch-all | `/docs/anything/here` |
| `/*` | Global catch | Any unmatched path |

---

### Link

Client-side navigation component.

```python
<Link to="/about" className="nav-link" activeClassName="active">
    About
</Link>
```

**Props:**
| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `to` | str | *required* | Destination path |
| `className` | str | - | CSS class |
| `style` | dict | - | Inline styles |
| `activeClassName` | str | - | Class when active |
| `activeStyle` | dict | - | Styles when active |
| `target` | str | - | Link target |
| `onClick` | callable | - | Click handler |

---

### Switch

Renders only the first matching route.

```python
<Switch>
    <Route path="/" component={Home} />
    <Route path="/about" component={About} />
    <Route path="/*" component={NotFound} />
</Switch>
```

---

### NavLink

Alias for Link with active state support.

```python
<NavLink to="/about" activeClassName="active">About</NavLink>
```

---

### Redirect

Programmatic redirect component.

```python
<Redirect to="/new-page" />
```

**Props:**
| Prop | Type | Description |
|------|------|-------------|
| `to` | str | Destination path |

---

### use_router()

Hook for programmatic navigation.

```python
from volta import use_router

def Navigation():
    router = use_router()
    
    # Current path
    current = router["path"]
    
    # Navigate
    router["push"]("/new-path")
    router["replace"]("/other-path")
    
    return h("p", {}, f"Current: {current}")
```

**Returns:**
| Key | Type | Description |
|-----|------|-------------|
| `path` | str | Current path |
| `push` | callable | Navigate (add to history) |
| `replace` | callable | Navigate (replace history) |

---

### use_params()

Hook to access route parameters.

```python
def UserProfile():
    params = use_params()
    user_id = params.get("id")
    return h("h1", {}, f"User: {user_id}")
```

---

## Error Handling

### not_found(message)

Programmatically trigger 404 page.

```python
from volta import not_found

def BlogPost(**props):
    post_id = props.get("id")
    post = get_post(post_id)
    
    if not post:
        not_found(f"Post {post_id} not found")
        return None
    
    return h("article", {}, post["title"])
```

**Parameters:**
| Name | Type | Default | Description |
|------|------|---------|-------------|
| `message` | str | None | Custom error message |

---

### NotFoundPage

Built-in 404 page component.

```python
from volta import NotFoundPage

# Automatically rendered when:
# 1. No routes match
# 2. not_found() is called

# Custom usage
<Route path="/*" component={NotFoundPage} />
```

**Props:**
| Prop | Type | Description |
|------|------|-------------|
| `error` | str | Custom error message |

---

## Components

### Image

Enhanced image component.

```python
from volta import Image

<Image 
    src="/photo.jpg" 
    alt="Description"
    loading="lazy"
    width={300}
    height={200}
/>
```

**Props:**
| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `src` | str | *required* | Image source |
| `alt` | str | *required* | Alt text |
| `loading` | str | `"lazy"` | `"lazy"` or `"eager"` |
| `width` | str\|int | - | Width |
| `height` | str\|int | - | Height |
| `className` | str | - | CSS class |
| `style` | dict | - | Inline styles |

---

## Security

The `volta.security` module provides a comprehensive suite of security features to protect your application.

### CSRF Protection

Protects against Cross-Site Request Forgery.

```python
from volta.security import CSRFProtection

csrf = CSRFProtection(secret_key="your-secret")
token = csrf.generate_token()
is_valid = csrf.validate_token(received_token)
```

### XSS Protection

Automatic HTML escaping and input sanitization.

```python
from volta.security import XSSProtection

xss = XSSProtection()
safe_html = xss.escape("<b>Hello</b>")
sanitized = xss.sanitize_input("<script>alert(1)</script>")
```

### Rate Limiting

Prevents abuse and brute-force attacks.

```python
from volta.security import RateLimiter

limiter = RateLimiter(requests=100, window=60)
if limiter.is_allowed(client_ip):
    # Process request
    pass
```

### Security Headers

Configure secure browser headers (CSP, HSTS, etc.).

```python
from volta.security import SecurityHeaders

headers = SecurityHeaders()
header_dict = headers.get_headers()
# {'Content-Security-Policy': '...', 'X-Frame-Options': 'DENY', ...}
```

---

## Rendering

### render(element, root)

Renders a Volta element tree.

```python
from volta import h, render
from volta.html_renderer import HTMLRenderer

renderer = HTMLRenderer()
root = renderer.create_instance("div", {"id": "root"})

from volta.reconciler import Reconciler
reconciler = Reconciler(renderer)

reconciler.render(h(App), root)
html = str(root)
```

---

### HTMLRenderer

Server-side HTML renderer.

```python
from volta.html_renderer import HTMLRenderer

renderer = HTMLRenderer()

# Create instance
element = renderer.create_instance("div", {"className": "box"})

# Create text
text = renderer.create_text_instance("Hello")

# Append
renderer.append_child(element, text)

# Get HTML
html = str(element)  # <div class="box">Hello</div>
```

---

### Reconciler

Reconciles virtual DOM to renderer.

```python
from volta.reconciler import Reconciler
from volta.html_renderer import HTMLRenderer

renderer = HTMLRenderer()
reconciler = Reconciler(renderer)

root = renderer.create_instance("div", {"id": "root"})
reconciler.render(h(App), root)
```

---

## Loader

### install()

Installs the .vpx file loader.

```python
from volta.loader import install

install()

# Now you can import .vpx files
from app.App import App
```

---

## Transpiler

### transpile(source)

Transpiles JSX-like syntax to Python.

```python
from volta.transpiler import transpile

source = '''
def Button():
    return <button className="btn">Click</button>
'''

python_code = transpile(source)
# Results in h() calls
```

---

## Types Summary

### VoltaElement

```python
class VoltaElement:
    tag: str | callable
    props: dict
    children: list
    key: str | None
```

### Context

```python
class Context:
    Provider: Component  # Context provider component
    default: any         # Default value
```

### Ref

```python
class Ref:
    current: any  # Mutable value
```

---

## Import Summary

```python
from volta import (
    # Core
    h,
    fragment,
    VoltaElement,
    
    # Hooks
    use_state,
    use_effect,
    use_ref,
    use_memo,
    use_callback,
    use_reducer,
    
    # Context
    create_context,
    use_context,
    
    # Routing
    Router,
    Route,
    Switch,
    Link,
    NavLink,
    Redirect,
    use_router,
    use_params,
    
    # Error Handling
    not_found,
    NotFoundPage,
    
    # Components
    Image,
    
    # Rendering
    render,
    HTMLRenderer,
)

from volta.loader import install
from volta.transpiler import transpile
from volta.reconciler import Reconciler
```

---

## Version

Current version: 1.0.0

---

*Volta Framework API Reference*
