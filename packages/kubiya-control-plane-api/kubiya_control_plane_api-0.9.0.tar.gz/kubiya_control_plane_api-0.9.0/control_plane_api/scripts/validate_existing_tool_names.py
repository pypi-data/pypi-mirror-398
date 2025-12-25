#!/usr/bin/env python3
"""
Database Tool Name Validation Script

Scans existing agents, teams, and skills for invalid tool names that don't meet
universal LLM provider requirements. Provides detailed report and optionally fixes them.

Usage:
    # Scan only (no changes):
    python validate_existing_tool_names.py --scan

    # Scan and auto-fix invalid names:
    python validate_existing_tool_names.py --fix

    # Export report to file:
    python validate_existing_tool_names.py --scan --output report.json
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import structlog

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from control_plane_api.app.database import get_session_local
from control_plane_api.app.models.agent import Agent
from control_plane_api.app.models.team import Team
from control_plane_api.app.models.skill import Skill
from control_plane_api.worker.utils.tool_validation import (
    validate_tool_name,
    sanitize_tool_name,
    is_valid_tool_name,
)

logger = structlog.get_logger()


class ToolNameValidator:
    """Validates and optionally fixes tool names in the database."""

    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        SessionLocal = get_session_local()
        self.db = SessionLocal()
        self.issues: List[Dict[str, Any]] = []

    def _extract_tool_names_from_config(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract tool names from various configuration formats.

        Returns:
            List of dicts with {path: str, tool_name: str}
        """
        tool_names = []

        # MCP servers - tool names come from server responses, not config
        # But server names themselves could be used in tool name construction
        if "mcpServers" in config:
            for server_name in config["mcpServers"].keys():
                tool_names.append({
                    "path": f"mcpServers.{server_name}",
                    "tool_name": server_name,
                    "type": "mcp_server_name"
                })

        # Skills - skill names could be tool names
        if "skills" in config and isinstance(config["skills"], list):
            for idx, skill in enumerate(config["skills"]):
                if isinstance(skill, dict) and "name" in skill:
                    tool_names.append({
                        "path": f"skills[{idx}].name",
                        "tool_name": skill["name"],
                        "type": "skill_name"
                    })

        # Custom tools - check for tool definitions
        if "tools" in config and isinstance(config["tools"], list):
            for idx, tool in enumerate(config["tools"]):
                if isinstance(tool, dict):
                    name = tool.get("name") or tool.get("function", {}).get("name")
                    if name:
                        tool_names.append({
                            "path": f"tools[{idx}].name",
                            "tool_name": name,
                            "type": "custom_tool"
                        })

        return tool_names

    async def validate_agents(self) -> Dict[str, Any]:
        """Validate all agent configurations."""
        logger.info("validating_agents")

        agents = self.db.query(Agent).all()

        stats = {
            "total": len(agents),
            "invalid_count": 0,
            "issues": []
        }

        for agent in agents:
            agent_id = str(agent.id)
            agent_name = agent.name or "unnamed"
            config = agent.configuration or {}

            tool_names = self._extract_tool_names_from_config(config)

            for tool_info in tool_names:
                tool_name = tool_info["tool_name"]
                is_valid, error_msg, violations = validate_tool_name(tool_name)

                if not is_valid:
                    issue = {
                        "entity_type": "agent",
                        "entity_id": agent_id,
                        "entity_name": agent_name,
                        "path": tool_info["path"],
                        "tool_name": tool_name,
                        "tool_type": tool_info["type"],
                        "error": error_msg,
                        "violations": violations,
                        "suggested_fix": sanitize_tool_name(tool_name)
                    }
                    stats["issues"].append(issue)
                    stats["invalid_count"] += 1

                    logger.warning(
                        "invalid_agent_tool_name",
                        agent_id=agent_id,
                        agent_name=agent_name,
                        tool_name=tool_name,
                        error=error_msg,
                    )

        self.issues.extend(stats["issues"])
        return stats

    async def validate_teams(self) -> Dict[str, Any]:
        """Validate all team configurations."""
        logger.info("validating_teams")

        teams = self.db.query(Team).all()

        stats = {
            "total": len(teams),
            "invalid_count": 0,
            "issues": []
        }

        for team in teams:
            team_id = str(team.id)
            team_name = team.name or "unnamed"
            config = team.configuration or {}

            tool_names = self._extract_tool_names_from_config(config)

            for tool_info in tool_names:
                tool_name = tool_info["tool_name"]
                is_valid, error_msg, violations = validate_tool_name(tool_name)

                if not is_valid:
                    issue = {
                        "entity_type": "team",
                        "entity_id": team_id,
                        "entity_name": team_name,
                        "path": tool_info["path"],
                        "tool_name": tool_name,
                        "tool_type": tool_info["type"],
                        "error": error_msg,
                        "violations": violations,
                        "suggested_fix": sanitize_tool_name(tool_name)
                    }
                    stats["issues"].append(issue)
                    stats["invalid_count"] += 1

                    logger.warning(
                        "invalid_team_tool_name",
                        team_id=team_id,
                        team_name=team_name,
                        tool_name=tool_name,
                        error=error_msg,
                    )

        self.issues.extend(stats["issues"])
        return stats

    async def validate_skills(self) -> Dict[str, Any]:
        """Validate all skill configurations."""
        logger.info("validating_skills")

        skills = self.db.query(Skill).all()

        stats = {
            "total": len(skills),
            "invalid_count": 0,
            "issues": []
        }

        for skill in skills:
            skill_id = str(skill.id)
            skill_name = skill.name or "unnamed"

            # Validate skill name itself
            is_valid, error_msg, violations = validate_tool_name(skill_name)

            if not is_valid:
                issue = {
                    "entity_type": "skill",
                    "entity_id": skill_id,
                    "entity_name": skill_name,
                    "path": "name",
                    "tool_name": skill_name,
                    "tool_type": "skill_name",
                    "error": error_msg,
                    "violations": violations,
                    "suggested_fix": sanitize_tool_name(skill_name)
                }
                stats["issues"].append(issue)
                stats["invalid_count"] += 1

                logger.warning(
                    "invalid_skill_name",
                    skill_id=skill_id,
                    skill_name=skill_name,
                    error=error_msg,
                )

        self.issues.extend(stats["issues"])
        return stats

    async def fix_issues(self) -> Dict[str, Any]:
        """
        Attempt to fix invalid tool names by sanitizing them.

        WARNING: This modifies the database!
        """
        if self.dry_run:
            logger.info("dry_run_mode_no_changes_will_be_made")
            return {
                "fixed": 0,
                "failed": 0,
                "message": "Dry run - no changes made"
            }

        logger.warning("fixing_invalid_tool_names_this_modifies_database")

        fixed = 0
        failed = 0
        fix_details = []

        for issue in self.issues:
            try:
                entity_type = issue["entity_type"]
                entity_id = issue["entity_id"]
                suggested_fix = issue["suggested_fix"]

                # For skill names, update the name directly
                if entity_type == "skill" and issue["path"] == "name":
                    skill = self.db.query(Skill).filter(Skill.id == entity_id).first()
                    if skill:
                        skill.name = suggested_fix
                        self.db.commit()

                        fixed += 1
                        fix_details.append({
                            "entity": f"{entity_type}:{entity_id}",
                            "original": issue["tool_name"],
                            "fixed": suggested_fix,
                            "path": issue["path"]
                        })

                        logger.info(
                            "fixed_tool_name",
                            entity_type=entity_type,
                            entity_id=entity_id,
                            original=issue["tool_name"],
                            fixed=suggested_fix,
                        )
                else:
                    # For nested config paths, log but don't auto-fix
                    # (requires deep config modification)
                    logger.warning(
                        "cannot_auto_fix_nested_config",
                        entity_type=entity_type,
                        entity_id=entity_id,
                        path=issue["path"],
                        requires_manual_fix=True,
                    )
                    failed += 1

            except Exception as e:
                logger.error(
                    "failed_to_fix_tool_name",
                    entity_type=issue["entity_type"],
                    entity_id=issue["entity_id"],
                    error=str(e),
                )
                failed += 1

        return {
            "fixed": fixed,
            "failed": failed,
            "details": fix_details
        }

    async def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive validation report."""
        agent_stats = await self.validate_agents()
        team_stats = await self.validate_teams()
        skill_stats = await self.validate_skills()

        report = {
            "summary": {
                "total_entities_scanned": (
                    agent_stats["total"] +
                    team_stats["total"] +
                    skill_stats["total"]
                ),
                "total_invalid_tool_names": len(self.issues),
                "agents": {
                    "total": agent_stats["total"],
                    "invalid": agent_stats["invalid_count"]
                },
                "teams": {
                    "total": team_stats["total"],
                    "invalid": team_stats["invalid_count"]
                },
                "skills": {
                    "total": skill_stats["total"],
                    "invalid": skill_stats["invalid_count"]
                }
            },
            "issues": self.issues,
            "recommendations": self._generate_recommendations()
        }

        return report

    def close(self):
        """Close database connection."""
        if self.db:
            self.db.close()

    def _generate_recommendations(self) -> List[str]:
        """Generate actionable recommendations based on issues found."""
        recommendations = []

        if not self.issues:
            recommendations.append(
                "✅ All tool names are valid! No action needed."
            )
            return recommendations

        recommendations.append(
            f"⚠️  Found {len(self.issues)} invalid tool names that need attention."
        )

        # Group issues by type
        issue_types = {}
        for issue in self.issues:
            issue_type = issue["tool_type"]
            if issue_type not in issue_types:
                issue_types[issue_type] = []
            issue_types[issue_type].append(issue)

        for issue_type, issues in issue_types.items():
            recommendations.append(
                f"   • {len(issues)} invalid {issue_type}(s)"
            )

        recommendations.append("")
        recommendations.append("Recommended actions:")
        recommendations.append("1. Run with --fix to automatically sanitize fixable tool names")
        recommendations.append("2. Review the detailed issues list below")
        recommendations.append("3. Manually update nested configuration paths that cannot be auto-fixed")
        recommendations.append("4. Test agent/team executions after fixes")

        return recommendations


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate and fix tool names in database"
    )
    parser.add_argument(
        "--scan",
        action="store_true",
        help="Scan for invalid tool names (default, no changes)"
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Fix invalid tool names (WARNING: modifies database)"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output report to JSON file"
    )

    args = parser.parse_args()

    # Default to scan if nothing specified
    if not args.scan and not args.fix:
        args.scan = True

    validator = ToolNameValidator(dry_run=not args.fix)

    print("=" * 70)
    print("Tool Name Validation Script")
    print("=" * 70)
    print(f"Mode: {'FIX (modifies database!)' if args.fix else 'SCAN (read-only)'}")
    print()

    # Generate report
    report = await validator.generate_report()

    # Print summary
    print("\nValidation Summary:")
    print("-" * 70)
    print(f"Total entities scanned: {report['summary']['total_entities_scanned']}")
    print(f"Total invalid tool names: {report['summary']['total_invalid_tool_names']}")
    print()
    print(f"Agents:  {report['summary']['agents']['total']} scanned, "
          f"{report['summary']['agents']['invalid']} invalid")
    print(f"Teams:   {report['summary']['teams']['total']} scanned, "
          f"{report['summary']['teams']['invalid']} invalid")
    print(f"Skills:  {report['summary']['skills']['total']} scanned, "
          f"{report['summary']['skills']['invalid']} invalid")
    print()

    # Print recommendations
    for rec in report["recommendations"]:
        print(rec)

    # Fix if requested
    if args.fix:
        print("\n" + "=" * 70)
        print("Applying Fixes...")
        print("=" * 70)

        fix_result = await validator.fix_issues()

        print(f"\nFixed: {fix_result['fixed']}")
        print(f"Failed: {fix_result['failed']}")

        if fix_result.get("details"):
            print("\nFixed tool names:")
            for detail in fix_result["details"]:
                print(f"  • {detail['entity']}: {detail['original']} → {detail['fixed']}")

    # Print detailed issues
    if report["issues"]:
        print("\n" + "=" * 70)
        print("Detailed Issues:")
        print("=" * 70)

        for idx, issue in enumerate(report["issues"][:10], 1):  # Show first 10
            print(f"\n{idx}. {issue['entity_type'].upper()}: {issue['entity_name']}")
            print(f"   Tool: {issue['tool_name']}")
            print(f"   Path: {issue['path']}")
            print(f"   Error: {issue['error']}")
            print(f"   Suggested fix: {issue['suggested_fix']}")

        if len(report["issues"]) > 10:
            print(f"\n... and {len(report['issues']) - 10} more issues")

    # Export report if requested
    if args.output:
        with open(args.output, "w") as f:
            json.dump(report, f, indent=2)
        print(f"\nFull report exported to: {args.output}")

    print("\n" + "=" * 70)

    # Close database connection
    validator.close()

    # Exit with error code if issues found
    sys.exit(1 if report["issues"] else 0)


if __name__ == "__main__":
    asyncio.run(main())
