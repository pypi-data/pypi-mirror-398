# Styling

## Overview

Volta supports multiple approaches to styling your components, from inline styles to CSS classes and CSS-in-Python patterns.

---

## Table of Contents

1. [Inline Styles](#inline-styles)
2. [CSS Classes](#css-classes)
3. [Tailwind CSS](#tailwind-css)
4. [Dynamic Styling](#dynamic-styling)
5. [Theming](#theming)
6. [CSS Best Practices](#css-best-practices)

---

## Inline Styles

### Basic Inline Styles

Use the `style` prop with a Python dictionary:

```python
def StyledBox():
    return (
        <div style={{
            "backgroundColor": "#8b5cf6",
            "color": "white",
            "padding": "1rem",
            "borderRadius": "8px"
        }}>
            Hello, Styled World!
        </div>
    )
```

### Style Property Naming

Use **camelCase** for style properties (they're automatically converted to kebab-case):

```python
# ✅ Correct - camelCase
style={{
    "backgroundColor": "#333",      # → background-color
    "fontSize": "16px",             # → font-size
    "marginBottom": "1rem",         # → margin-bottom
    "borderTopLeftRadius": "8px",   # → border-top-left-radius
    "boxShadow": "0 2px 4px rgba(0,0,0,0.1)"  # → box-shadow
}}

# ❌ Avoid - kebab-case in Python dict
style={{
    "background-color": "#333",  # Works but not idiomatic
}}
```

### All Style Properties

```python
def CompletelyStyled():
    return (
        <div style={{
            # Layout
            "display": "flex",
            "flexDirection": "column",
            "alignItems": "center",
            "justifyContent": "center",
            
            # Sizing
            "width": "100%",
            "maxWidth": "600px",
            "height": "auto",
            "minHeight": "200px",
            
            # Spacing
            "padding": "1.5rem",
            "margin": "0 auto",
            "gap": "1rem",
            
            # Colors
            "backgroundColor": "#1f2937",
            "color": "#f9fafb",
            
            # Border
            "border": "1px solid #374151",
            "borderRadius": "12px",
            
            # Shadow
            "boxShadow": "0 4px 6px -1px rgba(0, 0, 0, 0.1)",
            
            # Typography
            "fontFamily": "system-ui, sans-serif",
            "fontSize": "1rem",
            "fontWeight": "500",
            "lineHeight": "1.5",
            "textAlign": "center",
            
            # Effects
            "opacity": "1",
            "transition": "all 0.2s ease",
            
            # Positioning
            "position": "relative",
            "zIndex": "10"
        }}>
            Fully styled component
        </div>
    )
```

### Style Objects

Define reusable style objects:

```python
# Define styles
card_style = {
    "backgroundColor": "white",
    "borderRadius": "8px",
    "boxShadow": "0 2px 4px rgba(0,0,0,0.1)",
    "padding": "1.5rem"
}

heading_style = {
    "fontSize": "1.5rem",
    "fontWeight": "bold",
    "marginBottom": "0.5rem"
}

# Use in components
def Card(**props):
    title = props.get("title")
    children = props.get("children")
    
    return (
        <div style={card_style}>
            <h2 style={heading_style}>{title}</h2>
            {children}
        </div>
    )
```

### Merging Styles

```python
def Button(**props):
    variant = props.get("variant", "primary")
    custom_style = props.get("style", {})
    
    base_style = {
        "padding": "0.75rem 1.5rem",
        "borderRadius": "6px",
        "fontWeight": "600",
        "cursor": "pointer",
        "border": "none",
        "transition": "background-color 0.2s"
    }
    
    variant_styles = {
        "primary": {
            "backgroundColor": "#8b5cf6",
            "color": "white"
        },
        "secondary": {
            "backgroundColor": "#e5e7eb",
            "color": "#374151"
        },
        "danger": {
            "backgroundColor": "#ef4444",
            "color": "white"
        }
    }
    
    # Merge: base → variant → custom
    final_style = {
        **base_style,
        **variant_styles.get(variant, {}),
        **custom_style
    }
    
    return (
        <button style={final_style}>
            {props.get("children")}
        </button>
    )

# Usage
<Button variant="primary">Click Me</Button>
<Button variant="danger" style={{"width": "100%"}}>Delete</Button>
```

---

## CSS Classes

### Using className

```python
def Card(**props):
    return (
        <div className="card">
            <h2 className="card-title">{props.get("title")}</h2>
            <p className="card-content">{props.get("content")}</p>
        </div>
    )
```

### Multiple Classes

```python
def Button(**props):
    size = props.get("size", "medium")
    variant = props.get("variant", "primary")
    disabled = props.get("disabled", False)
    
    classes = f"btn btn-{size} btn-{variant}"
    if disabled:
        classes += " btn-disabled"
    
    return (
        <button className={classes} disabled={disabled}>
            {props.get("children")}
        </button>
    )
```

### Conditional Classes

```python
def NavLink(**props):
    is_active = props.get("isActive", False)
    
    base_class = "nav-link"
    active_class = "nav-link--active" if is_active else ""
    
    return (
        <a className={f"{base_class} {active_class}".strip()}>
            {props.get("children")}
        </a>
    )
```

### Class Builder Function

```python
def classnames(*classes, **conditional):
    """Build className string from multiple sources"""
    result = list(classes)
    
    for class_name, condition in conditional.items():
        if condition:
            result.append(class_name)
    
    return " ".join(filter(None, result))

# Usage
def Button(**props):
    is_loading = props.get("loading", False)
    is_disabled = props.get("disabled", False)
    size = props.get("size", "md")
    
    class_name = classnames(
        "btn",
        f"btn-{size}",
        loading=is_loading,
        disabled=is_disabled
    )
    
    return <button className={class_name}>{props.get("children")}</button>
```

---

## Tailwind CSS

Volta includes Tailwind CSS by default via CDN.

### Basic Tailwind Usage

```python
def Card(**props):
    return (
        <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
            <h2 className="text-xl font-bold text-gray-900 mb-2">
                {props.get("title")}
            </h2>
            <p className="text-gray-600">
                {props.get("content")}
            </p>
        </div>
    )
```

### Responsive Design

```python
def ResponsiveGrid():
    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 p-4">
            <Card title="Card 1" content="Content here" />
            <Card title="Card 2" content="Content here" />
            <Card title="Card 3" content="Content here" />
        </div>
    )
```

### Hover & Focus States

```python
def InteractiveButton():
    return (
        <button className="
            px-6 py-3 
            bg-violet-600 
            text-white 
            font-semibold 
            rounded-lg 
            hover:bg-violet-700 
            focus:outline-none 
            focus:ring-2 
            focus:ring-violet-500 
            focus:ring-offset-2 
            active:bg-violet-800 
            transition-colors
            disabled:opacity-50 
            disabled:cursor-not-allowed
        ">
            Click Me
        </button>
    )
```

### Dark Mode

```python
def ThemeAwareCard():
    return (
        <div className="
            bg-white dark:bg-gray-800 
            text-gray-900 dark:text-gray-100
            rounded-lg shadow-md 
            p-6
        ">
            <h2 className="text-xl font-bold mb-2">
                Theme Aware
            </h2>
            <p className="text-gray-600 dark:text-gray-400">
                This card adapts to dark mode
            </p>
        </div>
    )
```

### Flexbox & Grid

```python
# Flexbox
def FlexLayout():
    return (
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex-1">Left</div>
            <div className="flex-shrink-0">Center</div>
            <div className="flex-1 text-right">Right</div>
        </div>
    )

# Grid
def GridLayout():
    items = [1, 2, 3, 4, 5, 6]
    
    return (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {[
                <div 
                    key={item}
                    className="bg-gray-100 p-4 rounded text-center"
                >
                    Item {item}
                </div>
            for item in items]}
        </div>
    )
```

### Complete Tailwind Component

```python
def ProductCard(**props):
    product = props.get("product", {})
    
    return (
        <div className="group bg-white rounded-2xl shadow-sm hover:shadow-xl transition-all duration-300 overflow-hidden">
            {/* Image */}
            <div className="aspect-square overflow-hidden">
                <Image 
                    src={product.get("image", "/placeholder.jpg")}
                    alt={product.get("name", "Product")}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                />
            </div>
            
            {/* Content */}
            <div className="p-4">
                <h3 className="font-semibold text-gray-900 group-hover:text-violet-600 transition-colors">
                    {product.get("name")}
                </h3>
                <p className="text-sm text-gray-500 mt-1 line-clamp-2">
                    {product.get("description")}
                </p>
                <div className="flex items-center justify-between mt-4">
                    <span className="text-xl font-bold text-violet-600">
                        ${product.get("price", 0):.2f}
                    </span>
                    <button className="px-4 py-2 bg-violet-600 text-white text-sm font-medium rounded-lg hover:bg-violet-700 transition-colors">
                        Add to Cart
                    </button>
                </div>
            </div>
        </div>
    )
```

---

## Dynamic Styling

### Style Based on Props

```python
def ProgressBar(**props):
    value = props.get("value", 0)  # 0-100
    color = props.get("color", "#8b5cf6")
    
    container_style = {
        "width": "100%",
        "height": "8px",
        "backgroundColor": "#e5e7eb",
        "borderRadius": "4px",
        "overflow": "hidden"
    }
    
    bar_style = {
        "width": f"{value}%",
        "height": "100%",
        "backgroundColor": color,
        "transition": "width 0.3s ease"
    }
    
    return (
        <div style={container_style}>
            <div style={bar_style}></div>
        </div>
    )
```

### Style Based on State

```python
def ToggleButton():
    is_on, set_is_on = use_state(False)
    
    button_style = {
        "padding": "0.75rem 1.5rem",
        "borderRadius": "9999px",
        "border": "none",
        "cursor": "pointer",
        "fontWeight": "600",
        "transition": "all 0.2s ease",
        "backgroundColor": "#10b981" if is_on else "#6b7280",
        "color": "white",
        "transform": "scale(1.05)" if is_on else "scale(1)"
    }
    
    return (
        <button style={button_style} onClick={lambda: set_is_on(not is_on)}>
            {is_on and "ON"}
            {not is_on and "OFF"}
        </button>
    )
```

### Animation-Ready Styles

```python
def AnimatedCard(**props):
    is_hovered, set_is_hovered = use_state(False)
    
    card_style = {
        "padding": "1.5rem",
        "borderRadius": "12px",
        "backgroundColor": "white",
        "boxShadow": "0 10px 40px rgba(0,0,0,0.15)" if is_hovered else "0 4px 6px rgba(0,0,0,0.1)",
        "transform": "translateY(-4px)" if is_hovered else "translateY(0)",
        "transition": "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)"
    }
    
    return (
        <div 
            style={card_style}
            onMouseEnter={lambda: set_is_hovered(True)}
            onMouseLeave={lambda: set_is_hovered(False)}
        >
            {props.get("children")}
        </div>
    )
```

---

## Theming

### Theme Context

```python
from volta import create_context, use_context, use_state

# Theme definitions
themes = {
    "light": {
        "colors": {
            "background": "#ffffff",
            "surface": "#f9fafb",
            "text": "#111827",
            "textSecondary": "#6b7280",
            "primary": "#8b5cf6",
            "primaryHover": "#7c3aed"
        },
        "shadows": {
            "sm": "0 1px 2px rgba(0,0,0,0.05)",
            "md": "0 4px 6px rgba(0,0,0,0.1)"
        }
    },
    "dark": {
        "colors": {
            "background": "#111827",
            "surface": "#1f2937",
            "text": "#f9fafb",
            "textSecondary": "#9ca3af",
            "primary": "#a78bfa",
            "primaryHover": "#8b5cf6"
        },
        "shadows": {
            "sm": "0 1px 2px rgba(0,0,0,0.3)",
            "md": "0 4px 6px rgba(0,0,0,0.4)"
        }
    }
}

ThemeContext = create_context(None)

def ThemeProvider(**props):
    children = props.get("children")
    initial = props.get("initialTheme", "light")
    
    theme_name, set_theme_name = use_state(initial)
    
    value = {
        "theme": themes[theme_name],
        "themeName": theme_name,
        "setTheme": set_theme_name,
        "toggle": lambda: set_theme_name("dark" if theme_name == "light" else "light")
    }
    
    return (
        <ThemeContext.Provider value={value}>
            <div style={{"backgroundColor": value["theme"]["colors"]["background"]}}>
                {children}
            </div>
        </ThemeContext.Provider>
    )

def use_theme():
    return use_context(ThemeContext)
```

### Using Theme in Components

```python
def ThemedCard(**props):
    ctx = use_theme()
    theme = ctx["theme"]
    
    style = {
        "backgroundColor": theme["colors"]["surface"],
        "color": theme["colors"]["text"],
        "padding": "1.5rem",
        "borderRadius": "8px",
        "boxShadow": theme["shadows"]["md"]
    }
    
    return (
        <div style={style}>
            {props.get("children")}
        </div>
    )

def ThemedButton(**props):
    ctx = use_theme()
    theme = ctx["theme"]
    is_hovered, set_hovered = use_state(False)
    
    style = {
        "backgroundColor": theme["colors"]["primaryHover"] if is_hovered else theme["colors"]["primary"],
        "color": "white",
        "padding": "0.75rem 1.5rem",
        "borderRadius": "6px",
        "border": "none",
        "cursor": "pointer",
        "transition": "background-color 0.2s"
    }
    
    return (
        <button 
            style={style}
            onMouseEnter={lambda: set_hovered(True)}
            onMouseLeave={lambda: set_hovered(False)}
        >
            {props.get("children")}
        </button>
    )

def ThemeToggle():
    ctx = use_theme()
    
    return (
        <button onClick={ctx["toggle"]}>
            {ctx["themeName"] == "light" and "🌙 Dark Mode"}
            {ctx["themeName"] == "dark" and "☀️ Light Mode"}
        </button>
    )
```

---

## CSS Best Practices

### 1. Prefer Utility Classes for Simple Styles

```python
# ✅ Good - Tailwind for simple styling
<div className="p-4 bg-white rounded-lg shadow">

# ❌ Overkill for simple styling
<div style={{
    "padding": "1rem",
    "backgroundColor": "white",
    "borderRadius": "0.5rem",
    "boxShadow": "0 2px 4px rgba(0,0,0,0.1)"
}}>
```

### 2. Use Inline Styles for Dynamic Values

```python
# ✅ Good - dynamic value needs inline style
<div 
    className="progress-bar"
    style={{"width": f"{progress}%"}}
/>

# ❌ Can't do dynamic in Tailwind
<div className="w-{progress}%">  # Doesn't work
```

### 3. Extract Reusable Style Objects

```python
# ✅ Good - reusable styles
BUTTON_STYLES = {
    "base": {
        "padding": "0.75rem 1.5rem",
        "borderRadius": "6px",
        "cursor": "pointer"
    },
    "primary": {
        "backgroundColor": "#8b5cf6",
        "color": "white"
    }
}

def Button(**props):
    return (
        <button style={{**BUTTON_STYLES["base"], **BUTTON_STYLES["primary"]}}>
            {props.get("children")}
        </button>
    )
```

### 4. Keep Styles Close to Components

```python
# ✅ Good - styles defined with component
def Card(**props):
    CARD_STYLE = {
        "backgroundColor": "white",
        "borderRadius": "8px",
        "padding": "1rem"
    }
    
    return <div style={CARD_STYLE}>{props.get("children")}</div>
```

### 5. Use Semantic Class Names

```python
# ✅ Good - descriptive
<div className="product-card product-card--featured">

# ❌ Bad - non-semantic
<div className="div1 box-thing">
```

---

## Next Steps

- [Development](./09-development.md) - Development workflow
- [Deployment](./10-deployment.md) - Going to production
