# Volta Framework

Volta is a modern, React-inspired UI framework for Python. It allows you to build component-based user interfaces using Python functions, Hooks, and a JSX-like syntax (`.vpx`).

## Features

*   **Component-Based**: Build UI using functional components.
*   **JSX-like Syntax**: Write XML-like markup directly in Python (`.vpx` files).
*   **Hooks API**: Manage state and side effects with `use_state`, `use_effect`, `use_ref`, `use_context`, etc.
*   **Server-Side Rendering (SSR)**: Renders to valid HTML strings out of the box.
*   **CLI Tooling**: robust `volta` command for dev server, building, and running.
*   **Hot Reloading**: Instant feedback during development.

## Installation

```bash
pip install volta-framework
```

(Or install from source with `pip install -e .`)

## Quick Start

### 1. Create a Project

Initialize a new project structure:

```bash
volta init my-app
cd my-app
```

### 2. Run Development Server

Start the hot-reloading dev server:

```bash
volta dev
```
Open [http://localhost:3000](http://localhost:3000) to see your app.

## Writing Components

Volta components are just Python functions that return elements.

**`App.vpx`**:
```python
from volta import use_state

def Counter():
    count, set_count = use_state(0)
    
    return (
        <div>
            <p>Count: {count}</p>
            <button onClick={lambda: set_count(count + 1)}>Increment</button>
        </div>
    )

def App():
    return (
        <div>
            <h1>Welcome to Volta</h1>
            <Counter />
        </div>
    )
```

## CLI Reference

*   `volta init [name]`: Create a new project.
*   `volta dev [--port]`: Start dev server with hot reload.
*   `volta run <file.vpx>`: Execute a .vpx file directly.
*   `volta build <file.vpx>`: Transpile a .vpx file to .py.
*   `volta clean`: Remove cached artifacts.

## Advanced Features

*   **Context API**: `create_context`, `use_context`.
*   **Refs**: `use_ref`.
*   **Memoization**: `use_memo`, `use_callback`.
*   **Routing**: Built-in `Router`, `Route`, `Link` (in `volta.router`).

