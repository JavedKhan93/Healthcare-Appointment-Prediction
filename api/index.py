import os
import sys

# Ensure project root is in Python sys.path so 'backend' and 'ml' can be resolved
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.run import create_app

app = create_app()

if __name__ == "__main__":
    app.run()
