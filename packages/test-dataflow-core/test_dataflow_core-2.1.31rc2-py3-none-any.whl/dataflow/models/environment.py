from sqlalchemy import (
    Column, Integer, String, Boolean, Text, 
    ForeignKey, DateTime, UniqueConstraint, CheckConstraint, Index
)
from sqlalchemy.orm import relationship, Session
from sqlalchemy.sql import func
from datetime import datetime, timezone
from dataflow.db import Base
from enum import Enum

class EnvironmentAttributes(Base):

    """
    Abstract base class for common environment attributes.

    Attributes:
        name (str): Name of the environment.
        url (str): URL associated with the environment.
        enabled (bool): Indicates if the environment is enabled.
        version (str): Version of the environment.
        is_latest (bool): Indicates if this is the latest version.
        base_env_id (int): ID of the base environment.
        short_name (str): Short name identifier for the environment.
        status (str): Current status of the environment.
        icon (str): Icon representing the environment.
        py_version (str): Python version used in the environment.
        r_version (str): R version used in the environment.
        pip_libraries (str): Pip libraries installed in the environment.
        conda_libraries (str): Conda libraries installed in the environment.
        r_requirements (str): R requirements for the environment.
        created_date (datetime): Timestamp of when the environment was created.
        created_by (str): User who created the environment.
        org_id (int): Foreign key referencing the organization.
    """
    __abstract__ = True 

    name = Column(String, nullable=False)
    url = Column(String)
    enabled = Column(Boolean, default=True, server_default='true')
    version = Column(String, default=0, server_default='0')
    is_latest = Column(Boolean, default=True, server_default='true')
    base_env_id = Column(Integer, default=None)
    short_name = Column(String(5))
    status = Column(String, default="Saved", server_default="Saved")
    icon = Column(String)
    py_version = Column(String)
    r_version = Column(String)
    pip_libraries = Column(Text)
    conda_libraries = Column(Text)
    r_requirements = Column(Text)
    created_date = Column(DateTime, server_default=func.now())
    created_by = Column(String)
    org_id = Column(Integer, ForeignKey('ORGANIZATION.id'))

class Environment(EnvironmentAttributes): 

    """TABLE 'ENVIRONMENT'.
    
    Attributes:
        id (int): Primary key for the environment.
        Extends EnvironmentAttributes for common environment fields.
    
    Relationships:
        organization: Many-to-one relationship with Organization model.
        archived_versions: One-to-many relationship with ArchivedEnvironment model.
    
    Constraints:
        UniqueConstraint: Ensures unique combination of short_name and org_id.
    """

    __tablename__ = 'ENVIRONMENT'
    id = Column(Integer, primary_key=True, autoincrement=True)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    organization = relationship("Organization", back_populates="environments")
    archived_versions = relationship("ArchivedEnvironment", back_populates="original_environment")

    __table_args__ = (
        Index(
            'uq_active_env_short_name',
            'created_by', 'org_id', 'short_name',
            unique=True,
            postgresql_where=deleted_at.is_(None)
        ),
    )

class ArchivedEnvironment(EnvironmentAttributes):

    """TABLE 'ARCHIVED_ENVIRONMENT'.
    
    Attributes:
        id (int): Primary key for the archived environment.
        original_env_id (int): Foreign key referencing the original ENVIRONMENT table.
        Extends EnvironmentAttributes for common environment fields.
    
    Relationships:
        original_environment: Many-to-one relationship with Environment model.
    """

    __tablename__ = 'ARCHIVED_ENVIRONMENT'

    id = Column(Integer, primary_key=True, autoincrement=True)
    original_env_id = Column(Integer, ForeignKey('ENVIRONMENT.id', ondelete='CASCADE'))

    # Relationship with Environment
    original_environment = relationship("Environment", back_populates="archived_versions")

class JobLogs(Base):

    """TABLE 'JOB_LOG'.

    Attributes:
        id (int): Primary key for the job log.
        created_at (datetime): Timestamp of when the job log was created.
        completed_at (datetime): Timestamp of when the job log was completed.
        log_file_name (str): Name of the log file.
        log_file_location (str): Location of the log file.
        status (str): Status of the job.
        created_by (str): User who created the job log.
        org_id (int): Foreign key referencing the organization.
    
    Constraints:
        UniqueConstraint: Ensures unique combination of log_file_name and org_id.
    """
    __tablename__ = "JOB_LOG"
    __table_args__ = (UniqueConstraint('log_file_name', 'org_id', name='_job_log_file_org_uc'),)

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.now, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)
    log_file_name = Column(String, nullable=False)
    log_file_location = Column(String, nullable=False)
    status = Column(String)
    created_by = Column(String)
    org_id = Column(Integer, ForeignKey('ORGANIZATION.id', ondelete='CASCADE'))

