# Props & Children

## Overview

Props (properties) are how you pass data from parent components to child components. Children are special props that represent nested content.

---

## Table of Contents

1. [Passing Props](#passing-props)
2. [Receiving Props](#receiving-props)
3. [Default Props](#default-props)
4. [Children Props](#children-props)
5. [Spreading Props](#spreading-props)
6. [Prop Types and Validation](#prop-types-and-validation)
7. [Event Handler Props](#event-handler-props)
8. [Render Props Pattern](#render-props-pattern)

---

## Passing Props

### Basic Props

```python
# Parent component
def App():
    return (
        <div>
            <Greeting name="Alice" age={25} />
            <Greeting name="Bob" age={30} />
        </div>
    )

# Child component
def Greeting(**props):
    name = props.get("name")
    age = props.get("age")
    
    return (
        <p>Hello, {name}! You are {age} years old.</p>
    )
```

### Different Prop Types

```python
def Example():
    user = {"name": "John", "email": "john@example.com"}
    items = ["Apple", "Banana", "Cherry"]
    
    return (
        <div>
            {/* String */}
            <Text value="Hello World" />
            
            {/* Number */}
            <Counter initial={10} />
            
            {/* Boolean */}
            <Toggle enabled={True} />
            
            {/* Object/Dict */}
            <UserCard user={user} />
            
            {/* Array/List */}
            <ItemList items={items} />
            
            {/* Function */}
            <Button onClick={handle_click} />
        </div>
    )
```

---

## Receiving Props

### Using **props (Recommended)

```python
def Card(**props):
    title = props.get("title", "Default Title")
    content = props.get("content", "")
    footer = props.get("footer")
    
    return (
        <div className="card">
            <h2>{title}</h2>
            <p>{content}</p>
            {footer and <div className="footer">{footer}</div>}
        </div>
    )
```

### Destructuring Pattern

```python
def UserProfile(name=None, email=None, avatar=None, **kwargs):
    return (
        <div className="profile">
            <img src={avatar or "/default-avatar.png"} alt={name} />
            <h3>{name or "Unknown User"}</h3>
            <p>{email or "No email"}</p>
        </div>
    )
```

### Mixed Approach

```python
def Button(variant="primary", size="medium", **props):
    children = props.get("children")
    on_click = props.get("onClick")
    disabled = props.get("disabled", False)
    
    class_name = f"btn btn-{variant} btn-{size}"
    
    return (
        <button 
            className={class_name} 
            onClick={on_click}
            disabled={disabled}
        >
            {children}
        </button>
    )
```

---

## Default Props

### Using .get() with Defaults

```python
def Alert(**props):
    # Default values
    type_ = props.get("type", "info")  # info, warning, error, success
    title = props.get("title", "Notice")
    message = props.get("message", "")
    dismissible = props.get("dismissible", True)
    
    colors = {
        "info": "blue",
        "warning": "yellow", 
        "error": "red",
        "success": "green"
    }
    
    return (
        <div className={f"alert alert-{colors[type_]}"}>
            <strong>{title}</strong>
            <p>{message}</p>
            {dismissible and <button>✕</button>}
        </div>
    )

# Usage
def App():
    return (
        <div>
            {/* Uses all defaults */}
            <Alert message="This is an info message" />
            
            {/* Override some defaults */}
            <Alert type="error" title="Error!" message="Something went wrong" />
            
            {/* Override all */}
            <Alert 
                type="success" 
                title="Success!" 
                message="Operation completed"
                dismissible={False}
            />
        </div>
    )
```

### Using Function Parameters

```python
def Avatar(
    src="/default-avatar.png",
    alt="User avatar",
    size="medium",
    rounded=True,
    **props
):
    sizes = {
        "small": "32px",
        "medium": "64px",
        "large": "128px"
    }
    
    style = {
        "width": sizes[size],
        "height": sizes[size],
        "borderRadius": "50%" if rounded else "8px"
    }
    
    return (
        <img src={src} alt={alt} style={style} />
    )
```

---

## Children Props

### Basic Children

```python
def Container(**props):
    children = props.get("children")
    
    return (
        <div className="container">
            {children}
        </div>
    )

# Usage
def App():
    return (
        <Container>
            <h1>Title</h1>
            <p>This is content inside the container</p>
        </Container>
    )
```

### Multiple Children

```python
def Layout(**props):
    children = props.get("children", [])
    
    # Ensure children is a list
    if not isinstance(children, list):
        children = [children]
    
    return (
        <div className="layout">
            {children}
        </div>
    )
```

### Named Slots Pattern

```python
def Modal(**props):
    title = props.get("title", "Modal")
    header = props.get("header")
    footer = props.get("footer")
    children = props.get("children")
    on_close = props.get("onClose")
    
    return (
        <div className="modal-overlay">
            <div className="modal">
                <div className="modal-header">
                    {header or <h2>{title}</h2>}
                    <button onClick={on_close}>✕</button>
                </div>
                <div className="modal-body">
                    {children}
                </div>
                {footer and (
                    <div className="modal-footer">
                        {footer}
                    </div>
                )}
            </div>
        </div>
    )

# Usage
def App():
    def close_modal():
        print("Modal closed")
    
    return (
        <Modal 
            title="Confirm Action"
            onClose={close_modal}
            footer={
                <div>
                    <button>Cancel</button>
                    <button>Confirm</button>
                </div>
            }
        >
            <p>Are you sure you want to continue?</p>
        </Modal>
    )
```

---

## Spreading Props

### Pass All Props to Child

```python
def EnhancedButton(**props):
    # Add default styling while preserving all other props
    class_name = props.get("className", "")
    enhanced_class = f"enhanced-btn {class_name}"
    
    # Create new props with overridden className
    new_props = {**props, "className": enhanced_class}
    
    return (
        <button {...new_props}>
            {props.get("children")}
        </button>
    )
```

### Filtering Props

```python
def Input(**props):
    # Separate custom props from DOM props
    label = props.pop("label", None)
    error = props.pop("error", None)
    
    # Pass remaining props to input
    return (
        <div className="form-field">
            {label and <label>{label}</label>}
            <input {...props} />
            {error and <span className="error">{error}</span>}
        </div>
    )

# Usage
def Form():
    return (
        <Input 
            label="Email"
            type="email"
            placeholder="Enter your email"
            error="Invalid email format"
            required={True}
        />
    )
```

---

## Prop Types and Validation

### Manual Validation

```python
def UserCard(**props):
    # Required props
    user = props.get("user")
    if not user:
        raise ValueError("UserCard requires 'user' prop")
    
    if not isinstance(user, dict):
        raise TypeError("'user' must be a dictionary")
    
    # Required user fields
    if "name" not in user:
        raise ValueError("user must have 'name' field")
    
    # Optional with defaults
    show_email = props.get("showEmail", True)
    
    return (
        <div className="user-card">
            <h3>{user["name"]}</h3>
            {show_email and user.get("email") and (
                <p>{user["email"]}</p>
            )}
        </div>
    )
```

### Using Type Hints (Documentation)

```python
def ProductCard(
    product: dict,           # Required: {name, price, image}
    on_add_to_cart=None,     # Optional: callback function
    show_rating: bool=True,  # Optional: show star rating
    **props
):
    """
    Display a product card.
    
    Args:
        product: Dict with keys 'name', 'price', 'image', optionally 'rating'
        on_add_to_cart: Callback when Add to Cart is clicked
        show_rating: Whether to display the rating stars
    """
    name = product.get("name", "Unknown")
    price = product.get("price", 0)
    image = product.get("image", "/placeholder.png")
    rating = product.get("rating", 0)
    
    return (
        <div className="product-card">
            <img src={image} alt={name} />
            <h3>{name}</h3>
            <p>${price:.2f}</p>
            {show_rating and rating > 0 and (
                <div className="rating">{"⭐" * rating}</div>
            )}
            {on_add_to_cart and (
                <button onClick={on_add_to_cart}>Add to Cart</button>
            )}
        </div>
    )
```

---

## Event Handler Props

### Passing Callbacks

```python
def Parent():
    items, set_items = use_state([])
    
    def handle_add(item):
        set_items([*items, item])
    
    def handle_remove(index):
        new_items = [i for idx, i in enumerate(items) if idx != index]
        set_items(new_items)
    
    return (
        <div>
            <AddItemForm onAdd={handle_add} />
            <ItemList items={items} onRemove={handle_remove} />
        </div>
    )

def AddItemForm(**props):
    on_add = props.get("onAdd")
    text, set_text = use_state("")
    
    def handle_submit():
        if text.strip():
            on_add(text)
            set_text("")
    
    return (
        <div>
            <input 
                value={text} 
                onChange={lambda e: set_text(e.target.value)}
            />
            <button onClick={handle_submit}>Add</button>
        </div>
    )

def ItemList(**props):
    items = props.get("items", [])
    on_remove = props.get("onRemove")
    
    return (
        <ul>
            {[
                <li>
                    {item}
                    <button onClick={lambda: on_remove(i)}>Remove</button>
                </li>
            for i, item in enumerate(items)]}
        </ul>
    )
```

### Event Handler Naming Convention

```python
# Convention: on[Event] for props, handle[Event] for handlers

def Form(**props):
    on_submit = props.get("onSubmit")      # Prop from parent
    on_change = props.get("onChange")       # Prop from parent
    
    def handle_submit():                     # Internal handler
        if on_submit:
            on_submit(form_data)
    
    def handle_change(field, value):        # Internal handler
        if on_change:
            on_change(field, value)
    
    return (
        <form onSubmit={handle_submit}>
            {/* ... */}
        </form>
    )
```

---

## Render Props Pattern

### Basic Render Prop

```python
def DataFetcher(**props):
    """Component that fetches data and renders via render prop"""
    url = props.get("url")
    render = props.get("render")
    
    data, set_data = use_state(None)
    loading, set_loading = use_state(True)
    error, set_error = use_state(None)
    
    # Simulate data fetching
    def fetch_data():
        # In real app, use actual HTTP request
        set_loading(True)
        try:
            result = {"name": "John", "age": 30}  # Simulated
            set_data(result)
        except Exception as e:
            set_error(str(e))
        finally:
            set_loading(False)
    
    use_effect(fetch_data, [url])
    
    # Call render prop with state
    return render({
        "data": data,
        "loading": loading,
        "error": error
    })

# Usage
def UserProfile():
    return (
        <DataFetcher 
            url="/api/user"
            render={lambda state: (
                <div>
                    {state["loading"] and <p>Loading...</p>}
                    {state["error"] and <p>Error: {state["error"]}</p>}
                    {state["data"] and (
                        <div>
                            <h2>{state["data"]["name"]}</h2>
                            <p>Age: {state["data"]["age"]}</p>
                        </div>
                    )}
                </div>
            )}
        />
    )
```

---

## Best Practices

### 1. Use Descriptive Prop Names

```python
# ✅ Good
<UserCard 
    userName="John"
    userEmail="john@example.com"
    isVerified={True}
    onProfileClick={handle_click}
/>

# ❌ Bad
<UserCard 
    n="John"
    e="john@example.com"
    v={True}
    c={handle_click}
/>
```

### 2. Provide Sensible Defaults

```python
# ✅ Good - works without props
def Button(variant="primary", size="medium", **props):
    pass

# ❌ Bad - requires all props
def Button(**props):
    variant = props["variant"]  # Crashes if not provided
```

### 3. Document Complex Props

```python
def DataTable(**props):
    """
    A sortable, filterable data table.
    
    Props:
        columns (list): List of column definitions
            - key (str): Data key
            - label (str): Column header
            - sortable (bool): Enable sorting
            - width (str): Column width
        
        data (list): List of row objects
        
        onSort (callable): Called with (column_key, direction)
        
        onRowClick (callable): Called with row data
        
        emptyMessage (str): Shown when no data
    """
    pass
```

---

## Next Steps

- [Hooks](./03-hooks.md) - State management and side effects
- [Context API](./04-context.md) - Sharing state across components
