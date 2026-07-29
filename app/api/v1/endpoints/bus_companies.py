from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.api.deps import require_permission
from app.schemas.bus_company import (
    BusCompanyCreate,
    BusCompanyUpdate,
    BusCompanyResponse,
)
from app.services.bus_company_service import BusCompanyService

router = APIRouter(
    prefix="/bus-companies",
    tags=["Bus Companies"],
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Not enough permissions"},
        404: {"description": "Company not found"},
    },
)


# ============================================
# 1. List All Companies (Public - No permission required)
# ============================================
@router.get(
    "/",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="List all bus companies",
    description="Public endpoint to list bus companies (active only by default)",
)
async def list_companies(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of records to return"),
    search: Optional[str] = Query(None, description="Search term for company name or description"),
    include_inactive: bool = Query(False, description="Include inactive companies in the results"),
    db: AsyncSession = Depends(get_db),
):
    service = BusCompanyService(db)
    result = await service.list_companies(skip=skip, limit=limit, search=search, include_inactive=include_inactive)
    return {"status": "success", "data": result}


# ============================================
# 2. Get Company by ID (Public)
# ============================================
@router.get(
    "/{company_id}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Get a bus company by ID",
)
async def get_company(
    company_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    service = BusCompanyService(db)
    company = await service.get_company(company_id)
    return {"status": "success", "data": BusCompanyResponse.model_validate(company)}


# ============================================
# 3. Create Company (Admin Only)
# Permission Required: bus_companies:write
# ============================================
@router.post(
    "/",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new bus company",
)
async def create_company(
    company_data: BusCompanyCreate,
    current_user: User = Depends(require_permission("bus_companies:write")),
    db: AsyncSession = Depends(get_db),
):
    service = BusCompanyService(db)
    company = await service.create_company(company_data)
    return {
        "status": "success",
        "message": "Bus Company created successfully",
        "data": BusCompanyResponse.model_validate(company),
    }

# ============================================
# 4. Update Company (Admin Only)
# Permission Required: bus_companies:write
# ============================================
@router.put(
    "/{company_id}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Update an existing bus company",
)
async def update_company(
    company_id: UUID,
    update_data: BusCompanyUpdate,
    current_user : User = Depends(require_permission("bus_companies:write")),
    db: AsyncSession = Depends(get_db),
):
    service = BusCompanyService(db)
    company = await service.update_company(company_id, update_data)
    return {
        "status": "success",
        "message": "Bus Company updated successfully",
        "data": BusCompanyResponse.model_validate(company),
    }

# ============================================
# 5. Delete Company (Admin Only)
# Permission Required: bus_companies:delete
# ============================================
@router.delete(
    "/{company_id}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Delete a bus company",
)
async def delete_company(
    company_id: UUID,
    hard_delete: bool = Query(False, description="Permanently delete (default: soft delete)"),
    current_user: User = Depends(require_permission("bus_companies:delete")),
    db: AsyncSession = Depends(get_db),
):
    service = BusCompanyService(db)
    if hard_delete:
        await service.delete_company(company_id)
    else:
        await service.soft_delete_company(company_id)
    return {
        "status": "success",
        "message": f"Bus Company {'hard ' if hard_delete else 'soft '}deleted successfully",
    }
