# Built-in Components

## Overview

Volta provides several built-in components that offer enhanced functionality, accessibility, and best practices out of the box.

---

## Table of Contents

1. [Image](#image) - Optimized image component
2. [Link](#link) - Client-side navigation
3. [Router](#router) - Routing container
4. [Route](#route) - Route definition
5. [Switch](#switch) - Exclusive route matching
6. [Redirect](#redirect) - Programmatic redirects
7. [NotFoundPage](#notfoundpage) - Built-in 404 page

---

## Image

The `Image` component replaces the standard `<img>` tag with enhanced features for accessibility and performance.

### Import

```python
from volta import Image
```

### Basic Usage

```python
def ProductCard():
    return (
        <div className="product">
            <Image 
                src="/products/laptop.jpg" 
                alt="MacBook Pro 16-inch"
            />
            <h3>MacBook Pro</h3>
        </div>
    )
```

### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `src` | string | *required* | Image source URL |
| `alt` | string | *required* | Alternative text for accessibility |
| `loading` | string | `"lazy"` | Loading behavior: `"lazy"` or `"eager"` |
| `width` | string/number | - | Image width |
| `height` | string/number | - | Image height |
| `className` | string | - | CSS class name |
| `style` | dict | - | Inline styles |

### Examples

#### Lazy Loading (Default)

```python
# Images load lazily by default - great for performance
<Image src="/hero.jpg" alt="Hero banner" />
```

#### Eager Loading

```python
# Force immediate loading for above-the-fold images
<Image 
    src="/logo.png" 
    alt="Company Logo" 
    loading="eager"
/>
```

#### With Dimensions

```python
<Image 
    src="/avatar.jpg" 
    alt="User Avatar"
    width={64}
    height={64}
    className="avatar rounded-full"
/>
```

#### Responsive Image

```python
<Image 
    src="/banner.jpg" 
    alt="Banner"
    style={{
        "width": "100%",
        "height": "auto",
        "maxHeight": "400px",
        "objectFit": "cover"
    }}
/>
```

#### Profile Avatar

```python
def UserAvatar(**props):
    user = props.get("user")
    size = props.get("size", 48)
    
    return (
        <Image 
            src={user.get("avatar", "/default-avatar.png")}
            alt={f"{user.get('name', 'User')}'s avatar"}
            width={size}
            height={size}
            className="avatar"
            style={{
                "borderRadius": "50%",
                "objectFit": "cover"
            }}
        />
    )

# Usage
<UserAvatar user={{"name": "John", "avatar": "/john.jpg"}} size={64} />
```

#### Gallery

```python
def ImageGallery(**props):
    images = props.get("images", [])
    
    return (
        <div className="gallery">
            {[
                <div className="gallery-item" key={img["id"]}>
                    <Image 
                        src={img["url"]}
                        alt={img["caption"]}
                        className="gallery-image"
                    />
                    <p className="caption">{img["caption"]}</p>
                </div>
            for img in images]}
        </div>
    )

# Usage
images = [
    {"id": 1, "url": "/photo1.jpg", "caption": "Mountain View"},
    {"id": 2, "url": "/photo2.jpg", "caption": "Beach Sunset"},
    {"id": 3, "url": "/photo3.jpg", "caption": "City Lights"}
]

<ImageGallery images={images} />
```

### Why Use Image Instead of <img>?

```python
# ❌ Raw <img> tag - triggers [Volta Warning]
<img src="/photo.jpg">  # Missing alt, no lazy loading, triggers warning

# ✅ Image component - enforces best practices
<Image src="/photo.jpg" alt="Description" />  # Accessible, lazy-loaded
```

**Benefits:**
- ✅ Enforces `alt` attribute for accessibility
- ✅ Lazy loading by default for performance
- ✅ Consistent API across your app
- ✅ Framework-level optimizations possible

---

## Link

The `Link` component provides client-side navigation without full page reloads.

### Import

```python
from volta import Link
```

### Basic Usage

```python
<Link to="/about">About Us</Link>
```

### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `to` | string | *required* | Destination path |
| `className` | string | - | CSS class name |
| `style` | dict | - | Inline styles |
| `activeClassName` | string | - | Class when link is active |
| `activeStyle` | dict | - | Styles when link is active |
| `target` | string | - | Link target (`"_blank"` for new tab) |
| `onClick` | function | - | Click handler |

### Examples

#### Navigation Bar

```python
def Navbar():
    return (
        <nav className="navbar">
            <Link to="/" className="nav-link">Home</Link>
            <Link to="/products" className="nav-link">Products</Link>
            <Link to="/about" className="nav-link">About</Link>
            <Link to="/contact" className="nav-link">Contact</Link>
        </nav>
    )
```

#### Active State Styling

```python
def Navigation():
    return (
        <nav>
            <Link 
                to="/" 
                className="nav-link"
                activeClassName="nav-link--active"
            >
                Home
            </Link>
            
            <Link 
                to="/about"
                className="nav-link"
                activeStyle={{
                    "color": "#8b5cf6",
                    "fontWeight": "bold"
                }}
            >
                About
            </Link>
        </nav>
    )
```

#### Button-Style Link

```python
<Link 
    to="/signup"
    className="btn btn-primary"
    style={{
        "display": "inline-block",
        "padding": "12px 24px",
        "backgroundColor": "#8b5cf6",
        "color": "white",
        "borderRadius": "8px",
        "textDecoration": "none"
    }}
>
    Sign Up Free
</Link>
```

#### Link with Icon

```python
<Link to="/dashboard" className="icon-link">
    <span className="icon">📊</span>
    <span>Dashboard</span>
</Link>
```

#### Breadcrumb Navigation

```python
def Breadcrumb(**props):
    items = props.get("items", [])
    
    return (
        <nav className="breadcrumb">
            {[
                <span key={i}>
                    {i > 0 and <span className="separator"> / </span>}
                    {i < len(items) - 1 ? (
                        <Link to={item["path"]}>{item["label"]}</Link>
                    ) : (
                        <span className="current">{item["label"]}</span>
                    )}
                </span>
            for i, item in enumerate(items)]}
        </nav>
    )

# Usage
<Breadcrumb items={[
    {"path": "/", "label": "Home"},
    {"path": "/products", "label": "Products"},
    {"path": "/products/electronics", "label": "Electronics"},
    {"label": "Laptops"}  # Current page, no link
]} />
```

### Why Use Link Instead of <a>?

```python
# ❌ Raw <a> tag - triggers [Volta Warning] and full page reload
<a href="/about">About</a>

# ✅ Link component - client-side navigation
<Link to="/about">About</Link>
```

**Benefits:**
- ✅ No full page reload - faster navigation
- ✅ Preserves application state
- ✅ Active state detection built-in
- ✅ Integrates with Router

---

## Router

The `Router` component is the container for all routing logic.

### Import

```python
from volta import Router
```

### Basic Usage

```python
def App():
    return (
        <Router>
            <Navbar />
            <Route path="/" component={HomePage} />
            <Route path="/about" component={AboutPage} />
        </Router>
    )
```

### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `initialPath` | string | `"/"` | Initial route path |
| `children` | elements | - | Route definitions and layout |

### Example with Layout

```python
def App():
    return (
        <Router>
            {/* Layout elements */}
            <Header />
            <Navbar />
            
            {/* Route definitions */}
            <main className="content">
                <Route path="/" component={HomePage} />
                <Route path="/about" component={AboutPage} />
                <Route path="/contact" component={ContactPage} />
            </main>
            
            {/* Footer always visible */}
            <Footer />
        </Router>
    )
```

---

## Route

The `Route` component defines a path-to-component mapping.

### Import

```python
from volta import Route
```

### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `path` | string | *required* | URL path pattern |
| `component` | function | *required* | Component to render |

### Path Patterns

```python
# Static path
<Route path="/" component={Home} />
<Route path="/about" component={About} />

# Dynamic segment
<Route path="/users/:id" component={UserProfile} />
<Route path="/posts/:slug" component={BlogPost} />

# Multiple dynamic segments
<Route path="/users/:userId/posts/:postId" component={UserPost} />

# Catch-all
<Route path="/docs/*" component={DocsPage} />
<Route path="/*" component={NotFoundPage} />
```

### Accessing Parameters

```python
def UserProfile(**props):
    # Dynamic segment passed as prop
    user_id = props.get("id")
    # or
    params = props.get("params", {})
    user_id = params.get("id")
    
    return <h1>User: {user_id}</h1>
```

---

## Switch

The `Switch` component renders only the **first** matching route.

### Import

```python
from volta import Switch
```

### Usage

```python
def App():
    return (
        <Router>
            <Switch>
                <Route path="/" component={HomePage} />
                <Route path="/about" component={AboutPage} />
                <Route path="/users/:id" component={UserProfile} />
                <Route path="/*" component={NotFoundPage} />
            </Switch>
        </Router>
    )
```

### When to Use Switch vs Router

```python
# Router renders ALL matching routes
<Router>
    <Route path="/" component={Home} />         {/* Matches / */}
    <Route path="/about" component={About} />   {/* Matches /about */}
</Router>
# At /about: Only About renders (/ doesn't match /about exactly)

# Switch renders ONLY FIRST matching route
<Switch>
    <Route path="/" component={Home} />
    <Route path="/*" component={NotFound} />  {/* Would never render if above matched */}
</Switch>
```

---

## Redirect

The `Redirect` component immediately navigates to another path.

### Import

```python
from volta import Redirect
```

### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `to` | string | *required* | Destination path |

### Usage

```python
def OldPage():
    # Redirect to new URL
    return <Redirect to="/new-page" />

# In routes
<Route path="/old-url" component={lambda: <Redirect to="/new-url" />} />
```

### Conditional Redirect

```python
def ProtectedPage():
    auth = use_auth()
    
    if not auth["isLoggedIn"]:
        return <Redirect to="/login" />
    
    return (
        <div>
            <h1>Protected Content</h1>
        </div>
    )
```

---

## NotFoundPage

The built-in 404 page component.

### Import

```python
from volta import NotFoundPage
```

### Automatic Rendering

The `NotFoundPage` is automatically rendered when:
1. No routes match the current URL
2. `not_found()` is called programmatically

### Props (when customizing)

| Prop | Type | Description |
|------|------|-------------|
| `error` | string | Custom error message |

### Using the Built-in Page

```python
# Just don't define a catch-all route
def App():
    return (
        <Router>
            <Route path="/" component={HomePage} />
            <Route path="/about" component={AboutPage} />
            {/* No catch-all - built-in 404 will show */}
        </Router>
    )
```

### Custom 404 Page

Override by defining your own catch-all:

```python
def MyNotFound(**props):
    error = props.get("error")
    
    return (
        <div className="my-404">
            <h1>🔍 Page Not Found</h1>
            <p>{error or "We couldn't find that page."}</p>
            <Link to="/">Return Home</Link>
        </div>
    )

def App():
    return (
        <Router>
            <Route path="/" component={HomePage} />
            <Route path="/*" component={MyNotFound} />
        </Router>
    )
```

---

## NavLink

`NavLink` is an alias for `Link` with active state support.

### Import

```python
from volta import NavLink
```

### Usage

```python
<NavLink to="/about" activeClassName="active">
    About
</NavLink>
```

---

## Complete Example

```python
from volta import (
    Router, Route, Link, Switch, Redirect,
    Image, use_state, not_found
)

# Components
def Header():
    return (
        <header className="header">
            <Link to="/" className="logo">
                <Image 
                    src="/logo.png" 
                    alt="My App Logo" 
                    loading="eager"
                    width={40}
                    height={40}
                />
                <span>My App</span>
            </Link>
            <nav>
                <Link to="/" activeClassName="active">Home</Link>
                <Link to="/products" activeClassName="active">Products</Link>
                <Link to="/about" activeClassName="active">About</Link>
            </nav>
        </header>
    )

def HomePage():
    return (
        <div className="home">
            <h1>Welcome</h1>
            <Image 
                src="/hero.jpg" 
                alt="Hero banner"
                className="hero-image"
            />
        </div>
    )

def ProductsPage():
    products = [
        {"id": 1, "name": "Widget", "image": "/widget.jpg"},
        {"id": 2, "name": "Gadget", "image": "/gadget.jpg"}
    ]
    
    return (
        <div className="products">
            <h1>Products</h1>
            <div className="grid">
                {[
                    <Link to={f"/products/{p["id"]}"} key={p["id"]}>
                        <Image src={p["image"]} alt={p["name"]} />
                        <h3>{p["name"]}</h3>
                    </Link>
                for p in products]}
            </div>
        </div>
    )

def ProductDetail(**props):
    product_id = props.get("id")
    
    products = {
        "1": {"name": "Widget", "image": "/widget.jpg", "price": 99},
        "2": {"name": "Gadget", "image": "/gadget.jpg", "price": 149}
    }
    
    product = products.get(product_id)
    
    if not product:
        not_found(f"Product {product_id} not found")
        return None
    
    return (
        <div className="product-detail">
            <Link to="/products">← Back</Link>
            <Image src={product["image"]} alt={product["name"]} />
            <h1>{product["name"]}</h1>
            <p>${product["price"]}</p>
        </div>
    )

def AboutPage():
    return (
        <div className="about">
            <h1>About Us</h1>
            <p>We make great products.</p>
        </div>
    )

# Main App
def App():
    return (
        <Router>
            <Header />
            <main>
                <Route path="/" component={HomePage} />
                <Route path="/products" component={ProductsPage} />
                <Route path="/products/:id" component={ProductDetail} />
                <Route path="/about" component={AboutPage} />
            </main>
        </Router>
    )
```

---

## Next Steps

- [Error Handling](./07-error-handling.md) - Handling errors gracefully
- [Styling](./08-styling.md) - CSS and styling approaches
