# Volta Security Guide

Volta is built with security as a top priority. This guide covers all the security features and best practices for building secure applications with Volta.

## 🛡️ Security Features Overview

| Feature | Description | Enabled By Default |
|---------|-------------|-------------------|
| XSS Protection | HTML/attribute escaping | ✅ Yes |
| CSRF Protection | Token-based request forgery prevention | ✅ Yes |
| Rate Limiting | Prevent DoS and brute force attacks | ✅ Yes |
| Path Traversal Protection | Prevent directory traversal attacks | ✅ Yes |
| Security Headers | CSP, X-Frame-Options, etc. | ✅ Yes |
| Secure Handler IDs | HMAC-signed event handler tokens | ✅ Yes |
| Error Sanitization | Hide internal errors in production | ✅ Yes |

---

## 🔐 XSS Prevention

All text content rendered by Volta is **automatically escaped** to prevent Cross-Site Scripting (XSS) attacks.

### Automatic Escaping

```python
from volta import h

def UserProfile(name):
    # This is SAFE - name is automatically escaped
    return <div className="profile">{name}</div>

# If name = "<script>alert('xss')</script>"
# Output: <div class="profile">&lt;script&gt;alert('xss')&lt;/script&gt;</div>
```

### Manual Escaping

For cases where you need explicit control:

```python
from volta import escape, escape_attr, escape_url

# Escape HTML content
safe_text = escape("<script>alert(1)</script>")
# Result: "&lt;script&gt;alert(1)&lt;/script&gt;"

# Escape attribute values
safe_attr = escape_attr('value" onclick="bad')
# Result: 'value&quot; onclick=&quot;bad'

# Sanitize URLs (blocks javascript: and data: schemes)
safe_url = escape_url("javascript:alert(1)")
# Result: "#blocked"
```

### URL Sanitization

All URL attributes (`href`, `src`, `action`, etc.) are automatically sanitized:

```python
# BLOCKED - dangerous URLs are replaced with #blocked
<a href="javascript:alert(1)">Click</a>  # href="#blocked"
<img src="data:text/html,<script>..." /> # src="#blocked"

# ALLOWED - safe URLs pass through
<a href="https://example.com">Safe Link</a>
<img src="/images/photo.jpg" />
```

---

## 🎫 CSRF Protection

Volta includes built-in Cross-Site Request Forgery protection.

### Automatic CSRF Tokens

In production builds, a CSRF meta tag is automatically added to every page:

```html
<meta name="csrf-token" content="abc123...">
```

### Using CSRF Tokens in Forms

```python
from volta import CSRFProtection

def ContactForm():
    csrf_field = CSRFProtection.get_token_html()
    
    return (
        <form method="POST" action="/submit">
            {csrf_field}  <!-- Hidden input with CSRF token -->
            <input type="text" name="message" />
            <button type="submit">Send</button>
        </form>
    )
```

### Validating CSRF Tokens

```python
from volta import CSRFProtection

def handle_form_submission(request):
    token = request.form.get('_csrf_token')
    
    if not CSRFProtection.validate_token(token):
        return "Invalid CSRF token", 403
    
    # Process the form...
```

---

## ⏱️ Rate Limiting

Built-in rate limiting prevents DoS attacks and brute force attempts.

### Default Configuration

- **100 requests** per **60 seconds** per IP
- **Burst capacity**: 20 requests
- Automatically returns `429 Too Many Requests` when exceeded

### Custom Configuration

Set environment variables to customize:

```bash
# Increase rate limit for high-traffic apps
export VOLTA_RATE_LIMIT_REQUESTS=500
export VOLTA_RATE_LIMIT_WINDOW=60
export VOLTA_RATE_LIMIT_BURST=50
```

### Disable Rate Limiting (Not Recommended)

```python
from volta import SecurityConfig

SecurityConfig.RATE_LIMIT_ENABLED = False
```

---

## 📁 Path Traversal Protection

Static file serving is protected against directory traversal attacks.

### Blocked Patterns

```
/../../etc/passwd  → BLOCKED
/%2e%2e/etc/passwd → BLOCKED (URL-encoded)
/..%5c..%5cetc/passwd → BLOCKED (backslash encoded)
```

### Allowed Extensions

Only these file types are served as static files:

- `.html`, `.css`, `.js`, `.json`
- `.png`, `.jpg`, `.jpeg`, `.gif`, `.svg`, `.ico`
- `.woff`, `.woff2`
- `.webmanifest`, `.txt`, `.xml`

---

## 🔒 Security Headers

Every response includes these security headers:

```http
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), microphone=(), camera=()
Content-Security-Policy: default-src 'self'; ...
```

### Content Security Policy (CSP)

The default CSP policy:

```
default-src 'self';
script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net;
style-src 'self' 'unsafe-inline' https://fonts.googleapis.com;
img-src 'self' data: https:;
font-src 'self' https://fonts.gstatic.com;
connect-src 'self';
frame-ancestors 'none';
base-uri 'self';
form-action 'self';
```

---

## 🔑 Secure Handler IDs

Event handlers use HMAC-signed tokens to prevent:

- Handler ID guessing
- Replay attacks
- Handler injection

```python
# Handler tokens look like:
# "random_id:timestamp:hmac_signature"

# Invalid or tampered tokens are rejected
```

---

## 🚨 Error Handling

### Development Mode

Full error details are shown for debugging:

```python
# Set environment variable
export VOLTA_DEBUG=true
```

### Production Mode

Errors are sanitized to prevent information leakage:

```python
export VOLTA_ENV=production

# Users see: "An internal error occurred. Please try again later."
# Full errors are logged server-side only
```

---

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VOLTA_SECRET_KEY` | Secret key for signing | Auto-generated |
| `VOLTA_DEBUG` | Enable debug mode | `false` |
| `VOLTA_ENV` | Environment (`development`/`production`) | `development` |
| `VOLTA_RATE_LIMIT_REQUESTS` | Requests per window | `100` |
| `VOLTA_RATE_LIMIT_WINDOW` | Window in seconds | `60` |

### Setting a Secret Key

**Always set a strong secret key in production:**

```bash
# Generate a secure key
python3 -c "import secrets; print(secrets.token_hex(32))"

# Set it as environment variable
export VOLTA_SECRET_KEY="your-generated-key-here"
```

---

## ✅ Security Checklist

Before deploying to production:

- [ ] Set `VOLTA_ENV=production`
- [ ] Set a strong `VOLTA_SECRET_KEY`
- [ ] Use HTTPS (TLS/SSL)
- [ ] Review CSP policy for your needs
- [ ] Enable rate limiting
- [ ] Test for XSS vulnerabilities
- [ ] Validate all user inputs
- [ ] Keep Volta updated

---

## 🐛 Reporting Security Issues

Found a security vulnerability? Please report it responsibly:

1. **Do NOT** open a public GitHub issue
2. Email: security@volta.dev
3. Include steps to reproduce
4. Allow time for a fix before disclosure

---

## 📚 Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Content Security Policy](https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP)
- [CSRF Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)

---

*Volta Security Module v1.0 - Built with ⚡ for secure Python web apps*
