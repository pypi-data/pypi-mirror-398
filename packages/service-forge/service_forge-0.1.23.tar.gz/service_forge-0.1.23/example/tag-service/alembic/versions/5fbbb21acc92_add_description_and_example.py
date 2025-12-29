"""add description and example

Revision ID: 5fbbb21acc92
Revises: 8ff25e2b3fd9
Create Date: 2025-08-26 09:47:13.181504

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5fbbb21acc92'
down_revision: Union[str, Sequence[str], None] = '8ff25e2b3fd9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('tag', sa.Column('description', sa.String(255), nullable=True))
    op.add_column('tag', sa.Column('example', sa.String(255), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('tag', 'description')
    op.drop_column('tag', 'example')
