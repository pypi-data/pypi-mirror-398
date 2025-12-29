"""add type

Revision ID: 483c59e9a5e1
Revises: 5fbbb21acc92
Create Date: 2025-08-26 10:33:30.871421

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '483c59e9a5e1'
down_revision: Union[str, Sequence[str], None] = '5fbbb21acc92'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('tag', sa.Column('type', sa.String(50), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('tag', 'type')
