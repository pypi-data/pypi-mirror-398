from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from control_plane_api.app.config import settings
import structlog
import os

logger = structlog.get_logger()

# Lazy-load engine and session to avoid crashing on import if DATABASE_URL not set
_engine = None
_SessionLocal = None

# Create base class for models
Base = declarative_base()

# Detect if running in serverless environment
# Only enable serverless mode in actual Vercel/Lambda, not in local development
IS_SERVERLESS = bool(os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"))


def get_engine():
    """Get or create the database engine optimized for serverless"""
    global _engine
    if _engine is None:
        if not settings.database_url:
            raise RuntimeError(
                "DATABASE_URL not configured. SQLAlchemy-based endpoints are not available. "
                "Please use Supabase-based endpoints instead."
            )

        # Serverless-optimized configuration
        if IS_SERVERLESS:
            logger.info("creating_serverless_database_engine")
            _engine = create_engine(
                settings.database_url,
                # Use NullPool for serverless - no connection pooling, create fresh connections
                poolclass=NullPool,
                # Verify connections are alive before using them
                pool_pre_ping=True,
                # Short connection timeout for serverless
                connect_args={
                    "connect_timeout": 5,
                    "options": "-c statement_timeout=30000",  # 30s query timeout
                    "keepalives": 1,
                    "keepalives_idle": 30,
                    "keepalives_interval": 10,
                    "keepalives_count": 5,
                }
            )
        else:
            # Traditional server configuration with connection pooling
            logger.info("creating_traditional_database_engine")
            _engine = create_engine(
                settings.database_url,
                pool_pre_ping=True,
                pool_size=2,  # Reduced for better resource management
                max_overflow=3,  # Reduced overflow
                pool_recycle=300,  # Recycle connections after 5 minutes
                pool_timeout=10,  # Reduced timeout
                connect_args={
                    "connect_timeout": 10,
                    "options": "-c statement_timeout=30000"
                }
            )

        # Add connection event listeners for better debugging
        @event.listens_for(_engine, "connect")
        def receive_connect(dbapi_conn, connection_record):
            logger.debug("database_connection_established")

        @event.listens_for(_engine, "close")
        def receive_close(dbapi_conn, connection_record):
            logger.debug("database_connection_closed")

        logger.info("database_engine_created", serverless=IS_SERVERLESS)
    return _engine


def get_session_local():
    """Get or create the session factory"""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _SessionLocal


def get_db():
    """Dependency for getting database sessions"""
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        yield db
    except Exception:
        # Rollback on any error during request processing
        db.rollback()
        raise
    finally:
        db.close()


def dispose_engine():
    """
    Dispose of the database engine to release all connections.
    Should be called at the end of serverless function invocations.
    """
    global _engine
    if _engine is not None:
        logger.info("disposing_database_engine")
        _engine.dispose()
        _engine = None


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=get_engine())


def health_check_db():
    """
    Health check for database connectivity.
    Returns True if database is accessible, False otherwise.
    """
    from sqlalchemy.exc import OperationalError, DisconnectionError

    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("database_health_check_passed")
        return True
    except (OperationalError, DisconnectionError) as e:
        logger.error("database_health_check_failed", error=str(e))
        return False
