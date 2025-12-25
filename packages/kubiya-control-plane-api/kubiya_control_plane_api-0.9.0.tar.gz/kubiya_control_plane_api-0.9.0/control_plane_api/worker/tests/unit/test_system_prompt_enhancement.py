"""Unit tests for system prompt enhancement."""
import pytest
import os
from unittest.mock import patch
from control_plane_api.worker.services.system_prompt_enhancement import (
    SystemPromptBuilder,
    TodoListEnhancement,
    MemoryToolsEnhancement,
    RuntimeType,
    create_default_prompt_builder,
)


class TestTodoListEnhancement:
    """Test TodoListEnhancement."""

    def test_applies_only_to_claude_code(self):
        """Test that enhancement only applies to claude_code runtime."""
        enhancement = TodoListEnhancement()

        assert enhancement.applies_to_runtime("claude_code")
        assert not enhancement.applies_to_runtime("agno")

    def test_name_property(self):
        """Test that enhancement has correct name."""
        enhancement = TodoListEnhancement()
        assert enhancement.name == "todo_list_instruction"

    def test_enhance_empty_prompt(self):
        """Test enhancing an empty base prompt."""
        enhancement = TodoListEnhancement()
        result = enhancement.enhance(None)

        assert "TODO list" in result
        assert "multi step tasks" in result
        assert "Task Management" in result
        assert not result.startswith("\n")  # Should strip leading newlines for empty prompt

    def test_enhance_existing_prompt(self):
        """Test enhancing an existing prompt."""
        enhancement = TodoListEnhancement()
        base = "You are a helpful assistant."
        result = enhancement.enhance(base)

        assert base in result
        assert "TODO list" in result
        assert "multi step tasks" in result
        assert len(result) > len(base)

    def test_enhancement_preserves_base_prompt(self):
        """Test that enhancement doesn't modify the base prompt."""
        enhancement = TodoListEnhancement()
        base = "You are a coding expert. Follow best practices."
        result = enhancement.enhance(base)

        # Base prompt should be unchanged
        assert result.startswith(base)
        # Enhancement should be appended
        assert "TODO list" in result[len(base):]


class TestMemoryToolsEnhancement:
    """Test MemoryToolsEnhancement."""

    def test_applies_to_all_runtimes(self):
        """Test that enhancement applies to all runtimes."""
        enhancement = MemoryToolsEnhancement()

        assert enhancement.applies_to_runtime("claude_code")
        assert enhancement.applies_to_runtime("agno")
        assert enhancement.applies_to_runtime("custom_runtime")

    def test_name_property(self):
        """Test that enhancement has correct name."""
        enhancement = MemoryToolsEnhancement()
        assert enhancement.name == "memory_tools_instruction"

    def test_enhance_empty_prompt(self):
        """Test enhancing an empty base prompt."""
        enhancement = MemoryToolsEnhancement()
        result = enhancement.enhance(None)

        assert "Memory & Knowledge Management" in result
        assert "recall_memory" in result
        assert "store_memory" in result
        assert "ALWAYS use recall_memory" in result
        assert "ALWAYS use store_memory" in result
        assert not result.startswith("\n")  # Should strip leading newlines

    def test_enhance_existing_prompt(self):
        """Test enhancing an existing prompt."""
        enhancement = MemoryToolsEnhancement()
        base = "You are a helpful assistant."
        result = enhancement.enhance(base)

        assert base in result
        assert "recall_memory" in result
        assert "store_memory" in result
        assert "ingest_knowledge" in result
        assert "process_dataset" in result
        assert len(result) > len(base)

    def test_enhancement_includes_best_practices(self):
        """Test that enhancement includes best practices."""
        enhancement = MemoryToolsEnhancement()
        result = enhancement.enhance("Base")

        assert "Best Practices" in result
        assert "Recall First" in result
        assert "Store Proactively" in result
        assert "Use Natural Language" in result
        assert "Categorize" in result
        assert "Be Specific" in result

    def test_enhancement_includes_example_workflow(self):
        """Test that enhancement includes example workflow."""
        enhancement = MemoryToolsEnhancement()
        result = enhancement.enhance("Base")

        assert "Example Workflow" in result
        assert 'recall_memory("user preferences' in result
        assert 'store_memory(' in result
        assert 'metadata=' in result

    def test_enhancement_emphasizes_proactive_usage(self):
        """Test that enhancement emphasizes proactive usage."""
        enhancement = MemoryToolsEnhancement()
        result = enhancement.enhance("Base")

        assert "IMPORTANT" in result
        assert "proactively" in result
        assert "not just when explicitly asked" in result


