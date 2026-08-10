from typing import Optional, List
from uuid import UUID
from datetime import datetime, date, time
from sqlalchemy import select, update, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from sqlalchemy.orm import selectinload

from app.models.schedule import Schedule
from app.models.route import Route
from app.models.bus import Bus
from app.models.bus_company import BusCompany


class ScheduleRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _get_time_range(self, time_of_day: str) -> tuple:
        """Get start and end time for a given time of day."""
        ranges = {
            "morning": (time(6, 0, 0), time(11, 59, 59)),
            "afternoon": (time(12, 0, 0), time(17, 59, 59)),
            "night": (time(18, 0, 0), time(23, 59, 59)),
        }
        return ranges.get(time_of_day.lower())

    # Search
    async def search_schedules(
        self,
        origin: Optional[str] = None,
        destination: Optional[str] = None,
        travel_date: Optional[date] = None,
        user_type: str = "local",
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        bus_type: Optional[str] = None,
        route_id: Optional[UUID] = None,
        bus_id: Optional[UUID] = None,
        status: Optional[str] = None,
        include_bookable_only: bool = True,
        include_inactive: bool = False,
        time_of_day: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> List[Schedule]:
        stmt = (
            select(Schedule)
            .select_from(Schedule)
            .join(Route, Schedule.route_id == Route.id)
            .join(Bus, Schedule.bus_id == Bus.id)
            .join(BusCompany, Bus.company_id == BusCompany.id)
            .options(
                selectinload(Schedule.route),
                selectinload(Schedule.bus).selectinload(Bus.company),
            )
        )

        # Filters
        if include_bookable_only:
            now = datetime.now()
            # If travel_date provided, ensure the travel date is within the booking window
            if travel_date:
                travel_datetime = datetime.combine(travel_date, datetime.min.time())
                stmt = stmt.where(
                    and_(
                        Schedule.booking_open_date <= now,
                        Schedule.booking_close_date >= now,
                        Schedule.is_active == True,
                        # Travel date must be within booking window
                        Schedule.booking_open_date <= travel_datetime,
                        Schedule.booking_close_date >= travel_datetime,
                    )
                )
            else:
                stmt = stmt.where(
                    and_(
                        Schedule.booking_open_date <= now,
                        Schedule.booking_close_date >= now,
                        Schedule.is_active == True,
                    )
                )

        if time_of_day:
            start_time, end_time = self._get_time_range(time_of_day)
            stmt = stmt.where(
                and_(
                    Schedule.departure_time >= start_time,
                    Schedule.departure_time <= end_time,
                )
            )

        # Active Status Filter
        if not include_inactive:
            stmt = stmt.where(Schedule.is_active == True)

        if origin:
            stmt = stmt.where(Route.origin.ilike(f"%{origin}%"))

        if destination:
            stmt = stmt.where(Route.destination.ilike(f"%{destination}%"))

        if route_id:
            stmt = stmt.where(Schedule.route_id == route_id)

        if bus_id:
            stmt = stmt.where(Schedule.bus_id == bus_id)

        if bus_type:
            stmt = stmt.where(Bus.bus_type == bus_type)

        if travel_date:
            start_of_day = datetime.combine(travel_date, datetime.min.time())
            end_of_day = datetime.combine(travel_date, datetime.max.time())

            stmt = stmt.where(
                and_(
                    Schedule.departure_time >= start_of_day.time(),
                    Schedule.departure_time <= end_of_day.time(),
                )
            )

        if status:
            stmt = stmt.where(Schedule.status == status)

        if min_price:
            stmt = stmt.where(Schedule.local_price >= min_price)

        if max_price:
            stmt = stmt.where(Schedule.local_price <= max_price)

        stmt = stmt.order_by(Schedule.departure_time.asc())

        stmt = stmt.offset(skip).limit(limit)

        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_by_id(self, schedule_id: UUID) -> Optional[Schedule]:
        stmt = (
            select(Schedule)
            .where(Schedule.id == schedule_id)
            .options(
                selectinload(Schedule.route),
                selectinload(Schedule.bus).selectinload(Bus.company),
            )
        )
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
        departure_date: Optional[datetime] = None,
        include_inactive: bool = False,
        include_bookable_only: bool = True,
        user_type: str = "local",
    ) -> List[Schedule]:

        stmt = (
            select(Schedule)
            .select_from(Schedule)
            .join(Route, Schedule.route_id == Route.id)
            .join(Bus, Schedule.bus_id == Bus.id)
            .join(BusCompany, Bus.company_id == BusCompany.id)
            .options(
                selectinload(Schedule.route),
                selectinload(Schedule.bus).selectinload(Bus.company),
            )
        )

        #  Bookable only filter (within booking window)
        if include_bookable_only:
            now = datetime.now()
            # If departure_date provided, ensure the travel date is within the booking window
            if departure_date:
                stmt = stmt.where(
                    and_(
                        Schedule.booking_open_date <= now,
                        Schedule.booking_close_date >= now,
                        Schedule.is_active == True,
                        # Departure date must be within booking window
                        Schedule.booking_open_date <= departure_date,
                        Schedule.booking_close_date >= departure_date,
                    )
                )
            else:
                stmt = stmt.where(
                    and_(
                        Schedule.booking_open_date <= now,
                        Schedule.booking_close_date >= now,
                        Schedule.is_active == True,
                    )
                )

        #  Filter by departure date
        if departure_date:
            start_of_day = departure_date.replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            end_of_day = departure_date.replace(
                hour=23, minute=59, second=59, microsecond=999999
            )
            stmt = stmt.where(
                and_(
                    Schedule.departure_time >= start_of_day.time(),
                    Schedule.departure_time <= end_of_day.time(),
                )
            )

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
                    Route.destination.ilike(search_term),
                    Bus.bus_number.ilike(search_term),
                    BusCompany.name.ilike(search_term),
                )
            )

        stmt = stmt.offset(skip).limit(limit).order_by(Schedule.departure_time.asc())
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def count(
        self,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
        route_id: Optional[UUID] = None,
        bus_id: Optional[UUID] = None,
        status: Optional[str] = None,
        departure_date: Optional[datetime] = None,
        include_inactive: bool = False,
        include_bookable_only: bool = True,
        user_type: str = "local",
    ) -> int:
        """
        Count total schedules matching the get_all filters (for pagination).
        """
        stmt = (
            select(func.count())
            .select_from(Schedule)
            .join(Route, Schedule.route_id == Route.id)
            .join(Bus, Schedule.bus_id == Bus.id)
            .join(BusCompany, Bus.company_id == BusCompany.id)
        )

        # Apply same filters as get_all
        #  Bookable only filter (within booking window)
        if include_bookable_only:
            now = datetime.now()
            # If departure_date provided, ensure the travel date is within the booking window
            if departure_date:
                stmt = stmt.where(
                    and_(
                        Schedule.booking_open_date <= now,
                        Schedule.booking_close_date >= now,
                        Schedule.is_active == True,
                        # Departure date must be within booking window
                        Schedule.booking_open_date <= departure_date,
                        Schedule.booking_close_date >= departure_date,
                    )
                )
            else:
                stmt = stmt.where(
                    and_(
                        Schedule.booking_open_date <= now,
                        Schedule.booking_close_date >= now,
                        Schedule.is_active == True,
                    )
                )

        #  Filter by departure date
        if departure_date:
            start_of_day = departure_date.replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            end_of_day = departure_date.replace(
                hour=23, minute=59, second=59, microsecond=999999
            )
            stmt = stmt.where(
                and_(
                    Schedule.departure_time >= start_of_day.time(),
                    Schedule.departure_time <= end_of_day.time(),
                )
            )

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
                    Route.destination.ilike(search_term),
                    Bus.bus_number.ilike(search_term),
                    BusCompany.name.ilike(search_term),
                )
            )

        result = await self.db.execute(stmt)
        return result.scalar()

    async def count_search(
        self,
        origin: Optional[str] = None,
        destination: Optional[str] = None,
        travel_date: Optional[date] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        bus_type: Optional[str] = None,
        route_id: Optional[UUID] = None,
        bus_id: Optional[UUID] = None,
        status: Optional[str] = None,
        include_bookable_only: bool = True,
        include_inactive: bool = False,
        time_of_day: Optional[str] = None,
    ) -> int:
        """
        Count total results for search (for pagination).
        """
        stmt = (
            select(func.count())
            .select_from(Schedule)
            .join(Route, Schedule.route_id == Route.id)
            .join(Bus, Schedule.bus_id == Bus.id)
            .join(BusCompany, Bus.company_id == BusCompany.id)
        )

        # Apply same filters as search_schedules
        if include_bookable_only:
            now = datetime.now()
            # If travel_date provided, ensure the travel date is within the booking window
            if travel_date:
                travel_datetime = datetime.combine(travel_date, datetime.min.time())
                stmt = stmt.where(
                    and_(
                        Schedule.booking_open_date <= now,
                        Schedule.booking_close_date >= now,
                        Schedule.is_active == True,
                        # Travel date must be within booking window
                        Schedule.booking_open_date <= travel_datetime,
                        Schedule.booking_close_date >= travel_datetime,
                    )
                )
            else:
                stmt = stmt.where(
                    and_(
                        Schedule.booking_open_date <= now,
                        Schedule.booking_close_date >= now,
                        Schedule.is_active == True,
                    )
                )

        if time_of_day:
            start_time, end_time = self._get_time_range(time_of_day)
            stmt = stmt.where(
                and_(
                    Schedule.departure_time >= start_time,
                    Schedule.departure_time <= end_time,
                )
            )

        if not include_inactive:
            stmt = stmt.where(Schedule.is_active == True)

        if origin:
            stmt = stmt.where(Route.origin.ilike(f"%{origin}%"))

        if destination:
            stmt = stmt.where(Route.destination.ilike(f"%{destination}%"))

        if route_id:
            stmt = stmt.where(Schedule.route_id == route_id)

        if bus_id:
            stmt = stmt.where(Schedule.bus_id == bus_id)

        if bus_type:
            stmt = stmt.where(Bus.bus_type == bus_type)

        if travel_date:
            start_of_day = datetime.combine(travel_date, time.min)
            end_of_day = datetime.combine(travel_date, time.max)
            stmt = stmt.where(
                and_(
                    Schedule.departure_time >= start_of_day.time(),
                    Schedule.departure_time <= end_of_day.time(),
                )
            )

        if status:
            stmt = stmt.where(Schedule.status == status)

        if min_price is not None:
            stmt = stmt.where(Schedule.local_price >= min_price)

        if max_price is not None:
            stmt = stmt.where(Schedule.local_price <= max_price)

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
            raise ValueError(
                "Failed to create schedule. Please check route and bus IDs."
            )

    async def update(self, schedule_id: UUID, update_data: dict) -> Optional[Schedule]:
        schedule = await self.get_by_id(schedule_id)
        if not schedule:
            return None

        try:
            stmt = (
                update(Schedule)
                .where(Schedule.id == schedule_id)
                .values(**update_data)
                .returning(Schedule.id)
            )
            await self.db.execute(stmt)
            await self.db.commit()
            # Reload with relationships for response serialization
            return await self.get_by_id(schedule_id)
        except IntegrityError:
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
        # Reload with relationships for response serialization
        return await self.get_by_id(schedule_id)
