"""
Schema Fix Mixin for Agno Tool Wrappers

This module provides a mixin class that fixes empty parameter schemas in agno tools.

PROBLEM:
The agno library (versions tested: all current versions) has a critical bug where
tool functions have empty parameter schemas:
  {'type': 'object', 'properties': {}, 'required': []}

This causes LLMs to call functions without required parameters, leading to
validation errors like:
  "pydantic_core.ValidationError: X validation errors... Missing required argument"

SOLUTION:
This mixin class provides a _rebuild_function_schemas() method that:
1. Inspects actual method signatures using Python's inspect module
2. Extracts parameter types from type hints
3. Extracts parameter descriptions from docstrings
4. Rebuilds the function.parameters dict with correct schema
5. Marks parameters without defaults as required

USAGE:
Add SchemaFixMixin as a base class to any agno tool wrapper:

  from agno.tools.shell import ShellTools as AgnoShellTools
  from control_plane_api.worker.skills.builtin.schema_fix_mixin import SchemaFixMixin

  class ShellTools(SchemaFixMixin, AgnoShellTools):
      def __init__(self, **kwargs):
          super().__init__(**kwargs)
          self._rebuild_function_schemas()  # Fix schemas after parent init

AFFECTED TOOLS:
All agno-based tools need this fix:
- FileTools (save_file, read_file, etc.) ✅ FIXED
- PythonTools (save_to_file_and_run, etc.) ✅ FIXED
- ShellTools (run_shell_command) ⚠️ NEEDS FIX
- DockerTools (all docker functions) ⚠️ NEEDS FIX
- SlackTools (all slack functions) ⚠️ NEEDS FIX
- Custom Toolkit subclasses ⚠️ NEEDS FIX
"""

import inspect
from typing import get_type_hints, get_origin, get_args


class SchemaFixMixin:
    """
    Mixin class that fixes empty parameter schemas in agno tool functions.

    CRITICAL: Call _rebuild_function_schemas() in your __init__ method
    after calling super().__init__() to ensure agno has initialized functions.

    Example:
        class MyTools(SchemaFixMixin, AgnoTools):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self._rebuild_function_schemas()  # Fix empty schemas
    """

    def _rebuild_function_schemas(self):
        """
        Rebuild function schemas to include proper parameter definitions.

        This method:
        1. Iterates through all functions in self.functions
        2. Gets the actual method from the class
        3. Extracts parameter info from signature and type hints
        4. Builds proper JSON schema for parameters
        5. Updates the function.parameters dict

        Handles:
        - Type hints (str, int, bool, float, list, dict, Optional)
        - Default values (parameters without defaults are marked required)
        - Docstring descriptions (:param name: description)
        """
        if not hasattr(self, 'functions') or not self.functions:
            return

        # Rebuild each function with proper parameter schema
        for func_name, func_obj in list(self.functions.items()):
            try:
                # Get the actual method
                method = getattr(self, func_name, None)
                if not method or not callable(method):
                    continue

                # Extract parameter schema from function signature
                sig = inspect.signature(method)
                type_hints = get_type_hints(method)

                properties = {}
                required = []

                for param_name, param in sig.parameters.items():
                    # Skip 'self'
                    if param_name == 'self':
                        continue

                    # Get type hint
                    param_type = type_hints.get(param_name, str)

                    # Determine JSON schema type and items type for arrays
                    json_type, items_type = self._python_type_to_json_schema(param_type)

                    # Build parameter schema
                    param_schema = {"type": json_type}

                    # Add items schema for arrays
                    if json_type == "array" and items_type:
                        param_schema["items"] = {"type": items_type}

                    # Add description from docstring if available
                    if method.__doc__:
                        # Try to extract parameter description from docstring
                        desc = self._extract_param_description(method.__doc__, param_name)
                        if desc:
                            param_schema["description"] = desc

                    properties[param_name] = param_schema

                    # Mark as required if no default value
                    if param.default == inspect.Parameter.empty:
                        required.append(param_name)

                # Update function parameters
                if properties:
                    func_obj.parameters = {
                        "type": "object",
                        "properties": properties,
                        "required": required
                    }

            except Exception as e:
                # Log but don't fail - some functions might not need schema fixing
                print(f"Warning: Could not rebuild schema for {func_name}: {e}")

    @staticmethod
    def _python_type_to_json_schema(python_type):
        """
        Convert Python type hint to JSON schema type and items type.

        Handles:
        - Basic types: str, int, bool, float
        - Collections: list, dict, List[T], Dict[K,V]
        - Optional types: Optional[str] -> str
        - Union types: Union[str, None] -> str

        Args:
            python_type: Python type from type hints

        Returns:
            Tuple of (json_type: str, items_type: Optional[str])
            - json_type: The JSON schema type (string, integer, array, etc.)
            - items_type: For arrays, the type of items; None otherwise
        """
        # Check for generic types first (List[str], Dict[str, int], etc.)
        origin = get_origin(python_type)
        items_type = None

        # Handle generic List[T] -> array with items type
        if origin is list:
            args = get_args(python_type)
            if args:
                # Get the item type from List[T]
                item_type = args[0]
                items_type = SchemaFixMixin._get_basic_json_type(item_type)
            return "array", items_type

        # Handle generic Dict[K, V] -> object
        if origin is dict:
            return "object", None

        # Handle Optional types (Union with None)
        if origin is not None:
            # For Optional, Union, etc., get the non-None type
            args = get_args(python_type)
            if args:
                for arg in args:
                    if arg is not type(None):
                        python_type = arg
                        # Recursively handle the unwrapped type
                        return SchemaFixMixin._python_type_to_json_schema(python_type)

        # Get basic type
        json_type = SchemaFixMixin._get_basic_json_type(python_type)
        return json_type, None

    @staticmethod
    def _get_basic_json_type(python_type) -> str:
        """
        Convert a basic Python type to JSON schema type.

        Args:
            python_type: Python type (str, int, list, etc.)

        Returns:
            JSON schema type string
        """
        if python_type == str or python_type == 'str':
            return "string"
        elif python_type == int or python_type == 'int':
            return "integer"
        elif python_type == float or python_type == 'float':
            return "number"
        elif python_type == bool or python_type == 'bool':
            return "boolean"
        elif python_type == list or python_type == 'list':
            return "array"
        elif python_type == dict or python_type == 'dict':
            return "object"
        else:
            return "string"  # Default to string for unknown types

    @staticmethod
    def _extract_param_description(docstring: str, param_name: str) -> str:
        """
        Extract parameter description from docstring.

        Supports formats:
        - :param name: description
        - Args:\n    name: description

        Args:
            docstring: Method docstring
            param_name: Parameter name to find

        Returns:
            Description string or empty string if not found
        """
        if not docstring:
            return ""

        lines = docstring.split('\n')

        # Try :param format
        for line in lines:
            if f":param {param_name}:" in line:
                # Extract description after ":param param_name:"
                parts = line.split(f":param {param_name}:")
                if len(parts) > 1:
                    return parts[1].strip()

        # Try Args: format
        in_args_section = False
        for line in lines:
            line = line.strip()
            if line == "Args:":
                in_args_section = True
                continue
            if in_args_section:
                if line.startswith(param_name + ":"):
                    desc = line.split(":", 1)[1].strip()
                    return desc
                # Stop at next section
                if line.endswith(":") and not line.startswith(" "):
                    break

        return ""
