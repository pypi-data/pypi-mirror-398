"""Python skill implementation for agno runtime."""
from agno.tools.python import PythonTools as AgnoPythonTools
from agno.tools.function import Function
from control_plane_api.worker.skills.builtin.schema_fix_mixin import SchemaFixMixin


class PythonTools(SchemaFixMixin, AgnoPythonTools):
    """
    Python code execution using agno PythonTools.

    Wraps agno's PythonTools to provide Python execution with proper parameter schemas.
    """

    def __init__(self, **kwargs):
        """
        Initialize Python tools.

        Args:
            **kwargs: Configuration (enable_code_execution, blocked_imports, etc.)
        """
        super().__init__()
        self.config = kwargs

        # Fix: Rebuild function schemas with proper parameters
        self._rebuild_function_schemas()
