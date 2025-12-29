import http.server
import socketserver
import urllib.parse
from urllib.parse import urlparse
import os
from error import error_page, error_path

ROUTES = {}
MIDDLEWARES = []
PORT = 8080
STATIC_DIR = "static"

ROUTES = {}

def route(path: str, methods=None):
    methods = methods or ["GET"]
    def decorator(func):
        for method in methods:
            ROUTES[(path, method.upper())] = func
        return func
    return decorator

def use(middleware_func):
    MIDDLEWARES.append(middleware_func)

from .error import error_page

class BoaskHandler(http.server.SimpleHTTPRequestHandler):
    def handle_request(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        method = self.command.upper()

        for mw in MIDDLEWARES:
            mw(self)

        if path.startswith("/static/"):
            file_path = os.path.join(STATIC_DIR, path[8:].lstrip("/"))
            full_path = os.path.abspath(file_path)
            if full_path.startswith(os.path.abspath(STATIC_DIR)) and os.path.isfile(full_path):
                return super().do_GET()
            else:
                return error_page(self, 404, "File not found")

        key = (path, method)
        if key in ROUTES:
            try:
                response = ROUTES[key](self)
                if isinstance(response, tuple) and len(response) == 2:
                    body, code = response
                    if isinstance(body, str):
                        body = body.encode("utf-8")
                    elif not isinstance(body, bytes):
                        body = b""
                    return error_page(self, code, body.decode("utf-8") if isinstance(body, bytes) else str(body))
                else:
                    if isinstance(response, str):
                        response = response.encode("utf-8")
                    elif not isinstance(response, bytes):
                        response = b""
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Content-Length", str(len(response)))
                    self.end_headers()
                    self.wfile.write(response)
            except Exception as e:
                return error_page(self, 500, f"Boask Error: {str(e)}")
        else:
            return error_page(self, 404)

    def do_GET(self):
        self.handle_request()

    def do_POST(self):
        self.handle_request()

    def do_PUT(self):
        self.handle_request()

    def do_DELETE(self):
        self.handle_request()

import os
import socketserver
import time
from threading import Thread

def run_server(port: int = 8080, host: str = "", debug: bool = False):
    global PORT
    PORT = port
    os.makedirs(STATIC_DIR, exist_ok=True)

    print(f"Boask is running → http://localhost:{port}")
    print(f"Static: ./{STATIC_DIR}/")
    print(f"Templates: ./templates/")

    def serve():
        with socketserver.TCPServer((host, port), BoaskHandler) as server:
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                print("\nBoask stopped.")

    if debug:
        files_to_watch = []
        for root, dirs, files in os.walk(os.getcwd()):
            for f in files:
                if f.endswith(".py") or root.endswith("templates"):
                    files_to_watch.append(os.path.join(root, f))
        last_mtimes = {f: os.path.getmtime(f) for f in files_to_watch}

        while True:
            serve_thread = Thread(target=serve)
            serve_thread.start()
            try:
                while serve_thread.is_alive():
                    time.sleep(1)
                    reload_needed = False
                    for f in files_to_watch:
                        if os.path.getmtime(f) != last_mtimes[f]:
                            reload_needed = True
                            last_mtimes[f] = os.path.getmtime(f)
                    if reload_needed:
                        print("Changes detected, restarting server...")
                        os._exit(3)
            except KeyboardInterrupt:
                break
    else:
        serve()
