"""Add custom Docker image support to PROJECT_DETAIL table

Revision ID: 004
Revises: 003
Create Date: 2025-11-13 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None

def upgrade():
    # Add custom image related columns to PROJECT_DETAIL table
    op.add_column('PROJECT_DETAIL', sa.Column('custom_image', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.add_column('PROJECT_DETAIL', sa.Column('repository_type', sa.String(50), nullable=True))
    op.add_column('PROJECT_DETAIL', sa.Column('image_repository', sa.String(255), nullable=True))
    op.add_column('PROJECT_DETAIL', sa.Column('image_name', sa.String(255), nullable=True))
    op.add_column('PROJECT_DETAIL', sa.Column('image_tag', sa.String(100), nullable=True))
    op.add_column('PROJECT_DETAIL', sa.Column('exposed_port', sa.Integer(), nullable=True))
    op.add_column('PROJECT_DETAIL', sa.Column('private_repo', sa.Boolean(), nullable=True, server_default=sa.text('false')))
    op.add_column('PROJECT_DETAIL', sa.Column('registry_secret_id', sa.Integer(), nullable=True))
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_project_detail_registry_secret',
        'PROJECT_DETAIL', 'VARIABLE',
        ['registry_secret_id'], ['id']
    )

def downgrade():
    # Drop foreign key constraint first
    op.drop_constraint('fk_project_detail_registry_secret', 'PROJECT_DETAIL', type_='foreignkey')
    
    # Remove custom image related columns from PROJECT_DETAIL table
    op.drop_column('PROJECT_DETAIL', 'registry_secret_id')
    op.drop_column('PROJECT_DETAIL', 'private_repo')
    op.drop_column('PROJECT_DETAIL', 'exposed_port')
    op.drop_column('PROJECT_DETAIL', 'image_tag')
    op.drop_column('PROJECT_DETAIL', 'image_name')
    op.drop_column('PROJECT_DETAIL', 'image_repository')
    op.drop_column('PROJECT_DETAIL', 'repository_type')
    op.drop_column('PROJECT_DETAIL', 'custom_image')
