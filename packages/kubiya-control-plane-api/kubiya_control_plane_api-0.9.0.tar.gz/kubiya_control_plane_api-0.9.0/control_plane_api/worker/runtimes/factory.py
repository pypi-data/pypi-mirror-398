"""
Runtime factory using the registry system.

This module provides a simplified factory that delegates to RuntimeRegistry.
"""

from typing import TYPE_CHECKING, List
import structlog

from .base import RuntimeType, BaseRuntime, RuntimeRegistry

if TYPE_CHECKING:
    from control_plane_client import ControlPlaneClient
    from services.cancellation_manager import CancellationManager

logger = structlog.get_logger(__name__)


class RuntimeFactory:
    """
    Factory for creating runtime instances.

    This is a thin wrapper around RuntimeRegistry that provides
    backward compatibility and convenience methods.
    """

    @staticmethod
    def create_runtime(
        runtime_type: RuntimeType,
        control_plane_client: "ControlPlaneClient",
        cancellation_manager: "CancellationManager",
        **kwargs,
    ) -> BaseRuntime:
        """
        Create a runtime instance using the registry.

        Args:
            runtime_type: Type of runtime to create
            control_plane_client: Client for Control Plane API
            cancellation_manager: Manager for execution cancellation
            **kwargs: Additional runtime-specific configuration

        Returns:
            BaseRuntime instance

        Raises:
            ValueError: If runtime_type is not supported

        Example:
            >>> factory = RuntimeFactory()
            >>> runtime = factory.create_runtime(
            ...     RuntimeType.CLAUDE_CODE,
            ...     control_plane_client,
            ...     cancellation_manager
            ... )
        """
        logger.info(
            "creating_runtime",
            runtime_type=runtime_type.value,
            has_kwargs=bool(kwargs),
        )

        return RuntimeRegistry.create(
            runtime_type=runtime_type,
            control_plane_client=control_plane_client,
            cancellation_manager=cancellation_manager,
            **kwargs,
        )

    @staticmethod
    def get_default_runtime_type() -> RuntimeType:
        """
        Get the default runtime type.

        This is used when no runtime is explicitly specified in agent config.

        Returns:
            Default RuntimeType (RuntimeType.DEFAULT)
        """
        return RuntimeType.DEFAULT

    @staticmethod
    def get_supported_runtimes() -> List[RuntimeType]:
        """
        Get list of supported runtimes from registry.

        Returns:
            List of RuntimeType enum values
        """
        return RuntimeRegistry.list_available()

    @staticmethod
    def parse_runtime_type(runtime_str: str) -> RuntimeType:
        """
        Parse runtime type from string with fallback to default.

        Args:
            runtime_str: Runtime type as string

        Returns:
            RuntimeType enum value, defaults to DEFAULT if invalid

        Example:
            >>> RuntimeFactory.parse_runtime_type("claude_code")
            RuntimeType.CLAUDE_CODE
            >>> RuntimeFactory.parse_runtime_type("invalid")
            RuntimeType.DEFAULT
        """
        try:
            return RuntimeType(runtime_str)
        except ValueError:
            logger.warning(
                "invalid_runtime_type_fallback",
                runtime_str=runtime_str,
                default=RuntimeType.DEFAULT.value,
            )
            return RuntimeType.DEFAULT

    @staticmethod
    def get_runtime_info_all() -> dict:
        """
        Get information about all available runtimes.

        Returns:
            Dict mapping runtime type to info dict
        """
        return RuntimeRegistry.get_runtime_info_all()

    @staticmethod
    def validate_runtime_config(
        runtime_type: RuntimeType, config: dict
    ) -> tuple[bool, str]:
        """
        Validate runtime-specific configuration.

        Args:
            runtime_type: Type of runtime
            config: Configuration dict to validate

        Returns:
            Tuple of (is_valid, error_message)

        Example:
            >>> is_valid, error = RuntimeFactory.validate_runtime_config(
            ...     RuntimeType.CLAUDE_CODE,
            ...     {"allowed_tools": ["Bash"]}
            ... )
        """
        # Get runtime class from registry
        try:
            runtime_class = RuntimeRegistry.get(runtime_type)

            # Create temporary instance to validate (with mocks)
            from unittest.mock import MagicMock
            temp_runtime = runtime_class(
                control_plane_client=MagicMock(),
                cancellation_manager=MagicMock(),
            )

            # Use runtime's validation if available
            if hasattr(temp_runtime, 'validate_config'):
                try:
                    temp_runtime.validate_config(config)
                    return True, ""
                except ValueError as e:
                    return False, str(e)

            return True, ""

        except ValueError as e:
            return False, f"Unknown runtime type: {str(e)}"
        except Exception as e:
            return False, f"Validation error: {str(e)}"
