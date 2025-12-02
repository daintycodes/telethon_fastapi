"""initial

Revision ID: 0001_initial
Revises: 
Create Date: 2025-12-02 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'channels',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('username', sa.String(), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=True, server_default=sa.sql.expression.true()),
    )

    op.create_table(
        'media_files',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('message_id', sa.Integer(), nullable=True, unique=True),
        sa.Column('channel_username', sa.String(), nullable=True),
        sa.Column('file_name', sa.String(), nullable=True),
        sa.Column('file_type', sa.String(), nullable=True),
        sa.Column('s3_key', sa.String(), nullable=True),
        sa.Column('downloaded_at', sa.DateTime(), nullable=True),
        sa.Column('approved', sa.Boolean(), nullable=True, server_default=sa.sql.expression.false()),
    )

    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('username', sa.String(), nullable=False, unique=True),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('is_admin', sa.Boolean(), nullable=True, server_default=sa.sql.expression.false()),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )


def downgrade():
    op.drop_table('users')
    op.drop_table('media_files')
    op.drop_table('channels')
