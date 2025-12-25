"""Integration tests for system prompt enhancement with runtimes."""
import pytest
import os
from unittest.mock import patch, MagicMock
from control_plane_api.worker.services.system_prompt_enhancement import (
    create_default_prompt_builder,
    TodoListEnhancement,
    SystemPromptBuilder,
)
from control_plane_api.worker.runtimes.agno.config import build_agno_agent_config
from control_plane_api.worker.runtimes.base import RuntimeExecutionContext


class TestClaudeCodeRuntimeIntegration:
    """Test integration with Claude Code runtime."""

    def test_claude_code_receives_enhanced_prompt(self):
        """Test that Claude Code runtime receives enhanced prompts with TODO instructions."""
        from control_plane_api.worker.runtimes.claude_code.config import _prompt_builder

        base_prompt = "You are a helpful coding assistant."
        enhanced = _prompt_builder.build(base_prompt, "claude_code")

        # Should have base prompt
        assert base_prompt in enhanced

        # Should have TODO list enhancement
        assert "TODO list" in enhanced
        assert "Task Management" in enhanced
        assert "multi step tasks" in enhanced

        # Should be longer than base
        assert len(enhanced) > len(base_prompt)

    def test_claude_code_prompt_builder_singleton(self):
        """Test that Claude Code runtime uses a singleton prompt builder."""
        from control_plane_api.worker.runtimes.claude_code.config import _prompt_builder

        # Should be a SystemPromptBuilder instance
        assert isinstance(_prompt_builder, SystemPromptBuilder)

        # Should have at least one enhancement (TodoList)
        assert len(_prompt_builder._enhancements) >= 1

        # First enhancement should be TodoListEnhancement
        assert isinstance(_prompt_builder._enhancements[0], TodoListEnhancement)

    def test_claude_code_runtime_with_empty_prompt(self):
        """Test Claude Code runtime with no base prompt."""
        from control_plane_api.worker.runtimes.claude_code.config import _prompt_builder

        enhanced = _prompt_builder.build(None, "claude_code")

        # Should still have enhancement
        assert "TODO list" in enhanced
        assert len(enhanced) > 0

    def test_claude_code_runtime_with_long_prompt(self):
        """Test Claude Code runtime with a long base prompt."""
        from control_plane_api.worker.runtimes.claude_code.config import _prompt_builder

        base_prompt = "You are an expert software engineer.\n" * 50
        enhanced = _prompt_builder.build(base_prompt, "claude_code")

        # Should preserve base prompt
        assert base_prompt in enhanced

        # Should add enhancement at the end
        assert enhanced.endswith("Task Management\n" +
                                 "Where suitable for multi step tasks, always create a TODO list " +
                                 "to decouple the task into subtasks. This helps you track progress " +
                                 "and ensures no steps are missed.")


class TestAgnoRuntimeIntegration:
    """Test integration with Agno runtime."""

    def test_agno_does_not_receive_todo_enhancement(self):
        """Test that Agno runtime does NOT receive TODO list enhancement."""
        from control_plane_api.worker.runtimes.agno.config import _prompt_builder

        base_prompt = "You are a helpful assistant."
        enhanced = _prompt_builder.build(base_prompt, "agno")

        # Should have base prompt unchanged
        assert enhanced == base_prompt

        # Should NOT have TODO list enhancement
        assert "TODO list" not in enhanced

    def test_agno_prompt_builder_singleton(self):
        """Test that Agno runtime uses a singleton prompt builder."""
        from control_plane_api.worker.runtimes.agno.config import _prompt_builder

        # Should be a SystemPromptBuilder instance
        assert isinstance(_prompt_builder, SystemPromptBuilder)

        # Should have at least one enhancement (TodoList)
        assert len(_prompt_builder._enhancements) >= 1

        # Even though it has TodoList enhancement, it shouldn't apply to agno
        base = "Test prompt"
        enhanced = _prompt_builder.build(base, "agno")
        assert enhanced == base

    @patch.dict(os.environ, {"LITELLM_API_KEY": "test-key"})
    def test_agno_agent_config_with_enhanced_prompt(self):
        """Test that Agno agent config properly uses enhanced prompts."""
        base_prompt = "You are a data analyst."

        agent = build_agno_agent_config(
            agent_id="test-agent",
            system_prompt=base_prompt,
            model_id="kubiya/claude-sonnet-4",
            skills=[],
        )

        # Agent role should match the base prompt (no TODO enhancement)
        assert agent.role == base_prompt
        assert "TODO list" not in agent.role

    @patch.dict(os.environ, {"LITELLM_API_KEY": "test-key"})
    def test_agno_agent_config_with_no_prompt(self):
        """Test Agno agent config with no system prompt."""
        agent = build_agno_agent_config(
            agent_id="test-agent",
            system_prompt=None,
            model_id="kubiya/claude-sonnet-4",
        )

        # Should use default prompt
        assert agent.role == "You are a helpful AI assistant"
        assert "TODO list" not in agent.role


