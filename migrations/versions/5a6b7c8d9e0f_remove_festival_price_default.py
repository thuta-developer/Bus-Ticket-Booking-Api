"""remove festival price default

Revision ID: 5a6b7c8d9e0f
Revises: 4892b765308e
Create Date: 2026-08-11 00:18:30.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5a6b7c8d9e0f'
down_revision: Union[str, None] = '4892b765308e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Remove default values so NULL is stored when not provided
    op.alter_column('schedules', 'local_festival_price',
               existing_type=sa.Numeric(10, 2),
               nullable=True,
               existing_server_default=sa.text('0.00'),
               server_default=None)
    op.alter_column('schedules', 'foreigner_festival_price',
               existing_type=sa.Numeric(10, 2),
               nullable=True,
               existing_server_default=sa.text('0.00'),
               server_default=None)

    # Convert existing 0.00 values to NULL so they are treated as "not set"
    op.execute("UPDATE schedules SET local_festival_price = NULL WHERE local_festival_price = 0.00")
    op.execute("UPDATE schedules SET foreigner_festival_price = NULL WHERE foreigner_festival_price = 0.00")


def downgrade() -> None:
    # Restore default values
    op.alter_column('schedules', 'foreigner_festival_price',
               existing_type=sa.Numeric(10, 2),
               nullable=True,
               server_default=sa.text('0.00'))
    op.alter_column('schedules', 'local_festival_price',
               existing_type=sa.Numeric(10, 2),
               nullable=True,
               server_default=sa.text('0.00'))