# Deployment

## Overview

This guide covers deploying Volta applications to production environments, including various hosting platforms and configuration options.

---

## Table of Contents

1. [Preparing for Production](#preparing-for-production)
2. [WSGI Application](#wsgi-application)
3. [Platform Deployments](#platform-deployments)
   - [Railway](#railway)
   - [Render](#render)
   - [Fly.io](#flyio)
   - [Heroku](#heroku)
   - [DigitalOcean](#digitalocean)
   - [AWS](#aws)
4. [Docker Deployment](#docker-deployment)
5. [Environment Variables](#environment-variables)
6. [Static Files](#static-files)
7. [Performance Optimization](#performance-optimization)
8. [Monitoring](#monitoring)

---

## Preparing for Production

### Required Files

Ensure your project has these files:

```
my-app/
├── app/
│   └── App.vpx
├── assets/
├── main.py
├── wsgi.py           # ← Required for production
├── requirements.txt  # ← Required for dependencies
└── Procfile          # ← Required for some platforms
```

### requirements.txt

```txt
# Production server
gunicorn>=21.0.0

# Add any additional dependencies your app needs
# requests>=2.28.0
# pillow>=9.0.0
```

### Procfile

```
web: gunicorn wsgi:app --bind 0.0.0.0:$PORT
```

---

## WSGI Application

### wsgi.py

This file is the production entry point:

```python
"""
WSGI Application for Volta
Usage: gunicorn wsgi:app --bind 0.0.0.0:8000
"""

import sys
import os

# Add volta framework to path
VOLTA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, VOLTA_PATH)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Install the .vpx loader
from volta.loader import install
install()

from volta import h
from volta.html_renderer import HTMLRenderer
from volta.reconciler import Reconciler
from volta.router import set_current_path, clear_not_found
from volta.events import clear_handlers

# Import your app
from app.App import App


def serve_static(environ, start_response):
    """Serve static files from assets/ directory"""
    path = environ.get('PATH_INFO', '/').lstrip('/')
    
    potential_paths = [
        os.path.join(os.path.dirname(__file__), path),
        os.path.join(os.path.dirname(__file__), 'assets', path)
    ]
    
    for file_path in potential_paths:
        if os.path.exists(file_path) and os.path.isfile(file_path):
            content_types = {
                '.html': 'text/html',
                '.css': 'text/css',
                '.js': 'application/javascript',
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
                '.svg': 'image/svg+xml',
                '.ico': 'image/x-icon',
            }
            
            ext = os.path.splitext(file_path)[1].lower()
            content_type = content_types.get(ext, 'application/octet-stream')
            
            with open(file_path, 'rb') as f:
                content = f.read()
            
            start_response('200 OK', [
                ('Content-Type', content_type),
                ('Content-Length', str(len(content)))
            ])
            return [content]
    
    return None


def application(environ, start_response):
    """WSGI application entry point"""
    path = environ.get('PATH_INFO', '/')
    
    # Check for static files
    if '.' in path.split('/')[-1] and path != '/':
        static_response = serve_static(environ, start_response)
        if static_response:
            return static_response
    
    # Clear state
    clear_handlers()
    clear_not_found()
    set_current_path(path)
    
    try:
        # Render app
        renderer = HTMLRenderer()
        root_node = renderer.create_instance("div", {"id": "root"})
        reconciler = Reconciler(renderer)
        reconciler.render(h(App), root_node)
        
        app_html = str(root_node)
        
        html = f'''<!DOCTYPE html>
<html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <base href="/" />
        <title>Volta App</title>
        <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
    </head>
    <body>
        {app_html}
    </body>
</html>'''
        
        response_body = html.encode('utf-8')
        start_response('200 OK', [
            ('Content-Type', 'text/html; charset=utf-8'),
            ('Content-Length', str(len(response_body)))
        ])
        return [response_body]
        
    except Exception as e:
        error_html = f'''<!DOCTYPE html>
<html>
<head><title>500 Error</title></head>
<body style="font-family: sans-serif; padding: 2rem;">
    <h1>500 - Internal Server Error</h1>
    <p>{str(e)}</p>
</body>
</html>'''
        response_body = error_html.encode('utf-8')
        start_response('500 Internal Server Error', [
            ('Content-Type', 'text/html; charset=utf-8'),
            ('Content-Length', str(len(response_body)))
        ])
        return [response_body]


# Alias for gunicorn
app = application


if __name__ == "__main__":
    from wsgiref.simple_server import make_server
    port = int(os.environ.get('PORT', 8000))
    print(f"Starting production server on http://localhost:{port}")
    httpd = make_server('', port, application)
    httpd.serve_forever()
```

### Testing Production Mode Locally

```bash
# Using Python's built-in server
python wsgi.py

# Using Gunicorn (install first: pip install gunicorn)
gunicorn wsgi:app --bind 0.0.0.0:8000
```

---

## Platform Deployments

### Railway

Railway auto-detects Python apps and deploys easily.

#### Steps

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git push -u origin main
   ```

2. **Deploy on Railway**
   - Go to [railway.app](https://railway.app)
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository
   - Railway detects Python and deploys automatically

3. **Environment Variables**
   - Add any needed env vars in Railway dashboard

#### railway.json (Optional)

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "gunicorn wsgi:app --bind 0.0.0.0:$PORT",
    "restartPolicyType": "ON_FAILURE"
  }
}
```

---

### Render

#### Steps

1. **Create Files**
   - Ensure `requirements.txt`, `wsgi.py`, and `Procfile` exist

2. **Deploy**
   - Go to [render.com](https://render.com)
   - Click "New" → "Web Service"
   - Connect your GitHub repository

3. **Configure**
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn wsgi:app`

#### render.yaml (Optional)

```yaml
services:
  - type: web
    name: my-volta-app
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn wsgi:app --bind 0.0.0.0:$PORT
    envVars:
      - key: PYTHON_VERSION
        value: 3.11
```

---

### Fly.io

#### Steps

1. **Install flyctl**
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. **Login**
   ```bash
   fly auth login
   ```

3. **Initialize**
   ```bash
   fly launch
   ```

4. **Deploy**
   ```bash
   fly deploy
   ```

#### fly.toml

```toml
app = "my-volta-app"
primary_region = "iad"

[build]
  builder = "paketobuildpacks/builder:base"

[http_service]
  internal_port = 8080
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true

[env]
  PORT = "8080"
```

---

### Heroku

#### Steps

1. **Install Heroku CLI**
   ```bash
   curl https://cli-assets.heroku.com/install.sh | sh
   ```

2. **Login**
   ```bash
   heroku login
   ```

3. **Create App**
   ```bash
   heroku create my-volta-app
   ```

4. **Deploy**
   ```bash
   git push heroku main
   ```

#### runtime.txt

```
python-3.11.5
```

---

### DigitalOcean

#### App Platform

1. Go to DigitalOcean App Platform
2. Connect GitHub repository
3. Configure build settings:
   - Run Command: `gunicorn wsgi:app --bind 0.0.0.0:$PORT`
   - HTTP Port: 8080

#### Droplet (VPS)

```bash
# SSH into droplet
ssh root@your-droplet-ip

# Install Python
apt update
apt install python3 python3-pip python3-venv

# Clone your app
git clone https://github.com/you/your-app.git
cd your-app

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install gunicorn

# Run with gunicorn
gunicorn wsgi:app --bind 0.0.0.0:8000 --daemon

# Or use systemd for production (see below)
```

#### Systemd Service

```ini
# /etc/systemd/system/volta-app.service
[Unit]
Description=Volta Application
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/my-volta-app
ExecStart=/var/www/my-volta-app/venv/bin/gunicorn wsgi:app --bind 0.0.0.0:8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start
sudo systemctl enable volta-app
sudo systemctl start volta-app
```

---

### AWS

#### Elastic Beanstalk

1. Install EB CLI: `pip install awsebcli`

2. Initialize:
   ```bash
   eb init -p python-3.11 my-volta-app
   ```

3. Create environment:
   ```bash
   eb create production
   ```

4. Deploy:
   ```bash
   eb deploy
   ```

#### .ebextensions/python.config

```yaml
option_settings:
  aws:elasticbeanstalk:container:python:
    WSGIPath: wsgi:app
```

---

## Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy framework
COPY volta /app/volta

# Copy application
COPY landing_page /app/project

WORKDIR /app/project

# Install dependencies
RUN pip install --no-cache-dir gunicorn

# Set Python path
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl -f http://localhost:8000/ || exit 1

# Run application
CMD ["gunicorn", "wsgi:app", "--bind", "0.0.0.0:8000", "--workers", "4"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - VOLTA_ENV=production
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - web
    restart: unless-stopped
```

### Build and Run

```bash
# Build
docker build -t volta-app .

# Run
docker run -p 8000:8000 volta-app

# With docker-compose
docker-compose up -d
```

---

## Environment Variables

### Setting Variables

#### Local Development

```bash
export VOLTA_ENV=development
export SECRET_KEY=your-secret-key
volta dev
```

#### Production

Set in your platform's dashboard or:

```bash
# Heroku
heroku config:set VOLTA_ENV=production

# Railway/Render
# Use the web dashboard

# Docker
docker run -e VOLTA_ENV=production volta-app
```

### Accessing in Code

```python
import os

# Get environment variable
env = os.environ.get('VOLTA_ENV', 'development')
secret = os.environ.get('SECRET_KEY')

# Use in component
def App():
    is_prod = os.environ.get('VOLTA_ENV') == 'production'
    
    return (
        <div>
            {not is_prod and <DebugPanel />}
            <MainContent />
        </div>
    )
```

---

## Static Files

### In Development

Static files are served from `assets/` automatically.

### In Production with Nginx

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    # Static files
    location /assets/ {
        alias /var/www/my-app/assets/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Application
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### Using a CDN

For better performance, serve assets from a CDN:

```python
# In wsgi.py or config
CDN_URL = os.environ.get('CDN_URL', '/assets')

# In templates
f'<img src="{CDN_URL}/images/logo.png" alt="Logo">'
```

---

## Performance Optimization

### Gunicorn Workers

```bash
# Calculate: (2 × CPU cores) + 1
gunicorn wsgi:app --workers 9 --bind 0.0.0.0:8000
```

### Gunicorn with Gevent

```bash
pip install gevent

gunicorn wsgi:app \
  --workers 4 \
  --worker-class gevent \
  --bind 0.0.0.0:8000
```

### Caching Headers

```python
def application(environ, start_response):
    # ... render app ...
    
    response_headers = [
        ('Content-Type', 'text/html; charset=utf-8'),
        ('Cache-Control', 'public, max-age=60'),  # Cache for 60 seconds
    ]
    
    start_response('200 OK', response_headers)
    return [response_body]
```

### Compression

Use nginx or middleware for gzip compression:

```nginx
gzip on;
gzip_types text/html text/css application/javascript;
gzip_min_length 1000;
```

---

## Monitoring

### Health Check Endpoint

Add to wsgi.py:

```python
def application(environ, start_response):
    path = environ.get('PATH_INFO', '/')
    
    # Health check
    if path == '/health':
        start_response('200 OK', [('Content-Type', 'application/json')])
        return [b'{"status": "healthy"}']
    
    # ... rest of application
```

### Logging

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('volta')

def application(environ, start_response):
    path = environ.get('PATH_INFO', '/')
    logger.info(f"Request: {path}")
    
    # ... handle request ...
```

### Error Tracking

Consider integrating with services like:
- Sentry
- Rollbar
- LogRocket

---

## Deployment Checklist

Before deploying:

- [ ] Test production build locally (`python wsgi.py`)
- [ ] Ensure all dependencies in `requirements.txt`
- [ ] Remove debug code and print statements
- [ ] Set appropriate environment variables
- [ ] Configure static file serving
- [ ] Set up SSL/HTTPS
- [ ] Configure health checks
- [ ] Set up logging and monitoring
- [ ] Test on a staging environment first

---

## Next Steps

- [API Reference](./11-api-reference.md) - Complete API documentation
- [Troubleshooting](./12-troubleshooting.md) - Common issues and solutions
