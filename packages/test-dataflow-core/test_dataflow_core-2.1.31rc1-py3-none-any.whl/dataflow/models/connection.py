from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from dataflow.db import Base

class Connection(Base):
    """TABLE 'CONNECTION'

    Attributes:
        id (int): Primary key for the connection.
        conn_id (str): Identifier for the connection.
        org_id (int): Foreign key referencing the organization.
        description (str): Description of the connection.
        conn_type (str): Type of the connection.
        runtime (str): Runtime environment for the connection.
        slug (str): Slug identifier for the connection.
        status (bool): Status of the connection (active/inactive).
        created_by (str): User who created the connection.
        created_at (datetime): Timestamp of when the connection was created.
        updated_at (datetime): Timestamp of the last update to the connection.
        is_active (bool): Indicates if the connection is active.
    
    Constraints:
        UniqueConstraint: Ensures unique active connections based on conn_id, org_id, runtime, slug, is_active, and created_by.
    """

    __tablename__ = "CONNECTION"

    id = Column(Integer, primary_key=True, index=True)
    conn_id = Column(String, index=True, nullable=False)
    org_id = Column(Integer, ForeignKey("ORGANIZATION.id"), index=True, nullable=False)
    description = Column(String, nullable=True)
    conn_type = Column(String, nullable=False)
    runtime = Column(String, nullable=True)
    slug = Column(String, nullable=True)
    status = Column(Boolean, default=False, server_default='false')
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True, server_default='true')
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    __table_args__ = (
        Index(
            'uq_active_connection_slug',
            'conn_id', 'created_by', 'org_id', 'runtime', 'slug',
            unique=True,
            postgresql_where=deleted_at.is_(None)
        ),
    )
