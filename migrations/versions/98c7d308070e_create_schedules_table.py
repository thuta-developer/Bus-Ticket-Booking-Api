"""create_schedules_table

Revision ID: 98c7d308070e
Revises: 1e41fb92622d
Create Date: 2026-07-31 22:47:07.573926

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '98c7d308070e'
down_revision: Union[str, None] = '1e41fb92622d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create schedules table
    op.create_table(
        'schedules',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('departure_time', sa.Time(timezone=True), nullable=False, comment='Departure date and time'),
        sa.Column('arrival_time', sa.Time(timezone=True), nullable=False, comment='Arrival date and time'),
        sa.Column('status', postgresql.ENUM('ACTIVE', 'CANCELLED', 'COMPLETED', 'DELAYED', name='schedulestatus', create_type=False), nullable=False, server_default='ACTIVE'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('route_id', sa.UUID(), nullable=False),
        sa.Column('bus_id', sa.UUID(), nullable=False),
        sa.Column('local_price', sa.Numeric(10, 2), nullable=False, server_default='0.00', comment='Price for local citizens'),
        sa.Column('foreigner_price', sa.Numeric(10, 2), nullable=False, server_default='0.00', comment='Price for foreigners citizens'),
        sa.Column('local_festival_price', sa.Numeric(10, 2), nullable=False, server_default='0.00', comment='Festival price for locals'),
        sa.Column('foreigner_festival_price', sa.Numeric(10, 2), nullable=False, server_default='0.00', comment='Festival price for foreigners'),
        sa.Column('booking_open_date', sa.DateTime(timezone=True), nullable=False, comment='When booking starts'),
        sa.Column('booking_close_date', sa.DateTime(timezone=True), nullable=False, comment='When booking ends'),
        sa.Column('festival_start_date', sa.DateTime(timezone=True), nullable=True, comment='Festival period start'),
        sa.Column('festival_end_date', sa.DateTime(timezone=True), nullable=True, comment='Festival period end'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['route_id'], ['routes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['bus_id'], ['buses.id'], ondelete='CASCADE'),
    )

    # Create indexes
    op.create_index('ix_schedules_id', 'schedules', ['id'], unique=True)
    op.create_index('ix_schedules_route_id', 'schedules', ['route_id'])
    op.create_index('ix_schedules_bus_id', 'schedules', ['bus_id'])


def downgrade() -> None:
    op.drop_index('ix_schedules_bus_id', table_name='schedules')
    op.drop_index('ix_schedules_route_id', table_name='schedules')
    op.drop_index('ix_schedules_id', table_name='schedules')
    op.drop_table('schedules')
    sa.Enum('ACTIVE', 'CANCELLED', 'COMPLETED', 'DELAYED', name='schedulestatus').drop(op.get_bind())