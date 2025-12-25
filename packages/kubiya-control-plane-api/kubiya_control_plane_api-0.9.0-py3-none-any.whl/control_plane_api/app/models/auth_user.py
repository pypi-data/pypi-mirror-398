"""Auth user model - external table managed by Supabase"""
from sqlalchemy import Column, String, DateTime, Text, Boolean, SmallInteger, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB

from control_plane_api.app.database import Base


class AuthUser(Base):
    """Model for auth.users table (managed by Supabase, read-only)"""

    __tablename__ = "users"
    __table_args__ = (
        {'schema': 'auth', 'extend_existing': True, 'info': {'skip_autogenerate': True}},
    )

    # Primary columns
    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    instance_id = Column(UUID(as_uuid=True), nullable=True)

    # Authentication fields
    aud = Column(String(255), nullable=True)
    role = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    encrypted_password = Column(String(255), nullable=True)

    # Email confirmation
    email_confirmed_at = Column(DateTime(timezone=True), nullable=True)
    confirmation_token = Column(String(255), nullable=True)
    confirmation_sent_at = Column(DateTime(timezone=True), nullable=True)

    # Recovery
    recovery_token = Column(String(255), nullable=True)
    recovery_sent_at = Column(DateTime(timezone=True), nullable=True)

    # Email change
    email_change_token_new = Column(String(255), nullable=True)
    email_change = Column(String(255), nullable=True)
    email_change_sent_at = Column(DateTime(timezone=True), nullable=True)
    email_change_token_current = Column(String(255), nullable=True)
    email_change_confirm_status = Column(SmallInteger, nullable=True, server_default='0')

    # Sign in tracking
    last_sign_in_at = Column(DateTime(timezone=True), nullable=True)
    invited_at = Column(DateTime(timezone=True), nullable=True)

    # Metadata
    raw_app_meta_data = Column(JSONB, nullable=True)
    raw_user_meta_data = Column(JSONB, nullable=True)

    # Flags
    is_super_admin = Column(Boolean, nullable=True)
    is_sso_user = Column(Boolean, nullable=False, server_default='false')
    is_anonymous = Column(Boolean, nullable=False, server_default='false')

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Phone fields
    phone = Column(Text, nullable=True)
    phone_confirmed_at = Column(DateTime(timezone=True), nullable=True)
    phone_change = Column(Text, nullable=True)
    phone_change_token = Column(String(255), nullable=True)
    phone_change_sent_at = Column(DateTime(timezone=True), nullable=True)

    # Reauthentication
    banned_until = Column(DateTime(timezone=True), nullable=True)
    reauthentication_token = Column(String(255), nullable=True)
    reauthentication_sent_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<AuthUser(id={self.id}, email={self.email})>"