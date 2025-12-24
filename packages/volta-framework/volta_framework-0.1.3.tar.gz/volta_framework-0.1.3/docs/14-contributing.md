# Contributing & Architecture

## Overview

This guide explains the internal architecture of Volta and how you can contribute to its development.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [的核心 Components](#的核心-components)
3. [Transpilation Process](#transpilation-process)
4. [Rendering & Reconciliation](#rendering--reconciliation)
5. [Hook Implementation](#hook-implementation)
6. [Router Mechanics](#router-mechanics)
7. [CLI Internals](#cli-internals)
8. [Setup for Development](#setup-for-development)

---

## Architecture Overview

Volta is a server-side framework that follows a virtual DOM pattern similar to React but implemented in Python.

**The Lifecycle:**
1. **Transpilation**: `.vpx` (JSX) → `.py` (h() calls)
2. **Importing**: Custom loader allows importing transpiled code
3. **Execution**: Python executes the components, building a Virtual DOM tree
4. **Rendering**: `HTMLRenderer` converts the Virtual DOM to HTML
5. **Hydration (Conceptual)**: Volta maps client-side events back to server-side components

---

## Core Components

The framework is organized into several key modules:

- `volta/element.py`: Defines `VoltaElement`, the building block of the VDOM.
- `volta/hooks.py`: Implements the state management and lifecycle hooks.
- `volta/html_renderer.py`: Handles conversion of VDOM to HTML string.
- `volta/reconciler.py`: Manages the tree diffing and updates.
- `volta/transpiler.py`: Parses JSX-like syntax into Python code.
- `volta/loader.py`: Integration with Python's import system.
- `volta/router.py`: Routing logic and components.
- `volta/cli.py`: The `volta` command-line interface.

---

## Transpilation Process

The `Transpiler` uses regex and state-based parsing to find JSX tags and convert them into `h()` function calls.

```python
# Before (.vpx)
<div>
    <h1>{name}</h1>
    <Button onClick={increment}>Add</Button>
</div>

# After (Python)
h("div", {},
    h("h1", {}, name),
    h(Button, {"onClick": increment}, "Add")
)
```

**Key rules:**
- Tags starting with uppercase are treated as components (functions).
- Tags starting with lowercase are treated as HTML primitives (strings).
- Braces `{}` contain raw Python expressions.

---

## Rendering & Reconciliation

Volta uses a two-phase process:

1. **Phase 1: Creation**: Build the virtual tree of `VoltaElement` objects.
2. **Phase 2: Reconciliation**: The `Reconciler` traverses this tree and uses the `HTMLRenderer` to produce the final output.

In the future, the Reconciler will handle high-performance diffing for client-side hydration. Currently, it focuses on generating clean, SEO-friendly HTML on the server.

---

## Hook Implementation

Hooks are implemented using a global `hook_state` that tracks the "current component" being rendered.

```python
# Internal simplified logic
_state_store = {}  # Indexed by component instance

def use_state(initial):
    comp_id = get_current_rendering_component()
    index = get_next_hook_index()
    
    if comp_id not in _state_store:
        _state_store[comp_id] = []
    
    if index >= len(_state_store[comp_id]):
        _state_store[comp_id].append(initial)
        
    def set_state(new_val):
        _state_store[comp_id][index] = new_val
        trigger_re_render(comp_id)
        
    return _state_store[comp_id][index], set_state
```

---

## Router Mechanics

The Router works by:
1. Identifying the current path (from URL or manual override).
2. Pattern matching the path against `Route` components using regex.
3. Managing history state for client-side navigation.
4. Handling "Not Found" states through a centralized dispatcher.

---

## CLI Internals

The CLI is built with `argparse`. The `dev` command is the most complex:
- It runs a custom `HTTPRequestHandler`.
- It sets up a file watcher.
- It injects a small script into the rendered HTML to handle hot-reloading and event dispatching.

---

## Setup for Development

If you want to modify the Volta framework itself:

1. **Clone the Source**:
   ```bash
   git clone https://github.com/volta-framework/volta.git
   cd volta
   ```

2. **Install in Editable Mode**:
   ```bash
   pip install -e .
   ```

3. **Run Tests**:
   ```bash
   pytest
   ```

4. **Add a Feature**:
   - Create a branch: `git checkout -b feature/my-new-hook`
   - Implement the feature in `volta/`
   - Add tests in `tests/`
   - Update documentation in `docs/`

---

## Coding Standards

- **Type Hinting**: Use Python type hints for all public APIs.
- **Documentation**: All new features must be documented in the `/docs` folder.
- **Tests**: Ensure 100% test coverage for core logic.
- **Clean Code**: Follow PEP 8 guidelines.

---

## Architecture roadmap

Future architectural goals:
- **Partial Hydration**: Sending minimal JavaScript to the client.
- **Isomorphic Fetch**: Uniform data fetching on server and client.
- **Streaming SSR**: Send HTML chunks to the browser as they are ready.
- **WebAssembly Core**: Moving the reconciler to Rust/Wasm for speed.

---

*Thank you for contributing to Volta!*
