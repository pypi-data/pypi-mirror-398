"""
Pytest configuration for worker tests.
Sets up sys.path to allow 'runtimes' imports.
"""

import sys
from pathlib import Path

# Add the worker directory to sys.path so that 'from runtimes import ...' works
worker_dir = Path(__file__).parent.parent
if str(worker_dir) not in sys.path:
    sys.path.insert(0, str(worker_dir))
