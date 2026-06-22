"""add_user_account_type

Revision ID: f4d2b7a9c1e3
Revises: cad62f1bd119
Create Date: 2026-06-22 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f4d2b7a9c1e3"
down_revision: Union[str, None] = "cad62f1bd119"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "account_type",
            sa.String(length=20),
            nullable=False,
            server_default="customer",
            comment="Account type: customer or staff",
        ),
    )
    op.create_check_constraint(
        "ck_users_account_type",
        "users",
        "account_type IN ('customer', 'staff')",
    )
    op.create_index("ix_users_account_type", "users", ["account_type"])
    op.execute("UPDATE users SET account_type = 'staff' WHERE is_superuser = true")


def downgrade() -> None:
    op.drop_index("ix_users_account_type", table_name="users")
    op.drop_constraint("ck_users_account_type", "users", type_="check")
    op.drop_column("users", "account_type")
