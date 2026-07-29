from typing import Optional, Dict, Any
from uuid import UUID
from datetime import date
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.schedule_repository import ScheduleRepository
from app.models.schedule import Schedule
from app.repositories.route_repository import RouteRepository
from app.repositories.bus_repository import BusRepository
from app.schemas.schedule import ScheduleCreate, ScheduleUpdate, ScheduleResponse


class ScheduleService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = ScheduleRepository(self.db)
        self.route_repository = RouteRepository(self.db)
        self.bus_repository = BusRepository(self.db)


    async def create_schedule(self, schedule_data: ScheduleCreate) -> ScheduleResponse:
        route = await self.route_repository.get_by_id(schedule_data.route_id)
        if not route:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Route not found"
            )

        bus = await self.bus_repository.get_by_id(schedule_data.bus_id)
        if not bus:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bus not found"
            )

        try:
            schedule = await self.repository.create(schedule_data.model_dump())
            return await self._to_response(schedule)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

    async def get_schedule(self, schedule_id: UUID) -> ScheduleResponse:
        schedule = await self.repository.get_by_id(schedule_id)
        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Schedule with ID '{schedule_id}' not found"
            )
        return await self._to_response(schedule)


    async def list_schedules(
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
    ) -> Dict[str, Any]:
        schedules = await self.repository.get_all(
            skip=skip,
            limit=limit,
            search=search,
            route_id=route_id,
            bus_id=bus_id,
            status=status,
            from_date=from_date,
            to_date=to_date,
            include_inactive=include_inactive,
        )

        total = await self.repository.count(
            search=search,
            route_id=route_id,
            bus_id=bus_id,
            status=status,
            from_date=from_date,
            to_date=to_date,
            include_inactive=include_inactive,
        )

        items = [await self._to_response(schedule) for schedule in schedules]

        return {
            "items": items,
            "total": total,
            "skip": skip,
            "limit": limit,
            "search": search,
        }

    async def update_schedule(
        self,
        schedule_id: UUID,
        update_data: ScheduleUpdate,
    ) -> ScheduleResponse:
        existing = await self.repository.get_by_id(schedule_id)

        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Schedule not found"
            )

        if update_data.route_id:
            route = await self.route_repository.get_by_id(update_data.route_id)
            if not route:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Route not found"
                )

        if update_data.bus_id:
            bus = await self.bus_repository.get_by_id(update_data.bus_id)
            if not bus:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Bus not found"
                )

        update_dict = update_data.model_dump(exclude_unset=True)

        if not update_dict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No data provided for update"
            )

        try:
            schedule = await self.repository.update(schedule_id, update_dict)
            if not schedule:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Schedule not found for update"
                )
            return await self._to_response(schedule)

        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

    async def delete_schedule(self, schedule_id: UUID) -> None:
        await self.get_schedule(schedule_id)

        deleted = await self.repository.delete(schedule_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Schedule not found"
            )

    async def soft_delete_schedule(self, schedule_id: UUID) -> None:
        await self.get_schedule(schedule_id)
        deleted = await self.repository.soft_delete(schedule_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Schedule not found"
            )


    async def update_schedule_status(self, schedule_id: UUID, status: str) -> ScheduleResponse:
        await self.get_schedule(schedule_id)
        schedule = await self.repository.update_status(schedule_id, status)
        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Schedule not found"
            )

    async def _to_response(self, schedule: Schedule) -> ScheduleResponse:
        response = ScheduleResponse.model_validate(schedule)
        if schedule.route:
            response.route_origin = schedule.route.origin
            response.route_destination = schedule.route.destination
        if schedule.bus:
            response.bus_number = schedule.bus.bus_number
            if schedule.bus.company:
                response.company_name = schedule.bus.company.name
        return response