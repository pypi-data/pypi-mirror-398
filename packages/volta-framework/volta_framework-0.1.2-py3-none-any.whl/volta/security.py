"""
Volta Security Module

This module provides comprehensive security features for Volta applications:
- XSS Prevention (HTML escaping)
- CSRF Protection (token-based)
- Path Traversal Prevention
- Rate Limiting
- Security Headers
- Input Sanitization
- Secure Token Generation

⚡ Security-first framework design
"""

import os
import re
import html
import time
import hmac
import hashlib
import secrets
import threading
from typing import Dict, Optional, List, Callable, Any
from functools import wraps
from collections import defaultdict


# =============================================================================
# CONFIGURATION
# =============================================================================

class SecurityConfig:
    """Security configuration with sensible defaults"""
    
    # Environment detection
    DEBUG = os.environ.get('VOLTA_DEBUG', 'false').lower() == 'true'
    PRODUCTION = os.environ.get('VOLTA_ENV', 'development').lower() == 'production'
    
    # Secret key for signing (auto-generated if not provided)
    SECRET_KEY = os.environ.get('VOLTA_SECRET_KEY', secrets.token_hex(32))
    
    # CSRF settings
    CSRF_ENABLED = True
    CSRF_TOKEN_LENGTH = 32
    CSRF_TOKEN_LIFETIME = 3600  # 1 hour
    
    # Rate limiting settings
    RATE_LIMIT_ENABLED = True
    RATE_LIMIT_REQUESTS = 100  # requests per window
    RATE_LIMIT_WINDOW = 60  # seconds
    RATE_LIMIT_BURST = 20  # burst capacity
    
    # XSS/Injection settings
    XSS_PROTECTION_ENABLED = True
    SANITIZE_HTML = True
    
    # Path traversal protection
    ALLOWED_STATIC_EXTENSIONS = {
        '.html', '.css', '.js', '.json', '.png', '.jpg', '.jpeg', '.gif', 
        '.svg', '.ico', '.woff', '.woff2', '.webmanifest', '.txt', '.xml'
    }
    
    # Security headers
    SECURITY_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
    }
    
    # Content Security Policy (strict by default)
    CSP_ENABLED = True
    CSP_POLICY = {
        'default-src': ["'self'"],
        'script-src': ["'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net"],
        'style-src': ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com"],
        'img-src': ["'self'", "data:", "https:"],
        'font-src': ["'self'", "https://fonts.gstatic.com"],
        'connect-src': ["'self'"],
        'frame-ancestors': ["'none'"],
        'base-uri': ["'self'"],
        'form-action': ["'self'"],
    }


# =============================================================================
# XSS PREVENTION
# =============================================================================

