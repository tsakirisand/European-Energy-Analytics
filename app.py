import sys
import os
import runpy

# Add current directory to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Execute main dashboard entrypoint
dashboard_app = os.path.abspath(os.path.join(os.path.dirname(__file__), "dashboard", "app.py"))
runpy.run_path(dashboard_app, run_name="__main__")
