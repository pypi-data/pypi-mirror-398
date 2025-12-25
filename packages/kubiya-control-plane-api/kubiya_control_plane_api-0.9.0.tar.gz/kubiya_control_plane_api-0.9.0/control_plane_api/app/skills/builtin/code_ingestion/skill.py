"""
Code Ingestion Skill

Provides code repository ingestion capabilities for semantic code analysis,
dependency tracking, and knowledge graph generation from code repositories.
"""
from typing import Dict, Any, List
from control_plane_api.app.skills.base import SkillDefinition, SkillType, SkillCategory, SkillVariant, SkillRequirements
from control_plane_api.app.skills.registry import register_skill


class CodeIngestionSkill(SkillDefinition):
    """Code Ingestion skill for repository analysis and knowledge graph generation"""

    @property
    def type(self) -> SkillType:
        return SkillType.CODE_INGESTION

    @property
    def name(self) -> str:
        return "Code Ingestion"

    @property
    def description(self) -> str:
        return "Ingest and analyze code repositories with automatic dependency extraction, semantic analysis, and knowledge graph generation"

    @property
    def icon(self) -> str:
        return "Code"

    def get_variants(self) -> List[SkillVariant]:
        return [
            SkillVariant(
                id="code_ingestion_standard",
                name="Code Ingestion - Standard",
                description="Standard code ingestion with balanced performance for typical repositories (50-1000 files)",
                category=SkillCategory.COMMON,
                badge="Recommended",
                icon="Code",
                configuration={
                    "batch_size": 50,
                    "session_duration_minutes": 120,
                    "extract_dependencies": True,
                    "extract_exports": True,
                    "auto_cognify": True,
                    "included_patterns": [
                        "**/*.py", "**/*.js", "**/*.ts", "**/*.tsx", "**/*.jsx",
                        "**/*.go", "**/*.java", "**/*.rs"
                    ],
                    "excluded_patterns": [
                        "**/__pycache__/**", "**/*.pyc", "**/node_modules/**",
                        "**/dist/**", "**/build/**", "**/.git/**", "**/.venv/**",
                        "**/venv/**", "**/target/**", "**/vendor/**"
                    ],
                    "max_file_size_kb": 1024,
                    "timeout": 60,
                },
                is_default=True,
            ),
            SkillVariant(
                id="code_ingestion_small_repo",
                name="Code Ingestion - Small Repository",
                description="Optimized for small repositories (<100 files) with faster processing",
                category=SkillCategory.COMMON,
                badge="Fast",
                icon="Zap",
                configuration={
                    "batch_size": 25,
                    "session_duration_minutes": 30,
                    "extract_dependencies": True,
                    "extract_exports": True,
                    "auto_cognify": True,
                    "included_patterns": [
                        "**/*.py", "**/*.js", "**/*.ts", "**/*.tsx", "**/*.jsx"
                    ],
                    "excluded_patterns": [
                        "**/__pycache__/**", "**/node_modules/**", "**/.git/**"
                    ],
                    "max_file_size_kb": 512,
                    "timeout": 30,
                },
                is_default=False,
            ),
            SkillVariant(
                id="code_ingestion_large_repo",
                name="Code Ingestion - Large Repository",
                description="Optimized for large repositories (1000+ files) with parallel processing",
                category=SkillCategory.ADVANCED,
                badge="Powerful",
                icon="Database",
                configuration={
                    "batch_size": 100,
                    "session_duration_minutes": 240,
                    "extract_dependencies": True,
                    "extract_exports": True,
                    "auto_cognify": True,
                    "included_patterns": [
                        "**/*.py", "**/*.js", "**/*.jsx", "**/*.ts", "**/*.tsx",
                        "**/*.go", "**/*.java", "**/*.rs", "**/*.rb", "**/*.php",
                        "**/*.c", "**/*.cpp", "**/*.h", "**/*.hpp"
                    ],
                    "excluded_patterns": [
                        "**/__pycache__/**", "**/*.pyc", "**/node_modules/**",
                        "**/dist/**", "**/build/**", "**/.git/**", "**/.venv/**",
                        "**/venv/**", "**/target/**", "**/vendor/**", "**/.next/**"
                    ],
                    "max_file_size_kb": 2048,
                    "timeout": 120,
                },
                is_default=False,
            ),
            SkillVariant(
                id="code_ingestion_python_only",
                name="Code Ingestion - Python Only",
                description="Specialized for Python repositories with detailed AST analysis",
                category=SkillCategory.COMMON,
                badge="Python",
                icon="FileCode",
                configuration={
                    "batch_size": 50,
                    "session_duration_minutes": 120,
                    "extract_dependencies": True,
                    "extract_exports": True,
                    "extract_docstrings": True,
                    "auto_cognify": True,
                    "included_patterns": ["**/*.py"],
                    "excluded_patterns": [
                        "**/__pycache__/**", "**/*.pyc", "**/.venv/**",
                        "**/venv/**", "**/site-packages/**"
                    ],
                    "max_file_size_kb": 1024,
                    "timeout": 60,
                },
                is_default=False,
            ),
            SkillVariant(
                id="code_ingestion_frontend",
                name="Code Ingestion - Frontend/JavaScript",
                description="Specialized for frontend repositories (React, Vue, Angular, etc.)",
                category=SkillCategory.COMMON,
                badge="Frontend",
                icon="FileCode",
                configuration={
                    "batch_size": 50,
                    "session_duration_minutes": 120,
                    "extract_dependencies": True,
                    "extract_exports": True,
                    "auto_cognify": True,
                    "included_patterns": [
                        "**/*.js", "**/*.jsx", "**/*.ts", "**/*.tsx",
                        "**/*.vue", "**/*.css", "**/*.scss"
                    ],
                    "excluded_patterns": [
                        "**/node_modules/**", "**/dist/**", "**/build/**",
                        "**/.next/**", "**/coverage/**"
                    ],
                    "max_file_size_kb": 512,
                    "timeout": 60,
                },
                is_default=False,
            ),
        ]

    def validate_configuration(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate code ingestion configuration"""
        validated = {
            "batch_size": config.get("batch_size", 50),
            "session_duration_minutes": config.get("session_duration_minutes", 120),
            "extract_dependencies": config.get("extract_dependencies", True),
            "extract_exports": config.get("extract_exports", True),
            "auto_cognify": config.get("auto_cognify", True),
            "included_patterns": config.get("included_patterns", [
                "**/*.py", "**/*.js", "**/*.ts"
            ]),
            "excluded_patterns": config.get("excluded_patterns", [
                "**/__pycache__/**", "**/node_modules/**"
            ]),
            "max_file_size_kb": config.get("max_file_size_kb", 1024),
            "timeout": config.get("timeout", 60),
        }

        # Validate batch size (1-100 per API limits)
        if not (1 <= validated["batch_size"] <= 100):
            raise ValueError("batch_size must be between 1 and 100")

        # Validate session duration (1-1440 minutes = 24 hours)
        if not (1 <= validated["session_duration_minutes"] <= 1440):
            raise ValueError("session_duration_minutes must be between 1 and 1440")

        # Validate max file size (1KB - 10MB)
        if not (1 <= validated["max_file_size_kb"] <= 10240):
            raise ValueError("max_file_size_kb must be between 1 and 10240")

        # Validate timeout (10-300 seconds)
        if not (10 <= validated["timeout"] <= 300):
            raise ValueError("timeout must be between 10 and 300 seconds")

        # Optional parameters
        if "extract_docstrings" in config:
            validated["extract_docstrings"] = bool(config["extract_docstrings"])

        if "context_graph_api_url" in config:
            validated["context_graph_api_url"] = str(config["context_graph_api_url"])

        if "source_type" in config:
            if config["source_type"] not in ["local", "git"]:
                raise ValueError("source_type must be 'local' or 'git'")
            validated["source_type"] = config["source_type"]

        # Git-specific configuration
        if "git_url" in config:
            validated["git_url"] = str(config["git_url"])

        if "git_branch" in config:
            validated["git_branch"] = str(config["git_branch"])

        return validated

    def get_default_configuration(self) -> Dict[str, Any]:
        """Default: standard ingestion with common file patterns"""
        return {
            "batch_size": 50,
            "session_duration_minutes": 120,
            "extract_dependencies": True,
            "extract_exports": True,
            "auto_cognify": True,
            "included_patterns": [
                "**/*.py", "**/*.js", "**/*.ts", "**/*.tsx", "**/*.jsx",
                "**/*.go", "**/*.java", "**/*.rs"
            ],
            "excluded_patterns": [
                "**/__pycache__/**", "**/*.pyc", "**/node_modules/**",
                "**/dist/**", "**/build/**", "**/.git/**", "**/.venv/**",
                "**/venv/**", "**/target/**", "**/vendor/**"
            ],
            "max_file_size_kb": 1024,
            "timeout": 60,
        }

    def get_framework_class_name(self) -> str:
        """
        Get the underlying framework tool class name.

        The implementation should be provided by the kubiya SDK package.
        """
        return "CodeIngestionTools"

    def get_requirements(self) -> SkillRequirements:
        """Get runtime requirements for this skill."""
        return SkillRequirements(
            python_packages=[
                "kubiya>=2.0.3",
                "httpx>=0.28.0",
                "pathlib>=1.0.0",
            ],
            external_dependencies=["Context Graph API"],
            required_env_vars=["CONTEXT_GRAPH_API_URL", "KUBIYA_API_KEY"],
            notes="Code Ingestion skill provides repository analysis and knowledge graph generation. "
                  "Requires Context Graph API to be available. "
                  "Works with local file paths on the agent's filesystem. "
                  "Git repository support requires git binary installed. "
                  "This skill must be explicitly associated with agents/teams - it is not built-in by default."
        )


# Auto-register this skill
register_skill(CodeIngestionSkill())
