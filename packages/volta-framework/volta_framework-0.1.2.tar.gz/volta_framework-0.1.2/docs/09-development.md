# Development

## Overview

This guide covers the development workflow for building Volta applications, including CLI commands, project structure, debugging, and best practices.

---

## Table of Contents

1. [CLI Commands](#cli-commands)
2. [Project Structure](#project-structure)
3. [Development Server](#development-server)
4. [Hot Reloading](#hot-reloading)
5. [File Organization](#file-organization)
6. [Debugging](#debugging)
7. [Testing](#testing)
8. [Best Practices](#best-practices)

---

## CLI Commands

### Available Commands

| Command | Description |
|---------|-------------|
| `volta dev` | Start development server with hot reload |
| `volta dev --port 8080` | Start on custom port |
| `volta init <name>` | Create new project |
| `volta clean` | Clear cache and compiled files |
| `volta build <file>` | Compile .vpx to .py |
| `volta run <file>` | Run a .vpx file directly |

### volta dev

Starts the development server with:
- Hot reloading on file changes
- Automatic .vpx transpilation
- Live error display
- Client-side interactivity support

```bash
# Default port 3000
volta dev

# Custom port
volta dev --port 8080
```

### volta init

Scaffolds a new Volta project:

```bash
volta init my-app
cd my-app
volta dev
```

Creates:
```
my-app/
├── app/                  # Application code
│   ├── __init__.py
│   └── App.vpx           # Root component
├── assets/               # Static assets
│   ├── logo.svg          # Volta logo
│   └── site.webmanifest  # Web app manifest
├── styles/               # Stylesheets
│   └── global.css        # Global CSS
└── wsgi.py               # Production entry
```

### volta clean

Clears Python cache files:

```bash
volta clean
```

Removes:
- `__pycache__` directories
- `.pyc` files
- Compiled artifacts

### volta run

Execute a .vpx file directly:

```bash
volta run components/Button.vpx
```

Useful for testing individual components.

---

## Project Structure

### Recommended Structure

```
my-volta-app/
├── app/                      # Application code
│   ├── __init__.py
│   ├── App.vpx              # Root component
│   ├── components/          # Reusable components
│   ├── pages/               # Page components
│   ├── hooks/               # Custom hooks
│   └── context/             # Context providers
├── assets/                   # Static files
│   ├── logo.svg
│   └── images/
├── styles/                   # CSS Stylesheets
│   └── global.css
├── wsgi.py                   # Production WSGI
├── requirements.txt          # Dependencies
└── SECURITY.md               # Security documentation
```

### Minimal Structure

```
my-app/
├── app/
│   └── App.vpx
├── assets/
├── styles/
└── wsgi.py
```

### file Purposes

| File/Folder | Purpose |
|-------------|---------|
| `app/App.vpx` | Root application component |
| `app/components/` | Reusable UI components |
| `app/pages/` | Page-level components (routes) |
| `assets/` | Static files (images, fonts) |
| `main.py` | SSR rendering entry |
| `wsgi.py` | Production server |

---

## Development Server

### Starting the Server

```bash
cd your-project
volta dev
```

Output:
```
[12:00:00] GET     /                                   200
[12:00:00] GET     /styles/global.css                  200
[12:00:01] GET     /assets/logo.svg                    200
```

> **Note**: Modern Volta CLI uses colorized output and suppresses internal hot-reload polling logs for a cleaner experience.
```

### Server Features

1. **Automatic Transpilation**: `.vpx` files are transpiled on-the-fly
2. **Hot Reload**: Page refreshes when files change
3. **Error Display**: Compilation errors shown in browser
4. **Asset Serving**: Static files from `assets/` directory
5. **Client Interactivity**: Event handlers work via server communication

### Custom Port

```bash
volta dev --port 8080
```

### Accessing the App

Open your browser to:
- http://localhost:3000 (default)
- http://localhost:XXXX (custom port)

---

## Hot Reloading

### How It Works

1. Dev server watches for file changes
2. When a file changes, server updates a hash
3. Client polls for hash changes every second
4. On change detection, browser reloads

### What Triggers Reload

- Saving any `.vpx` file
- Saving any `.py` file
- Saving files in `app/` directory

### Reload Indicator

In the browser console:
```
Change detected, reloading...
```

### Troubleshooting Hot Reload

If hot reload isn't working:

1. Check the server is running
2. Check the browser console for errors
3. Try hard refresh (Ctrl+Shift+R)
4. Restart the dev server

---

## File Organization

### Component Files

#### Single Component Per File

```python
# app/components/Button.vpx
from volta import h

def Button(**props):
    variant = props.get("variant", "primary")
    children = props.get("children")
    
    return (
        <button className={f"btn btn-{variant}"}>
            {children}
        </button>
    )
```

#### Multiple Related Components

```python
# app/components/Form.vpx
from volta import use_state

def FormField(**props):
    # ...
    pass

def FormLabel(**props):
    # ...
    pass

def FormInput(**props):
    # ...
    pass

def FormError(**props):
    # ...
    pass

# Main export
def Form(**props):
    return (
        <form>
            {props.get("children")}
        </form>
    )
```

### Importing Components

```python
# app/App.vpx
from volta import Router, Route

# Import from other files
from app.components.Button import Button
from app.components.Card import Card
from app.pages.Home import HomePage
from app.pages.About import AboutPage

def App():
    return (
        <Router>
            <Route path="/" component={HomePage} />
            <Route path="/about" component={AboutPage} />
        </Router>
    )
```

### Custom Hooks

```python
# app/hooks/useLocalStorage.py
from volta import use_state, use_effect

def use_local_storage(key, initial_value):
    """Persist state to localStorage"""
    value, set_value = use_state(initial_value)
    
    # In real implementation, would sync with localStorage
    
    return value, set_value

# Usage in component
# from app.hooks.useLocalStorage import use_local_storage
# 
# def Settings():
#     theme, set_theme = use_local_storage("theme", "light")
```

### Context Files

```python
# app/context/AuthContext.py
from volta import create_context, use_context, use_state

AuthContext = create_context(None)

def AuthProvider(**props):
    children = props.get("children")
    user, set_user = use_state(None)
    
    value = {
        "user": user,
        "isLoggedIn": user is not None,
        "login": lambda u: set_user(u),
        "logout": lambda: set_user(None)
    }
    
    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    )

def use_auth():
    context = use_context(AuthContext)
    if context is None:
        raise Exception("use_auth must be used within AuthProvider")
    return context
```

---

## Debugging

### Console Logging

```python
def MyComponent():
    data, set_data = use_state(None)
    
    def fetch_data():
        print("Fetching data...")  # Logs to server console
        result = {"name": "Test"}
        print(f"Got: {result}")    # Logs to server console
        set_data(result)
    
    use_effect(fetch_data, [])
    
    return <div>{data and data["name"]}</div>
```

### Viewing Server Logs

Dev server shows:
```
127.0.0.1 - - [18/Dec/2025 07:00:00] "GET / HTTP/1.1" 200 -
Fetching data...
Got: {'name': 'Test'}
```

### Error Display

Compilation errors appear in the browser:

```
SyntaxError: Failed to transpile Volta JSX in App.vpx: 
Unexpected token at line 15
```

### Debugging State

```python
def DebugComponent():
    count, set_count = use_state(0)
    items, set_items = use_state([])
    
    # Debug output
    print(f"Count: {count}, Items: {items}")
    
    return (
        <div>
            <p>Count: {count}</p>
            <pre>
                {str({"count": count, "items": items})}
            </pre>
        </div>
    )
```

### Debug Component

```python
def Debug(**props):
    """Render debug info"""
    data = props.get("data")
    label = props.get("label", "Debug")
    
    return (
        <div style={{
            "backgroundColor": "#1f2937",
            "color": "#10b981",
            "padding": "1rem",
            "fontFamily": "monospace",
            "fontSize": "12px",
            "borderRadius": "4px",
            "whiteSpace": "pre-wrap",
            "marginTop": "1rem"
        }}>
            <strong>{label}:</strong>
            <br />
            {str(data)}
        </div>
    )

# Usage
def MyPage():
    user, set_user = use_state({"name": "John", "age": 30})
    
    return (
        <div>
            <h1>{user["name"]}</h1>
            <Debug data={user} label="User State" />
        </div>
    )
```

---

## Testing

### Running Component Tests

```python
# tests/test_components.py
import sys
sys.path.insert(0, '..')

from volta import h
from volta.html_renderer import HTMLRenderer
from volta.reconciler import Reconciler

# Import component
from app.components.Button import Button

def test_button_renders():
    renderer = HTMLRenderer()
    root = renderer.create_instance("div", {})
    reconciler = Reconciler(renderer)
    
    reconciler.render(h(Button, {"children": "Click Me"}), root)
    
    html = str(root)
    assert "Click Me" in html
    assert "btn" in html

def test_button_variants():
    renderer = HTMLRenderer()
    root = renderer.create_instance("div", {})
    reconciler = Reconciler(renderer)
    
    reconciler.render(h(Button, {"variant": "danger", "children": "Delete"}), root)
    
    html = str(root)
    assert "btn-danger" in html

if __name__ == "__main__":
    test_button_renders()
    print("✓ Button renders")
    
    test_button_variants()
    print("✓ Button variants work")
    
    print("\nAll tests passed!")
```

### Running Tests

```bash
cd your-project
python -m pytest tests/
```

Or directly:

```bash
python tests/test_components.py
```

---

## Best Practices

### 1. Keep Components Small

```python
# ✅ Good - focused components
def UserAvatar(**props):
    return <Image src={props["src"]} alt={props["name"]} className="avatar" />

def UserInfo(**props):
    return (
        <div>
            <h3>{props["name"]}</h3>
            <p>{props["email"]}</p>
        </div>
    )

def UserCard(**props):
    user = props["user"]
    return (
        <div className="user-card">
            <UserAvatar src={user["avatar"]} name={user["name"]} />
            <UserInfo name={user["name"]} email={user["email"]} />
        </div>
    )
```

### 2. Use Meaningful Names

```python
# ✅ Good
def ProductCard():
    pass

def ShoppingCartSummary():
    pass

def UserAuthenticationForm():
    pass

# ❌ Bad
def Card1():
    pass

def Summary():
    pass

def Form():
    pass
```

### 3. Extract Custom Hooks

```python
# ✅ Good - reusable hook
def use_form_field(initial_value=""):
    value, set_value = use_state(initial_value)
    error, set_error = use_state(None)
    touched, set_touched = use_state(False)
    
    return {
        "value": value,
        "error": error,
        "touched": touched,
        "onChange": set_value,
        "onBlur": lambda: set_touched(True),
        "setError": set_error
    }
```

### 4. Separate Logic from UI

```python
# ✅ Good - logic separated
def use_product_data(product_id):
    product, set_product = use_state(None)
    loading, set_loading = use_state(True)
    
    def fetch():
        set_loading(True)
        # Fetch product
        set_product({"name": "Widget"})
        set_loading(False)
    
    use_effect(fetch, [product_id])
    
    return product, loading

def ProductPage(**props):
    product_id = props.get("id")
    product, loading = use_product_data(product_id)
    
    if loading:
        return <Spinner />
    
    return <ProductDisplay product={product} />
```

### 5. Use Type Hints in Python Files

```python
# app/hooks/useCounter.py
from typing import Tuple, Callable

def use_counter(initial: int = 0) -> Tuple[int, Callable[[], None], Callable[[], None]]:
    """
    Counter hook.
    
    Returns:
        Tuple of (count, increment, decrement)
    """
    count, set_count = use_state(initial)
    
    def increment():
        set_count(count + 1)
    
    def decrement():
        set_count(count - 1)
    
    return count, increment, decrement
```

---

## Next Steps

- [Deployment](./10-deployment.md) - Deploy to production
- [API Reference](./11-api-reference.md) - Complete API docs
