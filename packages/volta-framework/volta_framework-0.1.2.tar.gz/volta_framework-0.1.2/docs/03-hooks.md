# Hooks

## Overview

Hooks are special functions that let you "hook into" Volta's state and lifecycle features from functional components. They follow the same patterns as React hooks.

---

## Table of Contents

1. [use_state](#use_state) - Local state management
2. [use_effect](#use_effect) - Side effects and lifecycle
3. [use_ref](#use_ref) - Persistent mutable values
4. [use_memo](#use_memo) - Memoized computations
5. [use_callback](#use_callback) - Memoized callbacks
6. [use_reducer](#use_reducer) - Complex state logic
7. [Rules of Hooks](#rules-of-hooks)
8. [Custom Hooks](#custom-hooks)

---

## use_state

Manages local component state. Returns a tuple of `(current_value, setter_function)`.

### Basic Usage

```python
from volta import use_state

def Counter():
    count, set_count = use_state(0)
    
    def increment():
        set_count(count + 1)
    
    return (
        <div>
            <p>Count: {count}</p>
            <button onClick={increment}>Increment</button>
        </div>
    )
```

### With Different Data Types

```python
def MultipleStates():
    # String
    name, set_name = use_state("")
    
    # Number
    age, set_age = use_state(0)
    
    # Boolean
    is_active, set_is_active = use_state(False)
    
    # List
    items, set_items = use_state([])
    
    # Dict
    user, set_user = use_state({"name": "", "email": ""})
    
    return (
        <div>
            <p>Name: {name}</p>
            <p>Age: {age}</p>
            <p>Active: {str(is_active)}</p>
            <p>Items: {len(items)}</p>
        </div>
    )
```

### Updating State Based on Previous Value

```python
def Counter():
    count, set_count = use_state(0)
    
    def increment():
        # Use current value in update
        set_count(count + 1)
    
    def add_five():
        # Multiple sequential updates
        for _ in range(5):
            set_count(count + 1)  # ⚠️ May not work as expected
    
    return (
        <div>
            <p>{count}</p>
            <button onClick={increment}>+1</button>
            <button onClick={add_five}>+5</button>
        </div>
    )
```

### Updating Objects/Dicts

```python
def UserForm():
    user, set_user = use_state({
        "name": "",
        "email": "",
        "age": 0
    })
    
    def update_name(new_name):
        # Create new object, don't mutate!
        set_user({**user, "name": new_name})
    
    def update_email(new_email):
        set_user({**user, "email": new_email})
    
    def update_field(field, value):
        set_user({**user, field: value})
    
    return (
        <div>
            <input 
                value={user["name"]} 
                onChange={lambda: update_name("New Name")}
                placeholder="Name"
            />
            <input 
                value={user["email"]} 
                onChange={lambda: update_email("email@example.com")}
                placeholder="Email"
            />
        </div>
    )
```

### Updating Arrays/Lists

```python
def TodoList():
    todos, set_todos = use_state([])
    
    def add_todo(text):
        # Append - create new list
        set_todos([*todos, {"id": len(todos), "text": text, "done": False}])
    
    def remove_todo(id):
        # Filter - create new list
        set_todos([t for t in todos if t["id"] != id])
    
    def toggle_todo(id):
        # Map - create new list with modified item
        set_todos([
            {**t, "done": not t["done"]} if t["id"] == id else t
            for t in todos
        ])
    
    def clear_completed():
        set_todos([t for t in todos if not t["done"]])
    
    return (
        <div>
            <ul>
                {[
                    <li key={todo["id"]}>
                        <span 
                            style={{"textDecoration": "line-through" if todo["done"] else "none"}}
                            onClick={lambda: toggle_todo(todo["id"])}
                        >
                            {todo["text"]}
                        </span>
                        <button onClick={lambda: remove_todo(todo["id"])}>×</button>
                    </li>
                for todo in todos]}
            </ul>
        </div>
    )
```

### Lazy Initial State

```python
def ExpensiveComponent():
    # Initial value computed only once
    def compute_initial():
        # Expensive computation
        result = sum(range(10000))
        return result
    
    # Pass function reference, not called value
    value, set_value = use_state(compute_initial)
    
    return <p>{value}</p>
```

---

## use_effect

Performs side effects in function components. Runs after render.

### Basic Usage

```python
from volta import use_state, use_effect

def DataFetcher():
    data, set_data = use_state(None)
    loading, set_loading = use_state(True)
    
    def fetch_data():
        # Side effect: fetch data
        set_loading(True)
        # Simulated fetch
        result = {"name": "John", "age": 30}
        set_data(result)
        set_loading(False)
    
    # Run on mount
    use_effect(fetch_data, [])
    
    if loading:
        return <p>Loading...</p>
    
    return (
        <div>
            <h2>{data["name"]}</h2>
            <p>Age: {data["age"]}</p>
        </div>
    )
```

### Dependency Array

```python
def UserProfile(**props):
    user_id = props.get("userId")
    user, set_user = use_state(None)
    
    def fetch_user():
        # Fetch user by ID
        print(f"Fetching user {user_id}")
        set_user({"id": user_id, "name": f"User {user_id}"})
    
    # Runs when userId changes
    use_effect(fetch_user, [user_id])
    
    return (
        <div>
            {user and <p>{user["name"]}</p>}
        </div>
    )
```

### Effect with Cleanup

```python
def Timer():
    seconds, set_seconds = use_state(0)
    
    def setup_timer():
        # Effect: start interval
        interval_id = set_interval(lambda: set_seconds(seconds + 1), 1000)
        
        # Cleanup: clear interval
        def cleanup():
            clear_interval(interval_id)
        
        return cleanup
    
    use_effect(setup_timer, [])
    
    return <p>Seconds: {seconds}</p>
```

### Different Dependency Scenarios

```python
def EffectExamples(**props):
    value = props.get("value")
    count, set_count = use_state(0)
    
    # 1. Run ONCE on mount (empty deps)
    def on_mount():
        print("Component mounted!")
    use_effect(on_mount, [])
    
    # 2. Run when 'value' prop changes
    def on_value_change():
        print(f"Value changed to: {value}")
    use_effect(on_value_change, [value])
    
    # 3. Run when count OR value changes
    def on_count_or_value():
        print(f"Count: {count}, Value: {value}")
    use_effect(on_count_or_value, [count, value])
    
    # 4. Run on EVERY render (no deps array)
    # ⚠️ Use sparingly!
    def on_every_render():
        print("Rendered!")
    use_effect(on_every_render)
    
    return <p>Count: {count}</p>
```

### Common Use Cases

```python
# 1. Document Title
def PageTitle(**props):
    title = props.get("title", "My App")
    
    def update_title():
        # Would update document.title in browser
        print(f"Setting title: {title}")
    
    use_effect(update_title, [title])
    
    return <h1>{title}</h1>

# 2. Event Listeners
def WindowResize():
    width, set_width = use_state(1024)
    
    def handle_resize():
        def on_resize():
            # Get window width
            set_width(1024)  # Would be window.innerWidth
        
        # Add listener
        # window.addEventListener('resize', on_resize)
        
        # Cleanup
        def cleanup():
            pass  # window.removeEventListener('resize', on_resize)
        
        return cleanup
    
    use_effect(handle_resize, [])
    
    return <p>Window width: {width}px</p>

# 3. Local Storage
def PersistentCounter():
    # Load from storage
    def get_initial():
        # stored = localStorage.getItem('count')
        return 0  # int(stored) if stored else 0
    
    count, set_count = use_state(get_initial)
    
    def save_count():
        # localStorage.setItem('count', str(count))
        print(f"Saved count: {count}")
    
    use_effect(save_count, [count])
    
    return (
        <div>
            <p>{count}</p>
            <button onClick={lambda: set_count(count + 1)}>+</button>
        </div>
    )
```

---

## use_ref

Creates a mutable reference that persists across renders without causing re-renders.

### Basic Usage

```python
from volta import use_ref

def Timer():
    interval_ref = use_ref(None)
    count, set_count = use_state(0)
    
    def start():
        if interval_ref.current is None:
            # Store interval ID
            interval_ref.current = "interval_123"  # Simulated
    
    def stop():
        if interval_ref.current:
            # Clear interval
            interval_ref.current = None
    
    return (
        <div>
            <p>{count}</p>
            <button onClick={start}>Start</button>
            <button onClick={stop}>Stop</button>
        </div>
    )
```

### Storing Previous Value

```python
def Counter():
    count, set_count = use_state(0)
    prev_count_ref = use_ref(None)
    
    def save_previous():
        prev_count_ref.current = count
    
    use_effect(save_previous, [count])
    
    return (
        <div>
            <p>Current: {count}</p>
            <p>Previous: {prev_count_ref.current or "N/A"}</p>
            <button onClick={lambda: set_count(count + 1)}>Increment</button>
        </div>
    )
```

### Tracking Render Count

```python
def RenderCounter():
    render_count = use_ref(0)
    state, set_state = use_state(0)
    
    # Update ref on every render
    render_count.current += 1
    
    return (
        <div>
            <p>State: {state}</p>
            <p>Renders: {render_count.current}</p>
            <button onClick={lambda: set_state(state + 1)}>Update</button>
        </div>
    )
```

---

## use_memo

Memoizes expensive computations. Only recomputes when dependencies change.

### Basic Usage

```python
from volta import use_memo

def ExpensiveList(**props):
    items = props.get("items", [])
    filter_text = props.get("filter", "")
    
    # Only recalculate when items or filter changes
    filtered_items = use_memo(
        lambda: [item for item in items if filter_text.lower() in item.lower()],
        [items, filter_text]
    )
    
    return (
        <ul>
            {[<li>{item}</li> for item in filtered_items]}
        </ul>
    )
```

### Expensive Calculations

```python
def Statistics(**props):
    numbers = props.get("numbers", [])
    
    # Complex calculation - memoized
    stats = use_memo(
        lambda: {
            "sum": sum(numbers),
            "avg": sum(numbers) / len(numbers) if numbers else 0,
            "min": min(numbers) if numbers else 0,
            "max": max(numbers) if numbers else 0,
            "sorted": sorted(numbers)
        },
        [numbers]
    )
    
    return (
        <div>
            <p>Sum: {stats["sum"]}</p>
            <p>Average: {stats["avg"]:.2f}</p>
            <p>Min: {stats["min"]}</p>
            <p>Max: {stats["max"]}</p>
        </div>
    )
```

### Memoizing Objects

```python
def Chart(**props):
    data = props.get("data", [])
    options = props.get("options", {})
    
    # Memoize complex chart configuration
    chart_config = use_memo(
        lambda: {
            "type": options.get("type", "line"),
            "data": {
                "labels": [d["label"] for d in data],
                "values": [d["value"] for d in data]
            },
            "responsive": True,
            "animation": options.get("animate", True)
        },
        [data, options]
    )
    
    return (
        <div className="chart" data-config={str(chart_config)}>
            {/* Chart would render here */}
        </div>
    )
```

---

## use_callback

Memoizes callback functions. Useful for preventing unnecessary re-renders of child components.

### Basic Usage

```python
from volta import use_callback

def ParentComponent():
    count, set_count = use_state(0)
    
    # Memoized callback - same reference unless count changes
    increment = use_callback(
        lambda: set_count(count + 1),
        [count]
    )
    
    return (
        <div>
            <p>{count}</p>
            <ChildButton onClick={increment} />
        </div>
    )

def ChildButton(**props):
    on_click = props.get("onClick")
    print("ChildButton rendered")  # Check if re-rendering
    
    return <button onClick={on_click}>Click me</button>
```

### With Parameters

```python
def ItemList(**props):
    items = props.get("items", [])
    
    # Memoized delete handler
    handle_delete = use_callback(
        lambda item_id: print(f"Deleting {item_id}"),
        []  # No dependencies - stable reference
    )
    
    return (
        <ul>
            {[
                <ListItem 
                    key={item["id"]} 
                    item={item} 
                    onDelete={handle_delete}
                />
            for item in items]}
        </ul>
    )
```

---

## use_reducer

Manages complex state logic with a reducer function. Inspired by Redux.

### Basic Usage

```python
from volta import use_reducer

def reducer(state, action):
    if action["type"] == "INCREMENT":
        return {"count": state["count"] + 1}
    elif action["type"] == "DECREMENT":
        return {"count": state["count"] - 1}
    elif action["type"] == "RESET":
        return {"count": 0}
    elif action["type"] == "SET":
        return {"count": action["payload"]}
    return state

def Counter():
    initial_state = {"count": 0}
    state, dispatch = use_reducer(reducer, initial_state)
    
    return (
        <div>
            <p>Count: {state["count"]}</p>
            <button onClick={lambda: dispatch({"type": "INCREMENT"})}>+</button>
            <button onClick={lambda: dispatch({"type": "DECREMENT"})}>-</button>
            <button onClick={lambda: dispatch({"type": "RESET"})}>Reset</button>
            <button onClick={lambda: dispatch({"type": "SET", "payload": 100})}>
                Set to 100
            </button>
        </div>
    )
```

### Complex State Example: Todo App

```python
def todo_reducer(state, action):
    action_type = action["type"]
    
    if action_type == "ADD_TODO":
        new_todo = {
            "id": len(state["todos"]),
            "text": action["payload"],
            "completed": False
        }
        return {
            **state,
            "todos": [*state["todos"], new_todo]
        }
    
    elif action_type == "TOGGLE_TODO":
        todo_id = action["payload"]
        return {
            **state,
            "todos": [
                {**todo, "completed": not todo["completed"]} 
                if todo["id"] == todo_id else todo
                for todo in state["todos"]
            ]
        }
    
    elif action_type == "DELETE_TODO":
        return {
            **state,
            "todos": [t for t in state["todos"] if t["id"] != action["payload"]]
        }
    
    elif action_type == "SET_FILTER":
        return {**state, "filter": action["payload"]}
    
    elif action_type == "CLEAR_COMPLETED":
        return {
            **state,
            "todos": [t for t in state["todos"] if not t["completed"]]
        }
    
    return state

def TodoApp():
    initial_state = {
        "todos": [],
        "filter": "all"  # all, active, completed
    }
    
    state, dispatch = use_reducer(todo_reducer, initial_state)
    input_text, set_input_text = use_state("")
    
    def add_todo():
        if input_text.strip():
            dispatch({"type": "ADD_TODO", "payload": input_text})
            set_input_text("")
    
    # Filter todos based on current filter
    def get_visible_todos():
        if state["filter"] == "active":
            return [t for t in state["todos"] if not t["completed"]]
        elif state["filter"] == "completed":
            return [t for t in state["todos"] if t["completed"]]
        return state["todos"]
    
    visible_todos = get_visible_todos()
    
    return (
        <div className="todo-app">
            <h1>Todo App</h1>
            
            <div className="add-todo">
                <input 
                    value={input_text}
                    onChange={lambda: set_input_text("new value")}
                    placeholder="What needs to be done?"
                />
                <button onClick={add_todo}>Add</button>
            </div>
            
            <div className="filters">
                <button onClick={lambda: dispatch({"type": "SET_FILTER", "payload": "all"})}>
                    All
                </button>
                <button onClick={lambda: dispatch({"type": "SET_FILTER", "payload": "active"})}>
                    Active
                </button>
                <button onClick={lambda: dispatch({"type": "SET_FILTER", "payload": "completed"})}>
                    Completed
                </button>
            </div>
            
            <ul className="todo-list">
                {[
                    <li 
                        key={todo["id"]}
                        className={"completed" if todo["completed"] else ""}
                    >
                        <span onClick={lambda: dispatch({"type": "TOGGLE_TODO", "payload": todo["id"]})}>
                            {todo["text"]}
                        </span>
                        <button onClick={lambda: dispatch({"type": "DELETE_TODO", "payload": todo["id"]})}>
                            ×
                        </button>
                    </li>
                for todo in visible_todos]}
            </ul>
            
            <button onClick={lambda: dispatch({"type": "CLEAR_COMPLETED"})}>
                Clear Completed
            </button>
        </div>
    )
```

---

## Rules of Hooks

### 1. Only Call Hooks at the Top Level

```python
# ✅ Correct
def Component():
    count, set_count = use_state(0)
    name, set_name = use_state("")
    
    if count > 5:
        # Logic here, not hooks
        pass
    
    return <div>{count}</div>

# ❌ Wrong - conditional hook
def Component():
    count, set_count = use_state(0)
    
    if count > 5:
        name, set_name = use_state("")  # Error!
    
    return <div>{count}</div>
```

### 2. Only Call Hooks from Volta Components

```python
# ✅ Correct - in component
def MyComponent():
    count, set_count = use_state(0)
    return <div>{count}</div>

# ✅ Correct - in custom hook
def use_counter(initial=0):
    count, set_count = use_state(initial)
    return count, set_count

# ❌ Wrong - regular function
def helper_function():
    count, set_count = use_state(0)  # Error!
    return count
```

### 3. Same Order Every Render

```python
# ✅ Correct - consistent order
def Component():
    a, set_a = use_state(0)
    b, set_b = use_state("")
    c, set_c = use_state([])
    return <div />

# ❌ Wrong - conditional changes order
def Component(**props):
    a, set_a = use_state(0)
    
    if props.get("showExtra"):
        b, set_b = use_state("")  # Order changes!
    
    c, set_c = use_state([])
    return <div />
```

---

## Custom Hooks

Create reusable stateful logic.

### Basic Custom Hook

```python
def use_toggle(initial=False):
    """Toggle boolean state"""
    value, set_value = use_state(initial)
    
    def toggle():
        set_value(not value)
    
    def set_true():
        set_value(True)
    
    def set_false():
        set_value(False)
    
    return value, toggle, set_true, set_false

# Usage
def Modal():
    is_open, toggle, open_modal, close_modal = use_toggle(False)
    
    return (
        <div>
            <button onClick={open_modal}>Open Modal</button>
            {is_open and (
                <div className="modal">
                    <p>Modal Content</p>
                    <button onClick={close_modal}>Close</button>
                </div>
            )}
        </div>
    )
```

### use_counter Hook

```python
def use_counter(initial=0, step=1, min_val=None, max_val=None):
    """Counter with bounds"""
    count, set_count = use_state(initial)
    
    def increment():
        new_val = count + step
        if max_val is None or new_val <= max_val:
            set_count(new_val)
    
    def decrement():
        new_val = count - step
        if min_val is None or new_val >= min_val:
            set_count(new_val)
    
    def reset():
        set_count(initial)
    
    def set_value(val):
        if min_val is not None:
            val = max(val, min_val)
        if max_val is not None:
            val = min(val, max_val)
        set_count(val)
    
    return {
        "count": count,
        "increment": increment,
        "decrement": decrement,
        "reset": reset,
        "set": set_value
    }

# Usage
def QuantitySelector():
    counter = use_counter(initial=1, step=1, min_val=1, max_val=99)
    
    return (
        <div className="quantity">
            <button onClick={counter["decrement"]}>-</button>
            <span>{counter["count"]}</span>
            <button onClick={counter["increment"]}>+</button>
        </div>
    )
```

### use_form Hook

```python
def use_form(initial_values):
    """Form state management"""
    values, set_values = use_state(initial_values)
    errors, set_errors = use_state({})
    touched, set_touched = use_state({})
    
    def set_field(name, value):
        set_values({**values, name: value})
    
    def set_error(name, error):
        set_errors({**errors, name: error})
    
    def touch_field(name):
        set_touched({**touched, name: True})
    
    def reset():
        set_values(initial_values)
        set_errors({})
        set_touched({})
    
    def validate(validators):
        new_errors = {}
        for field, validator in validators.items():
            error = validator(values.get(field))
            if error:
                new_errors[field] = error
        set_errors(new_errors)
        return len(new_errors) == 0
    
    return {
        "values": values,
        "errors": errors,
        "touched": touched,
        "setField": set_field,
        "setError": set_error,
        "touchField": touch_field,
        "reset": reset,
        "validate": validate
    }

# Usage
def RegistrationForm():
    form = use_form({
        "name": "",
        "email": "",
        "password": ""
    })
    
    def handle_submit():
        validators = {
            "name": lambda v: "Required" if not v else None,
            "email": lambda v: "Invalid email" if "@" not in v else None,
            "password": lambda v: "Min 8 chars" if len(v) < 8 else None
        }
        
        if form["validate"](validators):
            print("Form submitted:", form["values"])
    
    return (
        <form>
            <input 
                value={form["values"]["name"]}
                onChange={lambda: form["setField"]("name", "new value")}
            />
            {form["errors"].get("name") and (
                <span className="error">{form["errors"]["name"]}</span>
            )}
            
            <button onClick={handle_submit}>Submit</button>
        </form>
    )
```

---

## Next Steps

- [Context API](./04-context.md) - Share state without prop drilling
- [Routing](./05-routing.md) - Navigation and routes
