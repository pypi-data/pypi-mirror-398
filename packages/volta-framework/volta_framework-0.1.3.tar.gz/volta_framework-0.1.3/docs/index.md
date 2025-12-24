# Volta Framework Documentation

Welcome to the official documentation for the **Volta Framework**. Volta is a modern, high-performance UI framework for Python, bringing the simplicity and power of component-based architecture to the server-side.

---

## Getting Started

- [**Introduction**](./00-introduction.md) - What is Volta? Feature overview and quick start.
- [**Development Workflow**](./09-development.md) - CLI commands, project structure, and debugging.
- [**Deployment Guide**](./10-deployment.md) - Detailed instructions for hosting your Volta apps.

---

## Core Concepts

- [**Components & JSX**](./01-components-jsx.md) - Building UI with functions and JSX-like syntax.
- [**Props & Children**](./02-props-children.md) - Passing data down the component tree.
- [**Hooks API**](./03-hooks.md) - State, effects, and lifecycle management.
- [**Context API**](./04-context.md) - Global state management without prop drilling.

---

## Features

- [**Routing**](./05-routing.md) - Client-side navigation, dynamic routes, and 404 handling.
- [**Built-in Components**](./06-components.md) - Optimized images, navigation links, and more.
- [**Error Handling**](./07-error-handling.md) - Managing 404s and runtime errors gracefully.
- [**Styling**](./08-styling.md) - Inline styles, CSS classes, and Tailwind CSS integration.
- [**Security**](./SECURITY.md) - XSS protection, CSRF, rate limiting, and secure headers.

---

## References & Resources

- [**API Reference**](./11-api-reference.md) - Complete technical reference for all exports.
- [**Examples**](./12-examples.md) - Common patterns and real-world app examples.
- [**Troubleshooting**](./13-troubleshooting.md) - Solutions to common issues.
- [**Contributing**](./14-contributing.md) - Framework architecture and how to help.

---

## Fast Track

If you're already familiar with React, here's the mapping:

| React | Volta |
|-------|-------|
| `useState` | `use_state` |
| `useEffect` | `use_effect` |
| `useContext` | `use_context` |
| `<BrowserRouter>` | `<Router>` |
| `<Link to="...">` | `<Link to="...">` |
| `className` | `className` |
| `style={{...}}` | `style={{...}}` |

---

## Philosophy

Volta is built on the belief that Python developers shouldn't have to switch to JavaScript to build modern, interactive web applications. By combining the power of Python's back-end ecosystem with the intuitive mental model of modern front-end frameworks, Volta provides a seamless development experience for the full stack.

---

*Volta Framework Documentation - Version 1.0.0*
