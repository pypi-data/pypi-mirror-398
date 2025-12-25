"""models/database.py"""
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class DatabaseManager:

    """Manages database connections and sessions."""

    def __init__(self, db_url):
        self.db_url = db_url
        self.engine = self.get_engine()

    def get_engine(self):
        
        """
        Create a new SQLAlchemy engine instance.

        Returns:
            Engine: The SQLAlchemy engine instance.
        """
        
        try:
            engine = create_engine(self.db_url)
            return engine
        except SQLAlchemyError as e:
            raise e
        
    def get_session(self):
        """
        Create a new SQLAlchemy session.

        Returns:
            Session: The SQLAlchemy session instance.
        """
        try:
            engine = self.engine
            session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            db = session()
            try:
                yield db
            finally:
                db.close()

        except SQLAlchemyError as e:
            raise e
    
    def get_base(self):
        """
        Get the declarative base class for the ORM models.

        Returns:
            Base: The declarative base class.
        """
        return declarative_base()