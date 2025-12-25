"""Database migrations entry point."""
import os
import sys
from pathlib import Path


def upgrade():
    """Run alembic upgrade head."""
    from alembic.config import Config
    from alembic import command

    # Get the package directory where alembic.ini lives
    package_dir = Path(__file__).parent.parent / "control_plane_api"
    alembic_ini = package_dir / "alembic.ini"

    if not alembic_ini.exists():
        print(f"Error: alembic.ini not found at {alembic_ini}")
        sys.exit(1)

    # Create Alembic config
    alembic_cfg = Config(str(alembic_ini))

    # Load .env file from current directory if it exists
    env_file = Path.cwd() / ".env"
    if env_file.exists():
        from dotenv import load_dotenv
        load_dotenv(env_file)

    # Get database URL from environment
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("Error: DATABASE_URL environment variable is not set")
        sys.exit(1)

    # Set the database URL in the config
    alembic_cfg.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))

    # Run the upgrade
    command.upgrade(alembic_cfg, "head")