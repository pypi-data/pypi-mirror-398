# Context API

## Overview

Context provides a way to pass data through the component tree without having to pass props manually at every level. It's useful for "global" data like themes, authentication, or language preferences.

---

## Table of Contents

1. [Creating Context](#creating-context)
2. [Providing Context](#providing-context)
3. [Consuming Context](#consuming-context)
4. [Multiple Contexts](#multiple-contexts)
5. [Context with Reducers](#context-with-reducers)
6. [Best Practices](#best-practices)

---

## Creating Context

Use `create_context` to create a new context object:

```python
from volta import create_context

# Create with default value
ThemeContext = create_context("light")

# Create with complex default
UserContext = create_context({
    "user": None,
    "isLoggedIn": False
})

# Create with no default
DataContext = create_context(None)
```

---

## Providing Context

Wrap components with a Provider to make the context value available:

```python
from volta import create_context, use_state

# Create context
ThemeContext = create_context("light")

def ThemeProvider(**props):
    children = props.get("children")
    theme, set_theme = use_state("light")
    
    def toggle_theme():
        set_theme("dark" if theme == "light" else "light")
    
    value = {
        "theme": theme,
        "toggleTheme": toggle_theme
    }
    
    return (
        <ThemeContext.Provider value={value}>
            {children}
        </ThemeContext.Provider>
    )

def App():
    return (
        <ThemeProvider>
            <MainContent />
        </ThemeProvider>
    )
```

---

## Consuming Context

Use `use_context` to access context values:

```python
from volta import use_context

def ThemedButton(**props):
    # Get context value
    theme_context = use_context(ThemeContext)
    theme = theme_context["theme"]
    toggle = theme_context["toggleTheme"]
    
    button_class = "btn-light" if theme == "light" else "btn-dark"
    
    return (
        <button className={button_class} onClick={toggle}>
            Toggle Theme (Current: {theme})
        </button>
    )

def ThemedCard(**props):
    children = props.get("children")
    theme_context = use_context(ThemeContext)
    theme = theme_context["theme"]
    
    card_style = {
        "backgroundColor": "#ffffff" if theme == "light" else "#1f2937",
        "color": "#000000" if theme == "light" else "#ffffff",
        "padding": "1rem",
        "borderRadius": "8px"
    }
    
    return (
        <div style={card_style}>
            {children}
        </div>
    )
```

---

## Complete Theme Example

```python
from volta import create_context, use_context, use_state

# 1. Create the context
ThemeContext = create_context(None)

# 2. Create provider component
def ThemeProvider(**props):
    children = props.get("children")
    initial_theme = props.get("initialTheme", "light")
    
    theme, set_theme = use_state(initial_theme)
    
    def toggle_theme():
        set_theme("dark" if theme == "light" else "light")
    
    def set_light():
        set_theme("light")
    
    def set_dark():
        set_theme("dark")
    
    # Context value
    value = {
        "theme": theme,
        "isDark": theme == "dark",
        "isLight": theme == "light",
        "toggle": toggle_theme,
        "setLight": set_light,
        "setDark": set_dark
    }
    
    # Apply theme class to wrapper
    return (
        <ThemeContext.Provider value={value}>
            <div className={f"theme-{theme}"}>
                {children}
            </div>
        </ThemeContext.Provider>
    )

# 3. Create custom hook for easy access
def use_theme():
    context = use_context(ThemeContext)
    if context is None:
        raise Exception("use_theme must be used within ThemeProvider")
    return context

# 4. Use in components
def Header():
    theme = use_theme()
    
    header_style = {
        "backgroundColor": "#1f2937" if theme["isDark"] else "#ffffff",
        "color": "#ffffff" if theme["isDark"] else "#000000",
        "padding": "1rem"
    }
    
    return (
        <header style={header_style}>
            <h1>My App</h1>
            <button onClick={theme["toggle"]}>
                {theme["isDark"] and "🌙"}
                {theme["isLight"] and "☀️"}
            </button>
        </header>
    )

def MainContent():
    theme = use_theme()
    
    content_style = {
        "backgroundColor": "#111827" if theme["isDark"] else "#f3f4f6",
        "color": "#f9fafb" if theme["isDark"] else "#111827",
        "minHeight": "100vh",
        "padding": "2rem"
    }
    
    return (
        <main style={content_style}>
            <h2>Welcome!</h2>
            <p>Current theme: {theme["theme"]}</p>
        </main>
    )

# 5. App with provider
def App():
    return (
        <ThemeProvider initialTheme="dark">
            <Header />
            <MainContent />
        </ThemeProvider>
    )
```

---

## Multiple Contexts

You can nest multiple providers:

```python
from volta import create_context, use_context, use_state

# Create multiple contexts
ThemeContext = create_context(None)
AuthContext = create_context(None)
LanguageContext = create_context(None)

# Providers
def AuthProvider(**props):
    children = props.get("children")
    user, set_user = use_state(None)
    
    def login(username, password):
        # Simulate login
        set_user({"name": username, "email": f"{username}@example.com"})
    
    def logout():
        set_user(None)
    
    return (
        <AuthContext.Provider value={{"user": user, "login": login, "logout": logout}}>
            {children}
        </AuthContext.Provider>
    )

def LanguageProvider(**props):
    children = props.get("children")
    language, set_language = use_state("en")
    
    translations = {
        "en": {"hello": "Hello", "goodbye": "Goodbye"},
        "es": {"hello": "Hola", "goodbye": "Adiós"},
        "fr": {"hello": "Bonjour", "goodbye": "Au revoir"}
    }
    
    def t(key):
        return translations.get(language, {}).get(key, key)
    
    return (
        <LanguageContext.Provider value={{"language": language, "setLanguage": set_language, "t": t}}>
            {children}
        </LanguageContext.Provider>
    )

# Combine all providers
def AppProviders(**props):
    children = props.get("children")
    
    return (
        <ThemeProvider>
            <AuthProvider>
                <LanguageProvider>
                    {children}
                </LanguageProvider>
            </AuthProvider>
        </ThemeProvider>
    )

# Use anywhere in tree
def UserGreeting():
    auth = use_context(AuthContext)
    lang = use_context(LanguageContext)
    theme = use_context(ThemeContext)
    
    if auth["user"]:
        return <p>{lang["t"]("hello")}, {auth["user"]["name"]}!</p>
    else:
        return <p>{lang["t"]("hello")}! Please log in.</p>

# App
def App():
    return (
        <AppProviders>
            <UserGreeting />
        </AppProviders>
    )
```

---

## Context with Reducers

Combine Context with useReducer for complex state management:

```python
from volta import create_context, use_context, use_reducer

# Create context for state and dispatch
CartContext = create_context(None)

# Reducer function
def cart_reducer(state, action):
    if action["type"] == "ADD_ITEM":
        item = action["payload"]
        existing = next((i for i in state["items"] if i["id"] == item["id"]), None)
        
        if existing:
            return {
                **state,
                "items": [
                    {**i, "quantity": i["quantity"] + 1} if i["id"] == item["id"] else i
                    for i in state["items"]
                ]
            }
        else:
            return {
                **state,
                "items": [*state["items"], {**item, "quantity": 1}]
            }
    
    elif action["type"] == "REMOVE_ITEM":
        return {
            **state,
            "items": [i for i in state["items"] if i["id"] != action["payload"]]
        }
    
    elif action["type"] == "UPDATE_QUANTITY":
        item_id = action["payload"]["id"]
        quantity = action["payload"]["quantity"]
        
        if quantity <= 0:
            return {
                **state,
                "items": [i for i in state["items"] if i["id"] != item_id]
            }
        
        return {
            **state,
            "items": [
                {**i, "quantity": quantity} if i["id"] == item_id else i
                for i in state["items"]
            ]
        }
    
    elif action["type"] == "CLEAR_CART":
        return {**state, "items": []}
    
    return state

# Provider component
def CartProvider(**props):
    children = props.get("children")
    
    initial_state = {"items": []}
    state, dispatch = use_reducer(cart_reducer, initial_state)
    
    # Computed values
    total_items = sum(item["quantity"] for item in state["items"])
    total_price = sum(item["price"] * item["quantity"] for item in state["items"])
    
    value = {
        "items": state["items"],
        "totalItems": total_items,
        "totalPrice": total_price,
        "dispatch": dispatch,
        # Convenience methods
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

# Custom hook
def use_cart():
    context = use_context(CartContext)
    if context is None:
        raise Exception("use_cart must be used within CartProvider")
    return context

# Components using cart
def CartIcon():
    cart = use_cart()
    
    return (
        <div className="cart-icon">
            🛒 <span className="badge">{cart["totalItems"]}</span>
        </div>
    )

def ProductCard(**props):
    product = props.get("product")
    cart = use_cart()
    
    def add_to_cart():
        cart["addItem"](product)
    
    return (
        <div className="product-card">
            <h3>{product["name"]}</h3>
            <p>${product["price"]}</p>
            <button onClick={add_to_cart}>Add to Cart</button>
        </div>
    )

def CartSummary():
    cart = use_cart()
    
    return (
        <div className="cart-summary">
            <h2>Shopping Cart</h2>
            {len(cart["items"]) == 0 and <p>Your cart is empty</p>}
            
            {[
                <div className="cart-item" key={item["id"]}>
                    <span>{item["name"]}</span>
                    <span>x{item["quantity"]}</span>
                    <span>${item["price"] * item["quantity"]:.2f}</span>
                    <button onClick={lambda: cart["removeItem"](item["id"])}>Remove</button>
                </div>
            for item in cart["items"]]}
            
            <div className="cart-total">
                <strong>Total: ${cart["totalPrice"]:.2f}</strong>
            </div>
            
            {len(cart["items"]) > 0 and (
                <button onClick={cart["clearCart"]}>Clear Cart</button>
            )}
        </div>
    )

# App
def App():
    products = [
        {"id": 1, "name": "Widget", "price": 9.99},
        {"id": 2, "name": "Gadget", "price": 19.99},
        {"id": 3, "name": "Gizmo", "price": 14.99}
    ]
    
    return (
        <CartProvider>
            <header>
                <h1>Shop</h1>
                <CartIcon />
            </header>
            
            <main>
                <div className="products">
                    {[<ProductCard product={p} key={p["id"]} /> for p in products]}
                </div>
                <CartSummary />
            </main>
        </CartProvider>
    )
```

---

## Best Practices

### 1. Create Custom Hooks for Context

```python
# ✅ Good - Custom hook with error checking
def use_auth():
    context = use_context(AuthContext)
    if context is None:
        raise Exception("use_auth must be used within AuthProvider")
    return context

# Usage
def Profile():
    auth = use_auth()  # Clear and safe
    return <p>{auth["user"]["name"]}</p>
```

### 2. Split Context by Domain

```python
# ✅ Good - Separate contexts
ThemeContext = create_context(None)
AuthContext = create_context(None)
CartContext = create_context(None)

# ❌ Bad - One giant context
AppContext = create_context({
    "theme": "light",
    "user": None,
    "cart": [],
    "language": "en",
    # ... many more
})
```

### 3. Memoize Context Values

```python
def AuthProvider(**props):
    children = props.get("children")
    user, set_user = use_state(None)
    
    # Memoize to prevent unnecessary re-renders
    value = use_memo(
        lambda: {
            "user": user,
            "login": lambda u, p: set_user({"name": u}),
            "logout": lambda: set_user(None)
        },
        [user]
    )
    
    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    )
```

### 4. Keep Providers Close to Usage

```python
# ✅ Good - Provider wraps only what needs it
def ProductsPage():
    return (
        <CartProvider>
            <ProductList />
            <CartSidebar />
        </CartProvider>
    )

# ❌ May be overkill - Provider at root when only one page needs it
def App():
    return (
        <CartProvider>
            <HomePage />      {/* Doesn't need cart */}
            <AboutPage />     {/* Doesn't need cart */}
            <ProductsPage />  {/* Needs cart */}
        </CartProvider>
    )
```

---

## Next Steps

- [Routing](./05-routing.md) - Navigation and dynamic routes
- [Built-in Components](./06-components.md) - Image, Link, etc.
