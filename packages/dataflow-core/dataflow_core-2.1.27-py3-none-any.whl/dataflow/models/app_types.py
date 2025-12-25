from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from dataflow.db import Base

class AppType(Base):

    """TABLE 'APP_TYPE'.
    
    Attributes:
        id (int): Primary key for the app type.
        name (str): Unique name identifier for the app type.
        display_name (str): Human-readable name for the app type.
        code_based (bool): Indicates if the app type is code-based.
        studio (bool): Indicates if the app type is associated with Dataflow Studio.
        runtime (bool): Indicates if the app type is a runtime application.
        organizations (list): Relationship to organizations using this app type.
    
    Relationships:
        organizations: Many-to-many relationship with Organization model via ORGANIZATION_APP_TYPE association table.
    """
    
    __tablename__ = "APP_TYPE"
    
    id = Column(Integer, primary_key=True, autoincrement=True, unique=True)
    name = Column(String, unique=True, nullable=False)
    display_name = Column(String, nullable=False)
    code_based = Column(Boolean, nullable=False)
    studio = Column(Boolean, nullable=False, default=False, server_default='false')
    runtime = Column(Boolean, nullable=False, default=False, server_default='false')

    organizations = relationship("Organization", secondary="ORGANIZATION_APP_TYPE", back_populates="apps")