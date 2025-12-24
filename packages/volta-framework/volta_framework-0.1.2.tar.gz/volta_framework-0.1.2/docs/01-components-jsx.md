# Components & JSX Syntax

## Overview

Volta uses a JSX-like syntax that allows you to write HTML-like code directly in Python. Component files use the `.vpx` extension and are automatically transpiled at runtime.

---

## Table of Contents

1. [Creating Components](#creating-components)
2. [JSX Syntax Rules](#jsx-syntax-rules)
3. [Expressions in JSX](#expressions-in-jsx)
4. [Conditional Rendering](#conditional-rendering)
5. [Lists and Iteration](#lists-and-iteration)
6. [Fragments](#fragments)
7. [Component Composition](#component-composition)

---

## Creating Components

### Basic Component

A component is simply a Python function that returns JSX:

```python
# components/Greeting.vpx
from volta import h

def Greeting():
    return (
        <div>
            <h1>Hello, World!</h1>
        </div>
    )
```

### Component with Logic

```python
from volta import use_state

def Counter():
    count, set_count = use_state(0)
    
    def increment():
        set_count(count + 1)
    
    def decrement():
        set_count(count - 1)
    
    return (
        <div className="counter-container">
            <h2>Counter: {count}</h2>
            <div className="buttons">
                <button onClick={decrement}>-</button>
                <button onClick={increment}>+</button>
            </div>
        </div>
    )
```

---

## JSX Syntax Rules

### 1. Single Root Element

Every component must return a single root element:

```python
# ✅ Correct - single root
def Good():
    return (
        <div>
            <h1>Title</h1>
            <p>Content</p>
        </div>
    )

# ❌ Wrong - multiple roots
def Bad():
    return (
        <h1>Title</h1>
        <p>Content</p>  # Error!
    )
```

### 2. Use `className` Instead of `class`

Since `class` is a reserved Python keyword:

```python
# ✅ Correct
<div className="container">

# ❌ Wrong
<div class="container">  # Python syntax error!
```

### 3. Self-Closing Tags

Empty elements must be self-closing:

```python
# ✅ Correct
<img src="logo.png" alt="Logo" />
<br />
<hr />
<input type="text" />

# ❌ Wrong
<img src="logo.png">  # Missing closing
```

### 4. Attribute Values

Use double quotes for strings, curly braces for expressions:

```python
# String values
<div className="my-class">

# Expression values
<div className={dynamic_class}>

# Python variables
<img src={image_url} alt={image_alt} />

# Inline styles (dict)
<div style={{"color": "red", "fontSize": "16px"}}>
```

---

## Expressions in JSX

### Variables

```python
def UserProfile():
    name = "John Doe"
    age = 30
    
    return (
        <div>
            <h1>{name}</h1>
            <p>Age: {age}</p>
        </div>
    )
```

### Function Calls

```python
def Formatted():
    def format_date(d):
        return d.strftime("%B %d, %Y")
    
    from datetime import datetime
    today = datetime.now()
    
    return (
        <p>Today is {format_date(today)}</p>
    )
```

### Arithmetic Operations

```python
def Calculator():
    a = 10
    b = 5
    
    return (
        <div>
            <p>Sum: {a + b}</p>
            <p>Product: {a * b}</p>
            <p>Division: {a / b}</p>
        </div>
    )
```

### String Interpolation

```python
def Message():
    user = "Alice"
    
    return (
        <p>{"Hello, " + user + "!"}</p>
    )
```

---

## Conditional Rendering

### Using Ternary-like Expressions

```python
def ConditionalGreeting():
    is_logged_in, set_logged_in = use_state(False)
    
    return (
        <div>
            {is_logged_in and <p>Welcome back!</p>}
            {not is_logged_in and <p>Please log in</p>}
        </div>
    )
```

### Using Helper Variables

```python
def UserStatus():
    user, set_user = use_state(None)
    
    if user:
        content = <p>Hello, {user["name"]}!</p>
    else:
        content = <p>Please log in</p>
    
    return (
        <div className="status">
            {content}
        </div>
    )
```

### Complex Conditions

```python
def StatusBadge():
    status = "active"  # active, pending, inactive
    
    def get_badge():
        if status == "active":
            return <span className="badge green">Active</span>
        elif status == "pending":
            return <span className="badge yellow">Pending</span>
        else:
            return <span className="badge red">Inactive</span>
    
    return (
        <div>
            {get_badge()}
        </div>
    )
```

---

## Lists and Iteration

### Basic List Rendering

```python
def FruitList():
    fruits = ["Apple", "Banana", "Cherry", "Date"]
    
    return (
        <ul>
            {[<li>{fruit}</li> for fruit in fruits]}
        </ul>
    )
```

### Rendering Objects

```python
def UserList():
    users = [
        {"id": 1, "name": "Alice", "role": "Admin"},
        {"id": 2, "name": "Bob", "role": "User"},
        {"id": 3, "name": "Carol", "role": "User"}
    ]
    
    return (
        <div className="user-list">
            {[
                <div className="user-card" key={user["id"]}>
                    <h3>{user["name"]}</h3>
                    <p>{user["role"]}</p>
                </div>
            for user in users]}
        </div>
    )
```

### With Index

```python
def NumberedList():
    items = ["First", "Second", "Third"]
    
    return (
        <ol>
            {[
                <li>{i + 1}. {item}</li>
            for i, item in enumerate(items)]}
        </ol>
    )
```

### Filtering Lists

```python
def ActiveUsers():
    users = [
        {"name": "Alice", "active": True},
        {"name": "Bob", "active": False},
        {"name": "Carol", "active": True}
    ]
    
    active_users = [u for u in users if u["active"]]
    
    return (
        <ul>
            {[<li>{user["name"]}</li> for user in active_users]}
        </ul>
    )
```

---

## Fragments

When you need multiple elements without a wrapper:

```python
from volta import fragment

def TableRow():
    return fragment(
        <td>Column 1</td>,
        <td>Column 2</td>,
        <td>Column 3</td>
    )
```

---

## Component Composition

### Nesting Components

```python
def Header():
    return (
        <header className="header">
            <h1>My App</h1>
        </header>
    )

def Footer():
    return (
        <footer className="footer">
            <p>© 2025 My App</p>
        </footer>
    )

def MainContent():
    return (
        <main className="content">
            <p>Welcome to my app!</p>
        </main>
    )

def App():
    return (
        <div className="app">
            <Header />
            <MainContent />
            <Footer />
        </div>
    )
```

### Extracting Reusable Components

```python
# Button component
def Button(**props):
    variant = props.get("variant", "primary")
    children = props.get("children")
    on_click = props.get("onClick")
    
    class_name = f"btn btn-{variant}"
    
    return (
        <button className={class_name} onClick={on_click}>
            {children}
        </button>
    )

# Usage
def App():
    def handle_save():
        print("Saved!")
    
    return (
        <div>
            <Button variant="primary" onClick={handle_save}>
                Save
            </Button>
            <Button variant="secondary">
                Cancel
            </Button>
            <Button variant="danger">
                Delete
            </Button>
        </div>
    )
```

---

## Best Practices

### 1. Keep Components Small

```python
# ✅ Good - focused components
def UserAvatar(**props):
    return <img src={props["src"]} alt={props["name"]} className="avatar" />

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
def NavigationBar():
    pass

def ShoppingCartItem():
    pass

# ❌ Bad
def Nav():
    pass

def Item():
    pass
```

### 3. Separate Logic from Presentation

```python
def ProductCard(**props):
    product = props["product"]
    
    # Logic
    is_on_sale = product["discount"] > 0
    final_price = product["price"] * (1 - product["discount"])
    
    def format_price(p):
        return f"${p:.2f}"
    
    # Presentation
    return (
        <div className="product-card">
            <img src={product["image"]} alt={product["name"]} />
            <h3>{product["name"]}</h3>
            {is_on_sale and (
                <span className="sale-badge">Sale!</span>
            )}
            <p className="price">{format_price(final_price)}</p>
        </div>
    )
```

---

## Next Steps

- [Props & Children](./02-props-children.md) - Learn about passing data
- [Hooks](./03-hooks.md) - Managing state and effects
