from typing import Optional
from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.api.deps import require_permission
from app.schemas.schedule import ScheduleCreate, ScheduleUpdate, ScheduleResponse
from app.services.schedule_service import ScheduleService

router = APIRouter(
    prefix="/schedules",
    tags=["Schedules"],
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Not enough permissions"},
        404: {"description": "Schedule not found"},
    },
)

# ============================================
# 1. List All Schedules (Public)
# ============================================
@router.get(
    "/",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="List all schedules",
)
async def list_schedules(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum records to return"),
    search: Optional[str] = Query(None, description="Search by route, bus, or company"),
    route_id: Optional[UUID] = Query(None, description="Filter by route ID"),
    bus_id: Optional[UUID] = Query(None, description="Filter by bus ID"),
    status: Optional[str] = Query(None, description="Filter by status (active, cancelled, completed, delayed)"),
    from_date: Optional[date] = Query(None, description="Filter from date"),
    to_date: Optional[date] = Query(None, description="Filter to date"),
    include_inactive: bool = Query(False, description="Include inactive schedules"),
    db: AsyncSession = Depends(get_db),
):
    service = ScheduleService(db)
    result = await service.list_schedules(
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
    return {"status": "success", "data": result}


# ============================================
# 2. Get Schedule by ID (Public)
# ============================================
@router.get(
    "/{schedule_id}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Get a schedule by ID",
)
async def get_schedule(
    schedule_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    service = ScheduleService(db)
    schedule = await service.get_schedule(schedule_id)
    return {"status": "success", "data": ScheduleResponse.model_validate(schedule)}



# ============================================
# 3. Create Schedule (Admin Only)
# Permission Required: schedules:write
# ============================================
@router.post(
    "/",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new schedule",
)
async def create_schedule(
    schedule_data: ScheduleCreate,
    current_user: User = Depends(require_permission("schedules:write")),
    db: AsyncSession = Depends(get_db),
):
    service = ScheduleService(db)
    schedule = await service.create_schedule(schedule_data)
    return {
        "status": "success",
        "message": "Schedule created successfully",
        "data": ScheduleResponse.model_validate(schedule),
    }


# ============================================
# 4. Update Schedule (Admin Only)
# Permission Required: schedules:write
# ============================================
@router.put(
    "/{schedule_id}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Update an existing schedule",
)
async def update_schedule(
    schedule_id: UUID,
    update_data: ScheduleUpdate,
    current_user: User = Depends(require_permission("schedules:write")),
    db: AsyncSession = Depends(get_db),
):
    service = ScheduleService(db)
    schedule = await service.update_schedule(schedule_id, update_data)
    return {
        "status": "success",
        "message": "Schedule updated successfully",
        "data": ScheduleResponse.model_validate(schedule),
    }


# ============================================
# 5. Update Schedule Status (Admin Only)
# ============================================
@router.put(
    "/{schedule_id}/status",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Update the status of a schedule",
)
async def update_schedule_status(
    schedule_id: UUID,
    status: str = Query(..., description="New status: active, cancelled, completed, delayed"),
    current_user: User = Depends(require_permission("schedules:write")),
    db: AsyncSession = Depends(get_db),
):
    service = ScheduleService(db)
    schedule = await service.update_schedule_status(schedule_id, status)
    return {
        "status": "success",
        "message": f"Schedule status updated to '{status}'",
        "data": schedule,
    }


# ============================================
# 6. Delete Schedule (Admin Only)
# Permission Required: schedules:write
# ============================================
@router.delete(
    "/{schedule_id}",
    response_model=None,
    status_code=status.HTTP_200_OK,
    summary="Delete a schedule by ID",
)
async def delete_schedule(
    schedule_id: UUID,
    hard_delete: bool = Query(False, description="Permanently delete (default: soft delete)"),
    current_user: User = Depends(require_permission("schedules:delete")),
    db: AsyncSession = Depends(get_db),
):
    service = ScheduleService(db)
    if hard_delete:
        await service.delete_schedule(schedule_id)
    else:
        await service.soft_delete_schedule(schedule_id)
    return None