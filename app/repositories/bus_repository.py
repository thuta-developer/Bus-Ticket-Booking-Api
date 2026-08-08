from typing import Optional, List
from uuid import UUID
from sqlalchemy import select, update, or_, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.models.bus import Bus
from app.models.feature import Feature
from app.models.bus_company import BusCompany


class BusRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # Read Operations
    async def get_by_id(self, bus_id: UUID) -> Optional[Bus]:
        stmt = select(Bus).where(Bus.id == bus_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_bus_number(self, bus_number: str) -> Optional[Bus]:
        stmt = select(Bus).where(Bus.bus_number == bus_number)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_license_plate(self, license_plate: str) -> Optional[Bus]:
        stmt = select(Bus).where(Bus.license_plate == license_plate)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_all(self, skip: int = 0, limit: int = 10, search: Optional[str] = None, company_id: Optional[UUID] = None, bus_type: Optional[str] = None, include_inactive: bool = False) -> List[Bus]:
        stmt = select(Bus).join(BusCompany)

        # Filters
        if not include_inactive:
            stmt = stmt.where(Bus.is_active == True)

        if company_id:
            stmt = stmt.where(Bus.company_id == company_id)

        if bus_type:
            stmt = stmt.where(Bus.bus_type == bus_type)

        if search:
            search_term = f"%{search}%"
            stmt = stmt.where(
                or_(
                    Bus.bus_number.ilike(search_term),
                    Bus.license_plate.ilike(search_term),
                    BusCompany.name.ilike(search_term)
                )
            )

        stmt = stmt.offset(skip).limit(limit).order_by(Bus.bus_number.desc())
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def count(self, search: Optional[str] = None, company_id: Optional[UUID] = None, bus_type: Optional[str] = None, include_inactive: bool = False) -> int:
        stmt = select(func.count()).select_from(Bus).join(BusCompany)

        # Filters
        if not include_inactive:
            stmt = stmt.where(Bus.is_active == True)

        if company_id:
            stmt = stmt.where(Bus.company_id == company_id)

        if bus_type:
            stmt = stmt.where(Bus.bus_type == bus_type)

        if search:
            search_term  = f"%{search}%"
            stmt = stmt.where(
                or_(
                    Bus.bus_number.ilike(search_term),
                    Bus.license_plate.ilike(search_term),
                    BusCompany.name.ilike(search_term)
                )
            )
        result = await self.db.execute(stmt)
        return result.scalar_one()
    
    # Create
    async def create(self, bus_data: dict, feature_ids: List[UUID]) -> Bus:
        try:
            bus = Bus(**bus_data)

            if feature_ids:
                stmt = select(Feature).where(Feature.id.in_(feature_ids))
                features = (await self.db.execute(stmt)).scalars().all()
                bus.features = features

            self.db.add(bus)
            await self.db.commit()
            await self.db.refresh(bus)
            return bus
        except IntegrityError as e:
            await self.db.rollback()
            if "bus_number" in str(e).lower():
                raise ValueError("Bus number already exists.")
            elif "license_plate" in str(e).lower():
                raise ValueError("License plate already exists.")
            raise e
        

    # Update
    async def update(self, bus_id: UUID, update_data: dict, feature_ids: Optional[List[UUID]] = None) -> Optional[Bus]:
        bus = await self.get_by_id(bus_id)
        if not bus:
            return None

        
        try:
            for key, value in update_data.items():
                setattr(bus, key, value)

            if feature_ids is not None:
                stmt = select(Feature).where(Feature.id.in_(feature_ids))
                features = (await self.db.execute(stmt)).scalars().all()
                bus.features = features

            await self.db.commit()
            await self.db.refresh(bus)
            return bus
        except IntegrityError as e:
            await self.db.rollback()
            if "bus_number" in str(e).lower():
                raise ValueError("Bus number already exists.")
            elif "license_plate" in str(e).lower():
                raise ValueError("License plate already exists.")
            raise e
        

    # Delete
    async def delete(self, bus_id: UUID) -> bool:
        bus = await self.get_by_id(bus_id)
        if not bus:
            return False
        
        await self.db.delete(bus)
        await self.db.commit()
        return True

    async def soft_delete(self, bus_id: UUID) -> bool:
        bus = await self.get_by_id(bus_id)
        if not bus:
            return False

        bus.is_active = False
        await self.db.commit()
        return True
    
    
