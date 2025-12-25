from sqlalchemy import Column, Integer, ForeignKey, Boolean, Index
from sqlalchemy.orm import relationship
from dataflow.db import Base

class RoleZone(Base):

    """TABLE 'ROLE_ZONE'

    Attributes:
        role_id (int): Foreign key referencing the ROLE table, also part of the primary key.
        zone_id (int): Foreign key referencing the DATAFLOW_ZONE table, also part of the primary key.
        is_default (bool): Indicates if this zone is the default for the role.

    Relationships:
        role: Many-to-one relationship with Role model.
        zone: Many-to-one relationship with DataflowZone model.
    
    Constraints:
        Index: Ensures unique default zone per role.
    """

    __tablename__ = 'ROLE_ZONE'
    
    role_id = Column(Integer, ForeignKey('ROLE.id', ondelete="CASCADE"), primary_key=True)
    zone_id = Column(Integer, ForeignKey('DATAFLOW_ZONE.id', ondelete="CASCADE"), primary_key=True)
    is_default = Column(Boolean, default=False, nullable=False, server_default='false')
    
    __table_args__ = (
        Index('idx_role_runtime_default', 'role_id', unique=True, 
              postgresql_where=is_default.is_(True)),
    )

    role = relationship("Role", back_populates="role_zone_assocs")
    zone = relationship("DataflowZone", back_populates="role_zone_assocs")

    def __repr__(self):
        return f"<RoleZone(role_id={self.role_id}, zone_id={self.zone_id}, is_default={self.is_default})>"