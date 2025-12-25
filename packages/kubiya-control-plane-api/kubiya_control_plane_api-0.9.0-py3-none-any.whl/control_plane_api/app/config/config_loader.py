"""YAML configuration file loader with environment variable substitution."""

import os
import re
from pathlib import Path
from typing import Optional, Dict, Any
import structlog

logger = structlog.get_logger(__name__)


class ConfigFileLoader:
    """Load and merge YAML configuration with environment variables."""

    # Pattern to match ${VAR_NAME} or ${VAR_NAME:default}
    ENV_VAR_PATTERN = re.compile(r"\$\{([^}:]+)(?::([^}]*))?\}")

    @staticmethod
    def _substitute_env_vars(value: Any) -> Any:
        """
        Recursively substitute environment variables in configuration values.

        Supports:
        - ${VAR_NAME} - Required variable, fails if not set
        - ${VAR_NAME:default} - Optional variable with default value

        Args:
            value: Configuration value (str, dict, list, or other)

        Returns:
            Value with environment variables substituted
        """
        if isinstance(value, str):
            # Substitute all ${VAR} occurrences in string
            def replacer(match):
                var_name = match.group(1)
                default_value = match.group(2)  # May be None

                env_value = os.getenv(var_name)

                if env_value is not None:
                    return env_value
                elif default_value is not None:
                    return default_value
                else:
                    # Required variable not set
                    raise ValueError(
                        f"Required environment variable not set: {var_name}"
                    )

            return ConfigFileLoader.ENV_VAR_PATTERN.sub(replacer, value)

        elif isinstance(value, dict):
            # Recursively process dictionary
            return {
                k: ConfigFileLoader._substitute_env_vars(v)
                for k, v in value.items()
            }

        elif isinstance(value, list):
            # Recursively process list
            return [ConfigFileLoader._substitute_env_vars(item) for item in value]

        else:
            # Return other types as-is (int, bool, None, etc.)
            return value

    @staticmethod
    def _find_config_file(config_path: Optional[str] = None) -> Optional[Path]:
        """
        Find configuration file.

        Search order:
        1. Explicit config_path parameter
        2. KUBIYA_CONFIG_FILE environment variable
        3. ./config.yaml (current directory)
        4. /etc/kubiya/config.yaml (system-wide)

        Args:
            config_path: Optional explicit path to config file

        Returns:
            Path to config file or None if not found
        """
        # 1. Explicit path
        if config_path:
            path = Path(config_path)
            if path.exists():
                return path
            else:
                logger.warning(
                    "config_file_not_found",
                    path=str(path),
                    message="Explicit config path does not exist"
                )
                return None

        # 2. Environment variable
        env_path = os.getenv("KUBIYA_CONFIG_FILE")
        if env_path:
            path = Path(env_path)
            if path.exists():
                return path
            else:
                logger.warning(
                    "config_file_not_found",
                    path=str(path),
                    env_var="KUBIYA_CONFIG_FILE",
                    message="Config file from env var does not exist"
                )
                return None

        # 3. Current directory
        cwd_config = Path("config.yaml")
        if cwd_config.exists():
            return cwd_config

        # 4. System-wide config
        system_config = Path("/etc/kubiya/config.yaml")
        if system_config.exists():
            return system_config

        # No config file found
        return None

    @staticmethod
    def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Load configuration from YAML file with environment variable substitution.

        Priority: Environment variables > YAML file > Defaults

        Args:
            config_path: Optional path to YAML config file

        Returns:
            Dict with configuration (empty dict if no config file found)

        Raises:
            ValueError: If required environment variable not set
            yaml.YAMLError: If YAML syntax error
        """
        # Find config file
        config_file = ConfigFileLoader._find_config_file(config_path)

        if not config_file:
            logger.info(
                "no_config_file_found",
                message="No config file found, using environment variables only",
                checked_paths=[
                    "config_path parameter",
                    "KUBIYA_CONFIG_FILE env var",
                    "./config.yaml",
                    "/etc/kubiya/config.yaml"
                ]
            )
            return {}

        try:
            # Import YAML parser
            try:
                import yaml
            except ImportError:
                raise ImportError(
                    "PyYAML is required for YAML config files. "
                    "Install it with: pip install PyYAML"
                )

            # Read and parse YAML
            with open(config_file, "r", encoding="utf-8") as f:
                raw_config = yaml.safe_load(f) or {}

            # Substitute environment variables
            config = ConfigFileLoader._substitute_env_vars(raw_config)

            logger.info(
                "config_file_loaded",
                path=str(config_file),
                keys=list(config.keys()) if isinstance(config, dict) else [],
            )

            return config

        except ImportError as e:
            logger.error(
                "config_loader_dependency_missing",
                error=str(e),
                path=str(config_file)
            )
            raise

        except ValueError as e:
            # Required env var not set
            logger.error(
                "config_env_var_required",
                error=str(e),
                path=str(config_file)
            )
            raise

        except Exception as e:
            logger.error(
                "config_file_load_error",
                error=str(e),
                path=str(config_file),
                error_type=type(e).__name__
            )
            raise


# Convenience function
def load_config_file(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from YAML file.

    Convenience wrapper around ConfigFileLoader.load_config().

    Args:
        config_path: Optional path to YAML config file

    Returns:
        Dict with configuration (empty dict if no config file found)
    """
    return ConfigFileLoader.load_config(config_path)
