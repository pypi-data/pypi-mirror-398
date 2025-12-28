from sqlalchemy import Column, DateTime, String
from sqlalchemy.ext.declarative import declarative_base

DBModelBase = declarative_base()


class SandboxRecord(DBModelBase):
    __tablename__ = "sandboxes"

    id = Column(String, primary_key=True)

    # Some grouping fields for filtering
    namespace = Column(String)
    user = Column(String)
    experiment_id = Column(String)

    created_at = Column(DateTime)
    # Last call time
    last_called_at = Column(DateTime)
    # Stop time/auto cleanup time
    stopped_at = Column(DateTime)

    # Some metadata information
    image = Column(String)
    spec_meta = Column(String)
    status_meta = Column(String)
