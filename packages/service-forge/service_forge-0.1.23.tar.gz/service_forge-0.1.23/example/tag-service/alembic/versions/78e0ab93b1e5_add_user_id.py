"""add user_id

Revision ID: 78e0ab93b1e5
Revises: 483c59e9a5e1
Create Date: 2025-08-26 16:58:39.437350

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '78e0ab93b1e5'
down_revision: Union[str, Sequence[str], None] = '483c59e9a5e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('tag', sa.Column('user_id', sa.Integer, nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('tag', 'user_id')
