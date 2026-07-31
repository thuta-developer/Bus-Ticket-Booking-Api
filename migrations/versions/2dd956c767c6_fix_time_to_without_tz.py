"""fix_time_to_without_tz

Revision ID: 2dd956c767c6
Revises: 98c7d308070e
Create Date: 2026-07-31 22:51:32.225447

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '2dd956c767c6'
down_revision: Union[str, None] = '98c7d308070e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Change TIME WITH TIME ZONE to TIME WITHOUT TIME ZONE
    # to match the model (Time(timezone=False)) and accept naive datetime.time objects
    op.alter_column('schedules', 'departure_time',
               existing_type=sa.Time(timezone=True),
               type_=sa.Time(timezone=False),
               existing_comment='Departure date and time',
               existing_nullable=False,
               postgresql_using='departure_time::time without time zone')
    op.alter_column('schedules', 'arrival_time',
               existing_type=sa.Time(timezone=True),
               type_=sa.Time(timezone=False),
               existing_comment='Arrival date and time',
               existing_nullable=False,
               postgresql_using='arrival_time::time without time zone')


def downgrade() -> None:
    op.alter_column('schedules', 'arrival_time',
               existing_type=sa.Time(timezone=False),
               type_=sa.Time(timezone=True),
               existing_comment='Arrival time',
               existing_nullable=False,
               postgresql_using='arrival_time::time with time zone')
    op.alter_column('schedules', 'departure_time',
               existing_type=sa.Time(timezone=False),
               type_=sa.Time(timezone=True),
               existing_comment='Departure time',
               existing_nullable=False,
               postgresql_using='departure_time::time with time zone')