import argparse
import os
import sys
import shutil
import time
import threading
import importlib
import importlib.util
from http.server import HTTPServer, SimpleHTTPRequestHandler
from socketserver import ThreadingMixIn
from .transpiler import transpile
from .html_renderer import HTMLRenderer
from .reconciler import render
from .element import h
from .loader import install as install_loader
import traceback

# Install the loader so .vpx files work
install_loader()

def clean_cache():
    """Removes __pycache__ and compiled .py files from .vpx"""
    print("Cleaning cache...")
    cwd = os.getcwd()
    
    # Remove __pycache__
    for root, dirs, files in os.walk(cwd):
        if "__pycache__" in dirs:
            pycache_path = os.path.join(root, "__pycache__")
            shutil.rmtree(pycache_path)
            print(f"Removed {pycache_path}")
            
    # Remove .py files that correspond to .vpx
    for root, dirs, files in os.walk(cwd):
        for file in files:
            if file.endswith(".vpx"):
                py_file = file[:-4] + ".py"
                py_path = os.path.join(root, py_file)
                if os.path.exists(py_path):
                     os.remove(py_path)
                     print(f"Removed generated {py_path}")
    print("Cache cleaned.")

def init_project(target_dir):
    """
    Scaffolds a new Volta project with the proper directory structure:
    
    project-name/
    ├── app/              # Main application files (.vpx and .py)
    │   ├── __init__.py
    │   └── App.vpx       # Main App component
    ├── assets/           # Static assets (images, webmanifest, etc.)
    │   └── .gitkeep
    └── styles/           # CSS stylesheets
        └── global.css    # Global styles
    """
    from .runtime import APP_VPX_TEMPLATE, GLOBAL_CSS_TEMPLATE
    
    if not target_dir:
        target_dir = "."
    
    # Resolve to absolute path
    target_dir = os.path.abspath(target_dir)
    project_name = os.path.basename(target_dir) if target_dir != "." else "volta-app"
    
    # Create main project directory
    os.makedirs(target_dir, exist_ok=True)
    
    # Create app/ directory (main application files)
    app_dir = os.path.join(target_dir, "app")
    os.makedirs(app_dir, exist_ok=True)
    
    # Create app/__init__.py
    with open(os.path.join(app_dir, "__init__.py"), "w") as f:
        f.write('"""Volta Application Package"""\n')
    
    # Create app/App.vpx (main component)
    with open(os.path.join(app_dir, "App.vpx"), "w") as f:
        f.write(APP_VPX_TEMPLATE)
    
    # Create assets/ directory (static assets)
    assets_dir = os.path.join(target_dir, "assets")
    os.makedirs(assets_dir, exist_ok=True)
    
    # Create .gitkeep to preserve empty directory
    with open(os.path.join(assets_dir, ".gitkeep"), "w") as f:
        f.write("# This file keeps the assets directory in git\n")
    
    # Copy official logo.svg to assets/ if it exists in the framework
    framework_dir = os.path.dirname(os.path.abspath(__file__))
    logo_src = os.path.join(framework_dir, "logo.svg")
    if os.path.exists(logo_src):
        shutil.copy2(logo_src, os.path.join(assets_dir, "logo.svg"))
    
    # Create a sample webmanifest
    webmanifest = '''{
    "name": "''' + project_name + '''",
    "short_name": "''' + project_name[:12] + '''",
    "description": "A Volta Framework Application",
    "start_url": "/",
    "display": "standalone",
    "background_color": "#0f0f23",
    "theme_color": "#7c3aed",
    "icons": []
}
'''
    with open(os.path.join(assets_dir, "site.webmanifest"), "w") as f:
        f.write(webmanifest)
    
    # Create styles/ directory
    styles_dir = os.path.join(target_dir, "styles")
    os.makedirs(styles_dir, exist_ok=True)
    
    # Create styles/global.css
    with open(os.path.join(styles_dir, "global.css"), "w") as f:
        f.write(GLOBAL_CSS_TEMPLATE)
    
    # Print success message with structure
    print(f"""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   ⚡ Volta Project Initialized Successfully!                     ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝

📁 Project Structure:
    {project_name}/
    ├── app/                  # Your application code
    │   ├── __init__.py
    │   └── App.vpx           # Main App component (edit this!)
    ├── assets/               # Static assets (images, icons, etc.)
    │   ├── .gitkeep
    │   └── site.webmanifest
    └── styles/               # CSS stylesheets
        └── global.css        # Global styles with utilities

🚀 Next Steps:
    1. cd {project_name}
    2. volta dev              # Start development server
    3. Edit app/App.vpx       # Build your app!

📖 Documentation: https://volta-framework.dev/docs
""")
    print("Happy coding! ⚡")

