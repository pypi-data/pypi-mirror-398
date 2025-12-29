"""create database

Revision ID: 8ff25e2b3fd9
Revises: 
Create Date: 2025-08-24 19:28:07.191002

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
import datetime
import uuid


# revision identifiers, used by Alembic.
revision: str = '8ff25e2b3fd9'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'tag',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('tag')
