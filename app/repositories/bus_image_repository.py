from typing import Optional, List
from uuid import UUID
from sqlalchemy import select, update, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bus_image import BusImage


class BusImageRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, image_id: UUID) -> Optional[BusImage]:
        stmt = select(BusImage).where(BusImage.id == image_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_bus(self, bus_id: UUID) -> List[BusImage]:
        stmt = select(BusImage).where(BusImage.bus_id == bus_id)
        stmt = stmt.order_by(BusImage.order.asc())
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_max_order(self, bus_id: UUID) -> int:
        stmt = select(func.max(BusImage.order)).where(BusImage.bus_id == bus_id)
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def count_by_bus(self, bus_id: UUID) -> int:
        stmt = select(func.count()).where(BusImage.bus_id == bus_id)
        result = await self.db.execute(stmt)
        return result.scalar()

    async def create(self, image_data: dict) -> BusImage:
        image = BusImage(**image_data)
        self.db.add(image)
        await self.db.commit()
        await self.db.refresh(image)
        return image

    async def create_batch(self, images_data: List[dict]) -> List[BusImage]:
        images = [BusImage(**data) for data in images_data]
        self.db.add_all(images)
        await self.db.commit()
        for image in images:
            await self.db.refresh(image)
        return images

    async def update(self, image_id: UUID, update_data: dict) -> Optional[BusImage]:
        stmt = (
            update(BusImage)
            .where(BusImage.id == image_id)
            .values(**update_data)
            .returning(BusImage)
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.scalar_one_or_none()

    async def delete(self, image_id: UUID) -> bool:
        image = await self.get_by_id(image_id)
        if not image:
            return False
        await self.db.delete(image)
        await self.db.commit()
        return True


    async def delete_all_by_bus(self, bus_id: UUID) -> int:
        stmt = delete(BusImage).where(BusImage.bus_id == bus_id)
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount