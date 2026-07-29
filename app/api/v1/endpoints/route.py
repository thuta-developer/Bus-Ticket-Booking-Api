from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, distinct, select

from app.core.database import get_db
from app.models.user import User
from app.api.deps import require_permission
from app.schemas.route import (
    RouteCreate,
    RouteUpdate,
    RouteResponse,
)
from app.models.route import Route
from app.services.route_service import RouteService

router = APIRouter(
    prefix="/routes",
    tags=["Routes"],
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Not enough permissions"},
        404: {"description": "Route not found"},
    },
)


# ============================================
# 1. List All Routes (Public - No permission required)
# ============================================
@router.get(
    "/",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="List all routes",
)
async def list_routes(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of records to return"),
    search: Optional[str] = Query(None, description="Search term for company name or description"),
    origin: Optional[str] = Query(None, description="Filter by origin city"),
    destination: Optional[str] = Query(None, description="Filter by destination city"),
    include_inactive: bool = Query(False, description="Include inactive routes"),
    db: AsyncSession = Depends(get_db),
):
    service = RouteService(db)
    result = await service.list_routes(skip=skip, limit=limit, search=search, origin=origin, destination=destination , include_inactive=include_inactive)
    return {"status": "success", "data": result}


# ============================================
# 2. Get Route by ID (Public)
# ============================================
@router.get(
    "/{route_id}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Get a route by ID",
)
async def get_route(
    route_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    service = RouteService(db)
    route = await service.get_route(route_id)
    return {"status": "success", "data": RouteResponse.model_validate(route)}

# ============================================
# 3. Create Route (Admin Only)
# Permission Required: routes:write
# ============================================
@router.post(
    "/",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new route",
)
async def create_route(
    route_data: RouteCreate,
    current_user: User = Depends(require_permission("routes:write")),
    db: AsyncSession = Depends(get_db),
):
    service = RouteService(db)
    route = await service.create_route(route_data)
    return {
        "status": "success",
        "message": "Route created successfully",
        "data": RouteResponse.model_validate(route),
    }


# ============================================
# 4. Update Route (Admin Only)
# Permission Required: route:write
# ============================================
@router.put(
    "/{route_id}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Update an existing route",
)
async def update_route(
    route_id: UUID,
    update_data: RouteUpdate,
    current_user : User = Depends(require_permission("routes:write")),
    db: AsyncSession = Depends(get_db),
):
    service = RouteService(db)
    route = await service.update_route(route_id, update_data)
    return {
        "status": "success",
        "message": "Route updated successfully",
        "data": RouteResponse.model_validate(route),
    }



# ============================================
# 5. Delete Route (Admin Only)
# Permission Required: routes:delete
# ============================================
@router.delete(
    "/{route_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a route (Admin)",
)
async def delete_route(
    route_id: UUID,
    hard_delete: bool = Query(False, description="Permanently delete (default: soft delete)"),
    current_user: User = Depends(require_permission("routes:delete")),
    db: AsyncSession = Depends(get_db),
):
    service = RouteService(db)
    await service.delete_route(route_id, hard_delete)
    return None



# ============================================
# 6. Get Origin/Destination List (Public)
# ============================================
@router.get(
    "/cities/origins",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Get all unique origins",
)
async def get_origins(
    db: AsyncSession = Depends(get_db),
):
    service = RouteService(db)
    stmt = select(distinct(Route.origin)).where(Route.is_active == True).order_by(Route.origin)
    result = await db.execute(stmt)
    origins = result.scalars().all()

    return {"status" : "success", "data": origins}




@router.get(
    "/cities/destinations",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Get all unique destinations",
)
async def get_destinations(
    db: AsyncSession = Depends(get_db),
):
    service = RouteService(db)
    stmt = select(distinct(Route.destination)).where(Route.is_active == True).order_by(Route.destination)
    result = await db.execute(stmt)
    destinations = result.scalars().all()

    return {"status" : "success", "data": destinations}