# --- Dev Server Logic (LiveView style) ---

import json
from .events import get_handler, clear_handlers

CURRENT_HASH = 0
WATCH_DIR = os.getcwd()

# Persistent state for "Single User" Dev Mode
GLOBAL_RENDERER = None # We might need to keep the Reconciler or Root Fiber
GLOBAL_ROOT_FIBER = None
GLOBAL_RECONCILER = None

# Colors for modern logging
BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

class DevRequestHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        # Silence hot reload requests
        if "/_hot_reload_hash" in str(args[0]):
            return

        # Format details
        # format basically: '"%s" %s %s' or similar
        # args: (request_line, status_code, size)
        request_line = str(args[0])
        status = str(args[1])
        
        # Determine parts
        parts = request_line.split()
        if len(parts) >= 2:
            method = parts[0].replace('"', '')
            path = parts[1]
        else:
            # Likely an error log or direct message
            method = "INFO"
            path = request_line
        
        # Color based on status code
        if status.isdigit():
            code_num = int(status)
            if code_num < 300: status_color = GREEN
            elif code_num < 400: status_color = CYAN
            elif code_num < 500: status_color = YELLOW
            else: status_color = RED
        else:
            status_color = RESET
            
        # Method color
        methods = {
            "GET": BLUE,
            "POST": MAGENTA,
            "PUT": YELLOW,
            "DELETE": RED,
            "INFO": CYAN
        }
        m_color = methods.get(method, RESET)
        
        timestamp = time.strftime("%H:%M:%S")
        
        # Modern modular format: [TIMESTAMP] METHOD  PATH  STATUS
        sys.stderr.write(
            f"{DIM}[{timestamp}]{RESET} "
            f"{m_color}{BOLD}{method:7}{RESET} "
            f"{path:35} "
            f"{status_color}{status}{RESET}\n"
        )

    def do_GET(self):
        # Handle hot reload hash
        if self.path == '/_hot_reload_hash':
            self.send_response(200)
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            self.wfile.write(str(CURRENT_HASH).encode('utf-8'))
            return
        
        # Handle static files (with extensions)
        if '.' in self.path.split('/')[-1] and self.path != '/':
            super().do_GET()
            return

        # Handle all routes - render the app with the current path
        try:
            # Set the current path for the router
            from volta.router import set_current_path
            # Remove query string if present
            path = self.path.split('?')[0]
            
            set_current_path(path)
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html = self.render_app()
            self.wfile.write(html.encode('utf-8'))
        except Exception as e:
            self.send_error_page(500, str(e))
            
    def send_head(self):
        """
        Custom send_head to support /assets and /styles directory fallback and clean path resolution.
        """
        # Determine path
        path = self.path.split('?')[0]
        clean_path = path.lstrip('/')
        cwd = os.getcwd()
        
        # Paths to check:
        # 1. Exact path relative to CWD
        # 2. Path in assets/ relative to CWD
        # 3. Path in styles/ relative to CWD
        potential_paths = [
            os.path.join(cwd, clean_path),
            os.path.join(cwd, "assets", clean_path),
            os.path.join(cwd, "styles", clean_path)
        ]
        
        found_path = None
        for p in potential_paths:
            if os.path.exists(p) and os.path.isfile(p):
                found_path = p
                break
                
        if found_path:
            try:
                f = open(found_path, 'rb')
            except OSError:
                self.send_error(404, "File not found")
                return None
            
            try:
                self.send_response(200)
                ctype = self.guess_type(found_path)
                self.send_header("Content-type", ctype)
                fs = os.fstat(f.fileno())
                self.send_header("Content-Length", str(fs[6]))
                self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
                self.end_headers()
                return f
            except:
                f.close()
                raise
        
        self.send_error(404, "File not found")
        return None
    
    def send_error_page(self, code, message=""):
        """Send a styled error page"""
        error_titles = {
            400: "Bad Request",
            401: "Unauthorized",
            403: "Forbidden",
            404: "Not Found",
            500: "Internal Server Error",
            502: "Bad Gateway",
            503: "Service Unavailable"
        }
        
        title = error_titles.get(code, "Error")
        
        html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{code} - {title}</title>
    <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
