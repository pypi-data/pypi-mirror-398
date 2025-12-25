from sqlalchemy import Column, Integer, ForeignKey
from dataflow.db import Base

class RecentProjects(Base):

    """TABLE 'RECENT_PROJECT'
    Attributes:
        id (int): Primary key for the recent project entry.
        project_id (int): Foreign key referencing the PROJECT_DETAIL table.
    """
    
    __tablename__ = "RECENT_PROJECT"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey('PROJECT_DETAIL.project_id', ondelete="CASCADE"), nullable=False)