class TestSystemPromptBuilder:
    """Test SystemPromptBuilder."""

    def test_add_enhancement(self):
        """Test adding enhancements."""
        builder = SystemPromptBuilder()
        enhancement = TodoListEnhancement()

        builder.add_enhancement(enhancement)
        assert len(builder._enhancements) == 1
        assert builder._enhancements[0] == enhancement

    def test_add_multiple_enhancements(self):
        """Test adding multiple enhancements."""
        builder = SystemPromptBuilder()
        enhancement1 = TodoListEnhancement()
        enhancement2 = TodoListEnhancement()  # Would be different in practice

        builder.add_enhancement(enhancement1)
        builder.add_enhancement(enhancement2)
        assert len(builder._enhancements) == 2

    def test_remove_enhancement(self):
        """Test removing enhancements."""
        builder = SystemPromptBuilder()
        enhancement = TodoListEnhancement()

        builder.add_enhancement(enhancement)
        builder.remove_enhancement("todo_list_instruction")
        assert len(builder._enhancements) == 0

    def test_remove_nonexistent_enhancement(self):
        """Test removing an enhancement that doesn't exist."""
        builder = SystemPromptBuilder()
        enhancement = TodoListEnhancement()

        builder.add_enhancement(enhancement)
        builder.remove_enhancement("nonexistent")
        assert len(builder._enhancements) == 1  # Should still have the original

    def test_build_with_no_enhancements(self):
        """Test building with no enhancements."""
        builder = SystemPromptBuilder()
        base = "You are helpful."

        result = builder.build(base, "claude_code")
        assert result == base

    def test_build_applies_runtime_specific_enhancement(self):
        """Test that runtime-specific enhancements are applied correctly."""
        builder = SystemPromptBuilder()
        builder.add_enhancement(TodoListEnhancement())

        # Should apply to claude_code
        result_claude = builder.build("Base prompt", "claude_code")
        assert "TODO list" in result_claude
        assert "Base prompt" in result_claude

        # Should NOT apply to agno
        result_agno = builder.build("Base prompt", "agno")
        assert "TODO list" not in result_agno
        assert result_agno == "Base prompt"

    def test_build_with_empty_base_prompt(self):
        """Test building with empty base prompt."""
        builder = SystemPromptBuilder()
        builder.add_enhancement(TodoListEnhancement())

        result = builder.build(None, "claude_code")
        assert "TODO list" in result
        assert len(result) > 0

    def test_disable_enhancements(self):
        """Test disabling all enhancements."""
        builder = SystemPromptBuilder()
        builder.add_enhancement(TodoListEnhancement())
        builder.disable()

        result = builder.build("Base prompt", "claude_code")
        assert result == "Base prompt"
        assert "TODO list" not in result

    def test_enable_enhancements(self):
        """Test enabling enhancements after disabling."""
        builder = SystemPromptBuilder()
        builder.add_enhancement(TodoListEnhancement())
        builder.disable()
        builder.enable()

        result = builder.build("Base prompt", "claude_code")
        assert "TODO list" in result

    def test_method_chaining(self):
        """Test that builder methods support chaining."""
        builder = SystemPromptBuilder()

        result = (
            builder
            .add_enhancement(TodoListEnhancement())
            .enable()
            .build("Test", "claude_code")
        )

        assert "TODO list" in result
        assert "Test" in result

    def test_build_handles_enhancement_errors(self):
        """Test that build() continues if an enhancement fails."""
        class FailingEnhancement(TodoListEnhancement):
            def enhance(self, base_prompt):
                raise ValueError("Test error")

        builder = SystemPromptBuilder()
        builder.add_enhancement(FailingEnhancement())

        # Should not raise, should return base prompt
        result = builder.build("Base", "claude_code")
        assert result == "Base"

    def test_build_with_empty_runtime_type(self):
        """Test building with empty runtime type."""
        builder = SystemPromptBuilder()
        builder.add_enhancement(TodoListEnhancement())

        result = builder.build("Base", "")
        # Should not match any runtime
        assert result == "Base"


