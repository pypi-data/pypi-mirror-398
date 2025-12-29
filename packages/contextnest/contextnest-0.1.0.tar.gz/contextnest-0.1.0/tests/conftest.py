"""
Pytest configuration for ContextNest tests.
"""
import sys
from pathlib import Path

# Add the contextnest package to the path so tests can import it
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import any necessary fixtures or configurations here
pytest_plugins = [
    # Add any plugin modules here if needed
]