class TestEnvironmentVariableConfiguration:
    """Test that environment variables control enhancements."""

    @patch.dict(os.environ, {"DISABLE_SYSTEM_PROMPT_ENHANCEMENTS": "true"})
    def test_global_disable_affects_both_runtimes(self):
        """Test that DISABLE_SYSTEM_PROMPT_ENHANCEMENTS disables for both runtimes."""
        # Need to reimport to pick up env var
        import importlib
        from control_plane_api.worker.services import system_prompt_enhancement
        importlib.reload(system_prompt_enhancement)

        builder = system_prompt_enhancement.create_default_prompt_builder()

        # Should not enhance for either runtime
        claude_result = builder.build("Test", "claude_code")
        assert "TODO list" not in claude_result
        assert claude_result == "Test"

        agno_result = builder.build("Test", "agno")
        assert "TODO list" not in agno_result
        assert agno_result == "Test"

    @patch.dict(os.environ, {"ENABLE_TODO_LIST_ENHANCEMENT": "false"})
    def test_disable_specific_enhancement(self):
        """Test that ENABLE_TODO_LIST_ENHANCEMENT=false disables TODO enhancement."""
        # Need to reimport to pick up env var
        import importlib
        from control_plane_api.worker.services import system_prompt_enhancement
        importlib.reload(system_prompt_enhancement)

        builder = system_prompt_enhancement.create_default_prompt_builder()

        # Should not have TODO enhancement
        result = builder.build("Test", "claude_code")
        assert "TODO list" not in result
        assert result == "Test"


