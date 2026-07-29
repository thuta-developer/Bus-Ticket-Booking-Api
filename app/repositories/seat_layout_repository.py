from typing import Optional
from uuid import UUID
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.seat_layout import SeatLayout


class SeatLayoutRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, layout_id: UUID) -> Optional[SeatLayout]:
        stmt = select(SeatLayout).where(SeatLayout.id == layout_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_bus_id(self, bus_id: UUID) -> Optional[SeatLayout]:
        stmt = select(SeatLayout).where(SeatLayout.bus_id == bus_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, layout_data: dict) -> SeatLayout:
        layout = SeatLayout(**layout_data)
        self.db.add(layout)
        await self.db.commit()
        await self.db.refresh(layout)
        return layout

    async def update(self, layout_id: UUID, update_data: dict) -> Optional[SeatLayout]:
        stmt = (
            update(SeatLayout)
            .where(SeatLayout.id == layout_id)
            .values(**update_data)
            .returning(SeatLayout)
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.scalar_one_or_none()

    async def delete_by_bus_id(self, bus_id: UUID) -> bool:
        layout = await self.get_by_bus_id(bus_id)
        if not layout:
            return False
        await self.db.delete(layout)
        await self.db.commit()
        return True