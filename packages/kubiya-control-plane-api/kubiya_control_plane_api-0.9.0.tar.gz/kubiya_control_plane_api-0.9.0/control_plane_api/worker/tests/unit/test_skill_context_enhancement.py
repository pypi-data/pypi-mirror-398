"""Unit tests for skill context enhancement."""
import pytest
from control_plane_api.worker.services.skill_context_enhancement import (
    SkillContextEnhancement,
)
from control_plane_api.worker.services.system_prompt_enhancement import (
    SystemPromptBuilder,
    TodoListEnhancement,
)


class TestSkillContextEnhancement:
    """Test SkillContextEnhancement."""

    def test_applies_to_all_runtimes(self):
        """Test that enhancement applies to all runtimes."""
        enhancement = SkillContextEnhancement([])

        assert enhancement.applies_to_runtime("claude_code")
        assert enhancement.applies_to_runtime("agno")
        assert enhancement.applies_to_runtime("any_runtime")

    def test_name_property(self):
        """Test that enhancement has correct name."""
        enhancement = SkillContextEnhancement([])
        assert enhancement.name == "skill_context"

    def test_enhance_with_no_skills(self):
        """Test enhancement with no skills configured."""
        enhancement = SkillContextEnhancement([])
        base = "You are helpful."

        result = enhancement.enhance(base)
        assert result == base  # Should return unchanged

    def test_enhance_with_skills_without_context(self):
        """Test enhancement with skills that have no context fields."""
        skills = [
            {
                "name": "Shell",
                "type": "shell",
                "configuration": {
                    "timeout": 30,
                    "allowed_commands": ["ls", "cat"],
                }
            }
        ]
        enhancement = SkillContextEnhancement(skills)
        base = "You are helpful."

        result = enhancement.enhance(base)
        assert result == base  # No context fields, so unchanged

    def test_enhance_with_usage_guidelines(self):
        """Test enhancement with usage guidelines."""
        skills = [
            {
                "name": "Shell - Safe",
                "type": "shell",
                "configuration": {
                    "timeout": 30,
                    "usage_guidelines": "Use for read-only operations.\nAvoid destructive commands.",
                }
            }
        ]
        enhancement = SkillContextEnhancement(skills)
        base = "You are helpful."

        result = enhancement.enhance(base)

        assert "Skill Context & Usage Guidelines" in result
        assert "Shell - Safe" in result
        assert "Usage Guidelines:" in result
        assert "Use for read-only operations." in result
        assert "Avoid destructive commands." in result
        assert base in result

    def test_enhance_with_environment_context(self):
        """Test enhancement with environment context."""
        skills = [
            {
                "name": "Debug Shell",
                "type": "shell",
                "configuration": {
                    "environment_context": "Running in debug mode with tracing enabled.",
                }
            }
        ]
        enhancement = SkillContextEnhancement(skills)
        base = "You are helpful."

        result = enhancement.enhance(base)

        assert "Environment Context:" in result
        assert "Running in debug mode" in result

    def test_enhance_with_shell_configuration(self):
        """Test enhancement with custom shell binary and args."""
        skills = [
            {
                "name": "Custom Shell",
                "type": "shell",
                "configuration": {
                    "shell_binary": "/bin/bash",
                    "shell_args": ["-x", "-e"],
                    "usage_guidelines": "Debug shell",
                }
            }
        ]
        enhancement = SkillContextEnhancement(skills)

        result = enhancement.enhance("Base prompt")

        assert "Shell Configuration:" in result
        assert "Binary: `/bin/bash`" in result
        assert "Arguments: `-x -e`" in result

    def test_enhance_with_multiple_skills(self):
        """Test enhancement with multiple skills having context."""
        skills = [
            {
                "name": "Shell - Safe",
                "type": "shell",
                "configuration": {
                    "usage_guidelines": "Read-only operations",
                }
            },
            {
                "name": "Shell - Debug",
                "type": "shell",
                "configuration": {
                    "usage_guidelines": "Debug with tracing",
                    "environment_context": "Debug mode",
                }
            },
        ]
        enhancement = SkillContextEnhancement(skills)

        result = enhancement.enhance("Base")

        assert "Shell - Safe" in result
        assert "Shell - Debug" in result
        assert "Read-only operations" in result
        assert "Debug with tracing" in result
        assert "Debug mode" in result

    def test_enhance_with_empty_base_prompt(self):
        """Test enhancement with empty base prompt."""
        skills = [
            {
                "name": "Shell",
                "type": "shell",
                "configuration": {
                    "usage_guidelines": "Test guidelines",
                }
            }
        ]
        enhancement = SkillContextEnhancement(skills)

        result = enhancement.enhance(None)

        assert "Skill Context & Usage Guidelines" in result
        assert "Test guidelines" in result
        assert not result.startswith("\n")  # Should strip leading newlines

    def test_has_context_fields(self):
        """Test _has_context_fields detection."""
        enhancement = SkillContextEnhancement([])

        # No context
        assert not enhancement._has_context_fields({
            "configuration": {"timeout": 30}
        })

        # Has usage_guidelines
        assert enhancement._has_context_fields({
            "configuration": {"usage_guidelines": "Test"}
        })

        # Has environment_context
        assert enhancement._has_context_fields({
            "configuration": {"environment_context": "Test"}
        })

        # Has shell_binary
        assert enhancement._has_context_fields({
            "configuration": {"shell_binary": "/bin/bash"}
        })

        # Has shell_args
        assert enhancement._has_context_fields({
            "configuration": {"shell_args": ["-x"]}
        })

    def test_has_context_fields_with_empty_strings(self):
        """Test that empty or whitespace-only strings are not considered context."""
        enhancement = SkillContextEnhancement([])

        # Empty usage_guidelines
        assert not enhancement._has_context_fields({
            "configuration": {"usage_guidelines": ""}
        })

        # Whitespace-only usage_guidelines
        assert not enhancement._has_context_fields({
            "configuration": {"usage_guidelines": "   "}
        })

        # Empty environment_context
        assert not enhancement._has_context_fields({
            "configuration": {"environment_context": ""}
        })

    def test_malformed_skill_config(self):
        """Test graceful handling of malformed skill configurations."""
        # Missing configuration key
        skills = [
            {
                "name": "Malformed",
                "type": "shell",
            }
        ]
        enhancement = SkillContextEnhancement(skills)

        # Should not crash
        result = enhancement.enhance("Base")
        assert result == "Base"  # No valid context, returns unchanged

    def test_skill_without_name(self):
        """Test handling of skill without name field."""
        skills = [
            {
                "type": "shell",
                "configuration": {
                    "usage_guidelines": "Test guidelines",
                }
            }
        ]
        enhancement = SkillContextEnhancement(skills)

        result = enhancement.enhance("Base")

        # Should use default name
        assert "Unknown Skill" in result
        assert "Test guidelines" in result