class XSSProtection:
    """Cross-Site Scripting (XSS) prevention utilities"""
    
    # Patterns that indicate potential XSS attacks
    DANGEROUS_PATTERNS = [
        re.compile(r'<script[^>]*>.*?</script>', re.IGNORECASE | re.DOTALL),
        re.compile(r'javascript:', re.IGNORECASE),
        re.compile(r'on\w+\s*=', re.IGNORECASE),
        re.compile(r'<iframe[^>]*>', re.IGNORECASE),
        re.compile(r'<object[^>]*>', re.IGNORECASE),
        re.compile(r'<embed[^>]*>', re.IGNORECASE),
        re.compile(r'expression\s*\(', re.IGNORECASE),
        re.compile(r'url\s*\([^)]*javascript:', re.IGNORECASE),
        re.compile(r'<svg[^>]*onload', re.IGNORECASE),
        re.compile(r'<img[^>]*onerror', re.IGNORECASE),
    ]
    
    @staticmethod
    def escape_html(text: str) -> str:
        """
        Escape HTML special characters to prevent XSS.
        This is the primary defense against XSS attacks.
        """
        if text is None:
            return ''
        return html.escape(str(text), quote=True)
    
    @staticmethod
    def escape_attribute(value: str) -> str:
        """
        Escape a value for use in an HTML attribute.
        More aggressive escaping for attribute contexts.
        """
        if value is None:
            return ''
        # Escape HTML entities and quotes
        escaped = html.escape(str(value), quote=True)
        # Additional escaping for attribute context
        escaped = escaped.replace('`', '&#96;')
        return escaped
    
    @staticmethod
    def escape_url(url: str) -> str:
        """
        Sanitize URLs to prevent javascript: and data: attacks.
        """
        if url is None:
            return ''
        
        url = str(url).strip()
        url_lower = url.lower()
        
        # Block dangerous URL schemes
        dangerous_schemes = ['javascript:', 'data:', 'vbscript:', 'file:']
        for scheme in dangerous_schemes:
            if url_lower.startswith(scheme):
                return '#blocked'
        
        return url
    
    @staticmethod
    def is_safe_string(text: str) -> bool:
        """
        Check if a string is safe from XSS patterns.
        Returns False if dangerous patterns are detected.
        """
        if text is None:
            return True
        
        text = str(text)
        for pattern in XSSProtection.DANGEROUS_PATTERNS:
            if pattern.search(text):
                return False
        return True
    
    @staticmethod
    def sanitize_html(html_content: str, allowed_tags: set = None) -> str:
        """
        Sanitize HTML content by removing dangerous tags and attributes.
        Only allows safe tags if specified.
        """
        if html_content is None:
            return ''
        
        if allowed_tags is None:
            allowed_tags = {'p', 'br', 'b', 'i', 'u', 'strong', 'em', 'span', 'div', 'a', 'ul', 'ol', 'li'}
        
        # Remove script tags completely
        html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove event handlers
        html_content = re.sub(r'\s+on\w+\s*=\s*["\'][^"\']*["\']', '', html_content, flags=re.IGNORECASE)
        html_content = re.sub(r'\s+on\w+\s*=\s*[^\s>]+', '', html_content, flags=re.IGNORECASE)
        
        # Remove javascript: URLs
        html_content = re.sub(r'javascript:[^"\'>\s]*', '#blocked', html_content, flags=re.IGNORECASE)
        
        return html_content


# =============================================================================
# CSRF PROTECTION
# =============================================================================

class CSRFProtection:
    """Cross-Site Request Forgery (CSRF) protection"""
    
    _tokens: Dict[str, float] = {}
    _lock = threading.Lock()
    
    @classmethod
    def generate_token(cls) -> str:
        """Generate a new CSRF token with timestamp"""
        token = secrets.token_urlsafe(SecurityConfig.CSRF_TOKEN_LENGTH)
        with cls._lock:
            cls._tokens[token] = time.time()
            # Cleanup old tokens
            cls._cleanup_expired_tokens()
        return token
    
    @classmethod
    def validate_token(cls, token: str) -> bool:
        """Validate a CSRF token"""
        if not token:
            return False
        
        with cls._lock:
            if token not in cls._tokens:
                return False
            
            # Check if token is expired
            created_at = cls._tokens[token]
            if time.time() - created_at > SecurityConfig.CSRF_TOKEN_LIFETIME:
                del cls._tokens[token]
                return False
            
            # Token is valid - remove it (one-time use)
            del cls._tokens[token]
            return True
    
    @classmethod
    def _cleanup_expired_tokens(cls):
        """Remove expired tokens to prevent memory leaks"""
        current_time = time.time()
        expired = [
            token for token, created_at in cls._tokens.items()
            if current_time - created_at > SecurityConfig.CSRF_TOKEN_LIFETIME
        ]
        for token in expired:
            del cls._tokens[token]
    
    @staticmethod
    def get_token_html() -> str:
        """Generate hidden form field with CSRF token"""
        token = CSRFProtection.generate_token()
        return f'<input type="hidden" name="_csrf_token" value="{XSSProtection.escape_attribute(token)}">'
    
    @staticmethod
    def get_token_meta() -> str:
        """Generate meta tag with CSRF token for AJAX requests"""
        token = CSRFProtection.generate_token()
        return f'<meta name="csrf-token" content="{XSSProtection.escape_attribute(token)}">'


# =============================================================================
# PATH TRAVERSAL PROTECTION
# =============================================================================

