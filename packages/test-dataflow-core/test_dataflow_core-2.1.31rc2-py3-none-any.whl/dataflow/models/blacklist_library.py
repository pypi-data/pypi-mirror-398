# models/blacklist_library.py
from sqlalchemy import Column, Integer, String, UniqueConstraint
from dataflow.db import Base

class BlacklistedLibrary(Base):
    """TABLE 'BLACKLISTED_LIBRARY'

    Attributes:
        id (int): Primary key of the table, auto-incremented.
        library_name (str): The name of the blacklisted library.
        version (str): The version of the blacklisted library.

    Constraints:
        Unique constraint to ensure unique combination of library_name and version.
    """

    __tablename__ = "BLACKLISTED_LIBRARY"
    
    id = Column(Integer, primary_key=True, index=True, doc="Primary key for the library.")
    library_name = Column(String, index=True, doc="The name of the blacklisted library.")
    version = Column(String, doc="The version of the blacklisted library.")

    __table_args__ = (
        UniqueConstraint('library_name', 'version', name='uq_library_version'),
    )
    
