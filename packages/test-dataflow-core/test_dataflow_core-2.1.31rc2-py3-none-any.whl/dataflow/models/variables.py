from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, func, UniqueConstraint, CheckConstraint, Boolean, Enum, Index
from dataflow.db import Base
import enum

class DataType(str, enum.Enum):

    """Enumeration for variable data types."""

    raw = "raw"
    json = "json"
    file = "file"
class Variable(Base):
    
    """TABLE 'VARIABLE'

    Attributes:
        id (int): Primary key for the variable entry.
        key (str): The key/name of the variable.
        org_id (int): Foreign key referencing the ORGANIZATION table.
        value (str): The value of the variable.
        type (str): The type of the variable ('variable' or 'secret').
        description (str): Description of the variable.
        filename (str): Optional filename associated with the variable.
        runtime (str): Runtime environment for the variable.
        slug (str): Slug identifier for the variable.
        created_at (datetime): Timestamp of when the variable was created.
        updated_at (datetime): Timestamp of the last update to the variable.
        created_by (str): User who created the variable.
        is_active (bool): Indicates if the variable is active.
        datatype (DataType): The data type of the variable (raw, json, file).
        set_as_env (bool): Flag indicating whether to set the variable as an environment variable.

    Constraints:
        CheckConstraint: Ensures 'type' is either 'variable' or 'secret'.
        UniqueConstraint: Ensures unique combination of key, org_id, runtime, slug, and created_by.
    """

    __tablename__ = 'VARIABLE'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    key = Column(String, index=True, nullable=False)
    org_id = Column(Integer, ForeignKey("ORGANIZATION.id"), index=True, nullable=False)
    value = Column(Text, nullable=False)
    type = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    filename = Column(String, nullable=True)
    runtime = Column(String, nullable=True)
    slug = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(String, ForeignKey('USER.user_name'), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, server_default='true')
    datatype = Column(Enum(DataType, name="data_type"), nullable=False)
    set_as_env = Column(Boolean, default=False, nullable=False, server_default='false')


    __table_args__ = (
        CheckConstraint(type.in_(['variable', 'secret']), name='check_variable_type'),
        # UniqueConstraint('key', 'org_id', 'runtime', 'slug', 'created_by', name='unique_key'),
        Index(
            'uq_active_secret_key',
            'key', 'created_by', 'org_id', 'runtime', 'slug',
            unique=True,
            postgresql_where=deleted_at.is_(None)
        ),
    )