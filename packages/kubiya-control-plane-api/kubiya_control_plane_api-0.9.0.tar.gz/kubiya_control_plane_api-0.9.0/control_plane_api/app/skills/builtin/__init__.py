"""
Built-in Skills Module

Contains all built-in skill definitions that are part of the Control Plane.
Each skill is in its own dedicated folder with proper structure.
"""
from .file_system import FileSystemSkill
from .shell import ShellSkill
from .python import PythonSkill
from .docker import DockerSkill
from .workflow_executor import WorkflowExecutorSkill
from .file_generation import FileGenerationSkill
from .data_visualization import DataVisualizationSkill
from .contextual_awareness import ContextualAwarenessSkill
from .knowledge_api import KnowledgeAPISkill
from .cognitive_memory import CognitiveMemorySkill
from .code_ingestion import CodeIngestionSkill
from .agent_communication import AgentCommunicationSkill
from .remote_filesystem import RemoteFilesystemSkill
from .slack import SlackSkill

__all__ = [
    "FileSystemSkill",
    "ShellSkill",
    "PythonSkill",
    "DockerSkill",
    "WorkflowExecutorSkill",
    "FileGenerationSkill",
    "DataVisualizationSkill",
    "ContextualAwarenessSkill",
    "KnowledgeAPISkill",
    "CognitiveMemorySkill",
    "CodeIngestionSkill",
    "AgentCommunicationSkill",
    "RemoteFilesystemSkill",
    "SlackSkill",
]
