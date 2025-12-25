from sqlalchemy import Column, String, Enum, DateTime, Integer, func, ForeignKey, UniqueConstraint, Boolean
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from dataflow.db import Base

class ProjectDetails(Base):

    """TABLE 'PROJECT_DETAIL'
    Attributes:
        project_id (int): Primary key for the project detail entry.
        project_name (str): Name of the project.
        git_url (str): URL of the Git repository.
        git_branch (str): Branch of the Git repository.
        git_folder (str): Folder path in the Git repository.
        type (str): Foreign key referencing the APP_TYPE table.
        slug (str): Slug identifier for the project.
        runtime (str): Runtime environment for the project.
        py_env (int): Foreign key referencing the PYTHON_ENV table.
        launch_url (str): URL to launch the project.
        status (str): Deployment status of the project.
        visibility (str): Project visibility (PUBLIC, ORG, TEAM).
        team_ids (list): List of team IDs that have access to this project.
        last_deployed (datetime): Timestamp of the last deployment.
        created_at (datetime): Timestamp of when the project was created.
        created_by (str): User who created the project.
        org_id (int): Foreign key referencing the ORGANIZATION table.
        airflow_config_file (str): Path to the Airflow configuration file.
        custom_image (bool): Whether this project uses a custom Docker image.
        repository_type (str): Type of repository server (docker=docker.io, github=ghcr.io).
        image_repository (str): Docker image repository/namespace (e.g., 'dataflowsnapshot').
        image_name (str): Docker image name (e.g., 'dataflow-hub').
        image_tag (str): Docker image tag (e.g., 'latest', 'v1.0.0').
        exposed_port (int): Port exposed by the custom image.
        private_repo (bool): Whether the image repository is private.
        registry_secret_id (int): Foreign key referencing the VARIABLE table for registry credentials.
    
    Relationships:
        app_type: Relationship to the AppType model.
    
    Constraints:
        UniqueConstraint: Ensures unique combination of org_id and slug.
    """
    __tablename__ = "PROJECT_DETAIL"
    __table_args__ = (UniqueConstraint('org_id', 'slug', name='uq_project_org_slug'),)
    
    project_id = Column(Integer, primary_key=True, autoincrement=True)
    project_name = Column(String, nullable=False)
    git_url = Column(String)
    git_branch = Column(String, nullable=True)
    git_folder = Column(String, nullable=True)
    type = Column(String, ForeignKey('APP_TYPE.name'), nullable=False)
    slug = Column(String, nullable=False)
    runtime = Column(String, nullable=False)
    py_env = Column(Integer, nullable=True)
    launch_url = Column(String, nullable=True)  
    status = Column(Enum("pending", "created" ,"deployed", "stopped", "failed", name="deployment_status"), default="created", server_default="created")
    visibility = Column(Enum("PUBLIC", "ORG", "TEAM", name="project_visibility"), default="ORG", server_default="ORG", nullable=False)
    team_ids = Column(ARRAY(Integer), nullable=True)
    last_deployed = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    created_by = Column(String, nullable=False)
    org_id = Column(Integer, ForeignKey('ORGANIZATION.id', ondelete='CASCADE'), nullable=False)
    airflow_config_file = Column(String, nullable=True)
    custom_image = Column(Boolean, default=False, server_default='false', nullable=False)
    repository_type = Column(String, nullable=True)
    image_repository = Column(String, nullable=True)
    image_name = Column(String, nullable=True)
    image_tag = Column(String, nullable=True)
    exposed_port = Column(Integer, nullable=True)
    private_repo = Column(Boolean, default=False, server_default='false', nullable=True)
    registry_secret_id = Column(Integer, ForeignKey('VARIABLE.id'), nullable=True)

    app_type = relationship("AppType")
    registry_secret = relationship("Variable", foreign_keys=[registry_secret_id])
