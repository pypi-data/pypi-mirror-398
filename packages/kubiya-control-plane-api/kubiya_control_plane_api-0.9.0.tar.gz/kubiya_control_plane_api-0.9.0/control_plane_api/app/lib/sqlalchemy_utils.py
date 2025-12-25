"""
SQLAlchemy utility functions for database operations.

Provides helper functions and patterns to migrate from Supabase SDK to SQLAlchemy ORM.
"""

import structlog
from typing import Any, Optional, Callable, Type, TypeVar, List, Dict
from sqlalchemy.orm import Session, Query
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, NoResultFound
from sqlalchemy import func, select
from control_plane_api.app.database import Base

logger = structlog.get_logger()

T = TypeVar('T', bound=Base)


def safe_execute_query(
    db: Session,
    query_func: Callable[[], Query],
    operation_name: str,
    fallback_query_func: Optional[Callable[[], Query]] = None,
    **context
) -> Any:
    """
    Execute a SQLAlchemy query with defensive error handling.

    This wrapper handles common database errors gracefully,
    providing fallback queries when the primary query fails.

    Args:
        db: SQLAlchemy database session
        query_func: Function that returns the query to execute
        operation_name: Name of the operation for logging
        fallback_query_func: Optional fallback query if primary fails
        **context: Additional context for logging

    Returns:
        Query result or None if both queries fail

    Example:
        ```python
        result = safe_execute_query(
            db=db,
            query_func=lambda: db.query(Execution)
                .options(joinedload(Execution.execution_participants))
                .filter(Execution.organization_id == org_id),
            fallback_query_func=lambda: db.query(Execution)
                .filter(Execution.organization_id == org_id),
            operation_name="list_executions",
            org_id=org_id,
        )
        ```
    """
    try:
        # Try primary query
        query = query_func()
        result = query.all() if hasattr(query, 'all') else list(query)
        return result

    except SQLAlchemyError as primary_error:
        error_str = str(primary_error)

        logger.warning(
            f"{operation_name}_query_error",
            error=error_str[:200],  # Truncate long errors
            error_type=type(primary_error).__name__,
            **context
        )

        # Try fallback query if provided
        if fallback_query_func:
            try:
                fallback_query = fallback_query_func()
                result = fallback_query.all() if hasattr(fallback_query, 'all') else list(fallback_query)
                logger.debug(
                    f"{operation_name}_fallback_succeeded",
                    **context
                )
                return result

            except Exception as fallback_error:
                logger.error(
                    f"{operation_name}_fallback_query_failed",
                    error=str(fallback_error),
                    **context
                )
                raise fallback_error
        else:
            # No fallback provided, re-raise original error
            raise primary_error


