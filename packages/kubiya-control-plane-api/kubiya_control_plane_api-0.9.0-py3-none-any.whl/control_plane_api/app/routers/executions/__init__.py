"""
Execution streaming components.

This package contains modular components for handling streaming execution data,
extracted from the monolithic executions.py router.
"""

# Import main router and utilities from parent executions.py
# This allows: from control_plane_api.app.routers.executions import router, validate_job_exists
import sys
from pathlib import Path

# Import from the sibling executions.py file (not this package)
_parent_dir = Path(__file__).parent.parent
_executions_module_path = _parent_dir / "executions.py"

# We need to import from ../executions.py, not this package
# Python's import system sees this directory first, so we explicitly import the file
import importlib.util
spec = importlib.util.spec_from_file_location("_executions_module", _executions_module_path)
_executions_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(_executions_module)

# Re-export the main router and utilities
router = _executions_module.router
validate_job_exists = _executions_module.validate_job_exists

__all__ = ["router", "validate_job_exists"]
