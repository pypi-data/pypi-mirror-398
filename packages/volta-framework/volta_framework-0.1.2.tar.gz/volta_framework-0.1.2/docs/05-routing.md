# Routing

## Overview

Volta includes a powerful client-side routing system that supports static routes, dynamic routes, nested routes, and programmatic navigation.

---

## Table of Contents

1. [Basic Setup](#basic-setup)
2. [Route Component](#route-component)
3. [Dynamic Routes](#dynamic-routes)
4. [Link Component](#link-component)
5. [Programmatic Navigation](#programmatic-navigation)
6. [Nested Routes](#nested-routes)
7. [Catch-All Routes](#catch-all-routes)
8. [404 Not Found Handling](#404-not-found-handling)
9. [Route Guards](#route-guards)
10. [Active Link Styling](#active-link-styling)

---

## Basic Setup

### Importing Router Components

```python
from volta import Router, Route, Link, use_router
```

### Simple Router Setup

```python
from volta import Router, Route, Link

def HomePage():
    return (
        <div>
            <h1>Home</h1>
            <p>Welcome to my app!</p>
        </div>
    )

def AboutPage():
    return (
        <div>
            <h1>About</h1>
            <p>Learn more about us.</p>
        </div>
    )

def ContactPage():
    return (
        <div>
            <h1>Contact</h1>
            <p>Get in touch!</p>
        </div>
    )

def App():
    return (
        <Router>
            <nav>
                <Link to="/">Home</Link>
                <Link to="/about">About</Link>
                <Link to="/contact">Contact</Link>
            </nav>
            
            <Route path="/" component={HomePage} />
            <Route path="/about" component={AboutPage} />
            <Route path="/contact" component={ContactPage} />
        </Router>
    )
```

---

## Route Component

The `Route` component renders its component when the path matches.

### Basic Route

```python
<Route path="/" component={HomePage} />
<Route path="/about" component={AboutPage} />
```

### Route with Component that Receives Props

```python
def UserPage(**props):
    # Route passes params as props
    params = props.get("params", {})
    user_id = params.get("id")
    
    return <h1>User: {user_id}</h1>

# In App
<Route path="/users/:id" component={UserPage} />
```

---

## Dynamic Routes

Use `:paramName` syntax for dynamic segments.

### Single Parameter

```python
def BlogPost(**props):
    # Access the dynamic parameter
    post_id = props.get("id")  # or props.get("params", {}).get("id")
    
    return (
        <article>
            <h1>Blog Post #{post_id}</h1>
            <p>Loading post {post_id}...</p>
        </article>
    )

def App():
    return (
        <Router>
            <Route path="/blog/:id" component={BlogPost} />
        </Router>
    )

# URLs that match:
# /blog/1 → id = "1"
# /blog/hello-world → id = "hello-world"
# /blog/2024-01-15 → id = "2024-01-15"
```

### Multiple Parameters

```python
def UserPost(**props):
    user_id = props.get("userId")
    post_id = props.get("postId")
    
    return (
        <div>
            <h1>User {user_id}'s Post #{post_id}</h1>
        </div>
    )

<Route path="/users/:userId/posts/:postId" component={UserPost} />

# URLs that match:
# /users/123/posts/456 → userId = "123", postId = "456"
# /users/john/posts/my-first-post → userId = "john", postId = "my-first-post"
```

### Complete Dynamic Route Example

```python
def ProductPage(**props):
    category = props.get("category")
    product_id = props.get("productId")
    
    # Simulate fetching product data
    products = {
        "electronics": {
            "1": {"name": "Laptop", "price": 999},
            "2": {"name": "Phone", "price": 699}
        },
        "clothing": {
            "1": {"name": "T-Shirt", "price": 29},
            "2": {"name": "Jeans", "price": 79}
        }
    }
    
    category_products = products.get(category, {})
    product = category_products.get(product_id)
    
    if not product:
        return <p>Product not found</p>
    
    return (
        <div className="product-page">
            <nav>
                <Link to={f"/{category}"}>← Back to {category}</Link>
            </nav>
            <h1>{product["name"]}</h1>
            <p className="price">${product["price"]}</p>
            <button>Add to Cart</button>
        </div>
    )

<Route path="/:category/:productId" component={ProductPage} />
```

---

## Link Component

The `Link` component provides client-side navigation without full page reloads.

### Basic Link

```python
<Link to="/about">About Us</Link>
<Link to="/contact">Contact</Link>
```

### Link with Styling

```python
<Link 
    to="/products" 
    className="nav-link"
    style={{"color": "blue", "textDecoration": "underline"}}
>
    Products
</Link>
```

### Active State Styling

```python
<Link 
    to="/about"
    className="nav-link"
    activeClassName="nav-link-active"
>
    About
</Link>

<Link 
    to="/contact"
    activeStyle={{"fontWeight": "bold", "color": "#8b5cf6"}}
>
    Contact
</Link>
```

### External Links

For external URLs, use a regular anchor tag:

```python
# Internal navigation - use Link
<Link to="/about">About</Link>

# External link - use anchor
<a href="https://github.com" target="_blank" rel="noopener noreferrer">
    GitHub
</a>
```

---

## Programmatic Navigation

Use the `use_router` hook for programmatic navigation.

### Basic Navigation

```python
from volta import use_router

def LoginButton():
    router = use_router()
    
    def handle_login():
        # Perform login logic
        # ...
        
        # Navigate to dashboard
        router["push"]("/dashboard")
    
    return <button onClick={handle_login}>Login</button>
```

### use_router API

```python
def NavigationExample():
    router = use_router()
    
    # Current path
    current_path = router["path"]  # e.g., "/users/123"
    
    # Navigate methods
    def go_home():
        router["push"]("/")  # Add to history
    
    def go_to_profile():
        router["replace"]("/profile")  # Replace current history entry
    
    return (
        <div>
            <p>Current: {current_path}</p>
            <button onClick={go_home}>Go Home</button>
            <button onClick={go_to_profile}>Profile</button>
        </div>
    )
```

### Navigation with Data

```python
def SearchForm():
    router = use_router()
    query, set_query = use_state("")
    
    def handle_search():
        if query.strip():
            # Navigate to search results
            router["push"](f"/search?q={query}")
    
    return (
        <form>
            <input 
                value={query}
                onChange={lambda: set_query("new value")}
                placeholder="Search..."
            />
            <button onClick={handle_search}>Search</button>
        </form>
    )
```

### Conditional Navigation

```python
def ProtectedPage():
    router = use_router()
    auth = use_auth()  # Custom auth hook
    
    def check_auth():
        if not auth["isLoggedIn"]:
            router["push"]("/login")
    
    use_effect(check_auth, [auth["isLoggedIn"]])
    
    if not auth["isLoggedIn"]:
        return <p>Redirecting...</p>
    
    return <h1>Protected Content</h1>
```

---

## Nested Routes

Create layouts with nested content areas.

### Layout Pattern

```python
def DashboardLayout(**props):
    children = props.get("children")
    
    return (
        <div className="dashboard">
            <aside className="sidebar">
                <Link to="/dashboard">Overview</Link>
                <Link to="/dashboard/analytics">Analytics</Link>
                <Link to="/dashboard/settings">Settings</Link>
            </aside>
            <main className="content">
                {children}
            </main>
        </div>
    )

def DashboardOverview():
    return <h2>Dashboard Overview</h2>

def DashboardAnalytics():
    return <h2>Analytics</h2>

def DashboardSettings():
    return <h2>Settings</h2>

def App():
    return (
        <Router>
            <Route path="/" component={HomePage} />
            
            {/* Dashboard routes */}
            <Route path="/dashboard" component={lambda: (
                <DashboardLayout>
                    <DashboardOverview />
                </DashboardLayout>
            )} />
            <Route path="/dashboard/analytics" component={lambda: (
                <DashboardLayout>
                    <DashboardAnalytics />
                </DashboardLayout>
            )} />
            <Route path="/dashboard/settings" component={lambda: (
                <DashboardLayout>
                    <DashboardSettings />
                </DashboardLayout>
            )} />
        </Router>
    )
```

---

## Catch-All Routes

Use `/*` to match any path under a prefix.

### Basic Catch-All

```python
def DocsPage(**props):
    # params["*"] contains the rest of the path
    path = props.get("*", "")
    
    return (
        <div>
            <h1>Documentation</h1>
            <p>Path: /docs/{path}</p>
        </div>
    )

<Route path="/docs/*" component={DocsPage} />

# Matches:
# /docs → path = ""
# /docs/getting-started → path = "getting-started"
# /docs/api/hooks → path = "api/hooks"
```

### Custom Not Found Page

```python
def CustomNotFound(**props):
    error = props.get("error")
    
    return (
        <div className="not-found">
            <h1>404</h1>
            <h2>Page Not Found</h2>
            {error and <p>{error}</p>}
            <Link to="/">Go Home</Link>
        </div>
    )

<Route path="/*" component={CustomNotFound} />
```

---

## 404 Not Found Handling

Volta provides built-in 404 handling that you can trigger programmatically.

### Using the Built-in 404 Page

If no route matches, Volta automatically shows a styled 404 page.

```python
def App():
    return (
        <Router>
            <Route path="/" component={HomePage} />
            <Route path="/about" component={AboutPage} />
            {/* No catch-all - built-in 404 will show */}
        </Router>
    )
```

### Programmatic 404 Trigger

Use `not_found()` to trigger a 404 from within a component:

```python
from volta import not_found

def BlogPost(**props):
    post_id = props.get("id")
    
    # Simulated database
    posts = {
        "1": {"title": "First Post", "content": "..."},
        "2": {"title": "Second Post", "content": "..."}
    }
    
    post = posts.get(post_id)
    
    # If post doesn't exist, trigger 404
    if not post:
        not_found(f"Blog post '{post_id}' was not found.")
        return None
    
    return (
        <article>
            <h1>{post["title"]}</h1>
            <div>{post["content"]}</div>
        </article>
    )
```

### not_found() with Custom Message

```python
from volta import not_found

def UserProfile(**props):
    user_id = props.get("id")
    
    user = fetch_user(user_id)  # Your data fetching logic
    
    if not user:
        # Custom message shown on 404 page
        not_found(f"User with ID {user_id} does not exist.")
        return None
    
    return <h1>{user["name"]}</h1>

def ProductPage(**props):
    product_id = props.get("id")
    
    product = fetch_product(product_id)
    
    if not product:
        # Different message
        not_found("This product is no longer available.")
        return None
    
    return <h1>{product["name"]}</h1>
```

### Custom 404 Page with User-Defined Route

Override the built-in 404 by defining your own catch-all:

```python
def MyCustom404(**props):
    error = props.get("error")
    router = use_router()
    
    return (
        <div className="custom-404">
            <div className="error-icon">🔍</div>
            <h1>Oops! Page not found</h1>
            <p>{error or "We couldn't find what you're looking for."}</p>
            <div className="actions">
                <Link to="/">Go Home</Link>
                <button onClick={lambda: router["push"](-1)}>Go Back</button>
            </div>
        </div>
    )

def App():
    return (
        <Router>
            <Route path="/" component={HomePage} />
            <Route path="/about" component={AboutPage} />
            
            {/* Your custom 404 - catches all unmatched routes */}
            <Route path="/*" component={MyCustom404} />
        </Router>
    )
```

---

## Route Guards

Protect routes based on conditions like authentication.

### Simple Auth Guard

```python
def PrivateRoute(**props):
    component = props.get("component")
    auth = use_auth()
    router = use_router()
    
    if not auth["isLoggedIn"]:
        # Redirect to login
        def redirect():
            router["push"]("/login")
        use_effect(redirect, [])
        
        return <p>Redirecting to login...</p>
    
    # Render the protected component
    return <component />

# Usage
def App():
    return (
        <Router>
            <Route path="/" component={HomePage} />
            <Route path="/login" component={LoginPage} />
            
            {/* Protected routes */}
            <Route path="/dashboard" component={lambda: (
                <PrivateRoute component={Dashboard} />
            )} />
            <Route path="/profile" component={lambda: (
                <PrivateRoute component={Profile} />
            )} />
        </Router>
    )
```

### Role-Based Access

```python
def RoleGuard(**props):
    required_role = props.get("role")
    component = props.get("component")
    fallback = props.get("fallback")
    
    auth = use_auth()
    user_role = auth["user"]["role"] if auth["user"] else None
    
    if not auth["isLoggedIn"]:
        return <Navigate to="/login" />
    
    if user_role != required_role:
        if fallback:
            return <fallback />
        return <p>Access Denied</p>
    
    return <component />

# Usage
<Route path="/admin" component={lambda: (
    <RoleGuard role="admin" component={AdminPanel} />
)} />

<Route path="/moderator" component={lambda: (
    <RoleGuard 
        role="moderator" 
        component={ModeratorTools}
        fallback={AccessDeniedPage}
    />
)} />
```

---

## Active Link Styling

Style links based on whether they match the current route.

### Using activeClassName

```python
def Navigation():
    return (
        <nav className="main-nav">
            <Link 
                to="/" 
                className="nav-link"
                activeClassName="active"
            >
                Home
            </Link>
            <Link 
                to="/about" 
                className="nav-link"
                activeClassName="active"
            >
                About
            </Link>
            <Link 
                to="/contact" 
                className="nav-link"
                activeClassName="active"
            >
                Contact
            </Link>
        </nav>
    )
```

```css
/* CSS */
.nav-link {
    color: #666;
    text-decoration: none;
    padding: 0.5rem 1rem;
}

.nav-link.active {
    color: #8b5cf6;
    font-weight: bold;
    border-bottom: 2px solid #8b5cf6;
}
```

### Using activeStyle

```python
def Navigation():
    active_style = {
        "color": "#8b5cf6",
        "fontWeight": "bold",
        "borderBottom": "2px solid #8b5cf6"
    }
    
    return (
        <nav>
            <Link to="/" activeStyle={active_style}>Home</Link>
            <Link to="/about" activeStyle={active_style}>About</Link>
        </nav>
    )
```

### Manual Active Check

```python
def Navigation():
    router = use_router()
    current = router["path"]
    
    def link_class(path):
        base = "nav-link"
        if current == path:
            return f"{base} active"
        return base
    
    return (
        <nav>
            <Link to="/" className={link_class("/")}>Home</Link>
            <Link to="/about" className={link_class("/about")}>About</Link>
        </nav>
    )
```

---

## Complete Example

```python
from volta import Router, Route, Link, use_router, use_state, not_found

# Pages
def HomePage():
    return (
        <div className="page home">
            <h1>Welcome to My App</h1>
            <p>Navigate using the links above.</p>
        </div>
    )

def AboutPage():
    return (
        <div className="page about">
            <h1>About Us</h1>
            <p>We build amazing things.</p>
        </div>
    )

def BlogPage():
    posts = [
        {"id": "1", "title": "Getting Started"},
        {"id": "2", "title": "Advanced Topics"},
        {"id": "3", "title": "Best Practices"}
    ]
    
    return (
        <div className="page blog">
            <h1>Blog</h1>
            <ul>
                {[
                    <li key={post["id"]}>
                        <Link to={f"/blog/{post["id"]}"}>
                            {post["title"]}
                        </Link>
                    </li>
                for post in posts]}
            </ul>
        </div>
    )

def BlogPostPage(**props):
    post_id = props.get("id")
    
    posts = {
        "1": {"title": "Getting Started", "content": "Welcome to our first post..."},
        "2": {"title": "Advanced Topics", "content": "Let's dive deeper..."},
        "3": {"title": "Best Practices", "content": "Here are some tips..."}
    }
    
    post = posts.get(post_id)
    
    if not post:
        not_found(f"Blog post '{post_id}' not found.")
        return None
    
    return (
        <div className="page blog-post">
            <Link to="/blog">← Back to Blog</Link>
            <h1>{post["title"]}</h1>
            <p>{post["content"]}</p>
        </div>
    )

# Navigation
def Navbar():
    return (
        <nav className="navbar">
            <div className="logo">My App</div>
            <div className="links">
                <Link to="/" activeClassName="active">Home</Link>
                <Link to="/about" activeClassName="active">About</Link>
                <Link to="/blog" activeClassName="active">Blog</Link>
            </div>
        </nav>
    )

# Main App
def App():
    return (
        <Router>
            <Navbar />
            <main>
                <Route path="/" component={HomePage} />
                <Route path="/about" component={AboutPage} />
                <Route path="/blog" component={BlogPage} />
                <Route path="/blog/:id" component={BlogPostPage} />
            </main>
        </Router>
    )
```

---

## Next Steps

- [Built-in Components](./06-components.md) - Image, Link, and more
- [Error Handling](./07-error-handling.md) - Handling errors gracefully
