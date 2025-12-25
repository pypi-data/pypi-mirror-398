"""Orchestration and namespace models"""
from sqlalchemy import Column, String, DateTime, Text, JSON, UUID, CheckConstraint, Index, UniqueConstraint, text
from sqlalchemy.sql import func
from datetime import datetime
import uuid

from control_plane_api.app.database import Base


class Namespace(Base):
    """Model for Temporal Cloud namespaces provisioned for each organization"""

    __tablename__ = "namespaces"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'), nullable=False)
    organization_id = Column(String(255), nullable=False)
    namespace_name = Column(String(255), nullable=False)
    status = Column(String(50), server_default=text("'provisioning'::character varying"), nullable=False)
    temporal_host = Column(String(255), nullable=True)
    api_key_encrypted = Column(Text, nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=True)

    __table_args__ = (
        UniqueConstraint('namespace_name', name='namespaces_namespace_name_key'),
        Index('idx_namespaces_organization_id', 'organization_id'),
        Index('idx_namespaces_status', 'status'),
    )

    def __repr__(self):
        return f"<Namespace(namespace_name={self.namespace_name}, status={self.status})>"


class TemporalNamespace(Base):
    """Model for Temporal Cloud namespaces provisioned per organization"""

    __tablename__ = "temporal_namespaces"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'), nullable=False)
    organization_id = Column(String(255), nullable=False)
    namespace_name = Column(String(255), nullable=False)
    account_id = Column(String(255), nullable=True)
    region = Column(String(50), server_default=text("'aws-us-east-1'::character varying"), nullable=True)
    api_key_encrypted = Column(Text, nullable=True)
    certificate_encrypted = Column(Text, nullable=True)
    status = Column(String(50), server_default=text("'pending'::character varying"), nullable=True)
    provisioning_workflow_id = Column(String(255), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=True)
    provisioned_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(String(255), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "status::text = ANY (ARRAY['pending'::character varying, 'provisioning'::character varying, 'ready'::character varying, 'error'::character varying, 'archived'::character varying]::text[])",
            name='temporal_namespaces_status_check'
        ),
        Index('idx_temporal_namespaces_organization_id', 'organization_id'),
        Index('idx_temporal_namespaces_status', 'status'),
    )

    def __repr__(self):
        return f"<TemporalNamespace(namespace_name={self.namespace_name}, status={self.status}, organization_id={self.organization_id})>"
