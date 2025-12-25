from sqlalchemy import Column , Integer, String, Boolean, ForeignKey, UniqueConstraint, Enum, JSON
from sqlalchemy.orm import relationship
from dataflow.db import Base
from dataflow.models.environment import EnvType

class OrganizationUser(Base):
    """TABLE 'ORGANIZATION_USER'

    Attributes:
        org_id (int): Foreign key referencing the ORGANIZATION table, also part of the primary key.
        user_id (int): Foreign key referencing the USER table, also part of the primary key.
        role_id (int): Foreign key referencing the ROLE table.
        active_env_short_name (str): Short name of the active environment for the user in the organization.
        active_env_type (EnvType): Type of the active environment for the user in the organization.
        active_server_id (int): Foreign key referencing the CUSTOM_SERVER table.
        show_server_page (bool): Indicates if the server page should be shown to the user.
        monthly_allocation (int): Monthly allocation for the user in the organization.
        used_cost (JSON): Current month's cost breakdown for the user (total, connections, secrets, environments, server_usage).
    
    Relationships:
        user: Relationship to the User model.
        role: Relationship to the Role model.
        organization: Relationship to the Organization model.

    Constraints:
        UniqueConstraint: Ensures unique combination of org_id and user_id.
    """
    __tablename__ = "ORGANIZATION_USER"
    __table_args__ = (UniqueConstraint('org_id', 'user_id', name='uq_org_user'),)

    org_id = Column(Integer, ForeignKey('ORGANIZATION.id', ondelete="CASCADE"), primary_key=True, nullable=False)
    user_id = Column(Integer, ForeignKey('USER.user_id', ondelete="CASCADE"), primary_key=True, nullable=False)
    role_id = Column(Integer, ForeignKey('ROLE.id', ondelete="SET NULL"), nullable=False)
    active_env_short_name = Column(String, nullable=True)
    active_env_type = Column(Enum(EnvType), nullable=True)
    active_server_id = Column(Integer, ForeignKey('SERVER_CONFIG.id', ondelete="SET NULL"))
    show_server_page = Column(Boolean, default = True, server_default='true')
    monthly_allocation = Column(Integer, nullable=True, default=0, server_default='0')
    used_cost = Column(JSON, nullable=True)

    # Relationships
    user = relationship("User", back_populates="org_user_assocs")
    role = relationship("Role", back_populates="org_user_assocs")
    organization = relationship("Organization", back_populates="org_user_assocs")

class OrganizationAppType(Base):

    """TABLE 'ORGANIZATION_APP_TYPE'

    Attributes:
        org_id (int): Foreign key referencing the ORGANIZATION table, also part of the primary key.
        app_type_id (int): Foreign key referencing the APP_TYPE table, also part of the primary key.
    """

    __tablename__ = "ORGANIZATION_APP_TYPE"

    org_id = Column(Integer, ForeignKey('ORGANIZATION.id', ondelete="CASCADE"), primary_key=True, nullable=False)
    app_type_id = Column(Integer, ForeignKey('APP_TYPE.id', ondelete="CASCADE"), primary_key=True, nullable=False)

# class OrganizationSubscription(Base):
    
#     """TABLE 'ORGANIZATION_SUBSCRIPTION'

#     Attributes:
#         org_id (int): Foreign key referencing the ORGANIZATION table, also part of the primary key.
#         subscription_id (int): Foreign key referencing the SUBSCRIPTION table.
#     """

#     __tablename__ = "ORGANIZATION_SUBSCRIPTION"

#     org_id = Column(Integer, ForeignKey('ORGANIZATION.id', ondelete="CASCADE"), primary_key=True, nullable=False)
#     subscription_id = Column(Integer, ForeignKey('SUBSCRIPTION.id', ondelete="CASCADE"), primary_key=True, nullable=False)