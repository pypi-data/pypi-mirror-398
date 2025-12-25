"""models.py"""
from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from dataflow.db import Base

class Team(Base):
    """Table TEAM

    Attributes:
        team_id (int): Primary key for the team entry.
        team_name (str): Name of the team.
        org_id (int): Foreign key referencing the ORGANIZATION table.
        description (str): Description of the team.
    
    Relationships:
        users: Many-to-many relationship with User model via USER_TEAM association table.
        organization: Relationship to the Organization model.
    """

    __tablename__='TEAM'
    __table_args__ = (
        UniqueConstraint('team_name', 'org_id', name='uc_team_name_org_id'),
    )

    team_id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    team_name = Column(String, nullable=False)
    org_id = Column(Integer, ForeignKey('ORGANIZATION.id', ondelete="CASCADE"), nullable=False)
    description = Column(String, nullable=True)

    # relationships
    users = relationship("User", secondary="USER_TEAM", back_populates="teams")
    organization = relationship("Organization")