# Volta Framework Documentation

## Introduction

**Volta** is a Python-based UI framework inspired by React. It brings the component-based architecture, hooks, and JSX-like syntax to Python, enabling developers to build modern, reactive web applications using familiar Python syntax.

---

## Key Features

| Feature | Description |
|---------|-------------|
| **JSX-like Syntax** | Write HTML-like templates directly in Python using `.vpx` files |
| **Component-Based** | Build reusable UI components with props and children |
| **Hooks** | `use_state`, `use_effect`, `use_ref`, `use_memo`, `use_callback`, `use_reducer` |
| **Context API** | Share state across components without prop drilling |
| **Client-Side Routing** | `Router`, `Route`, `Link` components with dynamic routes |
| **Server-Side Rendering** | Built-in SSR for fast initial page loads |
| **Hot Reloading** | Automatic page refresh during development |
| **Security First** | Built-in XSS protection, CSRF mitigation, and rate limiting |
| **Production Ready** | WSGI-compatible for deployment with Gunicorn |

---

## Why Volta?

### For Python Developers
- Write web UIs in pure Python
- No need to learn JavaScript/TypeScript
- Leverage Python's ecosystem

### For React Developers
- Familiar component patterns
- Same hooks API you already know
- JSX-like syntax feels like home

---

## Quick Example

```python
# app/App.vpx
from volta import use_state, Router, Route, Link

def Counter():
    count, set_count = use_state(0)
    
    def increment():
        set_count(count + 1)
    
    return (
        <div className="counter">
            <h1>Count: {count}</h1>
            <button onClick={increment}>Increment</button>
        </div>
    )

def App():
    return (
        <Router>
            <Route path="/" component={Counter} />
        </Router>
    )
```

---

## Installation

### Prerequisites
- Python 3.10 or higher
- pip (Python package manager)

### Setup

```bash
# Clone the framework
git clone https://github.com/your-repo/volta.git
cd volta/volta_framework

# Create a new project
volta init my-app
cd my-app

# Start development server
volta dev
```

---

## Project Structure

```
my-volta-app/
├── app/                    # Application code
│   ├── __init__.py
│   └── App.vpx            # Main application component
├── assets/                 # Static files (images, fonts, etc.)
│   ├── logo.svg           # Official Volta branding
│   └── site.webmanifest   # Web app manifest
├── styles/                 # CSS Stylesheets
│   └── global.css         # Global styles and utility classes
├── wsgi.py                 # Production WSGI application
├── requirements.txt        # Python dependencies
└── SECURITY.md             # Project security policy
```

---

## File Extensions

| Extension | Purpose |
|-----------|---------|
| `.vpx` | Volta component files with JSX-like syntax |
| `.py` | Standard Python files |

---

## Next Steps

1. [Components & JSX](./01-components-jsx.md) - Learn about component structure
2. [Props & Children](./02-props-children.md) - Passing data to components
3. [Hooks](./03-hooks.md) - State and side effects
4. [Routing](./05-routing.md) - Navigation and routes
5. [Deployment](./10-deployment.md) - Going to production

---

## Community & Support

- **GitHub**: Report issues and contribute
- **Documentation**: You're reading it!

---

*Volta - Build beautiful web apps with Python* ⚡
