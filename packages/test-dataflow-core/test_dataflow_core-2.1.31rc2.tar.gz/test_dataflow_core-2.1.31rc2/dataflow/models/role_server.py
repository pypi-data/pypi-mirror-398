# models/user_team.py
from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from dataflow.db import Base

class RoleServer(Base):

    """TABLE 'ROLE_SERVER'

    Attributes:
        role_id (int): Foreign key referencing the ROLE table, also part of the primary key.
        server_id (int): Foreign key referencing the SERVER_CONFIG table, also part of the primary key.
    """
    
    __tablename__ = 'ROLE_SERVER'
    __table_args__ = (UniqueConstraint('role_id', 'server_id', name='_role_server_uc'),)

    role_id = Column(Integer, ForeignKey('ROLE.id', ondelete="CASCADE"), nullable=False, primary_key=True)
    server_id = Column(Integer, ForeignKey('SERVER_CONFIG.id', ondelete="CASCADE"), nullable=False, primary_key=True)