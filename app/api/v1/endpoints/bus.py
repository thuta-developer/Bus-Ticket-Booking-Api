from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.api.deps import require_permission
from app.schemas.bus import (
    BusCreate,
    BusUpdate,
    BusResponse,
)
from app.services.bus_service import BusService

router = APIRouter(
    prefix="/buses",
    tags=["Buses"],
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Not enough permissions"},
        404: {"description": "Bus not found"},
    },
)


# ============================================
# 1. List All Companies (Public - No permission required)
# ============================================
@router.get(
    "/",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="List all buses",
    description="Public endpoint to list buses (active only by default)",
)
async def list_buses(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum records to return"),
    search: Optional[str] = Query(
        None, description="Search by bus number, license plate, or company name"
    ),
    company_id: Optional[UUID] = Query(None, description="Filter by company ID"),
    bus_type: Optional[str] = Query(
        None, description="Filter by bus type (AC, NON_AC, VIP, EXPRESS)"
    ),
    include_inactive: bool = Query(False, description="Include inactive buses"),
    db: AsyncSession = Depends(get_db),
):
    service = BusService(db)
    result = await service.list_buses(
        skip=skip,
        limit=limit,
        search=search,
        company_id=company_id,
        bus_type=bus_type,
        include_inactive=include_inactive,
    )
    return {"status": "success", "data": result}


# ============================================
# 2. Get Bus by ID (Public)
# ============================================
@router.get(
    "/{bus_id}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Get bus by ID",
)
async def get_bus(
    bus_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    service = BusService(db)
    bus = await service.get_bus(bus_id)
    return {"status": "success", "data": BusResponse.model_validate(bus)}


# ============================================
# 3. Create Bus (Admin Only)
# Permission Required: buses:write
# ============================================
@router.post(
    "/",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new bus",
)
async def create_bus(
    bus_data: BusCreate,
    current_user: User = Depends(require_permission("buses:write")),
    db: AsyncSession = Depends(get_db),
):
    service = BusService(db)
    bus = await service.create_bus(bus_data)
    return {
        "status": "success",
        "message": "Bus created successfully",
        "data": bus,
    }


# ============================================
# 4. Update Bus (Admin Only)
# Permission Required: buses:write
# ============================================
@router.put(
    "/{bus_id}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Update an existing bus company",
)
async def update_bus(
    bus_id: UUID,
    update_data: BusUpdate,
    current_user: User = Depends(require_permission("buses:write")),
    db: AsyncSession = Depends(get_db),
):
    service = BusService(db)
    bus = await service.update_bus(bus_id, update_data)
    return {
        "status": "success",
        "message": "Bus updated successfully",
        "data": BusResponse.model_validate(bus),
    }


# ============================================
# 5. Delete Bus (Admin Only)
# Permission Required: buses:delete
# ============================================
@router.delete(
    "/{bus_id}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Delete a bus",   
)
async def delete_bus(
    bus_id: UUID,
    hard_delete: bool = Query(False, description="Permanently delete (default: soft delete)"),
    current_user: User = Depends(require_permission("buses:delete")),
    db: AsyncSession = Depends(get_db),
):
    service = BusService(db)
    if hard_delete:
        await service.delete_bus(bus_id)
    else:
        await service.soft_delete_bus(bus_id)
    return {
        "status": "success",
        "message": f"Bus {'hard ' if hard_delete else 'soft '}deleted successfully",
    }