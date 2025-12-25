"""LLM Model database model"""
from sqlalchemy import Column, String, Boolean, Text, JSON, Integer
from datetime import datetime
from sqlalchemy import DateTime
import uuid as uuid_module

from control_plane_api.app.database import Base


class LLMModel(Base):
    """
    LLM Model configuration for agent execution.

    Stores available LLM models that can be used by agents and teams,
    including provider information, compatibility, and UI metadata.
    """

    __tablename__ = "llm_models"

    id = Column(String, primary_key=True, default=lambda: str(uuid_module.uuid4()))

    # Model identification
    value = Column(String, unique=True, nullable=False, index=True)
    label = Column(String, nullable=False)
    provider = Column(String, nullable=False, index=True)
    model_type = Column(String, default="text-generation", nullable=False, index=True)
    # Model type: "text-generation" (LLM), "embedding" (embedding model), "multimodal", etc.

    # UI metadata
    logo = Column(String, nullable=True)
    description = Column(Text, nullable=True)

    # Status and flags
    enabled = Column(Boolean, default=True, nullable=False, index=True)
    recommended = Column(Boolean, default=False, nullable=False)

    # Runtime compatibility
    # Store list of compatible runtime types (e.g., ["default", "claude_code"])
    compatible_runtimes = Column(JSON, default=list, nullable=False)

    # Model capabilities and metadata
    capabilities = Column(JSON, default=dict, nullable=False)
    # Example: {"vision": true, "function_calling": true, "max_tokens": 4096}

    # Pricing information (optional)
    pricing = Column(JSON, default=dict, nullable=True)
    # Example: {"input_cost_per_1k": 0.01, "output_cost_per_1k": 0.03}

    # Display order (lower = shown first)
    display_order = Column(Integer, default=1000, nullable=False)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(String, nullable=True)  # User ID who created this model entry

    def __repr__(self):
        return f"<LLMModel(id={self.id}, value={self.value}, provider={self.provider})>"

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "value": self.value,
            "label": self.label,
            "provider": self.provider,
            "model_type": self.model_type,
            "logo": self.logo,
            "description": self.description,
            "enabled": self.enabled,
            "recommended": self.recommended,
            "compatible_runtimes": self.compatible_runtimes,
            "capabilities": self.capabilities,
            "pricing": self.pricing,
            "display_order": self.display_order,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
