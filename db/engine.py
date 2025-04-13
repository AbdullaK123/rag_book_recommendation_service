from sqlmodel import create_engine, Session, SQLModel
from utils.config import settings
from utils.exceptions.db import ConnectionException


def get_engine():
    """
    Create and return a SQLAlchemy engine instance using connection details from settings.
    """
    try:
        connection_string = settings.db.DB_URI
        if not connection_string:
            raise ValueError("Database connection string is not configured.")
        
        engine = create_engine(
            connection_string,
            echo=settings.app.DEBUG,
            connect_args={"connect_timeout": 10}
        )
        return engine
    except Exception as e:
        raise ConnectionException(
            message="Failed to create database engine",
            original_exception=e
        )


def get_session():
    """
    Create and yield a database session.
    For use as a FastAPI dependency.
    """
    engine = get_engine()
    with Session(engine) as session:
        try:
            yield session
        except Exception as e:
            session.rollback()
            raise e