class EnvironmentJob(Base):
    """
    TABLE 'ENVIRONMENT_JOB'
    
    Tracks Kubernetes jobs for environment build/revert operations.
    This enables pod-independent job tracking.
    
    Attributes:
        id (int): Primary key
        env_id (int): Foreign key to ENVIRONMENT table
        job_name (str): Kubernetes job name
        operation_type (str): 'build' or 'revert'
        created_at (datetime): When the job was created
    
    Constraints:
        - job_name must be unique
    """
    
    __tablename__ = 'ENVIRONMENT_JOB'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    env_id = Column(Integer, ForeignKey('ENVIRONMENT.id', ondelete='CASCADE'), nullable=False, index=True)
    job_name = Column(String, nullable=False, unique=True, index=True)
    operation_type = Column(String, nullable=False)  # 'build' or 'revert'
    created_at = Column(DateTime, default=datetime.now, server_default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<EnvironmentJob(job_name='{self.job_name}', env_id={self.env_id})>"

class LocalEnvironment(Base):
    
    """TABLE 'LOCAL_ENVIRONMENT'.
    
    Attributes:
        id (int): Primary key for the local environment.
        name (str): Name of the local environment.
        user_name (str): Foreign key referencing the user.
        org_id (int): Foreign key referencing the organization.
        py_version (str): Python version used in the local environment.
        pip_libraries (str): Pip libraries installed in the local environment.
        conda_libraries (str): Conda libraries installed in the local environment.
        status (str): Current status of the local environment.
        cloned_from (str): Source from which the environment was cloned.
        updated_at (datetime): Timestamp of when the local environment was last updated.
        need_refresh (bool): Indicates if the local environment needs a refresh.
    """

    __tablename__ = "LOCAL_ENVIRONMENT"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, index=True)
    user_name = Column(String, ForeignKey('USER.user_name', ondelete='CASCADE'), nullable=False, index=True)
    org_id = Column(Integer, ForeignKey('ORGANIZATION.id', ondelete='CASCADE'), nullable=False, index=True)
    py_version = Column(String)
    pip_libraries = Column(Text)
    conda_libraries = Column(Text)
    status = Column(String, default="Created", server_default="Created")
    cloned_from = Column(String, nullable=True)
    updated_at = Column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    need_refresh = Column(Boolean, default=False, server_default='false')

class EnvType(str, Enum):

    """Enumeration for environment types."""

    dataflow = "dataflow"
    local = "local"

class PipSource(Base):

    """TABLE 'PIP_SOURCE'.
    
    Attributes:
        id (int): Primary key for the pip source.
        org_id (int): Foreign key referencing the organization.
        user_name (str): Foreign key referencing the user (nullable for org-level sources).
        name (str): Name of the pip source.
        url (str): URL of the pip source.
        is_index (bool): Indicates if the source is an index.
        created_at (datetime): Timestamp of when the pip source was created.
        updated_at (datetime): Timestamp of when the pip source was last updated.
        
    Constraints:
        UniqueConstraint: Ensures unique combination of org_id, name, and user_name.
        CheckConstraint: Ensures that if is_index is true, user_name must be null.
    
    Methods:
        get_org_sources(session, org_id): Returns all sources for the given org (org-level).
        get_user_sources(session, org_id, user_name): Returns merged sources for a user in an org (org-level + user-level personal sources).
    """

    __tablename__ = "PIP_SOURCE"

    id = Column(Integer, primary_key=True, autoincrement=True)
    org_id = Column(Integer, ForeignKey("ORGANIZATION.id", ondelete="CASCADE"), nullable=False, index=True)
    user_name = Column(String, ForeignKey("USER.user_name", ondelete="CASCADE"), nullable=True, index=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    is_index = Column(Boolean, default=False, nullable=False, server_default='false')
    created_at = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint("org_id", "name", "user_name", name="uq_pip_source_per_user_org"),
        CheckConstraint("NOT (is_index = TRUE AND user_name IS NOT NULL)", name="check_no_user_index_url"),
    )

    @classmethod
    def get_org_sources(cls, session: Session, org_id: int):

        """
        Returns all sources for the given org (org-level).

        Args:
            session (Session): SQLAlchemy session object.
            org_id (int): Organization ID.
        
        Returns:
            List of PipSource objects for the organization.
        """

        return session.query(cls).filter(
            cls.org_id == org_id,
            cls.user_name == None
        ).all()

    @classmethod
    def get_user_sources(cls, session: Session, org_id: int, user_name: str):
        """
        Returns merged sources for a user in an org (org-level + user-level personal sources).
        
        Args:
            session (Session): SQLAlchemy session object.
            org_id (int): Organization ID.
            user_name (str): User name.
        
        Returns:
            List of PipSource objects for the user in the organization.
        """
        
        return session.query(cls).filter(
            cls.org_id == org_id,
            ((cls.user_name == None) | (cls.user_name == user_name))
        ).all()

