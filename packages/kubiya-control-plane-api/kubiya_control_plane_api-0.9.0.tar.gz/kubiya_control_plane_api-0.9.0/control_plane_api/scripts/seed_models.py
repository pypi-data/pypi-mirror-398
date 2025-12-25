"""
Seed script for populating LLM models in the database.

Run this script to populate the database with default Kubiya-supported models.

Usage:
    python -m control_plane_api.scripts.seed_models
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from control_plane_api.app.database import SessionLocal
from control_plane_api.app.models.llm_model import LLMModel
from datetime import datetime


# Default models to seed
DEFAULT_MODELS = [
    {
        "value": "kubiya/claude-sonnet-4",
        "label": "Claude Sonnet 4",
        "provider": "Anthropic",
        "logo": "/logos/claude-color.svg",
        "description": "Most intelligent model with best reasoning capabilities",
        "enabled": True,
        "recommended": True,
        "compatible_runtimes": ["default", "claude_code"],
        "capabilities": {
            "vision": False,
            "function_calling": True,
            "max_tokens": 8192,
            "context_window": 200000,
        },
        "display_order": 1,
    },
    {
        "value": "kubiya/claude-opus-4",
        "label": "Claude Opus 4",
        "provider": "Anthropic",
        "logo": "/logos/claude-color.svg",
        "description": "Powerful model for complex tasks requiring deep analysis",
        "enabled": True,
        "recommended": False,
        "compatible_runtimes": ["default", "claude_code"],
        "capabilities": {
            "vision": True,
            "function_calling": True,
            "max_tokens": 4096,
            "context_window": 200000,
        },
        "display_order": 2,
    },
    {
        "value": "kubiya/claude-3-5-sonnet-20241022",
        "label": "Claude 3.5 Sonnet",
        "provider": "Anthropic",
        "logo": "/logos/claude-color.svg",
        "description": "Previous generation Sonnet with excellent performance",
        "enabled": True,
        "recommended": False,
        "compatible_runtimes": ["default", "claude_code"],
        "capabilities": {
            "vision": True,
            "function_calling": True,
            "max_tokens": 8192,
            "context_window": 200000,
        },
        "display_order": 3,
    },
    {
        "value": "kubiya/gpt-4o",
        "label": "GPT-4o",
        "provider": "OpenAI",
        "logo": "/thirdparty/logos/openai.svg",
        "description": "Fast and capable model with vision support",
        "enabled": True,
        "recommended": False,
        "compatible_runtimes": ["default"],
        "capabilities": {
            "vision": True,
            "function_calling": True,
            "max_tokens": 16384,
            "context_window": 128000,
        },
        "display_order": 4,
    },
    {
        "value": "kubiya/gpt-4-turbo",
        "label": "GPT-4 Turbo",
        "provider": "OpenAI",
        "logo": "/thirdparty/logos/openai.svg",
        "description": "Enhanced GPT-4 with improved speed and capabilities",
        "enabled": True,
        "recommended": False,
        "compatible_runtimes": ["default"],
        "capabilities": {
            "vision": True,
            "function_calling": True,
            "max_tokens": 4096,
            "context_window": 128000,
        },
        "display_order": 5,
    },
    {
        "value": "kubiya/gpt-4o-mini",
        "label": "GPT-4o Mini",
        "provider": "OpenAI",
        "logo": "/thirdparty/logos/openai.svg",
        "description": "Cost-effective model for simpler tasks",
        "enabled": True,
        "recommended": False,
        "compatible_runtimes": ["default"],
        "capabilities": {
            "vision": True,
            "function_calling": True,
            "max_tokens": 16384,
            "context_window": 128000,
        },
        "display_order": 6,
    },
    {
        "value": "kubiya/gemini-pro",
        "label": "Gemini Pro",
        "provider": "Google",
        "logo": "/thirdparty/logos/google.svg",
        "description": "Google's powerful multimodal model",
        "enabled": True,
        "recommended": False,
        "compatible_runtimes": ["default"],
        "capabilities": {
            "vision": True,
            "function_calling": True,
            "max_tokens": 8192,
            "context_window": 1000000,
        },
        "display_order": 7,
    },
]


def seed_models(force: bool = False):
    """
    Seed the database with default models.

    Args:
        force: If True, update existing models. If False, skip existing models.
    """
    db = SessionLocal()
    try:
        created_count = 0
        updated_count = 0
        skipped_count = 0

        for model_data in DEFAULT_MODELS:
            # Check if model exists
            existing = db.query(LLMModel).filter(LLMModel.value == model_data["value"]).first()

            if existing:
                if force:
                    # Update existing model
                    for key, value in model_data.items():
                        setattr(existing, key, value)
                    existing.updated_at = datetime.utcnow()
                    print(f"✓ Updated: {model_data['label']} ({model_data['value']})")
                    updated_count += 1
                else:
                    print(f"⊙ Skipped (exists): {model_data['label']} ({model_data['value']})")
                    skipped_count += 1
            else:
                # Create new model
                new_model = LLMModel(**model_data)
                db.add(new_model)
                print(f"✓ Created: {model_data['label']} ({model_data['value']})")
                created_count += 1

        db.commit()

        print("\n" + "=" * 60)
        print("Seeding complete!")
        print(f"  Created: {created_count}")
        print(f"  Updated: {updated_count}")
        print(f"  Skipped: {skipped_count}")
        print(f"  Total: {len(DEFAULT_MODELS)}")
        print("=" * 60)

    except Exception as e:
        db.rollback()
        print(f"\n❌ Error seeding models: {e}")
        raise
    finally:
        db.close()


def clear_models():
    """Clear all models from the database (use with caution!)"""
    db = SessionLocal()
    try:
        count = db.query(LLMModel).delete()
        db.commit()
        print(f"✓ Cleared {count} models from database")
    except Exception as e:
        db.rollback()
        print(f"❌ Error clearing models: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Seed LLM models database")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Update existing models (default: skip existing)",
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear all models before seeding (DANGEROUS)",
    )

    args = parser.parse_args()

    if args.clear:
        confirm = input("⚠️  This will delete ALL models. Are you sure? (yes/no): ")
        if confirm.lower() == "yes":
            clear_models()
        else:
            print("Cancelled.")
            sys.exit(0)

    print("Seeding models...")
    print("=" * 60)
    seed_models(force=args.force)
