"""force_create_permissions

Revision ID: 0ebbcb00ae6a
Revises: 9817d3d70a2c
Create Date: 2026-06-24 22:01:17.309351

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0ebbcb00ae6a'
down_revision: Union[str, None] = '9817d3d70a2c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
