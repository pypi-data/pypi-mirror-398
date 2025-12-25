"""models.py"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from dataflow.db import Base

class EnvironmentStatus(Base):
    """
    Table ENVIRONMENT_STATUS

    Attributes:
        id (int): Foreign key referencing the ENVIRONMENT table, also the primary key.
        status (str): Current status of the environment.
        comment (str): Additional comments regarding the status.
        status_changed_date (datetime): Timestamp of when the status was last changed.
    """

    __tablename__='ENVIRONMENT_STATUS'

    id = Column(Integer, ForeignKey('ENVIRONMENT.id', ondelete='CASCADE'), primary_key=True, nullable=False)
    status = Column(String, nullable=False)
    comment = Column(String)
    status_changed_date = Column(DateTime, server_default=func.now(), nullable=False)
    