</head>
<body>
    <div class="min-h-screen bg-gray-900 flex items-center justify-center p-6">
        <div class="text-center">
            <h1 class="text-9xl font-bold text-violet-500 mb-4">{code}</h1>
            <h2 class="text-3xl font-semibold text-white mb-4">{title}</h2>
            <p class="text-white/60 mb-8 max-w-md">{message or "Something went wrong. Please try again later."}</p>
            <a href="/" class="inline-block px-8 py-4 bg-violet-600 text-white font-semibold rounded-xl hover:bg-violet-700 transition-colors">
                Go Home
            </a>
        </div>
    </div>
</body>
</html>'''
        
        self.send_response(code)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
            
    def do_POST(self):
        global GLOBAL_RECONCILER, GLOBAL_ROOT_FIBER
        
        if self.path == '/_event':
            content_len = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_len).decode('utf-8')
            data = json.loads(body)
            
            handler_id = data.get("handler_id")
            # handler_args = data.get("args", [])
            
            handler = get_handler(handler_id)
            if handler:
                try:
                    # Execute handler. This usually updates state.
                    # e.g. set_count(c+1) calls schedule_update internally
                    handler() 
                    
                    # Now we need to re-render using the EXISTING reconciler
                    # The set_state inside handler triggered schedule -> perform_unit_of_work
                    # So the tree is likely already updated in memory?
                    # The Reconciler's schedule_update calls perform_unit_of_work.
                    # If we re-use the reconciler, the commit phase updates the state_node (HTMLElement).
                    
                    # However, Reconciler usually works by modifying the DOM.
                    # Our HTMLRenderer state_node IS the HTMLElement object.
                    # It should be updated in place.
                    
                    # We just need to serialize ROOT again.
                    if GLOBAL_ROOT_FIBER and GLOBAL_ROOT_FIBER.state_node:
                         new_html = str(GLOBAL_ROOT_FIBER.state_node)
                         self.send_response(200)
                         self.send_header('Content-type', 'application/json')
                         self.end_headers()
                         self.wfile.write(json.dumps({"html": new_html}).encode('utf-8'))
                         return
                         
                except Exception as e:
                    print(f"Error in handler: {e}")
                    traceback.print_exc()

            self.send_response(500)
            self.end_headers()

    def render_app(self):
        global GLOBAL_RECONCILER, GLOBAL_ROOT_FIBER
        try:
            sys.path.insert(0, os.getcwd())
            
            # Simple module reload check
            # Simple module reload check
            for mod in ["App", "app", "app.App"]:
                if mod in sys.modules:
                    del sys.modules[mod]
            
            # Reset handlers on full reload
            clear_handlers()
            
            # Try to import App from 'app' package first, then root 'App'
            app_module = None
            try:
                import app.App
                app_module = app.App
            except ImportError:
                # Fallback to root App
                try:
                    import App
                    app_module = App
                except ImportError:
                    return "<h1>Error: could not find 'app.App' or 'App' module.</h1>"

            # Initialize persistent reconciler for this session
            from .reconciler import Reconciler, Fiber, VoltaElement
            
            # Create Root
            root_node = HTMLRenderer().create_instance("div", {"id": "root"})
            renderer = HTMLRenderer()
            
            # We construct the reconciler manually to keep reference
            reconciler = Reconciler(renderer)
            # root_fiber = Fiber(VoltaElement("ROOT", {}, None))
            # root_fiber.state_node = root_node
            # reconciler.root_fiber = root_fiber
            # reconciler.last_root_fiber = None
            
            reconciler.render(h(app_module.App), root_node)
            
            GLOBAL_RECONCILER = reconciler
            GLOBAL_ROOT_FIBER = reconciler.root_fiber
            
            app_html = str(root_node)
            
            # Client Script for LiveView
            script = """
            <script>
                // Hot Reload
                const currentHash = "%s";
                setInterval(() => {
                    fetch('/_hot_reload_hash').then(r => r.text()).then(hash => {
                        if (hash !== currentHash) {
                            console.log("Change detected, reloading...");
                            location.reload();
                        }
                    });
                }, 1000);
                
                // Volta Live Interactivity
                document.addEventListener('click', (e) => {
                    // Find closest element with data-v-on-click
                    const target = e.target.closest('[data-v-on-click]');
                    if (target) {
                        const handlerId = target.getAttribute('data-v-on-click');
                        e.preventDefault();
                        
                        fetch('/_event', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({ handler_id: handlerId })
                        })
                        .then(res => res.json())
                        .then(data => {
                            if (data.html) {
                                // Simple Morph: Replace root content
                                // A better implementation would diff on client or morphdom
                                const root = document.getElementById('root');
                                const parser = new DOMParser();
                                const doc = parser.parseFromString(data.html, 'text/html');
                                const newRoot = doc.getElementById('root');
                                if (newRoot) {
                                     root.innerHTML = newRoot.innerHTML;
                                }
                            }
                        });
                    }
                });
            </script>
            """ % str(CURRENT_HASH)
            
            html = f"""<!DOCTYPE html>
<html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <base href="/" />
        <title>Volta App</title>
        <link rel="stylesheet" href="/styles/global.css">
        <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
    </head>
    <body>
        {app_html}
        {script}
    </body>
</html>"""
            return html

        except Exception as e:
            traceback.print_exc()
            return f"<h1>Build Error</h1><pre>{traceback.format_exc()}</pre>"

def start_dev_server(port=3000):
    global CURRENT_HASH
    
    server_address = ('', port)
    httpd = HTTPServer(server_address, DevRequestHandler)
    
    print(f"""
\033[95m\033[1m╔══════════════════════════════════════════════════════════════════╗\033[0m
\033[95m\033[1m║\033[0m                                                                  \033[95m\033[1m║\033[0m
\033[95m\033[1m║\033[0m   \033[1m⚡ Volta Dev Server started\033[0m                                     \033[95m\033[1m║\033[0m
\033[95m\033[1m║\033[0m   \033[94m➤ URL: http://localhost:{port}\033[0m                                   \033[95m\033[1m║\033[0m
\033[95m\033[1m║\033[0m   \033[2mWatching for file changes...\033[0m                                 \033[95m\033[1m║\033[0m
\033[95m\033[1m║\033[0m                                                                  \033[95m\033[1m║\033[0m
\033[95m\033[1m╚══════════════════════════════════════════════════════════════════╝\033[0m
""")
    
    # Start Watcher in background
    t = threading.Thread(target=watch_files_loop, daemon=True)
    t.start()
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        print("\n[Volta] Stopping server gracefully...")
        httpd.server_close()
        print("[Volta] Server stopped. Goodbye!")

def watch_files_loop():
    global CURRENT_HASH
    print("Watching for file changes...")
    
    last_mtime = 0
    
    while True:
        # Scan current dir for .vpx or .py changes
        max_mtime = 0
        for root, dirs, files in os.walk(WATCH_DIR):
            if "__pycache__" in root: continue
            for f in files:
                if f.endswith(".vpx") or f.endswith(".py"):
                    try:
                        mtime = os.path.getmtime(os.path.join(root, f))
                        max_mtime = max(max_mtime, mtime)
                    except:
                        pass
        
        if max_mtime > last_mtime:
            if last_mtime != 0:
                print("Change detected! Reloading...")
            last_mtime = max_mtime
            CURRENT_HASH = max_mtime
            
            # Also clear loader cache if possible? 
            # We delete sys.modules in render_app mostly.
            
        time.sleep(0.5)

# --- CLI Entry ---

def main():
    parser = argparse.ArgumentParser(prog="volta", description="Volta Framework CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # dev
    dev_parser = subparsers.add_parser("dev", help="Run in development mode with hot reload")
    dev_parser.add_argument("--port", type=int, default=3000, help="Port to run on")
    
    # start
    start_parser = subparsers.add_parser("start", help="Run in production mode")
    start_parser.add_argument("--port", type=int, default=8000, help="Port to run on")

    # clean
    subparsers.add_parser("clean", help="Clear cache and compiled artifacts")
    
    # init / restart
    init_parser = subparsers.add_parser("init", help="Initialize a new Volta project")
    init_parser.add_argument("name", nargs="?", help="Project name/directory")
    
    # build
    build_parser = subparsers.add_parser("build", help="Build for production deployment")
    build_parser.add_argument("--output", "-o", default=".", help="Output directory (default: current)")
    
    # run
    run_parser = subparsers.add_parser("run", help="Run a .vpx file directly (in-memory)")
    run_parser.add_argument("file", help="Input .vpx file")

    args = parser.parse_args()
    
    if args.command == "dev":
        start_dev_server(args.port)
        
    elif args.command == "start":
        print("Starting production server (simulated)...")
        # In real prod, use gunicorn or similar serving main.py
        # For now, reuse dev server logic without watcher logs?
        start_dev_server(args.port)
        
    elif args.command == "clean":
        clean_cache()
        
    elif args.command == "init":
        init_project(args.name)
    
    elif args.command == "build":
        # Generate production deployment files
        from .runtime import generate_production_files
        output_dir = os.path.abspath(args.output)
        
        print("""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   ⚡ Volta Production Build                                      ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
""")
        print(f"📦 Generating production files in: {output_dir}\n")
        
        generate_production_files(output_dir)
        
        print("✅ Generated files:")
        print("   • wsgi.py         - WSGI application entry point")
        print("   • Procfile        - Heroku/Railway deployment config")
        print("   • requirements.txt - Python dependencies")
        print("")
        print("🚀 Deploy with:")
        print("   gunicorn wsgi:app --bind 0.0.0.0:8000")
        print("")
        print("📖 See deployment docs: https://volta-framework.dev/docs/deployment")
        
    elif args.command == "run":
        # Run a .vpx file directly as a script
        target_file = args.file
        sys.path.insert(0, os.getcwd())
        
        # We use the loader logic manually or just transpile & exec
        if target_file.endswith(".vpx"):
             with open(target_file, "r") as f:
                 source = f.read()
             try:
                 # Transpile
                 code_str = transpile(source)
                 code_str = "from volta import h\n" + code_str
                 # Execute in new namespace
                 # We want __name__ = "__main__"
                 global_vars = {"__name__": "__main__", "__file__": os.path.abspath(target_file)}
                 exec(code_str, global_vars)
             except Exception as e:
                 print(f"Error executing {target_file}: {e}")
                 traceback.print_exc()
        else:
             # Plain python
             # We can just exec it, but we should ensure loader is active if it imports other vpx
             install_loader()
             with open(target_file, "r") as f:
                 exec(f.read(), {"__name__": "__main__", "__file__": os.path.abspath(target_file)})

if __name__ == "__main__":
    main()

