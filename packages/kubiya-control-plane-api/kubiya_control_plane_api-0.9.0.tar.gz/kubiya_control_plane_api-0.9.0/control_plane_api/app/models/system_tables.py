from sqlalchemy import Column, String, DateTime, Text, JSON, Boolean, Integer, BigInteger, LargeBinary, CheckConstraint, \
    ForeignKey, Index, Table, MetaData, UniqueConstraint, text, desc
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.orm import relationship
from datetime import datetime

from control_plane_api.app.database import Base

class PolicyAssociation(Base):
    """Policy associations for resources"""

    __tablename__ = "policy_associations"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    organization_id = Column(String(255), nullable=False)
    policy_id = Column(String(255), nullable=False)
    policy_name = Column(String(255), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    enabled = Column(Boolean, nullable=True, default=True, server_default=text("true"))
    priority = Column(Integer, nullable=True, default=0, server_default=text("0"))
    metadata_ = Column("metadata", JSON, nullable=True, default=dict, server_default=text("'{}'::jsonb"))
    created_at = Column(DateTime(timezone=False), nullable=True, default=datetime.utcnow, server_default=text("now()"))
    updated_at = Column(DateTime(timezone=False), nullable=True, default=datetime.utcnow, server_default=text("now()"), onupdate=datetime.utcnow)
    created_by = Column(String(255), nullable=True)

    __table_args__ = (
        UniqueConstraint('policy_id', 'entity_type', 'entity_id', name='unique_policy_association'),
        Index('idx_policy_assoc_org', 'organization_id'),
        Index('idx_policy_assoc_entity', 'entity_type', 'entity_id'),
        Index('idx_policy_assoc_policy', 'policy_id'),
        Index('idx_policy_assoc_enabled', 'enabled'),
        Index('idx_policy_assoc_priority', desc('priority')),
        Index('idx_policy_assoc_entity_enabled', 'entity_type', 'entity_id', 'enabled', desc('priority')),
        CheckConstraint(
            "entity_type IN ('agent', 'team', 'environment')",
            name='policy_associations_entity_type_check'
        ),
        {'schema': 'public'}
    )

    def __repr__(self):
        return f"<PolicyAssociation {self.id} ({self.policy_id} on {self.entity_type}:{self.entity_id})>"
