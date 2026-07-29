from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.api.deps import require_permission
from app.schemas.seat import SeatCreate, SeatUpdate, SeatResponse, SeatBatchCreate
from app.services.seat_service import SeatService
from app.schemas.seat_layout import SeatLayoutCreate, SeatLayoutUpdate, SeatLayoutResponse



router = APIRouter(
    prefix="/seats",
    tags=["Seat Management"],
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Not enough permissions"},
        404: {"description": "Seat not found"},
    },
)


# ============================================
# 1. List Seats by Bus (Public - No permission required)
# ============================================
@router.get(
    "/bus/{bus_id}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="List all seats for a bus",
)
async def list_seats_by_bus(
    bus_id: UUID,
    include_inactive: bool = Query(False, description="Include inactive seats"),
    db: AsyncSession = Depends(get_db),
):
    service = SeatService(db)
    result = await service.list_seats(bus_id, include_inactive)
    return {"status": "success", "data": result}

# ============================================
# 2. Get Seat by ID (Public)
# ============================================
@router.get(
    "/{seat_id}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Get seat by ID",
)
async def get_seat(
    seat_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    service = SeatService(db)
    seat = await service.get_seat(seat_id)
    return {"status": "success", "data": seat}

# ============================================
# 3. Generate Seats for Bus (Admin Only)
# Permission Required: seats:write
# ============================================
@router.post(
    "/generate",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Generate seats for a bus",
)
async def generate_seats(
    batch_data: SeatBatchCreate,
    current_user : User = Depends(require_permission("seats:write")),
    db: AsyncSession = Depends(get_db),
):
    service = SeatService(db)
    seats = await service.generate_seats_for_bus(
        bus_id=batch_data.bus_id,
        count=batch_data.count,
        start_from=batch_data.start_from
    )
    return {
        "status": "success",
        "message": f"Generated {len(seats)} seats successfully",
        "data": seats,
    }

# ============================================
# 4. Create Single Seat (Admin Only)
# Permission Required: seats:write
# ============================================
@router.post(
    "/",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Create a single seat",
)
async def create_seat(
    seat_data: SeatCreate,
    current_user: User = Depends(require_permission("seats:write")),
    db: AsyncSession = Depends(get_db),
):
    service = SeatService(db)
    seat = await service.create_seat(seat_data)
    return {
        "status": "success",
        "message": "Seat created successfully",
        "data": seat,
    }

# ============================================
# 5. Update Seat (Admin Only)
# Permission Required: seats:write
# ============================================
@router.put(
    "/{seat_id}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Update a seat",
)
async def update_seat(
    seat_id: UUID,
    update_data: SeatUpdate,
    current_user: User = Depends(require_permission("seats:write")),
    db: AsyncSession = Depends(get_db),
):
    service = SeatService(db)
    seat = await service.update_seat(seat_id, update_data)
    return {
        "status": "success",
        "message": "Seat updated successfully",
        "data": seat,
    }

# ============================================
# 6. Delete Seat (Admin Only)
# Permission Required: seats:delete
# ============================================
@router.delete(
    "/{seat_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a seat",
)
async def delete_seat(
    seat_id: UUID,
    hard_delete: bool = Query(False, description="Permanently delete (default: soft delete)"),
    current_user: User = Depends(require_permission("seats:delete")),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a seat. Admin only.
    - hard_delete=False: Soft delete (is_active=False)
    - hard_delete=True: Permanently delete
    """
    service = SeatService(db)
    await service.delete_seat(seat_id, hard_delete)
    return None


# ============================================
# 3a. Generate Seats with Dynamic Layout (NEW)
# ============================================
@router.post(
    "/generate-layout",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Generate seats with dynamic layout",
)
async def generate_seats_with_layout(
    bus_id: UUID,
    rows: int = Query(..., ge=1, le=50, description="Number of rows"),
    columns: int = Query(..., ge=1, le=10, description="Number of columns"),
    start_from: int = Query(1, ge=1, description="Starting seat number"),
    skip_seats: str = Query("", description="Comma-separated seats to skip"),
    seat_naming: str = Query(
        "default",
        description="Naming style: 'default' (A1,B1), 'prefix' (BUS-01A), 'custom' (R01C01), 'vip' (VIP-01A), 'numeric' (1,2,3)"
    ),
    prefix: str = Query("", description="Prefix for naming (if seat_naming='prefix')"),
    current_user: User = Depends(require_permission("seats:write")),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate seats for a bus with dynamic layout.
    
    Examples:
    - VIP Car: rows=11, columns=3, seat_naming=vip
    - Regular Bus: rows=10, columns=4, seat_naming=default
    - Numeric: rows=10, columns=4, seat_naming=numeric (1,2,3,4,...)
    - Custom: rows=10, columns=4, seat_naming=custom (R01C01, R01C02, ...)
    """
    skip_list = [s.strip().upper() for s in skip_seats.split(",") if s.strip()]

    config = {
        "skip_seats": skip_list,
        "seat_naming": seat_naming,
    }
    if prefix:
        config["prefix"] = prefix

    service = SeatService(db)
    seats = await service.generate_seats_for_bus_with_layout(
        bus_id=bus_id,
        rows=rows,
        columns=columns,
        start_from=start_from,
        config=config,
    )
    return {
        "status": "success",
        "message": f"Generated {len(seats)} seats successfully",
        "data": {
            "seats": seats,
            "layout": {
                "rows": rows,
                "columns": columns,
                "config": config,
            }
        },
    }



# ============================================
# 7. Get Seat Layout (Public)
# ============================================
@router.get(
    "/layout/{bus_id}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Get seat layout for a bus",
)
async def get_seat_layout(
    bus_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    service = SeatService(db)
    layout = await service.get_seat_layout(bus_id)
    return {
        "status": "success",
        "data": layout,
    }

# ============================================
# 8. Update Seat Layout (Admin Only)
# ============================================
@router.put(
    "/layout/{bus_id}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Update seat layout for a bus",
)
async def update_seat_layout(
    bus_id: UUID,
    update_data: SeatLayoutUpdate,
    current_user: User = Depends(require_permission("seats:write")),
    db: AsyncSession = Depends(get_db),
):
    service = SeatService(db)
    layout = await service.update_seat_layout(bus_id, update_data)
    return {
        "status": "success",
        "message": "Seat layout updated successfully",
        "data": layout,
    }