from sqlalchemy import (
    Column, Integer, String, Enum, DateTime, ForeignKey, Index, text, Boolean, Numeric
)
import uuid, enum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from dataflow.db import Base


class Organization(Base):

    """TABLE 'ORGANIZATION'

    Attributes:
        id (int): Primary key for the organization.
        uid (UUID): Unique identifier for the organization.
        name (str): Name of the organization.
        invite_code (str): Unique invite code for the organization.
        email_domain (str): Unique email domain associated with the organization.
        spark_enabled_zones (list): List of zone IDs where Spark is enabled.
        created_at (datetime): Timestamp of when the organization was created.
    
    Relationships:
        org_user_assocs: One-to-many relationship with OrganizationUser model.
        custom_servers: One-to-many relationship with CustomServerConfig model.
        onboarding_requests: One-to-many relationship with UserOnboarding model.
        invited_users: One-to-many relationship with InvitedUser model.
        servers: Many-to-many relationship with ServerConfig model via ORGANIZATION_SERVER association table.
        apps: Many-to-many relationship with AppType model via ORGANIZATION_APP_TYPE association table.
        roles: One-to-many relationship with Role model.
        environments: One-to-many relationship with Environment model.
    """

    __tablename__ = "ORGANIZATION"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uid = Column(UUID(as_uuid=True), default=uuid.uuid4, nullable=False, unique=True, server_default=text("gen_random_uuid()"))
    name = Column(String(255), nullable=False)
    invite_code = Column(String(64), nullable=False, unique=True)
    email_domain = Column(String(255), nullable=False)
    spark_enabled_zones = Column(JSONB, default=func.json([]), server_default=text("'[]'::jsonb"))  # List of zone IDs where Spark is enabled
    agent_enabled = Column(Boolean, default=False, server_default='false')
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), server_default=func.now())
    allow_auto_user_onboarding = Column(Boolean, nullable=False, default=True, server_default="true")
    active = Column(Boolean, nullable=False, default=True, server_default="true")
    subscription_id = Column(Integer, ForeignKey('SUBSCRIPTION.id'), nullable=True)
    stripe_customer_id = Column(String, nullable=True)
    credits_balance = Column(Numeric(10, 2), nullable=False, default=0, server_default="0")

    # Relationships
    org_user_assocs = relationship("OrganizationUser", back_populates="organization", cascade="all, delete-orphan")
    # subscriptions = relationship("Subscription", secondary="ORGANIZATION_SUBSCRIPTION", back_populates="organizations")
    onboarding_requests = relationship("UserOnboarding", back_populates="organization", cascade="all, delete-orphan")
    invited_users = relationship("InvitedUser", back_populates="organization", cascade="all, delete-orphan")
    # servers = relationship("ServerConfig", secondary="ORGANIZATION_SERVER", back_populates="organizations")
    apps = relationship("AppType", secondary="ORGANIZATION_APP_TYPE", back_populates="organizations")
    roles = relationship("Role", cascade="all, delete-orphan")
    environments = relationship("Environment", back_populates="organization")

class OnboardingStatus(enum.Enum):

    """Enumeration for organization onboarding status."""

    pending = 'pending'
    rejected = 'rejected'
    accepted = 'accepted'
    partial = 'partial'

class OrganizationOnboarding(Base):

    """TABLE 'ORGANIZATION_ONBOARDING'

    Attributes:
        id (int): Primary key for the onboarding entry.
        name (str): Name of the organization applying for onboarding.
        age (int): Age of the organization.
        domain (str): Domain of the organization.
        no_of_employees (str): Number of employees in the organization.
        address (str): Address of the organization.
        admin_first_name (str): First name of the admin.
        admin_last_name (str): Last name of the admin.
        admin_designation (str): Designation of the admin.
        admin_email (str): Email of the admin.
        admin_username (str): Username of the admin.
        admin_password (str): Password of the admin.
        discovery_source (str): Source through which the organization discovered the platform.
        additional_info (str): Additional information provided by the organization.
        size_of_data (str): Size of data handled by the organization.
        user_id (int): Foreign key referencing the USER table.
        status (OnboardingStatus): Current status of the onboarding application.
    
    Relationships:
        user: Relationship to the User model.
    
    Constraints:
        Index: Ensures unique pending or accepted applications based on organization name.
    """
    
    __tablename__ = 'ORGANIZATION_ONBOARDING'
    __table_args__ = (
        Index(
            'idx_pending_org_application',
            'name',
            unique=True,
            postgresql_where=Column('status').in_([
                OnboardingStatus.pending.value,
                OnboardingStatus.accepted.value
            ])
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    age = Column(Integer, nullable=True)
    domain = Column(String(255), nullable=True)
    no_of_employees = Column(String(50), nullable=True)
    address = Column(String(500), nullable=True)
    admin_first_name = Column(String(100), nullable=False)
    admin_last_name = Column(String(100), nullable=True)
    admin_designation = Column(String(100), nullable=True)
    admin_phone = Column(String(100), nullable=False)
    admin_email = Column(String(255), nullable=False, unique=True)
    admin_username = Column(String(100), nullable=False, unique=True)
    admin_password = Column(String(255), nullable=True)
    organization_website = Column(String(255), nullable=True)
    discovery_source = Column(String(255), nullable=True)
    additional_info = Column(String(1000), nullable=True)
    size_of_data = Column(String(100), nullable=True)
    user_id = Column(Integer, ForeignKey('USER.user_id'), nullable=False)
    status = Column(Enum(OnboardingStatus), default=OnboardingStatus.pending, nullable=False)

    user = relationship("User", back_populates="organization_onboarding")