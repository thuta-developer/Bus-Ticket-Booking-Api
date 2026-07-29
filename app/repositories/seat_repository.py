from typing import Optional, List
from uuid import UUID
from sqlalchemy import select, update, delete, and_,func

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError


from app.models.seat import Seat


class SeatRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, seat_id: UUID) -> Optional[Seat]:
        stmt = select(Seat).where(Seat.id == seat_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_bus(self, bus_id: UUID, include_inactive: bool = False) -> List[Seat]:
        stmt = select(Seat).where(Seat.bus_id == bus_id)
        if not include_inactive:
            stmt = stmt.where(Seat.is_active == True)

        stmt = stmt.order_by(Seat.seat_number.asc())
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_by_bus_and_number(self, bus_id: UUID, seat_number: str) -> Optional[Seat]:
        stmt = select(Seat).where(
            and_(
                Seat.bus_id == bus_id,
                Seat.seat_number == seat_number
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def count_by_bus(self, bus_id: UUID, include_inactive: bool = False) -> int:
        stmt = select(func.count()).select_from(Seat).where(Seat.bus_id == bus_id)
        if not include_inactive:
            stmt = stmt.where(Seat.is_active == True)
        result = await self.db.execute(stmt)
        return result.scalar()

    async def create(self, seat_data: dict) -> Seat:
        try:
            seat = Seat(**seat_data)
            self.db.add(seat)
            await self.db.commit()
            await self.db.refresh(seat)
            return seat
        except IntegrityError as e:
            await self.db.rollback()
            raise ValueError("Seat with this number already exists for this bus")

    async def create_batch(self, seat_data_list: List[dict]) -> List[Seat]:
        try:
            seats = [Seat(**data) for data in seat_data_list]
            self.db.add_all(seats)
            await self.db.commit()
            for seat in seats:
                await self.db.refresh(seat)
            return seats
        except IntegrityError as e:
            await self.db.rollback()
            raise ValueError("One or more seat numbers already exist for this bus")

    async def update(self, seat_id: UUID, update_data: dict) -> Optional[Seat]:
        seat = await self.get_by_id(seat_id)
        if not seat:
            return None
        
        try:
            stmt = (
                update(Seat)
                .where(Seat.id == seat_id)
                .values(**update_data)
                .returning(Seat)
            )
            result = await self.db.execute(stmt)
            await self.db.commit()
            return result.scalar_one_or_none()
        except IntegrityError:
            await self.db.rollback()
            raise ValueError("Seat number conflict")

    async def delete(self, seat_id: UUID) -> bool:
        seat = await self.get_by_id(seat_id)
        if not seat:
            return False

        await self.db.delete(seat)
        await self.db.commit()
        return True

    async def soft_delete(self, seat_id: UUID) -> bool:
        seat = await self.get_by_id(seat_id)
        if not seat:
            return False

        seat.is_active = False
        await self.db.commit()
        return True


    async def delete_all_by_bus(self, bus_id: UUID) -> int:
        stmt = delete(Seat).where(Seat.bus_id == bus_id)
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount