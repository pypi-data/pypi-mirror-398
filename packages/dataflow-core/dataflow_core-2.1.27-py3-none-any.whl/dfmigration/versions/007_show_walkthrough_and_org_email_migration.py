"""Add show_walkthrough to USER and drop email_domain constraint on ORGANIZATION

Revision ID: 007
Revises: 006
Create Date: 2025-11-24 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None

def upgrade():
    # Add show_walkthrough column to USER table with default value TRUE
    op.add_column('USER', sa.Column('show_walkthrough', sa.Boolean(), nullable=True, server_default=sa.text('true')))

def downgrade():
    
    # Remove show_walkthrough column from USER table
    op.drop_column('USER', 'show_walkthrough')
