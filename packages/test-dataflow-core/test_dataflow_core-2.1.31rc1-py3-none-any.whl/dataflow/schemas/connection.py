"""schemas/connection.py"""

from pydantic import BaseModel, field_validator
from typing import Optional
from enum import Enum


class ConnectionType(str, Enum):

    """Enum for supported connection types."""

    POSTGRESQL = "PostgreSQL"
    MYSQL = "MySQL"


class ConnectionBase(BaseModel):
    
    """Base connection model with common fields.
    
    Attributes:
        conn_id (str): Unique identifier for the connection.
        conn_type (ConnectionType): Type of the connection (e.g., PostgreSQL, MySQL).
        description (Optional[str]): Optional description of the connection.
        host (str): Hostname or IP address of the database server.
        schemas (Optional[str]): Optional schemas associated with the connection.
        password (str): Password for the database connection.
        login (str): Login/username for the database connection.
        port (int): Port number for the database connection.
        extra (Optional[str]): Optional extra parameters for the connection.
    
    Validations:
        validate_conn_id: Ensures conn_id meets length and character requirements.
        validate_conn_type: Ensures conn_type is a valid ConnectionType enum member.
    """

    conn_id: str
    conn_type: ConnectionType
    description: Optional[str] = None
    host: str
    schemas: Optional[str] = None
    password: str
    login: str
    port: int
    extra: Optional[str] = None

    @field_validator("conn_id")
    def validate_conn_id(cls, v) -> str:
        import re
        if not isinstance(v, str):
            raise ValueError("Connection ID must be a string.")
        if len(v) > 30:
            raise ValueError("Connection ID must be at most 30 characters long.")
        # Must start with letter, end with letter or digit
        # Can contain letters, numbers, and underscores
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*[A-Za-z0-9]|[A-Za-z]", v):
            raise ValueError(
                "Connection ID must start with a letter, end with a letter or digit, "
                "and contain only letters, numbers, and underscores (_)!"
            )
        return v

    @field_validator("conn_type")
    def validate_conn_type(cls, v) -> ConnectionType:
        if isinstance(v, str):
            try:
                return ConnectionType(v)
            except ValueError:
                raise ValueError(f'conn_type must be one of {[e.value for e in ConnectionType]}')
        return v


class ConnectionSave(ConnectionBase):
    """Model for creating a new connection.
    
    Extends ConnectionBase without adding new fields.
    """
    pass


class ConnectionUpdate(BaseModel):
    """Model for updating an existing connection.

    Extends ConnectionBase
    
    Attributes:
        conn_type (Optional[ConnectionType]): Type of the connection (e.g., PostgreSQL, MySQL).
        description (Optional[str]): Optional description of the connection.
        host (Optional[str]): Hostname or IP address of the database server.
        schemas (Optional[str]): Optional schemas associated with the connection.
        login (Optional[str]): Login/username for the database connection.  
        password (Optional[str]): Password for the database connection.
        port (Optional[int]): Port number for the database connection.
        extra (Optional[str]): Optional extra parameters for the connection.
    
    Validations:
        validate_conn_type: Ensures conn_type is a valid ConnectionType enum member if provided.
    """

    conn_type: Optional[ConnectionType] = None
    description: Optional[str] = None
    host: Optional[str] = None
    schemas: Optional[str] = None
    login: Optional[str] = None
    password: Optional[str] = None
    port: Optional[int] = None
    extra: Optional[str] = None

    @field_validator("conn_type")
    def validate_conn_type(cls, v) -> Optional[ConnectionType]:
        if v is None:
            return v
        if isinstance(v, str):
            # Convert string to enum if needed
            try:
                return ConnectionType(v)
            except ValueError:
                raise ValueError(f'conn_type must be one of {[e.value for e in ConnectionType]}')
        return v


class ConnectionRead(ConnectionBase):
    """Model for reading/displaying connection data.
    
    Extends ConnectionBase without adding new fields.
    """
    pass

    class Config:
        from_attributes = True
