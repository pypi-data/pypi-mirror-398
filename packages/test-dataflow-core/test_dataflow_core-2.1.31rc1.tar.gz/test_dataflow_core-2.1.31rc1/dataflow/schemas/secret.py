"""schemas/secret.py"""

from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime


class SecretBase(BaseModel):
    """Base secret model with common fields.
    
    Attributes:
        key (str): The secret key.
        value (str): The secret value.
        description (Optional[str]): Optional description of the secret.
    
    Validations:
        validate_key: Ensures key meets length and character requirements.
    """
    
    key: str
    value: str
    description: Optional[str] = None

    @field_validator("key")
    def validate_key(cls, v) -> str:
        import re
        if not isinstance(v, str):
            raise ValueError("Secret key must be a string.")
        if len(v) > 30:
            raise ValueError("Secret key must be at most 30 characters long.")
        # Must start with letter, end with letter or digit
        # Can contain letters, numbers, and underscores
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*[A-Za-z0-9]|[A-Za-z]", v):
            raise ValueError(
                "Secret key must start with a letter, end with a letter or digit, "
                "and contain only letters, numbers, and underscores (_)!"
            )
        return v


class SecretSave(SecretBase):
    """Model for creating a new secret.

    Extends SecretBase without additional fields.
    """
    pass


class SecretUpdate(BaseModel):
    """Model for updating an existing secret.
    
    Extends SecretBase.
    
    Attributes:
        value (Optional[str]): The secret value.
        description (Optional[str]): Optional description of the secret.
    """
    
    value: Optional[str] = None
    description: Optional[str] = None


class SecretRead(SecretBase):
    """Model for reading/displaying secret data.
    
    Extends SecretBase.
    
    Attributes:
        created_date (Optional[datetime]): Timestamp of when the secret was created.
    """
    
    created_date: Optional[datetime] = None

    class Config:
        from_attributes = True
