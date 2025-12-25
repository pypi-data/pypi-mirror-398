"""File Generation skill implementation for agno runtime."""
from agno.tools.file import FileTools
from control_plane_api.worker.skills.builtin.schema_fix_mixin import SchemaFixMixin


class FileGenerationTools(SchemaFixMixin, FileTools):
    """
    File generation tools using agno FileTools.

    Provides file generation capabilities for various formats.
    """

    def __init__(
        self,
        enable_json_generation: bool = True,
        enable_csv_generation: bool = True,
        enable_pdf_generation: bool = True,
        enable_txt_generation: bool = True,
        output_directory: str = "",
        max_file_size: int = 10,
        **kwargs
    ):
        """
        Initialize file generation tools.

        Args:
            enable_json_generation: Enable JSON generation
            enable_csv_generation: Enable CSV generation
            enable_pdf_generation: Enable PDF generation
            enable_txt_generation: Enable TXT generation
            output_directory: Default output directory
            max_file_size: Maximum file size in MB
            **kwargs: Additional configuration
        """
        from pathlib import Path
        base_dir = Path(output_directory) if output_directory else Path.cwd()
        super().__init__(base_dir=base_dir)
        self.config = {
            "enable_json": enable_json_generation,
            "enable_csv": enable_csv_generation,
            "enable_pdf": enable_pdf_generation,
            "enable_txt": enable_txt_generation,
            "max_size": max_file_size,
        }

        # Fix: Rebuild function schemas with proper parameters
        self._rebuild_function_schemas()
