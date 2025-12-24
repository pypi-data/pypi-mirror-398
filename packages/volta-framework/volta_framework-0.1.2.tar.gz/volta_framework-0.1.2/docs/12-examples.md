# Examples

## Overview

This document contains complete, working examples of common patterns and use cases in Volta applications.

---

## Table of Contents

1. [Todo App](#todo-app)
2. [Form with Validation](#form-with-validation)
3. [Data Fetching](#data-fetching)
4. [Authentication](#authentication)
5. [Shopping Cart](#shopping-cart)
6. [Dark Mode Toggle](#dark-mode-toggle)
7. [Infinite Scroll](#infinite-scroll)
8. [Modal Component](#modal-component)
9. [Tabs Component](#tabs-component)
10. [Accordion Component](#accordion-component)

---

## Todo App

Complete todo application with add, toggle, delete, and filter functionality.

```python
# app/TodoApp.vpx
from volta import use_state, use_reducer

def todo_reducer(state, action):
    action_type = action["type"]
    
    if action_type == "ADD_TODO":
        new_id = max([t["id"] for t in state["todos"]], default=0) + 1
        new_todo = {
            "id": new_id,
            "text": action["payload"],
            "completed": False
        }
        return {**state, "todos": [*state["todos"], new_todo]}
    
    elif action_type == "TOGGLE_TODO":
        return {
            **state,
            "todos": [
                {**t, "completed": not t["completed"]} if t["id"] == action["payload"] else t
                for t in state["todos"]
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
    state, dispatch = use_reducer(todo_reducer, {
        "todos": [
            {"id": 1, "text": "Learn Volta", "completed": True},
            {"id": 2, "text": "Build an app", "completed": False},
            {"id": 3, "text": "Deploy to production", "completed": False}
        ],
        "filter": "all"
    })
    
    input_text, set_input_text = use_state("")
    
    def add_todo():
        if input_text.strip():
            dispatch({"type": "ADD_TODO", "payload": input_text})
            set_input_text("")
    
    def get_filtered_todos():
        if state["filter"] == "active":
            return [t for t in state["todos"] if not t["completed"]]
        elif state["filter"] == "completed":
            return [t for t in state["todos"] if t["completed"]]
        return state["todos"]
    
    filtered_todos = get_filtered_todos()
    active_count = len([t for t in state["todos"] if not t["completed"]])
    
    return (
        <div className="max-w-md mx-auto mt-10 p-6 bg-white rounded-xl shadow-lg">
            <h1 className="text-2xl font-bold text-gray-800 mb-6">Todo App</h1>
            
            {/* Add Todo */}
            <div className="flex gap-2 mb-6">
                <input 
                    className="flex-1 px-4 py-2 border rounded-lg focus:ring-2 focus:ring-violet-500 outline-none"
                    value={input_text}
                    placeholder="What needs to be done?"
                />
                <button 
                    className="px-6 py-2 bg-violet-600 text-white rounded-lg hover:bg-violet-700"
                    onClick={add_todo}
                >
                    Add
                </button>
            </div>
            
            {/* Filter Tabs */}
            <div className="flex gap-2 mb-4">
                {[
                    <button 
                        key={f}
                        className={f"px-4 py-1 rounded-lg {' bg-violet-600 text-white' if state["filter"] == f else ' bg-gray-100'}"}
                        onClick={lambda: dispatch({"type": "SET_FILTER", "payload": f})}
                    >
                        {f.capitalize()}
                    </button>
                for f in ["all", "active", "completed"]]}
            </div>
            
            {/* Todo List */}
            <ul className="space-y-2 mb-4">
                {[
                    <li 
                        key={todo["id"]}
                        className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg"
                    >
                        <input 
                            type="checkbox"
                            checked={todo["completed"]}
                            onChange={lambda: dispatch({"type": "TOGGLE_TODO", "payload": todo["id"]})}
                            className="w-5 h-5"
                        />
                        <span className={f"flex-1 {' line-through text-gray-400' if todo["completed"] else ''}"}> 
                            {todo["text"]}
                        </span>
                        <button 
                            className="text-red-500 hover:text-red-700"
                            onClick={lambda: dispatch({"type": "DELETE_TODO", "payload": todo["id"]})}
                        >
                            ×
                        </button>
                    </li>
                for todo in filtered_todos]}
            </ul>
            
            {/* Footer */}
            <div className="flex justify-between items-center text-sm text-gray-500">
                <span>{active_count} items left</span>
                <button 
                    className="hover:text-gray-700"
                    onClick={lambda: dispatch({"type": "CLEAR_COMPLETED"})}
                >
                    Clear completed
                </button>
            </div>
        </div>
    )
```

---

## Form with Validation

Complete form with field validation and error display.

```python
# app/ContactForm.vpx
from volta import use_state

def ContactForm():
    # Form state
    form, set_form = use_state({
        "name": "",
        "email": "",
        "phone": "",
        "message": ""
    })
    
    errors, set_errors = use_state({})
    touched, set_touched = use_state({})
    submitted, set_submitted = use_state(False)
    
    # Validation rules
    def validate():
        new_errors = {}
        
        # Name
        if not form["name"].strip():
            new_errors["name"] = "Name is required"
        elif len(form["name"]) < 2:
            new_errors["name"] = "Name must be at least 2 characters"
        
        # Email
        if not form["email"].strip():
            new_errors["email"] = "Email is required"
        elif "@" not in form["email"] or "." not in form["email"]:
            new_errors["email"] = "Please enter a valid email"
        
        # Phone (optional but validate format if provided)
        if form["phone"] and not form["phone"].replace("-", "").replace(" ", "").isdigit():
            new_errors["phone"] = "Please enter a valid phone number"
        
        # Message
        if not form["message"].strip():
            new_errors["message"] = "Message is required"
        elif len(form["message"]) < 10:
            new_errors["message"] = "Message must be at least 10 characters"
        
        set_errors(new_errors)
        return len(new_errors) == 0
    
    def update_field(field, value):
        set_form({**form, field: value})
    
    def touch_field(field):
        set_touched({**touched, field: True})
    
    def handle_submit():
        # Touch all fields to show errors
        set_touched({"name": True, "email": True, "phone": True, "message": True})
        
        if validate():
            print("Form submitted:", form)
            set_submitted(True)
    
    if submitted:
        return (
            <div className="max-w-md mx-auto mt-10 p-6 bg-green-50 rounded-xl text-center">
                <div className="text-4xl mb-4">✓</div>
                <h2 className="text-xl font-bold text-green-800 mb-2">Thank You!</h2>
                <p className="text-green-600">We'll get back to you soon.</p>
                <button 
                    className="mt-4 px-6 py-2 bg-green-600 text-white rounded-lg"
                    onClick={lambda: (set_submitted(False), set_form({"name": "", "email": "", "phone": "", "message": ""}))}
                >
                    Send Another
                </button>
            </div>
        )
    
    return (
        <div className="max-w-md mx-auto mt-10 p-6 bg-white rounded-xl shadow-lg">
            <h1 className="text-2xl font-bold text-gray-800 mb-6">Contact Us</h1>
            
            {/* Name Field */}
            <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                    Name *
                </label>
                <input 
                    className={f"w-full px-4 py-2 border rounded-lg outline-none focus:ring-2 {' border-red-500 focus:ring-red-500' if errors.get("name") and touched.get("name") else ' focus:ring-violet-500'}"}
                    value={form["name"]}
                    onBlur={lambda: touch_field("name")}
                    placeholder="John Doe"
                />
                {errors.get("name") and touched.get("name") and (
                    <p className="text-red-500 text-sm mt-1">{errors["name"]}</p>
                )}
            </div>
            
            {/* Email Field */}
            <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                    Email *
                </label>
                <input 
                    type="email"
                    className={f"w-full px-4 py-2 border rounded-lg outline-none focus:ring-2 {' border-red-500 focus:ring-red-500' if errors.get("email") and touched.get("email") else ' focus:ring-violet-500'}"}
                    value={form["email"]}
                    onBlur={lambda: touch_field("email")}
                    placeholder="john@example.com"
                />
                {errors.get("email") and touched.get("email") and (
                    <p className="text-red-500 text-sm mt-1">{errors["email"]}</p>
                )}
            </div>
            
            {/* Phone Field */}
            <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                    Phone <span className="text-gray-400">(optional)</span>
                </label>
                <input 
                    type="tel"
                    className={f"w-full px-4 py-2 border rounded-lg outline-none focus:ring-2 {' border-red-500 focus:ring-red-500' if errors.get("phone") and touched.get("phone") else ' focus:ring-violet-500'}"}
                    value={form["phone"]}
                    onBlur={lambda: touch_field("phone")}
                    placeholder="555-123-4567"
                />
                {errors.get("phone") and touched.get("phone") and (
                    <p className="text-red-500 text-sm mt-1">{errors["phone"]}</p>
                )}
            </div>
            
            {/* Message Field */}
            <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                    Message *
                </label>
                <textarea 
                    className={f"w-full px-4 py-2 border rounded-lg outline-none focus:ring-2 h-32 resize-none {' border-red-500 focus:ring-red-500' if errors.get("message") and touched.get("message") else ' focus:ring-violet-500'}"}
                    value={form["message"]}
                    onBlur={lambda: touch_field("message")}
                    placeholder="How can we help you?"
                />
                {errors.get("message") and touched.get("message") and (
                    <p className="text-red-500 text-sm mt-1">{errors["message"]}</p>
                )}
            </div>
            
            <button 
                className="w-full py-3 bg-violet-600 text-white font-semibold rounded-lg hover:bg-violet-700 transition-colors"
                onClick={handle_submit}
            >
                Send Message
            </button>
        </div>
    )
```

---

## Data Fetching

Pattern for fetching and displaying data with loading and error states.

```python
# app/UserList.vpx
from volta import use_state, use_effect

def UserList():
    users, set_users = use_state([])
    loading, set_loading = use_state(True)
    error, set_error = use_state(None)
    
    def fetch_users():
        set_loading(True)
        set_error(None)
        
        try:
            # Simulated API response
            data = [
                {"id": 1, "name": "Alice Johnson", "email": "alice@example.com", "role": "Admin"},
                {"id": 2, "name": "Bob Smith", "email": "bob@example.com", "role": "User"},
                {"id": 3, "name": "Carol White", "email": "carol@example.com", "role": "Editor"},
                {"id": 4, "name": "David Brown", "email": "david@example.com", "role": "User"}
            ]
            set_users(data)
        except Exception as e:
            set_error(str(e))
        finally:
            set_loading(False)
    
    use_effect(fetch_users, [])
    
    if loading:
        return (
            <div className="flex items-center justify-center p-10">
                <div className="w-8 h-8 border-4 border-violet-600 border-t-transparent rounded-full animate-spin"></div>
                <span className="ml-3 text-gray-600">Loading users...</span>
            </div>
        )
    
    if error:
        return (
            <div className="max-w-md mx-auto mt-10 p-6 bg-red-50 rounded-xl text-center">
                <div className="text-4xl mb-4">❌</div>
                <h2 className="text-xl font-bold text-red-800 mb-2">Error Loading Data</h2>
                <p className="text-red-600 mb-4">{error}</p>
                <button 
                    className="px-6 py-2 bg-red-600 text-white rounded-lg"
                    onClick={fetch_users}
                >
                    Try Again
                </button>
            </div>
        )
    
    return (
        <div className="max-w-2xl mx-auto mt-10 p-6 bg-white rounded-xl shadow-lg">
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-2xl font-bold text-gray-800">Users</h1>
                <button 
                    className="px-4 py-2 bg-gray-100 rounded-lg hover:bg-gray-200"
                    onClick={fetch_users}
                >
                    🔄 Refresh
                </button>
            </div>
            
            <div className="divide-y">
                {[
                    <div key={user["id"]} className="py-4 flex items-center gap-4">
                        <div className="w-12 h-12 bg-violet-100 rounded-full flex items-center justify-center">
                            <span className="text-violet-600 font-bold">
                                {user["name"][0]}
                            </span>
                        </div>
                        <div className="flex-1">
                            <h3 className="font-semibold text-gray-800">{user["name"]}</h3>
                            <p className="text-sm text-gray-500">{user["email"]}</p>
                        </div>
                        <span className={f"px-3 py-1 text-xs rounded-full {' bg-green-100 text-green-800' if user["role"] == "Admin" else ' bg-gray-100 text-gray-600'}"}>
                            {user["role"]}
                        </span>
                    </div>
                for user in users]}
            </div>
        </div>
    )
```

---

## Authentication

Complete authentication flow with context.

```python
# app/context/AuthContext.py
from volta import create_context, use_context, use_state

AuthContext = create_context(None)

def AuthProvider(**props):
    children = props.get("children")
    
    user, set_user = use_state(None)
    loading, set_loading = use_state(False)
    error, set_error = use_state(None)
    
    def login(email, password):
        set_loading(True)
        set_error(None)
        
        try:
            # Simulate API call
            if email == "admin@example.com" and password == "password":
                set_user({
                    "id": 1,
                    "name": "Admin User",
                    "email": email,
                    "role": "admin"
                })
            else:
                set_error("Invalid email or password")
        except Exception as e:
            set_error(str(e))
        finally:
            set_loading(False)
    
    def logout():
        set_user(None)
    
    def register(name, email, password):
        set_loading(True)
        set_error(None)
        
        try:
            # Simulate registration
            set_user({
                "id": 2,
                "name": name,
                "email": email,
                "role": "user"
            })
        except Exception as e:
            set_error(str(e))
        finally:
            set_loading(False)
    
    value = {
        "user": user,
        "isLoggedIn": user is not None,
        "isAdmin": user and user.get("role") == "admin",
        "loading": loading,
        "error": error,
        "login": login,
        "logout": logout,
        "register": register,
        "clearError": lambda: set_error(None)
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

```python
# app/LoginPage.vpx
from volta import use_state
from app.context.AuthContext import use_auth

def LoginPage():
    auth = use_auth()
    email, set_email = use_state("")
    password, set_password = use_state("")
    
    def handle_login():
        auth["login"](email, password)
    
    if auth["isLoggedIn"]:
        return (
            <div className="max-w-md mx-auto mt-10 p-6 bg-white rounded-xl shadow-lg text-center">
                <div className="w-20 h-20 mx-auto mb-4 bg-violet-100 rounded-full flex items-center justify-center">
                    <span className="text-2xl">{auth["user"]["name"][0]}</span>
                </div>
                <h2 className="text-xl font-bold">{auth["user"]["name"]}</h2>
                <p className="text-gray-500 mb-6">{auth["user"]["email"]}</p>
                <button 
                    className="px-6 py-2 bg-gray-100 rounded-lg hover:bg-gray-200"
                    onClick={auth["logout"]}
                >
                    Sign Out
                </button>
            </div>
        )
    
    return (
        <div className="max-w-md mx-auto mt-10 p-6 bg-white rounded-xl shadow-lg">
            <h1 className="text-2xl font-bold text-center mb-6">Sign In</h1>
            
            {auth["error"] and (
                <div className="mb-4 p-3 bg-red-50 text-red-600 rounded-lg text-sm">
                    {auth["error"]}
                </div>
            )}
            
            <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                <input 
                    type="email"
                    className="w-full px-4 py-2 border rounded-lg"
                    value={email}
                    placeholder="admin@example.com"
                />
            </div>
            
            <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
                <input 
                    type="password"
                    className="w-full px-4 py-2 border rounded-lg"
                    value={password}
                    placeholder="password"
                />
            </div>
            
            <button 
                className="w-full py-3 bg-violet-600 text-white font-semibold rounded-lg disabled:opacity-50"
                onClick={handle_login}
                disabled={auth["loading"]}
            >
                {auth["loading"] and "Signing in..."}
                {not auth["loading"] and "Sign In"}
            </button>
            
            <p className="mt-4 text-center text-sm text-gray-500">
                Test: admin@example.com / password
            </p>
        </div>
    )
```

---

## Shopping Cart

Shopping cart with context and reduce.

```python
# app/ShoppingCart.vpx
from volta import use_state, use_reducer, create_context, use_context

# Cart context and reducer
CartContext = create_context(None)

def cart_reducer(state, action):
    if action["type"] == "ADD_ITEM":
        item = action["payload"]
        existing = next((i for i in state if i["id"] == item["id"]), None)
        
        if existing:
            return [{**i, "quantity": i["quantity"] + 1} if i["id"] == item["id"] else i for i in state]
        else:
            return [*state, {**item, "quantity": 1}]
    
    elif action["type"] == "REMOVE_ITEM":
        return [i for i in state if i["id"] != action["payload"]]
    
    elif action["type"] == "UPDATE_QUANTITY":
        item_id = action["payload"]["id"]
        quantity = action["payload"]["quantity"]
        
        if quantity <= 0:
            return [i for i in state if i["id"] != item_id]
        
        return [{**i, "quantity": quantity} if i["id"] == item_id else i for i in state]
    
    elif action["type"] == "CLEAR_CART":
        return []
    
    return state

def CartProvider(**props):
    children = props.get("children")
    items, dispatch = use_reducer(cart_reducer, [])
    
    total_items = sum(item["quantity"] for item in items)
    total_price = sum(item["price"] * item["quantity"] for item in items)
    
    value = {
        "items": items,
        "totalItems": total_items,
        "totalPrice": total_price,
        "addItem": lambda item: dispatch({"type": "ADD_ITEM", "payload": item}),
        "removeItem": lambda id: dispatch({"type": "REMOVE_ITEM", "payload": id}),
        "updateQuantity": lambda id, qty: dispatch({"type": "UPDATE_QUANTITY", "payload": {"id": id, "quantity": qty}}),
        "clearCart": lambda: dispatch({"type": "CLEAR_CART"})
    }
    
    return (
        <CartContext.Provider value={value}>
            {children}
        </CartContext.Provider>
    )

def use_cart():
    return use_context(CartContext)

# Product Card
def ProductCard(**props):
    product = props.get("product")
    cart = use_cart()
    
    return (
        <div className="bg-white rounded-xl shadow-sm p-4 hover:shadow-md transition-shadow">
            <div className="aspect-square bg-gray-100 rounded-lg mb-4"></div>
            <h3 className="font-semibold text-gray-800">{product["name"]}</h3>
            <p className="text-violet-600 font-bold">${product["price"]:.2f}</p>
            <button 
                className="mt-3 w-full py-2 bg-violet-600 text-white rounded-lg hover:bg-violet-700"
                onClick={lambda: cart["addItem"](product)}
            >
                Add to Cart
            </button>
        </div>
    )

# Cart Sidebar
def CartSidebar():
    cart = use_cart()
    
    return (
        <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-xl font-bold mb-4">Shopping Cart</h2>
            
            {len(cart["items"]) == 0 and (
                <p className="text-gray-500 text-center py-8">Your cart is empty</p>
            )}
            
            <div className="space-y-4">
                {[
                    <div key={item["id"]} className="flex items-center gap-4 pb-4 border-b">
                        <div className="w-16 h-16 bg-gray-100 rounded-lg"></div>
                        <div className="flex-1">
                            <h4 className="font-medium">{item["name"]}</h4>
                            <p className="text-gray-500 text-sm">${item["price"]:.2f}</p>
                        </div>
                        <div className="flex items-center gap-2">
                            <button 
                                className="w-8 h-8 rounded bg-gray-100"
                                onClick={lambda: cart["updateQuantity"](item["id"], item["quantity"] - 1)}
                            >
                                -
                            </button>
                            <span className="w-8 text-center">{item["quantity"]}</span>
                            <button 
                                className="w-8 h-8 rounded bg-gray-100"
                                onClick={lambda: cart["updateQuantity"](item["id"], item["quantity"] + 1)}
                            >
                                +
                            </button>
                        </div>
                    </div>
                for item in cart["items"]]}
            </div>
            
            {len(cart["items"]) > 0 and (
                <div className="mt-6 pt-4 border-t">
                    <div className="flex justify-between mb-4">
                        <span className="font-semibold">Total:</span>
                        <span className="font-bold text-violet-600">${cart["totalPrice"]:.2f}</span>
                    </div>
                    <button className="w-full py-3 bg-violet-600 text-white rounded-lg">
                        Checkout ({cart["totalItems"]} items)
                    </button>
                </div>
            )}
        </div>
    )

# Main Shop
def Shop():
    products = [
        {"id": 1, "name": "Wireless Headphones", "price": 99.99},
        {"id": 2, "name": "Smart Watch", "price": 249.99},
        {"id": 3, "name": "Laptop Stand", "price": 49.99},
        {"id": 4, "name": "USB-C Hub", "price": 79.99}
    ]
    
    return (
        <CartProvider>
            <div className="max-w-6xl mx-auto p-6">
                <h1 className="text-3xl font-bold mb-8">Shop</h1>
                
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    {/* Products */}
                    <div className="lg:col-span-2 grid grid-cols-2 md:grid-cols-3 gap-4">
                        {[<ProductCard product={p} key={p["id"]} /> for p in products]}
                    </div>
                    
                    {/* Cart */}
                    <div>
                        <CartSidebar />
                    </div>
                </div>
            </div>
        </CartProvider>
    )
```

---

## Dark Mode Toggle

Complete dark mode implementation with persistence.

```python
# app/DarkMode.vpx
from volta import create_context, use_context, use_state, use_effect

ThemeContext = create_context(None)

def ThemeProvider(**props):
    children = props.get("children")
    
    # Could load from localStorage in real app
    theme, set_theme = use_state("light")
    
    def toggle():
        set_theme("dark" if theme == "light" else "light")
    
    value = {
        "theme": theme,
        "isDark": theme == "dark",
        "toggle": toggle
    }
    
    wrapper_style = {
        "minHeight": "100vh",
        "backgroundColor": "#111827" if theme == "dark" else "#f9fafb",
        "color": "#f9fafb" if theme == "dark" else "#111827",
        "transition": "background-color 0.3s, color 0.3s"
    }
    
    return (
        <ThemeContext.Provider value={value}>
            <div style={wrapper_style}>
                {children}
            </div>
        </ThemeContext.Provider>
    )

def use_theme():
    return use_context(ThemeContext)

def ThemeToggle():
    theme = use_theme()
    
    button_style = {
        "padding": "0.75rem 1.5rem",
        "borderRadius": "9999px",
        "border": "none",
        "cursor": "pointer",
        "backgroundColor": "#374151" if theme["isDark"] else "#e5e7eb",
        "color": "#f9fafb" if theme["isDark"] else "#111827",
        "display": "flex",
        "alignItems": "center",
        "gap": "0.5rem",
        "fontSize": "1rem"
    }
    
    return (
        <button style={button_style} onClick={theme["toggle"]}>
            {theme["isDark"] and <span>🌙</span>}
            {not theme["isDark"] and <span>☀️</span>}
            {theme["isDark"] and "Dark Mode"}
            {not theme["isDark"] and "Light Mode"}
        </button>
    )

def ThemedCard(**props):
    theme = use_theme()
    
    card_style = {
        "padding": "1.5rem",
        "borderRadius": "12px",
        "backgroundColor": "#1f2937" if theme["isDark"] else "#ffffff",
        "boxShadow": "0 4px 6px rgba(0,0,0,0.3)" if theme["isDark"] else "0 4px 6px rgba(0,0,0,0.1)"
    }
    
    return (
        <div style={card_style}>
            {props.get("children")}
        </div>
    )

def DarkModeDemo():
    return (
        <ThemeProvider>
            <div style={{"padding": "2rem", "maxWidth": "600px", "margin": "0 auto"}}>
                <div style={{"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "2rem"}}>
                    <h1 style={{"fontSize": "2rem", "fontWeight": "bold"}}>Dark Mode Demo</h1>
                    <ThemeToggle />
                </div>
                
                <ThemedCard>
                    <h2 style={{"fontSize": "1.25rem", "fontWeight": "600", "marginBottom": "0.5rem"}}>
                        Welcome!
                    </h2>
                    <p style={{"opacity": "0.7"}}>
                        Click the toggle above to switch between light and dark mode.
                        The theme smoothly transitions between modes.
                    </p>
                </ThemedCard>
            </div>
        </ThemeProvider>
    )
```

---

## Modal Component

Reusable modal with backdrop and close handling.

```python
# app/components/Modal.vpx
from volta import use_state, use_effect

def Modal(**props):
    is_open = props.get("isOpen", False)
    on_close = props.get("onClose")
    title = props.get("title")
    children = props.get("children")
    size = props.get("size", "medium")  # small, medium, large
    
    if not is_open:
        return None
    
    sizes = {
        "small": "400px",
        "medium": "500px",
        "large": "700px"
    }
    
    overlay_style = {
        "position": "fixed",
        "top": "0",
        "left": "0",
        "right": "0",
        "bottom": "0",
        "backgroundColor": "rgba(0, 0, 0, 0.5)",
        "display": "flex",
        "alignItems": "center",
        "justifyContent": "center",
        "zIndex": "50",
        "padding": "1rem"
    }
    
    modal_style = {
        "backgroundColor": "white",
        "borderRadius": "12px",
        "width": "100%",
        "maxWidth": sizes[size],
        "maxHeight": "90vh",
        "overflow": "auto",
        "boxShadow": "0 25px 50px -12px rgba(0, 0, 0, 0.25)"
    }
    
    return (
        <div style={overlay_style} onClick={on_close}>
            <div style={modal_style} onClick={lambda e: e.stopPropagation()}>
                {/* Header */}
                <div style={{
                    "display": "flex",
                    "justifyContent": "space-between",
                    "alignItems": "center",
                    "padding": "1rem 1.5rem",
                    "borderBottom": "1px solid #e5e7eb"
                }}>
                    <h2 style={{"fontSize": "1.25rem", "fontWeight": "600"}}>{title}</h2>
                    <button 
                        style={{
                            "background": "none",
                            "border": "none",
                            "fontSize": "1.5rem",
                            "cursor": "pointer",
                            "color": "#9ca3af"
                        }}
                        onClick={on_close}
                    >
                        ×
                    </button>
                </div>
                
                {/* Body */}
                <div style={{"padding": "1.5rem"}}>
                    {children}
                </div>
            </div>
        </div>
    )

# Usage Example
def ModalDemo():
    is_open, set_is_open = use_state(False)
    
    return (
        <div style={{"padding": "2rem"}}>
            <button 
                style={{
                    "padding": "0.75rem 1.5rem",
                    "backgroundColor": "#8b5cf6",
                    "color": "white",
                    "borderRadius": "8px",
                    "border": "none",
                    "cursor": "pointer"
                }}
                onClick={lambda: set_is_open(True)}
            >
                Open Modal
            </button>
            
            <Modal 
                isOpen={is_open}
                onClose={lambda: set_is_open(False)}
                title="Confirm Action"
            >
                <p style={{"marginBottom": "1.5rem"}}>
                    Are you sure you want to perform this action? This cannot be undone.
                </p>
                <div style={{"display": "flex", "gap": "0.75rem", "justifyContent": "flex-end"}}>
                    <button 
                        style={{
                            "padding": "0.5rem 1rem",
                            "backgroundColor": "#e5e7eb",
                            "borderRadius": "6px",
                            "border": "none",
                            "cursor": "pointer"
                        }}
                        onClick={lambda: set_is_open(False)}
                    >
                        Cancel
                    </button>
                    <button 
                        style={{
                            "padding": "0.5rem 1rem",
                            "backgroundColor": "#ef4444",
                            "color": "white",
                            "borderRadius": "6px",
                            "border": "none",
                            "cursor": "pointer"
                        }}
                        onClick={lambda: set_is_open(False)}
                    >
                        Confirm
                    </button>
                </div>
            </Modal>
        </div>
    )
```

---

## Tabs Component

Reusable tabs component with content panels.

```python
# app/components/Tabs.vpx
from volta import use_state

def Tabs(**props):
    tabs = props.get("tabs", [])  # [{label, content}]
    default_index = props.get("defaultIndex", 0)
    
    active_index, set_active_index = use_state(default_index)
    
    return (
        <div>
            {/* Tab Headers */}
            <div style={{
                "display": "flex",
                "borderBottom": "1px solid #e5e7eb"
            }}>
                {[
                    <button 
                        key={i}
                        style={{
                            "padding": "0.75rem 1.5rem",
                            "border": "none",
                            "background": "none",
                            "cursor": "pointer",
                            "borderBottom": "2px solid #8b5cf6" if i == active_index else "2px solid transparent",
                            "color": "#8b5cf6" if i == active_index else "#6b7280",
                            "fontWeight": "600" if i == active_index else "400"
                        }}
                        onClick={lambda: set_active_index(i)}
                    >
                        {tab["label"]}
                    </button>
                for i, tab in enumerate(tabs)]}
            </div>
            
            {/* Tab Content */}
            <div style={{"padding": "1.5rem"}}>
                {tabs[active_index]["content"]}
            </div>
        </div>
    )

# Usage
def TabsDemo():
    tabs = [
        {
            "label": "Profile",
            "content": (
                <div>
                    <h3 style={{"fontWeight": "bold", "marginBottom": "0.5rem"}}>Profile Settings</h3>
                    <p>Manage your profile information here.</p>
                </div>
            )
        },
        {
            "label": "Account",
            "content": (
                <div>
                    <h3 style={{"fontWeight": "bold", "marginBottom": "0.5rem"}}>Account Settings</h3>
                    <p>Update your password and security settings.</p>
                </div>
            )
        },
        {
            "label": "Notifications",
            "content": (
                <div>
                    <h3 style={{"fontWeight": "bold", "marginBottom": "0.5rem"}}>Notification Preferences</h3>
                    <p>Control how you receive notifications.</p>
                </div>
            )
        }
    ]
    
    return (
        <div style={{"maxWidth": "600px", "margin": "2rem auto", "backgroundColor": "white", "borderRadius": "12px", "boxShadow": "0 4px 6px rgba(0,0,0,0.1)"}}>
            <Tabs tabs={tabs} defaultIndex={0} />
        </div>
    )
```

---

## Accordion Component

Expandable accordion sections.

```python
# app/components/Accordion.vpx
from volta import use_state

def AccordionItem(**props):
    title = props.get("title")
    children = props.get("children")
    is_open = props.get("isOpen", False)
    on_toggle = props.get("onToggle")
    
    header_style = {
        "display": "flex",
        "justifyContent": "space-between",
        "alignItems": "center",
        "padding": "1rem 1.5rem",
        "cursor": "pointer",
        "backgroundColor": "#f9fafb" if is_open else "white",
        "borderBottom": "1px solid #e5e7eb"
    }
    
    content_style = {
        "padding": "1rem 1.5rem" if is_open else "0 1.5rem",
        "maxHeight": "500px" if is_open else "0",
        "overflow": "hidden",
        "transition": "all 0.3s ease"
    }
    
    return (
        <div style={{"borderBottom": "1px solid #e5e7eb"}}>
            <div style={header_style} onClick={on_toggle}>
                <span style={{"fontWeight": "500"}}>{title}</span>
                <span style={{"transform": "rotate(180deg)" if is_open else "rotate(0)", "transition": "transform 0.3s"}}>
                    ▼
                </span>
            </div>
            <div style={content_style}>
                {is_open and (
                    <div style={{"paddingTop": "1rem", "paddingBottom": "1rem"}}>
                        {children}
                    </div>
                )}
            </div>
        </div>
    )

def Accordion(**props):
    items = props.get("items", [])  # [{title, content}]
    allow_multiple = props.get("allowMultiple", False)
    
    open_indices, set_open_indices = use_state([])
    
    def toggle_index(index):
        if allow_multiple:
            if index in open_indices:
                set_open_indices([i for i in open_indices if i != index])
            else:
                set_open_indices([*open_indices, index])
        else:
            if index in open_indices:
                set_open_indices([])
            else:
                set_open_indices([index])
    
    return (
        <div style={{"backgroundColor": "white", "borderRadius": "12px", "overflow": "hidden", "boxShadow": "0 4px 6px rgba(0,0,0,0.1)"}}>
            {[
                <AccordionItem 
                    key={i}
                    title={item["title"]}
                    isOpen={i in open_indices}
                    onToggle={lambda: toggle_index(i)}
                >
                    {item["content"]}
                </AccordionItem>
            for i, item in enumerate(items)]}
        </div>
    )

# Usage
def AccordionDemo():
    faq_items = [
        {
            "title": "What is Volta?",
            "content": "Volta is a Python-based UI framework inspired by React. It brings components, hooks, and JSX-like syntax to Python."
        },
        {
            "title": "How do I install Volta?",
            "content": "Clone the repository and run 'volta init my-app' to create a new project. Then 'volta dev' to start the development server."
        },
        {
            "title": "Can I use Volta in production?",
            "content": "Yes! Volta includes a WSGI application that works with Gunicorn and other production servers. See the deployment guide for details."
        },
        {
            "title": "Does Volta support TypeScript?",
            "content": "Volta uses Python instead of JavaScript/TypeScript. It provides type hints for IDE support and documentation."
        }
    ]
    
    return (
        <div style={{"maxWidth": "600px", "margin": "2rem auto", "padding": "0 1rem"}}>
            <h1 style={{"fontSize": "2rem", "fontWeight": "bold", "marginBottom": "1.5rem"}}>FAQ</h1>
            <Accordion items={faq_items} />
        </div>
    )
```

---

*These examples demonstrate common patterns in Volta applications. Combine and adapt them for your specific needs.*
