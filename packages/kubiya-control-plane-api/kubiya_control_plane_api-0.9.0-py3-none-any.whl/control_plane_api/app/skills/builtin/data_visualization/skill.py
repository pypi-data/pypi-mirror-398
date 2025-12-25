"""
Data Visualization Skill

Provides data visualization and diagramming capabilities using Mermaid syntax.
Agents can create flowcharts, sequence diagrams, class diagrams, ER diagrams,
and other visualizations for data intelligence and business intelligence use cases.
"""
from typing import Dict, Any, List
from control_plane_api.app.skills.base import SkillDefinition, SkillType, SkillCategory, SkillVariant
from control_plane_api.app.skills.registry import register_skill


class DataVisualizationSkill(SkillDefinition):
    """Data visualization and diagramming skill"""

    @property
    def type(self) -> SkillType:
        return SkillType.DATA_VISUALIZATION

    @property
    def name(self) -> str:
        return "Data Visualization"

    @property
    def description(self) -> str:
        return "Create diagrams and visualizations using Mermaid syntax for data analysis and BI intelligence"

    @property
    def icon(self) -> str:
        return "BarChart3"

    def get_variants(self) -> List[SkillVariant]:
        return [
            SkillVariant(
                id="diagramming_full",
                name="Full Diagramming Suite",
                description="All diagram types: flowcharts, sequences, class diagrams, ER diagrams, Gantt charts, and more",
                category=SkillCategory.COMMON,
                badge="Recommended",
                icon="BarChart3",
                configuration={
                    "enable_flowchart": True,
                    "enable_sequence": True,
                    "enable_class_diagram": True,
                    "enable_er_diagram": True,
                    "enable_gantt": True,
                    "enable_pie_chart": True,
                    "enable_state_diagram": True,
                    "enable_git_graph": True,
                    "enable_user_journey": True,
                    "enable_quadrant_chart": True,
                    "max_diagram_size": 50000,  # Max characters per diagram
                },
                is_default=True,
            ),
            SkillVariant(
                id="diagramming_data_viz",
                name="Data Visualization",
                description="Focus on data visualization: charts, ER diagrams, and analytics diagrams",
                category=SkillCategory.COMMON,
                badge="Analytics",
                icon="PieChart",
                configuration={
                    "enable_flowchart": False,
                    "enable_sequence": False,
                    "enable_class_diagram": False,
                    "enable_er_diagram": True,
                    "enable_gantt": True,
                    "enable_pie_chart": True,
                    "enable_state_diagram": False,
                    "enable_git_graph": False,
                    "enable_user_journey": False,
                    "enable_quadrant_chart": True,
                    "max_diagram_size": 30000,
                },
                is_default=False,
            ),
            SkillVariant(
                id="diagramming_technical",
                name="Technical Diagrams",
                description="Technical diagrams: flowcharts, sequences, class diagrams, state machines",
                category=SkillCategory.ADVANCED,
                badge="Engineering",
                icon="GitBranch",
                configuration={
                    "enable_flowchart": True,
                    "enable_sequence": True,
                    "enable_class_diagram": True,
                    "enable_er_diagram": True,
                    "enable_gantt": False,
                    "enable_pie_chart": False,
                    "enable_state_diagram": True,
                    "enable_git_graph": True,
                    "enable_user_journey": False,
                    "enable_quadrant_chart": False,
                    "max_diagram_size": 50000,
                },
                is_default=False,
            ),
        ]

    def validate_configuration(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate diagramming configuration"""
        validated = {
            "enable_flowchart": config.get("enable_flowchart", True),
            "enable_sequence": config.get("enable_sequence", True),
            "enable_class_diagram": config.get("enable_class_diagram", True),
            "enable_er_diagram": config.get("enable_er_diagram", True),
            "enable_gantt": config.get("enable_gantt", True),
            "enable_pie_chart": config.get("enable_pie_chart", True),
            "enable_state_diagram": config.get("enable_state_diagram", True),
            "enable_git_graph": config.get("enable_git_graph", True),
            "enable_user_journey": config.get("enable_user_journey", True),
            "enable_quadrant_chart": config.get("enable_quadrant_chart", True),
        }

        # Add max_diagram_size if specified
        max_size = config.get("max_diagram_size", 50000)
        validated["max_diagram_size"] = min(max_size, 100000)  # Cap at 100k characters

        # Add optional theme settings
        if "theme" in config:
            theme = config["theme"]
            if theme in ["default", "dark", "forest", "neutral"]:
                validated["theme"] = theme

        return validated

    def get_default_configuration(self) -> Dict[str, Any]:
        """Default: all diagram types enabled"""
        return {
            "enable_flowchart": True,
            "enable_sequence": True,
            "enable_class_diagram": True,
            "enable_er_diagram": True,
            "enable_gantt": True,
            "enable_pie_chart": True,
            "enable_state_diagram": True,
            "enable_git_graph": True,
            "enable_user_journey": True,
            "enable_quadrant_chart": True,
            "max_diagram_size": 50000,
        }

    def get_framework_class_name(self) -> str:
        """
        Get the underlying framework tool class name.
        Returns the class name for DiagrammingTools.
        """
        return "DataVisualizationTools"


# Auto-register this skill
register_skill(DataVisualizationSkill())
