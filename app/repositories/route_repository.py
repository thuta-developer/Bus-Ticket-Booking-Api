from typing import Optional, List
from uuid import UUID
from sqlalchemy import func, select, update, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.models.route import Route


class RouteRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, route_id: UUID) -> Optional[Route]:
        stmt = select(Route).where(Route.id == route_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Optional[Route]:
        stmt = select(Route).where(Route.name.ilike(name))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_origin_destination(
        self, origin: str, destination: str
    ) -> Optional[Route]:
        stmt = select(Route).where(
            and_(Route.origin.ilike(origin), Route.destination.ilike(destination))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        origin: Optional[str] = None,
        destination: Optional[str] = None,
        include_inactive: bool = False,
    ) -> List[Route]:
        stmt = select(Route)

        if not include_inactive:
            stmt = stmt.where(Route.is_active == True)

        if origin:
            stmt = stmt.where(Route.origin.ilike(f"%{origin}%"))

        if destination:
            stmt = stmt.where(Route.destination.ilike(f"%{destination}%"))

        if search:
            search_term = f"%{search}%"
            stmt = stmt.where(
                or_(
                    Route.name.ilike(search_term),
                    Route.origin.ilike(search_term),
                    Route.destination.ilike(search_term),
                    Route.description.ilike(search_term),
                )
            )

        stmt = stmt.offset(skip).limit(limit).order_by(Route.origin.asc(), Route.destination.asc())
        result = await self.db.execute(stmt)
        return result.scalars().all()


    async def count(
        self, 
        search: Optional[str] = None,
        origin: Optional[str] = None,
        destination: Optional[str] = None,
        include_inactive: bool = False
    ) -> int:
        stmt = select(func.count()).select_from(Route)

        if not include_inactive:
            stmt = stmt.where(Route.is_active == True)


        if origin:
            stmt = stmt.where(Route.origin.ilike(f"%{origin}%"))
        
        if destination:
            stmt = stmt.where(Route.destination.ilike(f"%{destination}%"))

        if search:
            search_term = f"%{search}%"
            stmt = stmt.where(
                or_(
                    Route.name.ilike(search_term),
                    Route.origin.ilike(search_term),
                    Route.destination.ilike(search_term),
                    Route.description.ilike(search_term),
                )
            )
        result = await self.db.execute(stmt)
        return result.scalar()

    async def create(self, route_data: dict) -> Route:
        try:
            route = Route(**route_data)
            self.db.add(route)
            await self.db.commit()
            await self.db.refresh(route)
            return route
        except IntegrityError as e:
            await self.db.rollback()
            raise ValueError("A route with this name already exists")

    
    async def update(self, route_id: UUID, update_data: dict) -> Optional[Route]:
        route = await self.get_by_id(route_id)
        if not route:
            return None
        
        try:
            stmt = (
                update(Route)
                .where(Route.id == route_id)
                .values(**update_data)
                .returning(Route)
            )
            result = await self.db.execute(stmt)
            await self.db.commit()
            return result.scalar_one_or_none()
        except IntegrityError:
            await self.db.rollback()
            raise ValueError("A route with this name already exists")
        


    async def delete(self, route_id: UUID) -> bool:
        route = await self.get_by_id(route_id)
        if not route:
            return False

        await self.db.delete(route)
        await self.db.commit()
        return True

    async def soft_delete(self, route_id: UUID) -> bool:
        route = await self.get_by_id(route_id)
        if not route:
            return False

        route.is_active = False
        await self.db.commit()
        return True