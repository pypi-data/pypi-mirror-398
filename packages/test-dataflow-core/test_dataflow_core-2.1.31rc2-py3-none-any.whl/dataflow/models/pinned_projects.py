from sqlalchemy import Column, Integer, ForeignKey, DateTime, UniqueConstraint, func
from dataflow.db import Base
from datetime import datetime

class PinnedProject(Base):

    """TABLE 'PINNED_PROJECT'

    Attributes:
        id (int): Primary key for the pinned project entry.
        user_id (int): Foreign key referencing the USER table.
        project_id (int): Foreign key referencing the PROJECT_DETAIL table.
        pinned_at (datetime): Timestamp of when the project was pinned.

    Constraints:
        UniqueConstraint: Ensures unique combination of user_id and project_id.
    """
    
    __tablename__ = "PINNED_PROJECT"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('USER.user_id', ondelete="CASCADE"), index=True)
    project_id = Column(Integer, ForeignKey('PROJECT_DETAIL.project_id', ondelete="CASCADE"), index=True)
    pinned_at = Column(DateTime, default=datetime.utcnow, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "project_id", name="uix_user_project"),
    )