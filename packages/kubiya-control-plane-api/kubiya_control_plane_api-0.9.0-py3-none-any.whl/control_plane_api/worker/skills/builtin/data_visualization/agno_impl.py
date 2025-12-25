"""Data Visualization skill implementation for all runtimes."""
from control_plane_api.worker.services.data_visualization import DataVisualizationTools as BaseDataVisualizationTools


class DataVisualizationTools(BaseDataVisualizationTools):
    """
    Data visualization and diagramming tools using Mermaid syntax.

    This wrapper imports the full implementation from services.data_visualization
    and makes it available as a builtin skill.

    For agno runtime: Used directly as agno.tools.Toolkit
    For claude_code runtime: Automatically converted to MCP server

    The class already extends agno.tools.Toolkit and has all tools registered,
    so no additional wrapper logic is needed.
    """
    pass
