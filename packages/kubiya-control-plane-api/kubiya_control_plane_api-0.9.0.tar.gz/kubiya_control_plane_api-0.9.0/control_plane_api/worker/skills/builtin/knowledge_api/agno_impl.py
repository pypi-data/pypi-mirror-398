"""
Knowledge API skill implementation for all runtimes.

This skill imports the KnowledgeAPITools implementation from the kubiya SDK package.
It provides semantic search capabilities across the organization's knowledge base.

NOTE: This is an opt-in skill that must be explicitly associated with agents/teams.
It is NOT auto-included like context_graph_search.
"""

try:
    from kubiya.tools import KnowledgeAPITools as SDKKnowledgeAPITools

    class KnowledgeAPITools(SDKKnowledgeAPITools):
        """
        Knowledge API tools for semantic search.

        This wrapper imports the implementation from kubiya SDK and makes it
        available as a builtin skill that can be associated with agents/teams.

        For agno runtime: Used directly as agno.tools.Toolkit
        For claude_code runtime: Automatically converted to MCP server

        The SDK class already extends agno.tools.Toolkit and has all tools registered.
        """
        pass

except ImportError as e:
    # If kubiya SDK is not installed, provide a fallback that explains the issue
    import structlog
    from agno.tools import Toolkit

    logger = structlog.get_logger()

    class KnowledgeAPITools(Toolkit):
        """
        Fallback implementation when kubiya SDK is not available.

        This will raise an error during instantiation to guide users.
        """

        def __init__(self, **kwargs):
            super().__init__(name="knowledge_api")
            error_msg = (
                "KnowledgeAPITools requires kubiya SDK (kubiya>=2.0.3). "
                f"Import error: {str(e)}. "
                "Please ensure the kubiya SDK package is installed: pip install 'kubiya>=2.0.3'"
            )
            logger.error("knowledge_api_sdk_missing", error=error_msg, import_error=str(e))
            raise ImportError(error_msg)
