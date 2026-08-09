from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timezone, date
from decimal import Decimal
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.schedule_repository import ScheduleRepository
from app.repositories.route_repository import RouteRepository
from app.repositories.bus_repository import BusRepository
from app.models.schedule import Schedule
from app.schemas.schedule import (
    ScheduleCreate,
    ScheduleUpdate,
    ScheduleResponse,
    SchedulePriceResponse,
    ScheduleSearchFilter,
)


class ScheduleService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = ScheduleRepository(db)
        self.route_repository = RouteRepository(db)
        self.bus_repository = BusRepository(db)

    # ========================================
    # Price Calculation
    # ========================================
    def calculate_price(
        self,
        schedule: Schedule,
        user_type: str = "local",
        check_date: Optional[datetime] = None,
    ) -> SchedulePriceResponse:
        """
        Calculate the appropriate price based on user type and festival status.
        """
        if check_date is None:
            check_date = datetime.now(timezone.utc)
        elif check_date.tzinfo is None:
            check_date = check_date.replace(tzinfo=timezone.utc)

        is_festival = False
        final_price = schedule.local_price
        price_type = "local"

        festival_start = schedule.festival_start_date
        festival_end = schedule.festival_end_date

        if festival_start and festival_end:
            if festival_start.tzinfo is None:
                festival_start = festival_start.replace(tzinfo=timezone.utc)

            if festival_end.tzinfo is None:
                festival_end = festival_end.replace(tzinfo=timezone.utc)

            if festival_start <= check_date <= festival_end:
                is_festival = True

        #  Determine price based on user type and festival status
        if is_festival:
            if (
                user_type == "foreigner"
                and schedule.foreigner_festival_price is not None
            ):
                final_price = schedule.foreigner_festival_price
                price_type = "festival_foreigner"
            elif schedule.local_festival_price is not None:
                final_price = schedule.local_festival_price
                price_type = "festival_local"
            else:
                # Fallback to regular prices if festival prices not set
                if user_type == "foreigner":
                    final_price = schedule.foreigner_price
                    price_type = "foreigner"
                else:
                    final_price = schedule.local_price
                    price_type = "local"
        else:
            if user_type == "foreigner":
                final_price = schedule.foreigner_price
                price_type = "foreigner"
            else:
                final_price = schedule.local_price
                price_type = "local"

        return SchedulePriceResponse(
            schedule_id=schedule.id,
            base_price=schedule.local_price,
            final_price=final_price,
            price_type=price_type,
            is_festival=is_festival,
            user_type=user_type,
        )

    # ========================================
    # Search
    # ========================================
    async def search_schedules(
        self,
        origin: Optional[str] = None,
        destination: Optional[str] = None,
        travel_date: Optional[date] = None,
        user_type: str = "local",
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        bus_type: Optional[str] = None,
        include_bookable_only: bool = True,
        skip: int = 0,
        limit: int = 20,
    ):
        schedules = await self.repository.search_schedules(
            origin=origin,
            destination=destination,
            travel_date=travel_date,
            user_type=user_type,
            min_price=min_price,
            max_price=max_price,
            bus_type=bus_type,
            include_bookable_only=include_bookable_only,
            skip=skip,
            limit=limit,
        )

        total = await self.repository.count_search(
            origin=origin,
            destination=destination,
            travel_date=travel_date,
            min_price=min_price,
            max_price=max_price,
            bus_type=bus_type,
            include_bookable_only=include_bookable_only,
        )

        items = []
        for schedule in schedules:
            schedule_res = await self._to_response(schedule)

            price_info = self.calculate_price(
                schedule, user_type, check_date=travel_date
            )

            items.append(
                {
                    "schedule": schedule_res,
                    "price": price_info,
                }
            )



        return {
            "items": items,
            "total": total,
            "skip": skip,
            "limit": limit,
            "filters": {
                "origin": origin,
                "destination": destination,
                "travel_date": travel_date.isoformat() if travel_date else None,
                "user_type": user_type,
                "min_price": min_price,
                "max_price": max_price,
                "bus_type": bus_type,
                "include_bookable_only": include_bookable_only,
            }
        }

    # ========================================
    # CRUD Operations
    # ========================================
    async def create_schedule(self, schedule_data: ScheduleCreate) -> ScheduleResponse:
        # Validate route
        route = await self.route_repository.get_by_id(schedule_data.route_id)
        if not route:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Route not found"
            )

        # Validate bus
        bus = await self.bus_repository.get_by_id(schedule_data.bus_id)
        if not bus:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Bus not found"
            )

        try:
            schedule = await self.repository.create(schedule_data.model_dump())
            return await self._to_response(schedule)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def get_schedule(self, schedule_id: UUID) -> ScheduleResponse:
        schedule = await self.repository.get_by_id(schedule_id)
        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Schedule with ID '{schedule_id}' not found",
            )
        return await self._to_response(schedule)

    async def get_schedule_with_price(
        self,
        schedule_id: UUID,
        user_type: str = "local",
        travel_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Get schedule with calculated price for the user.
        """
        schedule = await self.repository.get_by_id(schedule_id)
        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found"
            )

        price_info = self.calculate_price(schedule, user_type, check_date=travel_date)
        response = await self._to_response(schedule)

        return {
            "schedule": response,
            "price": price_info,
        }

    async def list_schedules(
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
        travel_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        schedules = await self.repository.get_all(
            skip=skip,
            limit=limit,
            search=search,
            route_id=route_id,
            bus_id=bus_id,
            status=status,
            departure_date=departure_date,
            include_inactive=include_inactive,
            include_bookable_only=include_bookable_only,
            user_type=user_type,
        )

        total = await self.repository.count(
            search=search,
            route_id=route_id,
            bus_id=bus_id,
            status=status,
            departure_date=departure_date,
            include_inactive=include_inactive,
            include_bookable_only=include_bookable_only,
        )

        # Use travel_date for price calculation if provided, otherwise fallback to departure_date or None (defaults to now)
        check_date = travel_date or departure_date

        items = []
        for schedule in schedules:
            response = await self._to_response(schedule)
            price_info = self.calculate_price(
                schedule, user_type, check_date=check_date
            )
            items.append(
                {
                    "schedule": response,
                    "price": price_info,
                }
            )

        return {
            "items": items,
            "total": total,
            "skip": skip,
            "limit": limit,
            "search": search,
            "user_type": user_type,
        }

    async def update_schedule(
        self,
        schedule_id: UUID,
        update_data: ScheduleUpdate,
    ) -> ScheduleResponse:
        existing = await self.repository.get_by_id(schedule_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found"
            )

        if update_data.route_id:
            route = await self.route_repository.get_by_id(update_data.route_id)
            if not route:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Route not found"
                )

        if update_data.bus_id:
            bus = await self.bus_repository.get_by_id(update_data.bus_id)
            if not bus:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Bus not found"
                )

        update_dict = update_data.model_dump(exclude_unset=True)
        if not update_dict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No data provided for update",
            )

        try:
            schedule = await self.repository.update(schedule_id, update_dict)
            if not schedule:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Schedule not found for update",
                )
            return await self._to_response(schedule)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def delete_schedule(self, schedule_id: UUID) -> None:
        await self.get_schedule(schedule_id)
        deleted = await self.repository.delete(schedule_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found"
            )

    async def soft_delete_schedule(self, schedule_id: UUID) -> None:
        await self.get_schedule(schedule_id)
        deleted = await self.repository.soft_delete(schedule_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found"
            )

    async def update_schedule_status(
        self,
        schedule_id: UUID,
        status: str,
    ) -> ScheduleResponse:
        await self.get_schedule(schedule_id)
        schedule = await self.repository.update_status(schedule_id, status)
        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found"
            )
        return await self._to_response(schedule)

    # ========================================
    # Helper
    # ========================================
    async def _to_response(self, schedule: Schedule) -> ScheduleResponse:
        response = ScheduleResponse.model_validate(schedule)
        if schedule.route:
            response.route_origin = schedule.route.origin
            response.route_destination = schedule.route.destination
        if schedule.bus:
            response.bus_number = schedule.bus.bus_number
            if schedule.bus.company:
                response.company_name = schedule.bus.company.name
                response.company_logo_url = schedule.bus.company.logo_url
        return response
