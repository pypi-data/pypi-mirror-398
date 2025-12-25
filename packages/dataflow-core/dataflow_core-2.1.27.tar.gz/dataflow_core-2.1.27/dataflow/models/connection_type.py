from sqlalchemy import Column, Integer, String, DateTime, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB   # use JSONB for Postgres
from dataflow.db import Base

class ConnectionType(Base):
    """
    Stores key–value JSON records.
    
    Fields:
        id    : Primary key
        key   : Unique string identifier
        data : JSON payload (any structure)
    """

    __tablename__ = "CONNECTION_TYPE"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, nullable=False, index=True)
    data = Column(JSONB, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('key', name='uq_CONNECTION_TYPE_key'),
    )
