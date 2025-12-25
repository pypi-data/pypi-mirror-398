"""
Skill Definitions Router

Provides endpoints to query available skill types, variants, and templates
from the skill registry.
"""
from fastapi import APIRouter
from typing import List, Dict, Any
import structlog

from control_plane_api.app.skills import get_all_skills, get_skill, SkillType

logger = structlog.get_logger()

router = APIRouter()


@router.get("/definitions")
async def list_skill_definitions():
    """
    Get all available skill definitions with their variants.

    This returns the registry of all skill types that can be instantiated,
    along with their predefined variants/presets.
    """
    skills = get_all_skills()

    result = []
    for skill in skills:
        result.append(skill.to_dict())

    logger.info(f"Returning {len(result)} skill definitions")
    return {"skills": result}


@router.get("/definitions/{skill_type}")
async def get_skill_definition(skill_type: str):
    """
    Get a specific skill definition by type.

    Returns detailed information about a skill type including all variants.
    """
    try:
        ts_type = SkillType(skill_type)
    except ValueError:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Skill type '{skill_type}' not found")

    skill = get_skill(ts_type)
    if not skill:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Skill type '{skill_type}' not registered")

    return skill.to_dict()


@router.get("/definitions/{skill_type}/variants")
async def list_skill_variants(skill_type: str):
    """
    Get all variants/presets for a specific skill type.

    Variants are predefined configurations (e.g., "Read Only", "Full Access")
    that users can quickly apply.
    """
    try:
        ts_type = SkillType(skill_type)
    except ValueError:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Skill type '{skill_type}' not found")

    skill = get_skill(ts_type)
    if not skill:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Skill type '{skill_type}' not registered")

    variants = skill.get_variants()
    return {
        "type": skill.type.value,
        "name": skill.name,
        "variants": [v.model_dump() for v in variants]
    }


@router.get("/templates")
async def list_skill_templates():
    """
    Get all predefined skill templates (flattened variants).

    This is a convenience endpoint that returns all variants from all skills
    as a flat list of ready-to-use templates.
    """
    skills = get_all_skills()

    templates = []
    for skill in skills:
        for variant in skill.get_variants():
            templates.append({
                "id": variant.id,
                "name": variant.name,
                "type": skill.type.value,
                "description": variant.description,
                "icon": variant.icon or skill.icon,
                "icon_type": skill.icon_type,
                "category": variant.category.value,
                "badge": variant.badge,
                "configuration": variant.configuration,
                "is_default": variant.is_default,
            })

    logger.info(f"Returning {len(templates)} skill templates")
    return {"templates": templates}


@router.post("/definitions/{skill_type}/validate")
async def validate_skill_configuration(skill_type: str, configuration: Dict[str, Any]):
    """
    Validate a configuration for a specific skill type.

    Returns the validated and normalized configuration.
    """
    try:
        ts_type = SkillType(skill_type)
    except ValueError:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=f"Invalid skill type: {skill_type}")

    skill = get_skill(ts_type)
    if not skill:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Skill type '{skill_type}' not registered")

    try:
        validated_config = skill.validate_configuration(configuration)
        return {
            "valid": True,
            "configuration": validated_config
        }
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=f"Invalid configuration: {str(e)}")
