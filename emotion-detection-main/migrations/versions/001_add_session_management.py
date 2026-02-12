"""Add session management tables

Revision ID: 001_add_session_management
Revises: 
Create Date: 2026-02-11

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime, timedelta

# revision identifiers, used by Alembic.
revision = '001_add_session_management'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to user table if they don't exist
    # These commands are safe for SQLite
    try:
        op.add_column('user', sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')))
    except Exception:
        pass  # Column might already exist
    
    try:
        op.add_column('user', sa.Column('last_login', sa.DateTime(), nullable=True))
    except Exception:
        pass
    
    try:
        op.add_column('user', sa.Column('is_active', sa.Boolean(), server_default=sa.text('1')))
    except Exception:
        pass
    
    # Create session table
    op.create_table(
        'session',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('session_token', sa.String(100), nullable=False, unique=True),
        sa.Column('ip_address', sa.String(50), nullable=True),
        sa.Column('user_agent', sa.String(255), nullable=True),
        sa.Column('login_time', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('last_activity', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('logout_time', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('1')),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.ForeignKey('user.id', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for performance
    op.create_index('idx_session_user_id', 'session', ['user_id'])
    op.create_index('idx_session_token', 'session', ['session_token'])
    op.create_index('idx_session_is_active', 'session', ['is_active'])
    op.create_index('idx_session_expires_at', 'session', ['expires_at'])
    op.create_index('idx_session_login_time', 'session', ['login_time'])
    
    # Create indexes on user table
    op.create_index('idx_user_email', 'user', ['email'])
    op.create_index('idx_user_phone', 'user', ['phone'])
    op.create_index('idx_user_is_active', 'user', ['is_active'])


def downgrade():
    # Drop session table and indexes
    op.drop_index('idx_session_login_time')
    op.drop_index('idx_session_expires_at')
    op.drop_index('idx_session_is_active')
    op.drop_index('idx_session_token')
    op.drop_index('idx_session_user_id')
    op.drop_table('session')
    
    # Drop user table indexes
    try:
        op.drop_index('idx_user_is_active')
    except Exception:
        pass
    
    try:
        op.drop_index('idx_user_phone')
    except Exception:
        pass
    
    try:
        op.drop_index('idx_user_email')
    except Exception:
        pass
    
    # Remove columns from user table
    try:
        op.drop_column('user', 'is_active')
    except Exception:
        pass
    
    try:
        op.drop_column('user', 'last_login')
    except Exception:
        pass
    
    try:
        op.drop_column('user', 'created_at')
    except Exception:
        pass
