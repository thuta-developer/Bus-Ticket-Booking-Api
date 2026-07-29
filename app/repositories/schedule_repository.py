from typing import Optional, List
from uuid import UUID
from datetime import date, time
from sqlalchemy import select, update, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.models.schedule import Schedule
from app.models.route import Route
from app.models.bus import Bus
from app.models.bus_company import BusCompany

class ScheduleRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, schedule_id: UUID) -> Optional[Schedule]:
        stmt = select(Schedule).where(Schedule.id == schedule_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
        route_id: Optional[UUID] = None,
        bus_id: Optional[UUID] = None,
        status: Optional[str] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        include_inactive: bool = False,
    ) -> List[Schedule]:
        stmt = (
            select(Schedule)
            .join(Route)
            .join(Bus)
            .join(BusCompany)
        )

        # Filters
        if not include_inactive:
            stmt = stmt.where(Schedule.is_active == True)

        if route_id:
            stmt = stmt.where(Schedule.route_id == route_id)

        if bus_id:
            stmt = stmt.where(Schedule.bus_id == bus_id)

        if status:
            stmt = stmt.where(Schedule.status == status)

        if search:
            search_term = f"%{search}%"
            stmt = stmt.where(
                or_(
                    Route.origin.ilike(search_term),
                    Route.description.ilike(search_term),
                    Bus.bus_number.ilike(search_term),
                    BusCompany.name.ilike(search_term),
                )
            )

        if from_date:
            stmt = stmt.where(func.date(Schedule.created_at) >= from_date)

        if to_date:
            stmt = stmt.where(func.date(Schedule.created_at) <= to_date)

        stmt = stmt.offset(skip).limit(limit).order_by(Schedule.departure_time.asc())
        result = await self.db.execute(stmt)
        return result.scalars().all()


    async def count(
        self,
        search: Optional[str] = None,
        route_id: Optional[UUID] = None,
        bus_id: Optional[UUID] = None,
        status: Optional[str] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        include_inactive: bool = False,
    ) -> int:
        stmt = select(func.count()).select_from(Schedule).join(Route).join(Bus).join(BusCompany)

        # Filters
        if not include_inactive:
            stmt = stmt.where(Schedule.is_active == True)

        if route_id:
            stmt = stmt.where(Schedule.route_id == route_id)

        if bus_id:
            stmt = stmt.where(Schedule.bus_id == bus_id)

        if status:
            stmt = stmt.where(Schedule.status == status)

        if search:
            search_term = f"%{search}%"
            stmt = stmt.where(
                or_(
                    Route.origin.ilike(search_term),
                    Route.description.ilike(search_term),
                    BusCompany.name.ilike(search_term),
                )
            )

        if from_date:
            stmt = stmt.where(func.date(Schedule.created_at) >= from_date)

        if to_date:
            stmt = stmt.where(func.date(Schedule.created_at) <= to_date)

        result = await self.db.execute(stmt)
        return result.scalar()

    async def create(self, schedule_data: dict) -> Schedule:
        try:
            schedule = Schedule(**schedule_data)
            self.db.add(schedule)
            await self.db.commit()
            await self.db.refresh(schedule)
            return schedule
        except IntegrityError as e:
            await self.db.rollback()
            raise ValueError("Failed to create schedule. Please check route and bus IDs.")


    async def update(self, schedule_id: UUID, update_data: dict) -> Optional[Schedule]:
        schedule = await self.get_by_id(schedule_id)
        if not schedule:
            return None

        try:
            stmt = (
                update(Schedule)
                .where(Schedule.id == schedule_id)
                .values(**update_data)
                .returning(Schedule)
            )
            result = await self.db.execute(stmt)
            await self.db.commit()
            return result.scalar_one_or_none()

        except IntegrityError as e:
            await self.db.rollback()
            raise ValueError("Failed to update schedule.")


    async def delete(self, schedule_id: UUID) -> bool:
        schedule = await self.get_by_id(schedule_id)
        if not schedule:
            return False

        await self.db.delete(schedule)
        await self.db.commit()
        return True

    async def soft_delete(self, schedule_id: UUID) -> bool:
        schedule = await self.get_by_id(schedule_id)
        if not schedule:
            return False

        schedule.is_active = False
        await self.db.commit()
        return True


    async def update_status(self, schedule_id: UUID, status: str) -> Optional[Schedule]:
        schedule = await self.get_by_id(schedule_id)
        if not schedule:
            return None

        schedule.status = status
        await self.db.commit()
        await self.db.refresh(schedule)
        return schedule


























                