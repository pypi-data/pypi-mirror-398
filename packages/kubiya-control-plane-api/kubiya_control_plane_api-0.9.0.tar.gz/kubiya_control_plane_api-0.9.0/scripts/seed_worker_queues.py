#!/usr/bin/env python3
"""
Seed the environments and worker_queues tables with default data.

This script populates the database with environments and worker queues for Kubiya agent control plane.
"""

import sys
import os
from pathlib import Path

# Load .env file from current directory if it exists
env_file = Path.cwd() / ".env"
if env_file.exists():
    from dotenv import load_dotenv
    load_dotenv(env_file)

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from control_plane_api.app.database import get_engine
from control_plane_api.app.models.worker import WorkerQueue
from control_plane_api.app.models.environment import Environment
from sqlalchemy.orm import Session
import uuid


# Default environment ID used by worker queues
DEFAULT_ENVIRONMENT_ID = uuid.UUID("89441d4d-639a-4f2f-b204-30b42b65175f")


def seed_environments(session: Session) -> bool:
    """Seed the database with default environments. Returns True if seeded."""

    environments_data = [
        {
            "id": DEFAULT_ENVIRONMENT_ID,
            "organization_id": "kubiya-ai",
            "name": "default",
            "display_name": "Default Environment",
            "description": "Default environment for all workers",
            "tags": [],
            "settings": {},
            "status": "active",
            "created_by": "cb629448-4b7e-46cb-b321-dedefe79c381",
            "worker_token": uuid.UUID("4034ee2f-137c-456d-8616-10c2e5abe404"),
            "execution_environment": {},
            "policy_ids": [],
        },
    ]

    # Check if environments already exist
    existing_count = session.query(Environment).count()
    if existing_count > 0:
        print(f"⚠️  Database already has {existing_count} environments. Skipping environment seed.")
        return False

    print("🌱 Seeding environments...")

    for env_data in environments_data:
        env = Environment(**env_data)
        session.add(env)
        print(f"   ✅ Added {env_data['display_name']} ({env_data['id']})")

    session.commit()
    print(f"\n✨ Successfully seeded {len(environments_data)} environments!")
    return True


def seed_worker_queues(session: Session) -> bool:
    """Seed the database with default worker queues. Returns True if seeded."""

    queues_data = [
        {
            "id": uuid.UUID("e54ecc24-a818-40b6-b554-51005319b293"),
            "organization_id": "kubiya-ai",
            "environment_id": DEFAULT_ENVIRONMENT_ID,
            "name": "my-default-queue",
            "display_name": "My Default Queue",
            "description": "",
            "status": "active",
            "max_workers": 10,
            "heartbeat_interval": 60,
            "tags": [],
            "settings": {},
            "created_by": "cb629448-4b7e-46cb-b321-dedefe79c381",
        },
    ]

    # Check if queues already exist
    existing_count = session.query(WorkerQueue).count()
    if existing_count > 0:
        print(f"⚠️  Database already has {existing_count} worker queues. Skipping worker queue seed.")
        return False

    print("🌱 Seeding worker queues...")

    for queue_data in queues_data:
        queue = WorkerQueue(**queue_data)
        session.add(queue)
        print(f"   ✅ Added {queue_data['name']} ({queue_data['id']})")

    session.commit()
    print(f"\n✨ Successfully seeded {len(queues_data)} worker queues!")
    return True


def seed_all():
    """Seed all tables in the correct order"""

    engine = get_engine()

    with Session(engine) as session:
        # Seed environments first (worker_queues depends on it)
        seed_environments(session)

        # Then seed worker queues
        seed_worker_queues(session)


if __name__ == "__main__":
    try:
        seed_all()
    except Exception as e:
        print(f"❌ Error seeding data: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)