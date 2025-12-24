# Troubleshooting

## Overview

This guide covers common issues you might encounter while developing with Volta and how to resolve them.

---

## Table of Contents

1. [CLI Issues](#cli-issues)
2. [Transpilation Errors](#transpilation-errors)
3. [Runtime Errors](#runtime-errors)
4. [Routing Issues](#routing-issues)
5. [Hook Errors](#hook-errors)
6. [State & Interactivity](#state--interactivity)
7. [Production Deployment](#production-deployment)

---

## CLI Issues

### Command not found: `volta`

If you receive `bash: volta: command not found` after installation.

**Resolution:**
Ensure `~/.local/bin` (or your installation path) is in your `PATH` environment variable.

```bash
# Add to .bashrc or .zshrc
export PATH="$HOME/.local/bin:$PATH"
```

Then restart your terminal or run `source ~/.zshrc`.

### Port already in use

Error: `[Errno 98] Address already in use`

**Resolution:**
The default port 3000 is occupied. Use a different port:

```bash
volta dev --port 3001
```

Or find and kill the process:
```bash
lsof -i :3000
kill -9 <PID>
```

---

## Transpilation Errors

### Syntax Error in JSX

Error: `SyntaxError: Failed to transpile Volta JSX in YourFile.vpx: Unexpected token`

**Resolution:**
Check your JSX-like syntax:
1. Ensure all tags are closed (`<img />` instead of `<img>`).
2. Don't use Python keywords as prop names (though Volta tries to handle them).
3. Ensure expressions in `{}` are valid Python.
4. Check for nested JSX inside strings which might confuse the parser.

### Python Syntax Error in Compiled File

Error: `SyntaxError: invalid syntax` (pointing to a line in a .py file that looks like h() calls)

**Resolution:**
This usually happens if you have an unclosed parenthesis or bracket in a `{}` expression in your `.vpx` file.
The transpiler passes the expression through as-is, so any Python syntax error inside `{}` will break the resulting file.

---

## Runtime Errors

### Component not rendering

The page is blank, but there are no errors in the console.

**Resolution:**
1. Check if your component actually returns a value.
   ```python
   # ❌ Forgets return
   def MyComponent():
       <div>Title</div>
   
   # ✅ Returns JSX
   def MyComponent():
       return <div>Title</div>
   ```
2. Check if you're importing the component correctly.
3. Check `volta dev` logs on the server for any silent crashes.

### ModuleNotFoundError: No module named 'app'

**Resolution:**
Ensure your project structure follows the recommended layout. If you're importing from `app.App`, ensure there is an `app/` directory with an `__init__.py` file.

---

## Routing Issues

### Page not found (404) for existing route

**Resolution:**
1. Check for typos in the `path` prop of `Route`.
2. Ensure the `Route` is inside a `Router` component.
3. If using dynamic routes, ensure you are accessing params correctly via `props.get("params")`.

### Link doesn't change page

**Resolution:**
1. Ensure you are using the `Link` component from `volta`, not a raw `<a>` tag.
2. Check if the `to` prop matches your route definitions.
3. Check for errors in the browser console.

---

## Hook Errors

### Hooks called outside of component

Error: `Exception: Hooks can only be used inside a Volta component`

**Resolution:**
Ensure you are calling `use_state`, `use_effect`, etc., only inside a function that is being used as a Volta component or another hook. Do not call them in global scope or inside regular utility functions.

### Infinite Effect Loop

The browser hangs or the console logs repeatedly.

**Resolution:**
Check your `use_effect` dependencies. If you trigger a state update inside an effect that depends on that state, it will loop.

```python
# ❌ Infinite loop
def MyComponent():
    count, set_count = use_state(0)
    use_effect(lambda: set_count(count + 1), [count])
```

---

## State & Interactivity

### Event handler not firing

`onClick` or `onChange` doesn't seem to do anything.

**Resolution:**
1. Ensure the handler is a callable function.
2. Check if the component is being re-rendered and losing event attachment.
3. Verify the browser is able to communicate with the server for the event dispatch.

### State not updating

`set_state` is called but the UI doesn't reflect the change.

**Resolution:**
1. Remember that state updates in Volta (like React) are reflected in the *next* render.
2. If you're updating a dict or list, ensure you're creating a *new* copy.
   ```python
   # ❌ Mutation - might not trigger update
   items.append(new_item)
   set_items(items)
   
   # ✅ New copy - triggers update
   set_items([*items, new_item])
   ```

---

## Production Deployment

### Static assets not loading (404)

Images or CSS files return 404 in production.

**Resolution:**
1. Ensure `wsgi.py` is configured to serve static files.
2. Check if `assets/` exists and contains the files.
3. In production, check if your server (Gunicorn) has permissions to read the files.
4. If using Nginx, ensure the `alias` path is correct.

### Server error (500)

**Resolution:**
1. Check the server logs (Gunicorn output).
2. Ensure `requirements.txt` includes all necessary packages.
3. Verify `PYTHONPATH` includes both the framework and the application.
4. Check that `.vpx` files are being correctly transpiled (the `.vpx` loader must be installed in `wsgi.py`).

---

## Getting More Help

If your issue persists:

1. **Check Logs**: Run `volta dev` and watch the terminal output carefully.
2. **Clean Cache**: Run `volta clean` to remove any corrupted compiled files.
3. **Inspect HTML**: Right-click in browser and "Inspect" to see the generated structure and styles.
4. **Minimal Example**: Create the smallest possible code that reproduces the issue.
5. **Community**: Check the GitHub issues or documentation for similar problems.