class TestMultipleEnhancementsLayering:
    """Test that multiple enhancements can be layered."""

    def test_multiple_enhancements_stack(self):
        """Test that multiple enhancements are applied in order."""
        from control_plane_api.worker.services.system_prompt_enhancement import (
            SystemPromptEnhancement,
            RuntimeType,
        )

        class TestEnhancement1(SystemPromptEnhancement):
            def __init__(self):
                super().__init__(runtime_types=[RuntimeType.CLAUDE_CODE])

            @property
            def name(self):
                return "test_1"

            def enhance(self, base_prompt):
                return (base_prompt or "") + "\n\nEnhancement 1"

        class TestEnhancement2(SystemPromptEnhancement):
            def __init__(self):
                super().__init__(runtime_types=[RuntimeType.CLAUDE_CODE])

            @property
            def name(self):
                return "test_2"

            def enhance(self, base_prompt):
                return (base_prompt or "") + "\n\nEnhancement 2"

        builder = SystemPromptBuilder()
        builder.add_enhancement(TestEnhancement1())
        builder.add_enhancement(TestEnhancement2())

        result = builder.build("Base", "claude_code")

        # Should have base and both enhancements in order
        assert "Base" in result
        assert "Enhancement 1" in result
        assert "Enhancement 2" in result

        # Enhancements should be in order
        idx_base = result.index("Base")
        idx_e1 = result.index("Enhancement 1")
        idx_e2 = result.index("Enhancement 2")
        assert idx_base < idx_e1 < idx_e2

    def test_different_runtimes_get_different_enhancements(self):
        """Test that enhancements can be runtime-specific."""
        from control_plane_api.worker.services.system_prompt_enhancement import (
            SystemPromptEnhancement,
            RuntimeType,
        )

        class ClaudeOnlyEnhancement(SystemPromptEnhancement):
            def __init__(self):
                super().__init__(runtime_types=[RuntimeType.CLAUDE_CODE])

            @property
            def name(self):
                return "claude_only"

            def enhance(self, base_prompt):
                return (base_prompt or "") + "\nClaude Only"

        class AgnoOnlyEnhancement(SystemPromptEnhancement):
            def __init__(self):
                super().__init__(runtime_types=[RuntimeType.AGNO])

            @property
            def name(self):
                return "agno_only"

            def enhance(self, base_prompt):
                return (base_prompt or "") + "\nAgno Only"

        builder = SystemPromptBuilder()
        builder.add_enhancement(ClaudeOnlyEnhancement())
        builder.add_enhancement(AgnoOnlyEnhancement())

        # Claude Code should get Claude enhancement
        claude_result = builder.build("Base", "claude_code")
        assert "Claude Only" in claude_result
        assert "Agno Only" not in claude_result

        # Agno should get Agno enhancement
        agno_result = builder.build("Base", "agno")
        assert "Agno Only" in agno_result
        assert "Claude Only" not in agno_result


class TestRuntimeConfigBuilders:
    """Test integration with actual runtime config builders."""

    @patch.dict(os.environ, {"LITELLM_API_KEY": "test-key"})
    def test_agno_config_builder_integration(self):
        """Test full integration with Agno config builder."""
        agent = build_agno_agent_config(
            agent_id="integration-test",
            system_prompt="You are a DevOps expert.",
            model_id="kubiya/claude-sonnet-4",
        )

        # Role should be the prompt without TODO enhancement
        assert agent.role == "You are a DevOps expert."
        assert "TODO list" not in agent.role

    def test_enhancement_preserves_newlines_and_formatting(self):
        """Test that enhancements preserve newlines and formatting in base prompt."""
        from control_plane_api.worker.runtimes.claude_code.config import _prompt_builder

        base_prompt = """You are a helpful assistant.

Follow these rules:
1. Be concise
2. Be accurate
3. Be helpful"""

        enhanced = _prompt_builder.build(base_prompt, "claude_code")

        # Should preserve base prompt formatting
        assert base_prompt in enhanced

        # Should have enhancement appended
        assert "TODO list" in enhanced


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_enhancement_with_unicode_characters(self):
        """Test that enhancements work with unicode characters."""
        from control_plane_api.worker.runtimes.claude_code.config import _prompt_builder

        base_prompt = "You are a helpful assistant. 你好 🚀"
        enhanced = _prompt_builder.build(base_prompt, "claude_code")

        # Should preserve unicode
        assert base_prompt in enhanced
        assert "TODO list" in enhanced

    def test_enhancement_with_very_long_prompt(self):
        """Test that enhancements work with very long prompts."""
        from control_plane_api.worker.runtimes.claude_code.config import _prompt_builder

        # Create a 10KB prompt
        base_prompt = "You are a helpful assistant.\n" * 500
        enhanced = _prompt_builder.build(base_prompt, "claude_code")

        # Should preserve full base prompt
        assert base_prompt in enhanced

        # Should add enhancement
        assert "TODO list" in enhanced

    def test_enhancement_with_empty_string(self):
        """Test enhancement with empty string (not None)."""
        from control_plane_api.worker.runtimes.claude_code.config import _prompt_builder

        enhanced = _prompt_builder.build("", "claude_code")

        # Should add enhancement even for empty string
        assert "TODO list" in enhanced


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