class PathSecurity:
    """Path traversal and file access protection"""
    
    @staticmethod
    def is_safe_path(base_dir: str, requested_path: str) -> bool:
        """
        Validate that a requested path doesn't escape the base directory.
        Prevents path traversal attacks like ../../etc/passwd
        """
        # Normalize paths
        base_dir = os.path.abspath(base_dir)
        
        # Handle URL-encoded path traversal attempts
        requested_path = requested_path.replace('%2e', '.')
        requested_path = requested_path.replace('%2f', '/')
        requested_path = requested_path.replace('%5c', '\\')
        
        # Construct full path
        full_path = os.path.abspath(os.path.join(base_dir, requested_path))
        
        # Verify the resolved path is within base directory
        return full_path.startswith(base_dir + os.sep) or full_path == base_dir
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize a filename to prevent path traversal.
        Removes dangerous characters and patterns.
        """
        if not filename:
            return ''
        
        # Remove path separators
        filename = filename.replace('/', '').replace('\\', '')
        
        # Remove null bytes (used in null byte injection attacks)
        filename = filename.replace('\x00', '')
        
        # Remove path traversal patterns
        filename = filename.replace('..', '')
        
        # Remove hidden file indicators on Unix
        if filename.startswith('.'):
            filename = filename[1:]
        
        # Only allow safe characters
        safe_chars = re.sub(r'[^\w\-_.]', '', filename)
        
        return safe_chars
    
    @staticmethod
    def is_allowed_extension(filepath: str) -> bool:
        """Check if file extension is in allowed list"""
        ext = os.path.splitext(filepath)[1].lower()
        return ext in SecurityConfig.ALLOWED_STATIC_EXTENSIONS
    
    @staticmethod
    def validate_static_file(base_dir: str, requested_path: str) -> Optional[str]:
        """
        Validate and return safe path for static file serving.
        Returns None if the path is invalid or unsafe.
        """
        # Remove leading slash
        requested_path = requested_path.lstrip('/')
        
        # Check for path traversal
        if not PathSecurity.is_safe_path(base_dir, requested_path):
            return None
        
        # Construct full path
        full_path = os.path.normpath(os.path.join(base_dir, requested_path))
        
        # Verify file exists and is a file (not directory)
        if not os.path.isfile(full_path):
            return None
        
        # Check extension
        if not PathSecurity.is_allowed_extension(full_path):
            return None
        
        return full_path


# =============================================================================
# RATE LIMITING
# =============================================================================

class RateLimiter:
    """Token bucket rate limiter to prevent DoS and brute force attacks"""
    
    _buckets: Dict[str, Dict] = defaultdict(lambda: {
        'tokens': SecurityConfig.RATE_LIMIT_BURST,
        'last_update': time.time()
    })
    _lock = threading.Lock()
    
    @classmethod
    def is_allowed(cls, client_id: str) -> bool:
        """
        Check if request from client is allowed based on rate limits.
        Uses token bucket algorithm for smooth rate limiting.
        """
        if not SecurityConfig.RATE_LIMIT_ENABLED:
            return True
        
        with cls._lock:
            bucket = cls._buckets[client_id]
            current_time = time.time()
            
            # Refill tokens based on time passed
            time_passed = current_time - bucket['last_update']
            tokens_to_add = time_passed * (SecurityConfig.RATE_LIMIT_REQUESTS / SecurityConfig.RATE_LIMIT_WINDOW)
            bucket['tokens'] = min(SecurityConfig.RATE_LIMIT_BURST, bucket['tokens'] + tokens_to_add)
            bucket['last_update'] = current_time
            
            # Check if we have tokens available
            if bucket['tokens'] >= 1:
                bucket['tokens'] -= 1
                return True
            
            return False
    
    @classmethod
    def get_client_id(cls, environ: dict) -> str:
        """
        Extract client identifier from request.
        Uses IP address with fallback to forwarded headers.
        """
        # Check for proxy headers (in order of preference)
        client_id = environ.get('HTTP_X_REAL_IP')
        if not client_id:
            forwarded = environ.get('HTTP_X_FORWARDED_FOR', '')
            if forwarded:
                client_id = forwarded.split(',')[0].strip()
        if not client_id:
            client_id = environ.get('REMOTE_ADDR', 'unknown')
        
        return client_id
    
    @classmethod
    def cleanup_old_buckets(cls, max_age: int = 3600):
        """Remove stale rate limit buckets to prevent memory leaks"""
        current_time = time.time()
        with cls._lock:
            stale_clients = [
                client_id for client_id, bucket in cls._buckets.items()
                if current_time - bucket['last_update'] > max_age
            ]
            for client_id in stale_clients:
                del cls._buckets[client_id]


# =============================================================================
# SECURE HANDLER IDS
# =============================================================================

class SecureHandlerRegistry:
    """
    Secure handler registry with HMAC-signed tokens.
    Prevents handler ID guessing and replay attacks.
    """
    
    _handlers: Dict[str, Callable] = {}
    _handler_timestamps: Dict[str, float] = {}
    _lock = threading.Lock()
    
    # Handler expiry (handlers expire after 1 hour to prevent stale handlers)
    HANDLER_LIFETIME = 3600
    
    @classmethod
    def register_handler(cls, handler: Callable) -> str:
        """
        Register a handler and return a secure, signed token.
        Uses HMAC to prevent token forgery.
        """
        with cls._lock:
            # Generate cryptographically secure ID
            random_id = secrets.token_urlsafe(16)
            timestamp = str(int(time.time()))
            
            # Create HMAC signature
            message = f"{random_id}:{timestamp}"
            signature = hmac.new(
                SecurityConfig.SECRET_KEY.encode(),
                message.encode(),
                hashlib.sha256
            ).hexdigest()[:16]
            
            # Final token format: random_id:timestamp:signature
            token = f"{random_id}:{timestamp}:{signature}"
            
            cls._handlers[token] = handler
            cls._handler_timestamps[token] = time.time()
            
            # Cleanup expired handlers
            cls._cleanup_expired_handlers()
            
            return token
    
    @classmethod
    def get_handler(cls, token: str) -> Optional[Callable]:
        """
        Retrieve and validate a handler by its token.
        Verifies HMAC signature and checks expiry.
        """
        if not token:
            return None
        
        try:
            parts = token.split(':')
            if len(parts) != 3:
                return None
            
            random_id, timestamp, signature = parts
            
            # Verify HMAC signature
            message = f"{random_id}:{timestamp}"
            expected_signature = hmac.new(
                SecurityConfig.SECRET_KEY.encode(),
                message.encode(),
                hashlib.sha256
            ).hexdigest()[:16]
            
            if not hmac.compare_digest(signature, expected_signature):
                return None
            
            with cls._lock:
                if token not in cls._handlers:
                    return None
                
                # Check if handler is expired
                if time.time() - cls._handler_timestamps[token] > cls.HANDLER_LIFETIME:
                    del cls._handlers[token]
                    del cls._handler_timestamps[token]
                    return None
                
                return cls._handlers[token]
                
        except Exception:
            return None
    
    @classmethod
    def _cleanup_expired_handlers(cls):
        """Remove expired handlers to prevent memory leaks"""
        current_time = time.time()
        expired = [
            token for token, timestamp in cls._handler_timestamps.items()
            if current_time - timestamp > cls.HANDLER_LIFETIME
        ]
        for token in expired:
            cls._handlers.pop(token, None)
            cls._handler_timestamps.pop(token, None)
    
    @classmethod
    def clear_handlers(cls):
        """Clear all handlers (called between requests)"""
        with cls._lock:
            cls._handlers.clear()
            cls._handler_timestamps.clear()


# =============================================================================
# SECURITY HEADERS
# =============================================================================

class SecurityHeaders:
    """HTTP Security Headers management"""
    
    @staticmethod
    def get_security_headers() -> List[tuple]:
        """Get list of security headers to add to response"""
        headers = []
        
        # Add standard security headers
        for header, value in SecurityConfig.SECURITY_HEADERS.items():
            headers.append((header, value))
        
        # Add Content Security Policy
        if SecurityConfig.CSP_ENABLED:
            csp_parts = []
            for directive, values in SecurityConfig.CSP_POLICY.items():
                csp_parts.append(f"{directive} {' '.join(values)}")
            headers.append(('Content-Security-Policy', '; '.join(csp_parts)))
        
        # Add Strict-Transport-Security for HTTPS
        if SecurityConfig.PRODUCTION:
            headers.append(('Strict-Transport-Security', 'max-age=31536000; includeSubDomains; preload'))
        
        return headers
    
    @staticmethod
    def apply_headers(response_headers: list) -> list:
        """Add security headers to existing response headers"""
        security_headers = SecurityHeaders.get_security_headers()
        
        # Merge with existing headers (security headers take precedence)
        existing_header_names = {h[0].lower() for h in response_headers}
        for header in security_headers:
            if header[0].lower() not in existing_header_names:
                response_headers.append(header)
        
        return response_headers


# =============================================================================
# INPUT VALIDATION
# =============================================================================

class InputValidator:
    """Input validation and sanitization utilities"""
    
    @staticmethod
    def validate_string(value: Any, max_length: int = 10000, allow_empty: bool = True) -> Optional[str]:
        """
        Validate and sanitize a string input.
        Returns None if invalid.
        """
        if value is None:
            return '' if allow_empty else None
        
        try:
            value = str(value)
        except Exception:
            return None
        
        if not allow_empty and not value:
            return None
        
        if len(value) > max_length:
            return None
        
        # Remove null bytes
        value = value.replace('\x00', '')
        
        return value
    
    @staticmethod
    def validate_integer(value: Any, min_val: int = None, max_val: int = None) -> Optional[int]:
        """Validate an integer input within optional bounds"""
        try:
            value = int(value)
        except (TypeError, ValueError):
            return None
        
        if min_val is not None and value < min_val:
            return None
        if max_val is not None and value > max_val:
            return None
        
        return value
    
    @staticmethod
    def validate_email(email: str) -> Optional[str]:
        """Basic email validation"""
        if not email:
            return None
        
        email = str(email).strip().lower()
        
        # Basic email regex
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            return None
        
        return email
    
    @staticmethod
    def validate_json(data: str) -> Optional[dict]:
        """Safely parse and validate JSON input"""
        import json
        
        if not data:
            return None
        
        try:
            # Limit JSON parsing depth and size
            if len(data) > 1_000_000:  # 1MB limit
                return None
            
            parsed = json.loads(data)
            
            if not isinstance(parsed, dict):
                return None
            
            return parsed
        except json.JSONDecodeError:
            return None


# =============================================================================
# ERROR SANITIZATION
# =============================================================================

class ErrorSanitizer:
    """Sanitize error messages for safe display"""
    
    @staticmethod
    def sanitize_error(error: Exception, show_details: bool = None) -> str:
        """
        Return a safe error message.
        In production, hides internal details.
        """
        if show_details is None:
            show_details = SecurityConfig.DEBUG
        
        if show_details:
            return XSSProtection.escape_html(str(error))
        else:
            return "An internal error occurred. Please try again later."
    
    @staticmethod
    def safe_error_page(error: Exception, status_code: int = 500) -> str:
        """Generate a safe error page HTML"""
        message = ErrorSanitizer.sanitize_error(error)
        
        return f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{status_code} Error</title>
    <style>
        body {{ font-family: sans-serif; padding: 2rem; background: #111827; color: white; text-align: center; }}
        h1 {{ color: #ef4444; }}
    </style>
</head>
<body>
    <h1>{status_code} - Error</h1>
    <p>{message}</p>
</body>
</html>'''


# =============================================================================
# CONVENIENCE EXPORTS
# =============================================================================

# Create singleton instances
xss = XSSProtection()
csrf = CSRFProtection()
path_security = PathSecurity()
rate_limiter = RateLimiter()
secure_handlers = SecureHandlerRegistry()
security_headers = SecurityHeaders()
input_validator = InputValidator()
error_sanitizer = ErrorSanitizer()


def escape(text: str) -> str:
    """Shortcut for HTML escaping"""
    return XSSProtection.escape_html(text)


def escape_attr(value: str) -> str:
    """Shortcut for attribute escaping"""
    return XSSProtection.escape_attribute(value)


def escape_url(url: str) -> str:
    """Shortcut for URL sanitization"""
    return XSSProtection.escape_url(url)


def is_safe(text: str) -> bool:
    """Shortcut for XSS safety check"""
    return XSSProtection.is_safe_string(text)
