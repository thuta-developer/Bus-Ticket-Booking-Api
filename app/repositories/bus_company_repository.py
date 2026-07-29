from typing import Optional, List
from uuid import UUID
from sqlalchemy import func, select, update, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.models.bus_company import BusCompany

class BusCompanyRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, company_id: UUID) -> Optional[BusCompany]:
        stmt = select(BusCompany).where(BusCompany.id == company_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_name(self, name: str) -> Optional[BusCompany]:
        stmt = select(BusCompany).where(BusCompany.name == name)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_all(self, skip: int = 0, limit: int = 10, search: Optional[str] = None, include_inactive: bool = False,) ->  List[BusCompany]:
        stmt = select(BusCompany)

        if not include_inactive:
            stmt = stmt.where(BusCompany.is_active == True)

        if search:
            search_pattern = f"%{search}%"
            stmt = stmt.where(
                or_(
                    BusCompany.name.ilike(search_pattern),
                    BusCompany.description.ilike(search_pattern),
                    BusCompany.contact_email.ilike(search_pattern),
                    BusCompany.contact_phone.ilike(search_pattern),
                )
            )
        stmt = stmt.order_by(BusCompany.name.asc()).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()
    

    async def count(self, search: Optional[str] = None, include_inactive: bool = False) -> int:
        stmt = select(func.count()).select_from(BusCompany)

        if not include_inactive:
            stmt = stmt.where(BusCompany.is_active == True)

        if search:
            search_pattern = f"%{search}%"
            stmt = stmt.where(
                or_(
                    BusCompany.name.ilike(search_pattern),
                    BusCompany.description.ilike(search_pattern),
                    BusCompany.contact_email.ilike(search_pattern),
                    BusCompany.contact_phone.ilike(search_pattern),
                )
            )
        result = await self.db.execute(stmt)
        return result.scalar()
    
    async def create(self, company_data: dict) -> BusCompany:
        try:
            company = BusCompany(**company_data)
            self.db.add(company)
            await self.db.commit()
            await self.db.refresh(company)
            return company
        except IntegrityError as e:
            await self.db.rollback()
            raise ValueError("A company with this name already exists")
        

    async def update(self, company_id: UUID, update_data: dict) -> Optional[BusCompany]:
        company = await self.get_by_id(company_id)
        if not company:
            return None
        
        try:
            stmt = (
                update(BusCompany)
                .where(BusCompany.id == company_id)
                .values(**update_data)
                .returning(BusCompany)
            )
            result = await self.db.execute(stmt)
            await self.db.commit()
            return result.scalar_one_or_none()
        except IntegrityError:
            await self.db.rollback()
            raise ValueError("A company with this name already exists")
    
    async def delete(self, company_id: UUID) -> bool:
        company = await self.get_by_id(company_id)
        if not company:
            return False
        
        await self.db.delete(company)
        await self.db.commit()
        return True

    async def soft_delete(self, company_id: UUID) -> bool:
        company = await self.get_by_id(company_id)
        if not company:
            return False

        company.is_active = False
        await self.db.commit()
        return True
