"""Shell skill implementation for agno runtime."""
from pathlib import Path
from typing import Optional
from agno.tools.shell import ShellTools as AgnoShellTools
from control_plane_api.worker.skills.builtin.schema_fix_mixin import SchemaFixMixin


class ShellTools(SchemaFixMixin, AgnoShellTools):
    """
    Shell command execution using agno ShellTools.

    Wraps agno's ShellTools to provide shell access.
    """

    def __init__(self, base_directory: Optional[str] = None, **kwargs):
        """
        Initialize shell tools.

        Args:
            base_directory: Base directory for shell operations.
                          If None and execution_id provided, uses .kubiya/workspaces/<execution-id>
                          If None and no execution_id, uses current working directory
                          If set explicitly, uses provided path (user override)
            **kwargs: Configuration (allowed_commands, blocked_commands, timeout, etc.)
        """
        base_dir_path = Path(base_directory) if base_directory else None
        super().__init__(base_dir=base_dir_path)
        self.config = kwargs

        # Fix: Rebuild function schemas with proper parameters
        self._rebuild_function_schemas()
