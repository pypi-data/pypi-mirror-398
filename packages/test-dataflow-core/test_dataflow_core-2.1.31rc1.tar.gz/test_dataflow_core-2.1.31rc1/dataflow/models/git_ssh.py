"""models.py"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from dataflow.db import Base

class GitSSH(Base):

    """TABLE 'GIT_SSH'

    Attributes:
        id (int): Primary key for the Git SSH entry.
        user_name (str): Foreign key referencing the USER table.
        org_id (int): Foreign key referencing the ORGANIZATION table.
        description (str): Description of the Git SSH entry.
        key_name (str): Name of the SSH key.
        created_date (datetime): Timestamp of when the entry was created.
        last_used_date (datetime): Timestamp of when the entry was last used.
    
    Constraints:
        UniqueConstraint: Ensures unique combination of user_name, key_name, and org_id.
    """

    __tablename__ = 'GIT_SSH'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_name = Column(String, ForeignKey('USER.user_name', ondelete="CASCADE"), nullable=False)
    org_id = Column(Integer, ForeignKey("ORGANIZATION.id"), index=True, nullable=False)
    description = Column(String)
    key_name = Column(String, nullable=False)
    created_date = Column(DateTime, server_default=func.now(), nullable=False)
    last_used_date = Column(DateTime)

    __table_args__ = (
        UniqueConstraint(user_name, key_name, org_id, name='user_name_key_name_org_id_unique'),
    )