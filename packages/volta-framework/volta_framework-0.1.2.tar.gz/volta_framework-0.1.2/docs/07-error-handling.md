# Error Handling

## Overview

Volta provides built-in error handling for 404 (Not Found) scenarios and patterns for handling other types of errors gracefully.

---

## Table of Contents

1. [404 Not Found](#404-not-found)
2. [Programmatic 404 Trigger](#programmatic-404-trigger)
3. [Custom Error Pages](#custom-error-pages)
4. [Error Boundaries](#error-boundaries)
5. [Form Validation Errors](#form-validation-errors)
6. [API Error Handling](#api-error-handling)
7. [Best Practices](#best-practices)

---

## 404 Not Found

### Automatic 404 Handling

When no route matches the current URL, Volta automatically displays a built-in 404 page.

```python
def App():
    return (
        <Router>
            <Route path="/" component={HomePage} />
            <Route path="/about" component={AboutPage} />
            {/* If user visits /xyz, built-in 404 shows */}
        </Router>
    )
```

### Built-in 404 Page Features

The built-in `NotFoundPage` includes:
- Dark theme styling
- Large "404" heading
- "Page Not Found" message
- Custom error message (if provided)
- "Go Home" button

---

## Programmatic 404 Trigger

Use the `not_found()` function to trigger a 404 from within any component.

### Import

```python
from volta import not_found
```

### Basic Usage

```python
from volta import not_found

def UserProfile(**props):
    user_id = props.get("id")
    
    # Simulate database lookup
    users = {
        "1": {"name": "Alice"},
        "2": {"name": "Bob"}
    }
    
    user = users.get(user_id)
    
    if not user:
        not_found()  # Trigger 404
        return None
    
    return <h1>{user["name"]}</h1>
```

### With Custom Message

```python
def BlogPost(**props):
    post_id = props.get("id")
    
    post = get_post_from_database(post_id)
    
    if not post:
        not_found(f"Blog post with ID '{post_id}' was not found.")
        return None
    
    return (
        <article>
            <h1>{post["title"]}</h1>
            <div>{post["content"]}</div>
        </article>
    )
```

### Different Error Messages

```python
def ProductPage(**props):
    product_id = props.get("id")
    
    product = fetch_product(product_id)
    
    if not product:
        not_found("This product doesn't exist or has been removed.")
        return None
    
    if not product["available"]:
        not_found("This product is no longer available for purchase.")
        return None
    
    return <ProductDisplay product={product} />

def UserProfile(**props):
    username = props.get("username")
    
    user = fetch_user_by_username(username)
    
    if not user:
        not_found(f"User @{username} could not be found.")
        return None
    
    if user["private"] and not is_following(user):
        not_found("This profile is private.")
        return None
    
    return <ProfileDisplay user={user} />
```

### Automatic Reset on Navigation

The 404 state automatically clears when the user navigates to a new page:

```python
# User visits /blog/invalid-id
# → not_found("Post not found") triggers
# → 404 page displays

# User clicks "Home" link
# → Navigation to /
# → 404 state automatically clears
# → Home page displays normally
```

---

## Custom Error Pages

### Custom 404 Page

Override the built-in 404 by defining a catch-all route:

```python
def Custom404(**props):
    error = props.get("error")
    
    return (
        <div className="error-page">
            <div className="error-content">
                <span className="error-icon">🔍</span>
                <h1>Page Not Found</h1>
                <p className="error-message">
                    {error or "Sorry, we couldn't find what you're looking for."}
                </p>
                <div className="error-actions">
                    <Link to="/" className="btn btn-primary">
                        Go Home
                    </Link>
                    <Link to="/contact" className="btn btn-secondary">
                        Contact Support
                    </Link>
                </div>
            </div>
        </div>
    )

def App():
    return (
        <Router>
            <Route path="/" component={HomePage} />
            <Route path="/about" component={AboutPage} />
            {/* Your custom 404 - catches unmatched routes */}
            <Route path="/*" component={Custom404} />
        </Router>
    )
```

### Styled 404 Page

```python
def Styled404(**props):
    error = props.get("error")
    
    container_style = {
        "minHeight": "100vh",
        "display": "flex",
        "alignItems": "center",
        "justifyContent": "center",
        "backgroundColor": "#0f172a",
        "color": "white",
        "fontFamily": "system-ui, sans-serif",
        "textAlign": "center",
        "padding": "2rem"
    }
    
    title_style = {
        "fontSize": "10rem",
        "fontWeight": "bold",
        "background": "linear-gradient(135deg, #8b5cf6, #ec4899)",
        "WebkitBackgroundClip": "text",
        "WebkitTextFillColor": "transparent",
        "margin": "0"
    }
    
    return (
        <div style={container_style}>
            <div>
                <h1 style={title_style}>404</h1>
                <h2 style={{"marginBottom": "1rem"}}>Page Not Found</h2>
                <p style={{"color": "rgba(255,255,255,0.6)", "marginBottom": "2rem"}}>
                    {error or "The page you're looking for doesn't exist."}
                </p>
                <Link 
                    to="/"
                    style={{
                        "display": "inline-block",
                        "padding": "1rem 2rem",
                        "backgroundColor": "#8b5cf6",
                        "color": "white",
                        "borderRadius": "0.5rem",
                        "textDecoration": "none"
                    }}
                >
                    Return Home
                </Link>
            </div>
        </div>
    )
```

---

## Error Boundaries

Create components that catch and handle errors gracefully.

### Simple Error Wrapper

```python
def ErrorBoundary(**props):
    children = props.get("children")
    fallback = props.get("fallback")
    has_error, set_has_error = use_state(False)
    error_message, set_error_message = use_state("")
    
    # In a real implementation, you'd catch errors during render
    # This is a simplified pattern
    
    if has_error:
        if fallback:
            return <fallback error={error_message} />
        return (
            <div className="error-boundary">
                <h2>Something went wrong</h2>
                <p>{error_message}</p>
                <button onClick={lambda: set_has_error(False)}>
                    Try Again
                </button>
            </div>
        )
    
    return children

# Usage
def App():
    return (
        <ErrorBoundary fallback={ErrorFallback}>
            <MainContent />
        </ErrorBoundary>
    )
```

### Error Fallback Component

```python
def ErrorFallback(**props):
    error = props.get("error", "An unexpected error occurred")
    on_retry = props.get("onRetry")
    
    return (
        <div className="error-fallback">
            <div className="error-icon">⚠️</div>
            <h2>Oops! Something went wrong</h2>
            <p className="error-message">{error}</p>
            <div className="error-actions">
                {on_retry and (
                    <button onClick={on_retry} className="btn-retry">
                        Try Again
                    </button>
                )}
                <Link to="/" className="btn-home">
                    Go Home
                </Link>
            </div>
        </div>
    )
```

---

## Form Validation Errors

### Basic Form Validation

```python
def ContactForm():
    name, set_name = use_state("")
    email, set_email = use_state("")
    message, set_message = use_state("")
    errors, set_errors = use_state({})
    
    def validate():
        new_errors = {}
        
        if not name.strip():
            new_errors["name"] = "Name is required"
        
        if not email.strip():
            new_errors["email"] = "Email is required"
        elif "@" not in email:
            new_errors["email"] = "Please enter a valid email"
        
        if not message.strip():
            new_errors["message"] = "Message is required"
        elif len(message) < 10:
            new_errors["message"] = "Message must be at least 10 characters"
        
        set_errors(new_errors)
        return len(new_errors) == 0
    
    def handle_submit():
        if validate():
            # Submit form
            print("Form submitted!")
    
    return (
        <form className="contact-form">
            <div className="field">
                <label>Name</label>
                <input 
                    value={name}
                    onChange={lambda: set_name("new value")}
                    className={"error" if errors.get("name") else ""}
                />
                {errors.get("name") and (
                    <span className="error-text">{errors["name"]}</span>
                )}
            </div>
            
            <div className="field">
                <label>Email</label>
                <input 
                    type="email"
                    value={email}
                    onChange={lambda: set_email("new value")}
                    className={"error" if errors.get("email") else ""}
                />
                {errors.get("email") and (
                    <span className="error-text">{errors["email"]}</span>
                )}
            </div>
            
            <div className="field">
                <label>Message</label>
                <textarea 
                    value={message}
                    onChange={lambda: set_message("new value")}
                    className={"error" if errors.get("message") else ""}
                />
                {errors.get("message") and (
                    <span className="error-text">{errors["message"]}</span>
                )}
            </div>
            
            <button type="button" onClick={handle_submit}>
                Send Message
            </button>
        </form>
    )
```

### Reusable Form Field with Error

```python
def FormField(**props):
    label = props.get("label")
    name = props.get("name")
    value = props.get("value", "")
    error = props.get("error")
    type_ = props.get("type", "text")
    on_change = props.get("onChange")
    required = props.get("required", False)
    
    return (
        <div className={f"form-field {" has-error" if error else ""}"}>
            <label htmlFor={name}>
                {label}
                {required and <span className="required">*</span>}
            </label>
            <input 
                id={name}
                name={name}
                type={type_}
                value={value}
                onChange={on_change}
                className={"input-error" if error else ""}
            />
            {error and (
                <span className="field-error" role="alert">
                    {error}
                </span>
            )}
        </div>
    )

# Usage
<FormField 
    label="Email"
    name="email"
    type="email"
    value={email}
    error={errors.get("email")}
    onChange={handle_email_change}
    required={True}
/>
```

---

## API Error Handling

### Handling Fetch Errors

```python
def UserList():
    users, set_users = use_state([])
    loading, set_loading = use_state(True)
    error, set_error = use_state(None)
    
    def fetch_users():
        set_loading(True)
        set_error(None)
        
        try:
            # Simulated API call
            response = {"ok": True, "data": [{"id": 1, "name": "Alice"}]}
            
            if not response["ok"]:
                raise Exception("Failed to fetch users")
            
            set_users(response["data"])
        except Exception as e:
            set_error(str(e))
        finally:
            set_loading(False)
    
    use_effect(fetch_users, [])
    
    if loading:
        return <LoadingSpinner />
    
    if error:
        return (
            <div className="error-state">
                <p>Error: {error}</p>
                <button onClick={fetch_users}>Retry</button>
            </div>
        )
    
    return (
        <ul>
            {[<li key={user["id"]}>{user["name"]}</li> for user in users]}
        </ul>
    )
```

### Custom Hook for API Calls

```python
def use_fetch(url):
    """Custom hook for fetching data with error handling"""
    data, set_data = use_state(None)
    loading, set_loading = use_state(True)
    error, set_error = use_state(None)
    
    def do_fetch():
        set_loading(True)
        set_error(None)
        
        try:
            # Simulate fetch
            result = {"name": "Test"}  # Would be actual fetch
            set_data(result)
        except Exception as e:
            set_error(str(e))
        finally:
            set_loading(False)
    
    def refetch():
        do_fetch()
    
    use_effect(do_fetch, [url])
    
    return {
        "data": data,
        "loading": loading,
        "error": error,
        "refetch": refetch
    }

# Usage
def UserProfile(**props):
    user_id = props.get("id")
    result = use_fetch(f"/api/users/{user_id}")
    
    if result["loading"]:
        return <p>Loading...</p>
    
    if result["error"]:
        return (
            <div>
                <p>Error: {result["error"]}</p>
                <button onClick={result["refetch"]}>Retry</button>
            </div>
        )
    
    user = result["data"]
    return <h1>{user["name"]}</h1>
```

### Error States Pattern

```python
def DataDisplay(**props):
    url = props.get("url")
    
    data, set_data = use_state(None)
    status, set_status = use_state("idle")  # idle, loading, success, error
    error_message, set_error = use_state("")
    
    def load_data():
        set_status("loading")
        
        try:
            result = fetch_data(url)
            set_data(result)
            set_status("success")
        except Exception as e:
            set_error(str(e))
            set_status("error")
    
    use_effect(load_data, [url])
    
    # Render based on status
    if status == "idle":
        return <p>Ready to load</p>
    
    if status == "loading":
        return (
            <div className="loading">
                <Spinner />
                <p>Loading...</p>
            </div>
        )
    
    if status == "error":
        return (
            <div className="error">
                <span className="icon">❌</span>
                <h3>Failed to Load</h3>
                <p>{error_message}</p>
                <button onClick={load_data}>Try Again</button>
            </div>
        )
    
    # status == "success"
    return (
        <div className="data">
            {/* Render data */}
        </div>
    )
```

---

## Best Practices

### 1. Always Handle Loading and Error States

```python
# ✅ Good
def UserProfile():
    user, loading, error = use_user_data()
    
    if (loading) return <Spinner />
    if (error) return <ErrorMessage error={error} />
    
    return <ProfileDisplay user={user} />

# ❌ Bad - no error/loading handling
def UserProfile():
    user = use_user_data()
    return <ProfileDisplay user={user} />  # Crashes if user is None
```

### 2. Provide Actionable Error Messages

```python
# ✅ Good - tells user what to do
not_found("This product has been discontinued. Browse similar items.")

# ❌ Bad - generic message
not_found("Error 404")
```

### 3. Include Retry Actions

```python
# ✅ Good
<div className="error">
    <p>Failed to load data</p>
    <button onClick={retry}>Try Again</button>
</div>
```

### 4. Log Errors for Debugging

```python
def fetch_data():
    try:
        # API call
        pass
    except Exception as e:
        # Log for debugging
        print(f"[Error] Failed to fetch: {e}")
        
        # Show user-friendly message
        set_error("Unable to load data. Please try again later.")
```

### 5. Graceful Degradation

```python
def UserAvatar(**props):
    user = props.get("user", {})
    
    # Fallback if image fails
    avatar_url = user.get("avatar") or "/default-avatar.png"
    name = user.get("name") or "User"
    
    return (
        <Image 
            src={avatar_url}
            alt={f"{name}'s avatar"}
        />
    )
```

---

## Next Steps

- [Styling](./08-styling.md) - CSS and styling approaches
- [Development](./09-development.md) - Development workflow
