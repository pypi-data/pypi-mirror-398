from app.db.base import Base
from app.db.session import engine
from app import models  # noqa: F401  # ensure models are registered


def init_memory_os_schema() -> None:
    """Create required tables if they do not already exist."""
    Base.metadata.create_all(bind=engine)
