"""Convenience runner to start the Flask app from the repository root.

This allows running the application with `python run.py` regardless of the
current working directory and avoids "No module named application" import
errors when `application` is a package.
"""
import os
import sys

# Ensure repository root is on sys.path
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from application.app import app

if __name__ == "__main__":
    # Use env vars if provided
    debug = os.environ.get("FLASK_DEBUG", "0") in ("1", "true", "True")
    host = os.environ.get("FLASK_RUN_HOST", "127.0.0.1")
    port = int(os.environ.get("FLASK_RUN_PORT", "5000"))
    app.run(host=host, port=port, debug=debug)