class TestDefaultBuilder:
    """Test create_default_prompt_builder factory."""

    def test_creates_builder_with_todo_enhancement(self):
        """Test that default builder includes TODO enhancement."""
        builder = create_default_prompt_builder()

        result = builder.build("Test prompt", "claude_code")
        assert "TODO list" in result

    def test_creates_builder_with_memory_enhancement(self):
        """Test that default builder includes memory tools enhancement."""
        builder = create_default_prompt_builder()

        # Memory enhancement should apply to all runtimes
        claude_result = builder.build("Test prompt", "claude_code")
        assert "recall_memory" in claude_result
        assert "store_memory" in claude_result

        agno_result = builder.build("Test prompt", "agno")
        assert "recall_memory" in agno_result
        assert "store_memory" in agno_result

    def test_default_builder_respects_runtime(self):
        """Test that default builder respects runtime filtering."""
        builder = create_default_prompt_builder()

        # Claude code should get both TODO and memory enhancements
        claude_result = builder.build("Test", "claude_code")
        assert "TODO list" in claude_result
        assert "recall_memory" in claude_result

        # Agno should only get memory enhancement (not TODO)
        agno_result = builder.build("Test", "agno")
        assert "TODO list" not in agno_result
        assert "recall_memory" in agno_result

    @patch.dict(os.environ, {"DISABLE_SYSTEM_PROMPT_ENHANCEMENTS": "true"})
    def test_disable_via_env_var(self):
        """Test disabling all enhancements via environment variable."""
        builder = create_default_prompt_builder()

        result = builder.build("Test", "claude_code")
        assert "TODO list" not in result
        assert result == "Test"

    @patch.dict(os.environ, {"ENABLE_TODO_LIST_ENHANCEMENT": "false"})
    def test_disable_todo_enhancement_via_env_var(self):
        """Test disabling TODO list enhancement via environment variable."""
        builder = create_default_prompt_builder()

        result = builder.build("Test", "claude_code")
        assert "TODO list" not in result
        # Should still have memory enhancement
        assert "recall_memory" in result

    @patch.dict(os.environ, {"ENABLE_MEMORY_TOOLS_ENHANCEMENT": "false"})
    def test_disable_memory_enhancement_via_env_var(self):
        """Test disabling memory tools enhancement via environment variable."""
        builder = create_default_prompt_builder()

        claude_result = builder.build("Test", "claude_code")
        assert "recall_memory" not in claude_result
        # Should still have TODO enhancement for claude_code
        assert "TODO list" in claude_result

        agno_result = builder.build("Test", "agno")
        assert "recall_memory" not in agno_result
        # Should not have TODO enhancement for agno
        assert "TODO list" not in agno_result

    @patch.dict(os.environ, {"ENABLE_TODO_LIST_ENHANCEMENT": "true"})
    def test_enable_todo_enhancement_explicitly(self):
        """Test that TODO enhancement is enabled when env var is true."""
        builder = create_default_prompt_builder()

        result = builder.build("Test", "claude_code")
        assert "TODO list" in result

    def test_default_builder_is_enabled_by_default(self):
        """Test that builder is enabled by default without env vars."""
        # Clear relevant env vars
        with patch.dict(os.environ, {}, clear=True):
            # Explicitly set only the vars we need (not the enhancement ones)
            with patch.dict(os.environ, {
                "LITELLM_API_KEY": "test",  # May be needed by other code
            }, clear=False):
                builder = create_default_prompt_builder()

                result = builder.build("Test", "claude_code")
                assert "TODO list" in result


class TestRuntimeType:
    """Test RuntimeType enum."""

    def test_enum_values(self):
        """Test that enum has expected values."""
        assert RuntimeType.CLAUDE_CODE.value == "claude_code"
        assert RuntimeType.AGNO.value == "agno"
        assert RuntimeType.ALL.value == "all"

    def test_enum_can_be_compared(self):
        """Test that enum values can be compared."""
        assert RuntimeType.CLAUDE_CODE == RuntimeType.CLAUDE_CODE
        assert RuntimeType.CLAUDE_CODE != RuntimeType.AGNO


class TestIntegrationWithRuntimes:
    """Test integration with actual runtime configs."""

    def test_claude_code_config_integration(self):
        """Test that enhancement works with claude_code config builder."""
        builder = create_default_prompt_builder()
        enhanced = builder.build("You are a coding assistant.", "claude_code")

        assert "You are a coding assistant." in enhanced
        assert "TODO list" in enhanced
        assert "Task Management" in enhanced

    def test_agno_config_integration(self):
        """Test that agno runtime doesn't get claude_code enhancements but does get memory."""
        builder = create_default_prompt_builder()
        enhanced = builder.build("You are helpful.", "agno")

        # Should NOT have TODO enhancement (claude_code only)
        assert "TODO list" not in enhanced
        # Should have memory enhancement (applies to all runtimes)
        assert "recall_memory" in enhanced
        assert "You are helpful." in enhanced

    def test_none_prompt_becomes_empty_string_for_agno(self):
        """Test that None prompt gets memory enhancement for agno."""
        builder = create_default_prompt_builder()
        enhanced = builder.build(None, "agno")

        # Should have memory enhancement even with None base prompt
        assert "recall_memory" in enhanced
        assert len(enhanced) > 0

    def test_none_prompt_gets_enhancement_for_claude_code(self):
        """Test that None prompt still gets enhanced for claude_code."""
        builder = create_default_prompt_builder()
        enhanced = builder.build(None, "claude_code")

        assert "TODO list" in enhanced
        assert len(enhanced) > 0


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
