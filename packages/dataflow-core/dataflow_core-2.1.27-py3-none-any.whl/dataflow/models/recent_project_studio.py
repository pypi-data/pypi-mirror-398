"""models.py"""
from sqlalchemy import Column, Integer, String, DateTime, UniqueConstraint, Boolean
from sqlalchemy.sql import func
from dataflow.db import Local_Base as Base

class RecentProjectStudio(Base):
    
    """TABLE 'RECENT_PROJECT_STUDIO'

    Attributes:
        id (int): Primary key for the recent project studio entry.
        user_name (str): The username of the user.
        app_name (str): The name of the application used.
        project_name (str): The name of the project.
        project_path (str): The file path of the project.
        last_opened_date (datetime): Timestamp of when the project was last opened.
        remember (bool): Flag indicating whether to remember this project.

    Constraints:
        UniqueConstraint: Ensures unique combination of user_name, project_path, and app_name.
    """

    __tablename__ = 'RECENT_PROJECT_STUDIO'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_name = Column(String, nullable=False, index=True)
    app_name = Column(String, nullable=False, index=True)
    project_name = Column(String, nullable=False)
    project_path = Column(String, nullable=False)
    last_opened_date = Column(DateTime, server_default=func.now(), nullable=False)
    remember = Column(Boolean, default=False, server_default='false')

    __table_args__ = (
        UniqueConstraint(user_name, project_path, app_name, name='user_name_project_path_app_name_unique'),
    )