"""Add project visibility and team access control

Revision ID: 003
Revises: 002
Create Date: 2025-09-10 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None

def upgrade() -> None:
    project_visibility_enum = postgresql.ENUM('PUBLIC', 'ORG', 'TEAM', name='project_visibility')
    project_visibility_enum.create(op.get_bind())
    
    op.add_column('PROJECT_DETAIL', sa.Column('visibility', 
        sa.Enum('PUBLIC', 'ORG', 'TEAM', name='project_visibility'), 
        nullable=False, 
        server_default='ORG'))
    
    op.add_column('PROJECT_DETAIL', sa.Column('team_ids', 
        postgresql.ARRAY(sa.Integer), 
        nullable=True))

def downgrade() -> None:
    op.drop_column('PROJECT_DETAIL', 'team_ids')
    op.drop_column('PROJECT_DETAIL', 'visibility')
    
    project_visibility_enum = postgresql.ENUM('PUBLIC', 'ORG', 'TEAM', name='project_visibility')
    project_visibility_enum.drop(op.get_bind())