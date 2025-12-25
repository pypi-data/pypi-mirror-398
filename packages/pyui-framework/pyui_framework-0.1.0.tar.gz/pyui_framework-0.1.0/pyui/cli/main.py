import argparse
import importlib.util
import os
import sys
import http.server
import socketserver
from types import ModuleType


def load_app_module(path: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location("pyui_app", path)

    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from {path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build():
    app_file = "app.py"

    if not os.path.exists(app_file):
        print("❌ app.py not found in current directory")
        sys.exit(1)

    module = load_app_module(app_file)

    if hasattr(module, "router"):
        module.router.build()
    elif hasattr(module, "page"):
        module.page.build()
    else:
        print("❌ app.py must define `page` or `router`")
        sys.exit(1)

    print("✅ Build successful")


def serve():
    if not os.path.exists("dist"):
        print("❌ dist/ not found. Run `pyui build` first.")
        sys.exit(1)

    os.chdir("dist")

    PORT = 8000
    Handler = http.server.SimpleHTTPRequestHandler

    print(f"🚀 Serving PyUI app at http://localhost:{PORT}")

    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        httpd.serve_forever()


def main():
    parser = argparse.ArgumentParser(prog="pyui")
    parser.add_argument("command", choices=["build", "serve"])

    args = parser.parse_args()

    if args.command == "build":
        build()
    elif args.command == "serve":
        serve()