class TestIntegrationWithSystemPromptBuilder:
    """Test integration with SystemPromptBuilder."""

    def test_skill_context_in_builder(self):
        """Test adding skill context enhancement to builder."""
        skills = [
            {
                "name": "Shell",
                "type": "shell",
                "configuration": {
                    "usage_guidelines": "Test guidelines",
                }
            }
        ]

        builder = SystemPromptBuilder()
        builder.add_enhancement(SkillContextEnhancement(skills))

        result = builder.build("Base prompt", "claude_code")

        assert "Base prompt" in result
        assert "Skill Context & Usage Guidelines" in result
        assert "Test guidelines" in result

    def test_skill_context_with_other_enhancements(self):
        """Test skill context enhancement alongside other enhancements."""
        skills = [
            {
                "name": "Shell",
                "type": "shell",
                "configuration": {
                    "usage_guidelines": "Shell guidelines",
                }
            }
        ]

        builder = SystemPromptBuilder()
        builder.add_enhancement(TodoListEnhancement())  # Claude Code only
        builder.add_enhancement(SkillContextEnhancement(skills))  # All runtimes

        # Claude Code gets both
        result_claude = builder.build("Base", "claude_code")
        assert "TODO list" in result_claude or "Task Management" in result_claude
        assert "Skill Context" in result_claude

        # Agno only gets skill context
        result_agno = builder.build("Base", "agno")
        assert "TODO list" not in result_agno and "Task Management" not in result_agno
        assert "Skill Context" in result_agno

    def test_builder_disabled(self):
        """Test that disabled builder returns base prompt unchanged."""
        skills = [
            {
                "name": "Shell",
                "type": "shell",
                "configuration": {
                    "usage_guidelines": "Should not appear",
                }
            }
        ]

        builder = SystemPromptBuilder()
        builder.add_enhancement(SkillContextEnhancement(skills))
        builder.disable()

        result = builder.build("Base", "claude_code")

        assert result == "Base"
        assert "Should not appear" not in result


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
