"""File System skill implementation for agno runtime."""
from pathlib import Path
from typing import Optional
from agno.tools.file import FileTools
from control_plane_api.worker.skills.builtin.schema_fix_mixin import SchemaFixMixin


class FileSystemTools(SchemaFixMixin, FileTools):
    """
    File system operations using agno FileTools.

    Wraps agno's FileTools to provide file system access.
    """

    def __init__(self, base_directory: Optional[str] = None, **kwargs):
        """
        Initialize file system tools.

        Args:
            base_directory: Base directory for file operations.
                          If None and execution_id provided, uses .kubiya/workspaces/<execution-id>
                          If None and no execution_id, uses current working directory
                          If set explicitly, uses provided path (user override)
            **kwargs: Additional configuration (read_only, max_file_size, etc.)
        """
        # Agno's FileTools handles None as current directory
        base_dir_path = Path(base_directory) if base_directory else None
        super().__init__(base_dir=base_dir_path)
        self.config = kwargs

        # Fix: Rebuild function schemas with proper parameters
        self._rebuild_function_schemas()
