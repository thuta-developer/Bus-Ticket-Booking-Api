from typing import Optional
from uuid import UUID
from datetime import datetime,date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.api.deps import require_permission
from app.schemas.schedule import ScheduleCreate, ScheduleUpdate, ScheduleResponse
from app.services.schedule_service import ScheduleService

from app.api.deps import get_current_active_user
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
#  SEARCH SCHEDULES
# ============================================
@router.get(
    "/search",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Search schedules with dynamic pricing",
    description="Search for schedules by origin, destination, travel date, and user type",
)
async def search_schedules(
    origin: Optional[str] = Query(None, description="Origin city"),
    destination: Optional[str] = Query(None, description="Destination city"),
    travel_date: Optional[datetime] = Query(None, description="Travel date"),
    user_type: str = Query(
        "local", 
        regex="^(local|foreigner)$",
        description="User type: 'local' or 'foreigner'"
    ),
    min_price: Optional[float] = Query(
        None, 
        ge=0, 
        description="Minimum price (MMK)"
    ),
    max_price: Optional[float] = Query(
        None, 
        ge=0, 
        description="Maximum price (MMK)"
    ),
     bus_type: Optional[str] = Query(
        None, 
        description="Bus type: AC, NonAC, VIP, Express, Normal"
    ),
    include_bookable_only: bool = Query(
        True, 
        description="Only show schedules within booking window"
    ),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum records to return"),
    time_of_day: Optional[str] = Query(
        None,
        description="Filter by time of day: morning, afternoon, night"
    ),
    
    db: AsyncSession = Depends(get_db),
):
    service = ScheduleService(db)
    result = await service.search_schedules(
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
        time_of_day=time_of_day
    )
    return {"status": "success", "data": result}
    








# ============================================
# 1. List Schedules with Search & Price
# ============================================
@router.get(
    "/",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="List all schedules with price calculation",
)
async def list_schedules(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum records to return"),
    search: Optional[str] = Query(None, description="Search by origin, destination, bus number, or company"),
    route_id: Optional[UUID] = Query(None, description="Filter by route ID"),
    bus_id: Optional[UUID] = Query(None, description="Filter by bus ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    departure_date: Optional[datetime] = Query(None, description="Filter by departure date"),
    include_inactive: bool = Query(False, description="Include inactive schedules"),
    include_bookable_only: bool = Query(True, description="Only show bookable schedules"),
    user_type: str = Query("local", description="User type: 'local' or 'foreigner'"),
    travel_date: Optional[datetime] = Query(None, description="Travel date for festival price calculation (defaults to now)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get schedules with dynamic pricing.
    
    - **user_type**: 'local' or 'foreigner' - determines which price to show
    - **departure_date**: Show schedules for a specific date
    - **travel_date**: The date you plan to travel. If it falls within the festival period,
      festival pricing will be applied. Defaults to current date/time.
    - **include_bookable_only**: Only show schedules within booking window
    """
    service = ScheduleService(db)
    result = await service.list_schedules(
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
        travel_date=travel_date,
    )
    return {"status": "success", "data": result}


# ============================================
# 2. Get Schedule with Price
# ============================================
@router.get(
    "/{schedule_id}/price",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Get schedule with price calculation",
)
async def get_schedule_with_price(
    schedule_id: UUID,
    user_type: str = Query("local", description="User type: 'local' or 'foreigner'"),
    travel_date: Optional[datetime] = Query(None, description="Travel date for festival price calculation (defaults to now)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific schedule with calculated price for the user.
    
    - **travel_date**: The date you plan to travel. If it falls within the festival period,
      festival pricing will be applied. Defaults to current date/time.
    """
    service = ScheduleService(db)
    result = await service.get_schedule_with_price(schedule_id, user_type, travel_date=travel_date)
    return {"status": "success", "data": result}


# ============================================
# 3. Get Schedule by ID (Legacy)
# # ============================================
# @router.get(
#     "/{schedule_id}",
#     response_model=dict,
#     status_code=status.HTTP_200_OK,
#     summary="Get a schedule by ID",
# )
# async def get_schedule(
#     schedule_id: UUID,
#     db: AsyncSession = Depends(get_db),
# ):
#     service = ScheduleService(db)
#     schedule = await service.get_schedule(schedule_id)
#     return {"status": "success", "data": ScheduleResponse.model_validate(schedule)}

@router.get(
    "/{schedule_id}/detail",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Get schedule detail with seats",
    description="Get complete schedule detail including bus info, seats, and price.",
)
async def get_schedule_detail(
    schedule_id: UUID,
    user_type: str = Query("local", regex="^(local|foreigner)$"),
    travel_date: Optional[date] = Query(None, description="Date of travel"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_active_user),
):
    """
    Get full schedule detail for seat selection.
    
    Returns:
    - Schedule info (route, time)
    - Bus info (company, type, features, images)
    - Seat layout (all seats with availability)
    - Price calculation (based on user type and date)
    """
    service = ScheduleService(db)
    result = await service.get_schedule_detail(
        schedule_id=schedule_id,
        user_type=user_type,
        travel_date=travel_date,
    )
    return {"status": "success", "data": result}
# ============================================
# 4. Create Schedule (Admin Only)
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
# 5. Update Schedule (Admin Only)
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
# 6. Update Schedule Status (Admin Only)
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
# 7. Delete Schedule (Admin Only)
# ============================================
@router.delete(
    "/{schedule_id}",
    response_model=None,
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a schedule",
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