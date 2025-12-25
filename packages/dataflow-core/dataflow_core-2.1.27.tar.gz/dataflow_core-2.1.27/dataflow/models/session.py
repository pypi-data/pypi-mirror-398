"""models.py"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, text
from datetime import datetime, timezone
from dataflow.db import Base

class Session(Base):
    """Table SESSION

    Attributes:
        id (int): Primary key for the session entry.
        session_id (str): Unique identifier for the session.
        jupyterhub_token (str): Token associated with the JupyterHub session.
        jupyterhub_token_id (str): Identifier for the JupyterHub token.
        user_id (int): Foreign key referencing the USER table.
        last_seen (DateTime): Last time the session was accessed (timezone-aware).
        expires_at (DateTime): When the session expires (timezone-aware).
        revoked (bool): Whether the session has been revoked.
    """

    __tablename__='SESSION'

    id = Column(Integer, primary_key=True, index=True, unique=True, nullable=False, autoincrement=True)
    session_id = Column(String, unique=True, nullable=False)
    jupyterhub_token = Column(String)
    jupyterhub_token_id = Column(String)
    user_id = Column(Integer, ForeignKey('USER.user_id', ondelete="CASCADE"), nullable=False)
    last_seen = Column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False
    )
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked = Column(Boolean, default=False, nullable=False)


