from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from dataflow.db import Base

class DataflowZone(Base):

    """TABLE 'DATAFLOW_ZONE'.
    
    Attributes:
        id (int): Primary key for the dataflow zone.
        slug (str): Unique slug identifier for the zone.
        display_name (str): Human-readable name for the zone.
        is_runtime (bool): Indicates if the zone is a runtime zone.
        subdomain (str): Subdomain associated with the zone.
        display_order (int): Order for displaying the zone in lists.
    
    Relationships:
        role_zone_assocs: One-to-many relationship with RoleZone model.
    """

    __tablename__ = "DATAFLOW_ZONE"

    id = Column(Integer, primary_key=True, autoincrement=True)
    slug = Column(String, unique=True, nullable=False)
    display_name = Column(String, nullable=False)
    is_runtime = Column(Boolean, default=False, server_default='false')
    subdomain = Column(String)
    display_order = Column(Integer, default=0, server_default='0')

    role_zone_assocs = relationship("RoleZone", back_populates="zone")

    def __repr__(self):
        return f"<DataflowZone(id={self.id}, slug='{self.slug}', display_name='{self.display_name}', display_order={self.display_order})>"