# models/user_team.py
from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from dataflow.db import Base

class UserTeam(Base):

    """TABLE 'USER_TEAM'

    Attributes:
        user_id (int): Foreign key referencing the USER table, also part of the primary key.
        team_id (int): Foreign key referencing the TEAM table, also part of the primary key.
    
    Constraints:
        UniqueConstraint: Ensures unique user-team pairs.
    """

    __tablename__ = 'USER_TEAM'
    __table_args__ = (UniqueConstraint('user_id', 'team_id', name='_user_team_uc'),)

    user_id = Column(Integer, ForeignKey('USER.user_id', ondelete="CASCADE"), nullable=False, primary_key=True)
    team_id = Column(Integer, ForeignKey('TEAM.team_id', ondelete="CASCADE"), nullable=False, primary_key=True)