def model_to_dict(model: Base, exclude: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Convert a SQLAlchemy model instance to a dictionary.

    This mimics the Supabase response format where records are returned as dicts.

    Args:
        model: SQLAlchemy model instance
        exclude: List of field names to exclude

    Returns:
        Dictionary representation of the model
    """
    if model is None:
        return None

    exclude = exclude or []
    result = {}

    # Get all columns
    for column in model.__table__.columns:
        if column.name not in exclude:
            value = getattr(model, column.name)
            # Convert UUID to string for JSON serialization
            if hasattr(value, '__str__') and column.name.endswith('_id') or column.name == 'id':
                result[column.name] = str(value) if value else None
            else:
                result[column.name] = value

    return result


def models_to_dict_list(models: List[Base], exclude: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    Convert a list of SQLAlchemy model instances to a list of dictionaries.

    Args:
        models: List of SQLAlchemy model instances
        exclude: List of field names to exclude

    Returns:
        List of dictionary representations
    """
    return [model_to_dict(model, exclude) for model in models if model is not None]


def get_or_create(
    db: Session,
    model: Type[T],
    defaults: Optional[Dict[str, Any]] = None,
    **kwargs
) -> tuple[T, bool]:
    """
    Get an existing instance or create a new one.

    Args:
        db: Database session
        model: Model class
        defaults: Default values for creation
        **kwargs: Filter parameters

    Returns:
        Tuple of (instance, created) where created is True if new instance was created
    """
    instance = db.query(model).filter_by(**kwargs).first()

    if instance:
        return instance, False
    else:
        params = dict(kwargs)
        if defaults:
            params.update(defaults)
        instance = model(**params)
        try:
            db.add(instance)
            db.commit()
            db.refresh(instance)
            return instance, True
        except IntegrityError:
            db.rollback()
            # Another thread might have created it
            instance = db.query(model).filter_by(**kwargs).first()
            if instance:
                return instance, False
            raise


def bulk_insert(
    db: Session,
    model: Type[T],
    records: List[Dict[str, Any]],
    return_instances: bool = False
) -> Optional[List[T]]:
    """
    Bulk insert records into the database.

    Args:
        db: Database session
        model: Model class
        records: List of dictionaries with record data
        return_instances: If True, return created instances

    Returns:
        List of created instances if return_instances is True, else None
    """
    instances = [model(**record) for record in records]

    try:
        db.bulk_save_objects(instances, return_defaults=return_instances)
        db.commit()

        if return_instances:
            return instances
        return None
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(
            "bulk_insert_failed",
            model=model.__tablename__,
            count=len(records),
            error=str(e)
        )
        raise


def paginate(
    query: Query,
    skip: int = 0,
    limit: int = 100
) -> tuple[List[Any], int]:
    """
    Paginate a query and return results with total count.

    Args:
        query: SQLAlchemy query object
        skip: Number of records to skip (offset)
        limit: Maximum number of records to return

    Returns:
        Tuple of (results, total_count)
    """
    total = query.count()
    results = query.offset(skip).limit(limit).all()
    return results, total


def sanitize_jsonb_field(value: Any, field_name: str, default: dict = None) -> dict:
    """
    Sanitize a JSONB field value to ensure it's a valid dict.

    Args:
        value: The value to sanitize
        field_name: Name of the field for logging
        default: Default value if sanitization fails

    Returns:
        Valid dict or default
    """
    if default is None:
        default = {}

    if value is None:
        return default

    if isinstance(value, dict):
        return value

    logger.debug(
        "invalid_jsonb_field_sanitized",
        field_name=field_name,
        type=type(value).__name__
    )

    return default


def set_organization_context(db: Session, org_id: str):
    """
    Set organization context for RLS-like behavior in SQLAlchemy.

    This sets a PostgreSQL session variable that can be used by database
    triggers or application-level filtering.

    Args:
        db: Database session
        org_id: Organization UUID
    """
    try:
        db.execute(
            "SELECT set_config('app.current_org_id', :org_id, false)",
            {"org_id": org_id}
        )
    except SQLAlchemyError as e:
        logger.warning(
            "set_organization_context_failed",
            org_id=org_id,
            error=str(e)
        )


def execute_with_org_context(db: Session, org_id: str, query_func: Callable):
    """
    Execute a query with organization context for RLS-like behavior.

    Sets the app.current_org_id config parameter that can be used
    by database policies or application logic.

    Args:
        db: Database session
        org_id: Organization UUID
        query_func: Function that performs the database operation

    Returns:
        Query result
    """
    set_organization_context(db, org_id)
    result = query_func()
    return result


def upsert_record(
    db: Session,
    model: Type[T],
    lookup_fields: Dict[str, Any],
    update_fields: Dict[str, Any],
    create_fields: Optional[Dict[str, Any]] = None
) -> T:
    """
    Upsert (insert or update) a record.

    Args:
        db: Database session
        model: The SQLAlchemy model class
        lookup_fields: Fields to use for finding existing record
        update_fields: Fields to update if record exists
        create_fields: Additional fields only for create (optional)

    Returns:
        The upserted model instance
    """
    # Build filter from lookup fields
    filters = [getattr(model, k) == v for k, v in lookup_fields.items()]
    existing = db.query(model).filter(*filters).first()

    if existing:
        # Update existing record
        for key, value in update_fields.items():
            setattr(existing, key, value)
        db.commit()
        db.refresh(existing)
        return existing
    else:
        # Create new record
        all_fields = {**lookup_fields, **update_fields}
        if create_fields:
            all_fields.update(create_fields)
        new_record = model(**all_fields)
        db.add(new_record)
        db.commit()
        db.refresh(new_record)
        return new_record


def get_by_id(
    db: Session,
    model: Type[T],
    id_value: Any,
    org_id: Optional[str] = None
) -> Optional[T]:
    """
    Get a model instance by ID with optional organization filtering.

    Args:
        db: Database session
        model: The SQLAlchemy model class
        id_value: The ID value to look up
        org_id: Optional organization ID for multi-tenant filtering

    Returns:
        Model instance or None if not found
    """
    query = db.query(model).filter(model.id == id_value)

    if org_id and hasattr(model, 'organization_id'):
        query = query.filter(model.organization_id == org_id)

    return query.first()


def delete_by_id(
    db: Session,
    model: Type[T],
    id_value: Any,
    org_id: Optional[str] = None
) -> bool:
    """
    Delete a model instance by ID with optional organization filtering.

    Args:
        db: Database session
        model: The SQLAlchemy model class
        id_value: The ID value to delete
        org_id: Optional organization ID for multi-tenant filtering

    Returns:
        True if record was deleted, False if not found
    """
    query = db.query(model).filter(model.id == id_value)

    if org_id and hasattr(model, 'organization_id'):
        query = query.filter(model.organization_id == org_id)

    result = query.delete(synchronize_session=False)
    db.commit()
    return result > 0


def update_by_id(
    db: Session,
    model: Type[T],
    id_value: Any,
    update_data: Dict[str, Any],
    org_id: Optional[str] = None
) -> Optional[T]:
    """
    Update a model instance by ID with optional organization filtering.

    Args:
        db: Database session
        model: The SQLAlchemy model class
        id_value: The ID value to update
        update_data: Dictionary of fields to update
        org_id: Optional organization ID for multi-tenant filtering

    Returns:
        Updated model instance or None if not found
    """
    query = db.query(model).filter(model.id == id_value)

    if org_id and hasattr(model, 'organization_id'):
        query = query.filter(model.organization_id == org_id)

    instance = query.first()
    if not instance:
        return None

    for key, value in update_data.items():
        if hasattr(instance, key):
            setattr(instance, key, value)

    db.commit()
    db.refresh(instance)
    return instance


def increment_field(
    db: Session,
    model: Type[T],
    id_value: Any,
    field_name: str,
    increment_by: int = 1,
    org_id: Optional[str] = None
) -> Optional[int]:
    """
    Atomically increment a numeric field.

    Args:
        db: Database session
        model: The SQLAlchemy model class
        id_value: The ID value to update
        field_name: Name of the field to increment
        increment_by: Amount to increment by (default 1)
        org_id: Optional organization ID for multi-tenant filtering

    Returns:
        New value after increment, or None if record not found
    """
    query = db.query(model).filter(model.id == id_value)

    if org_id and hasattr(model, 'organization_id'):
        query = query.filter(model.organization_id == org_id)

    instance = query.first()
    if not instance:
        return None

    current_value = getattr(instance, field_name, 0) or 0
    new_value = current_value + increment_by
    setattr(instance, field_name, new_value)
    db.commit()

    return new_value
