from typing import Dict, Optional, Any
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.route import Route
from app.repositories.route_repository import RouteRepository
from app.schemas.route import RouteCreate, RouteResponse, RouteUpdate


class RouteService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = RouteRepository(db)

    # Create #
    async def create_route(self, route_data: RouteCreate) -> Route:
        existing = await self.repository.get_by_name(route_data.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Route '{route_data.name}' already exists",
            )

        existing = await self.repository.get_by_origin_destination(
            route_data.origin, route_data.destination
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Route from '{route_data.origin}' to '{route_data.destination}' already exists",
            )

        try:
            return await self.repository.create(route_data.model_dump())
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Read #
    async def get_route(self, route_id: UUID) -> Route:
        route = await self.repository.get_by_id(route_id)
        if not route:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Route with ID '{route_id}' not found",
            )
        return route

    async def list_routes(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        origin: Optional[str] = None,
        destination: Optional[str] = None,
        include_inactive: bool = False,
    ) -> Dict[str, Any]:
        routes = await self.repository.get_all(
            skip=skip,
            limit=limit,
            search=search,
            origin=origin,
            destination=destination,
            include_inactive=include_inactive,
        )
        total = await self.repository.count(
            search=search,
            origin=origin,
            destination=destination,
            include_inactive=include_inactive,
        )

        items = [RouteResponse.model_validate(route) for route in routes]
        return {
            "items": items,
            "total": total,
            "skip": skip,
            "limit": limit,
            "search": search,
        }

    # Update #
    async def update_route(self, route_id: UUID, update_data: RouteUpdate) -> RouteResponse:
        # Check if route exists
        existing_route = await self.repository.get_by_id(route_id)
        if not existing_route:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Route not found"
            )

        # Check name conflict
        if update_data.name:
            existing = await self.repository.get_by_name(update_data.name)
            if existing and existing.id != route_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Route '{update_data.name}' already exists"
                )

        # Check origin/destination conflict
        if update_data.origin and update_data.destination:
            existing = await self.repository.get_by_origin_destination(
                update_data.origin,
                update_data.destination
            )
            if existing and existing.id != route_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Route from '{update_data.origin}' to '{update_data.destination}' already exists"
                )

        update_dict = update_data.model_dump(exclude_unset=True)
        if not update_dict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid fields to update"
            )

        try:
            route = await self.repository.update(route_id, update_dict)
            if not route:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Route not found"
                )
            return RouteResponse.model_validate(route)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

    # Delete #
    async def delete_route(self, route_id: UUID, hard_delete: bool = False) -> None:
        # Check if route exists
        await self.get_route(route_id)

        if hard_delete:
            deleted = await self.repository.delete(route_id)
        else:
            deleted = await self.repository.soft_delete(route_id)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Route not found"
            )