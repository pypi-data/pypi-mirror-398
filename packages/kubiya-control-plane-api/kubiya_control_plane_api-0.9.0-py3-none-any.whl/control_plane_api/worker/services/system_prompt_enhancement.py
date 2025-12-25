"""
System prompt enhancement framework for runtime-agnostic prompt modifications.

This module provides a flexible system for enhancing agent system prompts with
layered enhancements that can be applied selectively based on runtime type.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional, List
import structlog
import os

logger = structlog.get_logger(__name__)


class RuntimeType(Enum):
    """Runtime types for prompt enhancements."""
    CLAUDE_CODE = "claude_code"
    AGNO = "agno"
    ALL = "all"  # Apply to all runtimes


class SystemPromptEnhancement(ABC):
    """Base class for system prompt enhancements."""

    def __init__(self, runtime_types: Optional[List[RuntimeType]] = None):
        """
        Initialize enhancement.

        Args:
            runtime_types: List of runtimes this enhancement applies to.
                          If None, applies to all runtimes.
        """
        self.runtime_types = runtime_types or [RuntimeType.ALL]

    def applies_to_runtime(self, runtime_type: str) -> bool:
        """
        Check if this enhancement applies to the given runtime.

        Args:
            runtime_type: The runtime type string (e.g., "claude_code", "agno")

        Returns:
            True if enhancement applies to this runtime, False otherwise
        """
        if RuntimeType.ALL in self.runtime_types:
            return True
        return any(rt.value == runtime_type for rt in self.runtime_types)

    @abstractmethod
    def enhance(self, base_prompt: Optional[str]) -> str:
        """
        Enhance the base system prompt.

        Args:
            base_prompt: The base system prompt (may be None or empty)

        Returns:
            Enhanced system prompt
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of this enhancement for logging."""
        pass


class TodoListEnhancement(SystemPromptEnhancement):
    """Inject TODO list instructions for multi-step tasks."""

    def __init__(self):
        # Only apply to claude_code runtime
        super().__init__(runtime_types=[RuntimeType.CLAUDE_CODE])

    @property
    def name(self) -> str:
        return "todo_list_instruction"

    def enhance(self, base_prompt: Optional[str]) -> str:
        """
        Add TODO list instruction to the prompt.

        Args:
            base_prompt: The base system prompt

        Returns:
            Enhanced prompt with TODO list instructions
        """
        enhancement = (
            "\n\n"
            "## Task Management\n"
            "Where suitable for multi step tasks, always create a TODO list "
            "to decouple the task into subtasks. This helps you track progress "
            "and ensures no steps are missed."
        )

        if base_prompt:
            return base_prompt + enhancement
        else:
            return enhancement.lstrip()


class MemoryToolsEnhancement(SystemPromptEnhancement):
    """Inject memory tools usage instructions for persistent knowledge management."""

    def __init__(self):
        # Apply to all runtimes since memory tools are available everywhere
        super().__init__(runtime_types=[RuntimeType.ALL])

    @property
    def name(self) -> str:
        return "memory_tools_instruction"

    def enhance(self, base_prompt: Optional[str]) -> str:
        """
        Add memory tools usage instructions to the prompt.

        Args:
            base_prompt: The base system prompt

        Returns:
            Enhanced prompt with memory tools instructions
        """
        enhancement = (
            "\n\n"
            "## Memory & Knowledge Management\n\n"
            "You have access to powerful memory and knowledge management tools:\n\n"
            "### Memory Tools (recall_memory, store_memory)\n"
            "- **ALWAYS use recall_memory** at the start of conversations to retrieve relevant context\n"
            "- **ALWAYS use store_memory** to save important information for future reference\n"
            "- Store user preferences, decisions, configurations, and important facts\n"
            "- Memory persists across conversations and sessions\n\n"
            "### Knowledge Tools (ingest_knowledge, process_dataset)\n"
            "- Use ingest_knowledge to add documentation, guides, code snippets\n"
            "- Use process_dataset to make ingested knowledge searchable\n"
            "- Knowledge is organized in datasets for semantic search\n\n"
            "### Best Practices\n"
            "1. **Recall First**: Always check memory before answering questions\n"
            "2. **Store Proactively**: Save important context immediately, don't wait\n"
            "3. **Use Natural Language**: Memory search is semantic, use descriptive queries\n"
            "4. **Categorize**: Use metadata to organize memories by type/priority\n"
            "5. **Be Specific**: Store clear, specific information for better recall\n\n"
            "### Example Workflow\n"
            "```\n"
            "# Start of conversation\n"
            "recall_memory(\"user preferences and previous context\")\n\n"
            "# During work\n"
            "store_memory(\"User prefers Python over JavaScript\", metadata={\"type\": \"preference\"})\n"
            "store_memory(\"Production DB is read-only on weekends\", metadata={\"type\": \"policy\"})\n\n"
            "# Before answering\n"
            "recall_memory(\"relevant technical information about kubernetes\")\n"
            "```\n\n"
            "**IMPORTANT**: Memory tools are essential for providing context-aware, personalized assistance. "
            "Always use them proactively, not just when explicitly asked."
        )

        if base_prompt:
            return base_prompt + enhancement
        else:
            return enhancement.lstrip()


class SystemPromptBuilder:
    """
    Builder for system prompts with layered enhancements.

    This class manages a collection of prompt enhancements and applies
    them in order to build the final system prompt.

    Example:
        >>> builder = SystemPromptBuilder()
        >>> builder.add_enhancement(TodoListEnhancement())
        >>> enhanced = builder.build("You are helpful.", "claude_code")
    """

    def __init__(self):
        self._enhancements: List[SystemPromptEnhancement] = []
        self._enabled = True

    def add_enhancement(self, enhancement: SystemPromptEnhancement) -> "SystemPromptBuilder":
        """
        Add a prompt enhancement to the builder.

        Args:
            enhancement: The enhancement to add

        Returns:
            Self for method chaining
        """
        self._enhancements.append(enhancement)
        logger.debug(
            "system_prompt_enhancement_added",
            enhancement=enhancement.name,
            total_enhancements=len(self._enhancements),
        )
        return self

    def remove_enhancement(self, name: str) -> "SystemPromptBuilder":
        """
        Remove an enhancement by name.

        Args:
            name: Name of the enhancement to remove

        Returns:
            Self for method chaining
        """
        self._enhancements = [
            e for e in self._enhancements if e.name != name
        ]
        return self

    def disable(self) -> "SystemPromptBuilder":
        """
        Disable all enhancements (for testing/debugging).

        Returns:
            Self for method chaining
        """
        self._enabled = False
        return self

    def enable(self) -> "SystemPromptBuilder":
        """
        Enable enhancements.

        Returns:
            Self for method chaining
        """
        self._enabled = True
        return self

    def build(
        self,
        base_prompt: Optional[str],
        runtime_type: str,
    ) -> str:
        """
        Build the final system prompt with all applicable enhancements.

        Args:
            base_prompt: The base system prompt from agent config
            runtime_type: The runtime type (claude_code, agno, etc.)

        Returns:
            Enhanced system prompt
        """
        if not self._enabled:
            logger.debug("system_prompt_enhancements_disabled")
            return base_prompt or ""

        # Start with base prompt
        enhanced_prompt = base_prompt or ""

        # Apply each enhancement that applies to this runtime
        applied_enhancements = []
        for enhancement in self._enhancements:
            if enhancement.applies_to_runtime(runtime_type):
                try:
                    enhanced_prompt = enhancement.enhance(enhanced_prompt)
                    applied_enhancements.append(enhancement.name)
                except Exception as e:
                    logger.error(
                        "system_prompt_enhancement_failed",
                        enhancement=enhancement.name,
                        error=str(e),
                        exc_info=True,
                    )
                    # Continue with other enhancements

        if applied_enhancements:
            logger.info(
                "system_prompt_enhancements_applied",
                runtime_type=runtime_type,
                enhancements=applied_enhancements,
                original_length=len(base_prompt or ""),
                enhanced_length=len(enhanced_prompt),
            )

        return enhanced_prompt


def create_default_prompt_builder() -> SystemPromptBuilder:
    """
    Create a system prompt builder with default enhancements.

    Respects environment variables:
    - DISABLE_SYSTEM_PROMPT_ENHANCEMENTS: Set to "true" to disable all enhancements
    - ENABLE_TODO_LIST_ENHANCEMENT: Set to "false" to disable TODO list enhancement
    - ENABLE_MEMORY_TOOLS_ENHANCEMENT: Set to "false" to disable memory tools enhancement

    Returns:
        SystemPromptBuilder with standard enhancements configured
    """
    builder = SystemPromptBuilder()

    # Check if enhancements are globally disabled
    if os.getenv("DISABLE_SYSTEM_PROMPT_ENHANCEMENTS", "false").lower() == "true":
        logger.info("system_prompt_enhancements_disabled_by_config")
        return builder.disable()

    # Add memory tools enhancement (enabled by default for all runtimes)
    if os.getenv("ENABLE_MEMORY_TOOLS_ENHANCEMENT", "true").lower() == "true":
        builder.add_enhancement(MemoryToolsEnhancement())
        logger.debug("memory_tools_enhancement_enabled")

    # Add TODO list enhancement for claude_code (enabled by default)
    if os.getenv("ENABLE_TODO_LIST_ENHANCEMENT", "true").lower() == "true":
        builder.add_enhancement(TodoListEnhancement())
        logger.debug("todo_list_enhancement_enabled")

    # Future enhancements can be added here:
    # builder.add_enhancement(SecurityGuidelinesEnhancement())
    # builder.add_enhancement(CodeStyleEnhancement())

    return builder
