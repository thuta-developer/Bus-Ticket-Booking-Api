from typing import Optional, List, Dict, Any
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bus import BusType
from app.repositories.seat_repository import SeatRepository
from app.repositories.bus_repository import BusRepository
from app.repositories.seat_layout_repository import SeatLayoutRepository
from app.schemas.seat import SeatCreate, SeatUpdate, SeatResponse, SeatBatchCreate
from app.schemas.seat_layout import SeatLayoutResponse,SeatLayoutCreate, SeatLayoutUpdate
from app.models.seat import Seat



class SeatService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = SeatRepository(db)
        self.bus_repo = BusRepository(db)
        self.layout_repo = SeatLayoutRepository(db)

    # ====== Helper ======
    async def _to_response(self, seat: Seat) -> SeatResponse:
        response = SeatResponse.model_validate(seat)
        if seat.bus:
            response.bus_number = seat.bus.bus_number
        return response

    async def _get_bus_or_404(self, bus_id: UUID):
        bus = await self.bus_repo.get_by_id(bus_id)
        if not bus:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bus not found"
            )
        return bus

    # ====== Generate Seats (Batch) with Dynamic Layout ======
    async def generate_seats_for_bus_with_layout(
        self,
        bus_id: UUID,
        rows: int,
        columns: int,
        start_from: int = 1,
        config: Optional[Dict[str, Any]] = None,
    ) -> List[SeatResponse]:
        """
        Generate seats for a bus using dynamic layout.
        Supports custom seat naming: 'default', 'prefix', 'custom', 'vip'
        """
        await self._get_bus_or_404(bus_id)

        # Check if seats already exist
        existing = await self.repo.count_by_bus(bus_id)
        if existing > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Bus already has {existing} seats. Delete existing seats first to regenerate."
            )

        # Get config values
        config = config or {}
        skip_seats = config.get("skip_seats", [])
        seat_naming = config.get("seat_naming", "default")
        prefix = config.get("prefix", "")
        suffix = config.get("suffix", "")

        # Generate seat data based on rows and columns
        seat_data_list = []

        for row in range(1, rows + 1):
            for col in range(1, columns + 1):
                col_letter = chr(64 + col)  # A, B, C, D, ...

                # Custom naming based on seat_naming config
               
                if seat_naming == "standard":
                    seat_number_str = str(len(seat_data_list) + 1)
                elif seat_naming == "vip":
                    seat_number_str = f"{col_letter}{row}"
                else:
                    seat_number_str = f"{col_letter}{row}"

                # Skip reserved seats
                if seat_number_str in skip_seats:
                    continue

                seat_data_list.append({
                    "bus_id": bus_id,
                    "seat_number": seat_number_str,
                    "row": row,
                    "column": col_letter,
                    "is_available": True,
                    "is_active": True,
                })

        if not seat_data_list:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No seats generated. Check layout configuration."
            )

        try:
            seats = await self.repo.create_batch(seat_data_list)

            # Save layout configuration
            layout_data = SeatLayoutCreate(
                bus_id=bus_id,
                rows=rows,
                columns=columns,
                config=config or {}
            )
            await self.layout_repo.create(layout_data.model_dump())

            return [await self._to_response(seat) for seat in seats]
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )



    # ====== Generate Seats (Batch) ======
    async def generate_seats_for_bus(self, bus_id: UUID, count: int, start_from: int = 1) -> List[SeatResponse]:
        bus = await self._get_bus_or_404(bus_id)
        bus_type = bus.bus_type
        
        # Auto-detect layout based on bus type
        if bus_type == BusType.VIP:
            columns = 3
            rows = (count + columns - 1) // columns
            naming = "vip"
        elif bus_type == BusType.Standard:
            columns = 4
            rows = (count + columns - 1) // columns
            naming = "standard"
        else: 
            columns = 4
            rows = (count + columns - 1) // columns
            naming = "default"
        
        return await self.generate_seats_for_bus_with_layout(
            bus_id=bus_id,
            rows=rows,
            columns=columns,
            start_from=start_from,
            config={"seat_naming": naming}
        )

    async def get_seat_layout(self, bus_id: UUID) -> Optional[SeatLayoutResponse]:
        """Get seat layout for a bus."""
        layout = await self.layout_repo.get_by_bus_id(bus_id)
        if not layout:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Seat layout not found for this bus"
            )
        return SeatLayoutResponse.model_validate(layout)

    async def update_seat_layout(self, bus_id: UUID, update_data: SeatLayoutUpdate) -> SeatLayoutResponse:
        """Update seat layout for a bus."""
        await self._get_bus_or_404(bus_id)

        layout = await self.layout_repo.get_by_bus_id(bus_id)
        if not layout:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Seat layout not found for this bus"
            )

        update_dict = update_data.model_dump(exclude_unset=True)
        if not update_dict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid fields to update"
            )

        updated = await self.layout_repo.update(layout.id, update_dict)
        return SeatLayoutResponse.model_validate(updated)


    # ===== Create signle seat ======
    async def create_seat(self, seat_data: SeatCreate) -> SeatResponse:
        await self._get_bus_or_404(seat_data.bus_id)
        existing = await self.repo.get_by_bus_and_number(
            seat_data.bus_id, seat_data.seat_number
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Seat '{seat_data.seat_number}' already exists for this bus"
            )

        try:
            seat = await self.repo.create(seat_data.model_dump())
            return await self._to_response(seat)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

        

    # ===== Read =====
    async def get_seat(self, seat_id: UUID) -> SeatResponse:
        seat = await self.repo.get_by_id(seat_id)
        if not seat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Seat not found"
            )

        return await self._to_response(seat)

    async def list_seats(
        self,
        bus_id: UUID,
        include_inactive: bool = False
    ) -> Dict[str, Any]:
        await self._get_bus_or_404(bus_id)

        seats = await self.repo.get_by_bus(bus_id, include_inactive)
        total = await self.repo.count_by_bus(bus_id, include_inactive)
        items = [await self._to_response(seat) for seat in seats]

        return {
            "total": total,
            "items": items,
            "bus_id": bus_id
        }

    async def update_seat(self, seat_id: UUID, update_data: SeatUpdate) -> SeatResponse:
        seat = await self.repo.get_by_id(seat_id)
        if not seat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Seat not found"
            )

        update_dict = update_data.model_dump(exclude_unset=True)
        if not update_dict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No data provided for update"
            )

        try:
            updated = await self.repo.update(seat_id, update_dict)
            if not updated:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Seat not found"
                )

            return await self._to_response(updated)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

    async def delete_seat(self, seat_id: UUID, hard_delete: bool = False) -> None:
        seat = await self.repo.get_by_id(seat_id)
        if not seat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Seat not found"
            )

        if hard_delete:
            deleted = await self.repo.delete(seat_id)
        else:
            deleted = await self.repo.soft_delete(seat_id)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Seat not found"
            )

    async def delete_all_seats_by_bus(self, bus_id: UUID) -> int:
        # Check if bus exists
        await self._get_bus_or_404(bus_id)

        count = await self.repo.delete_all_by_bus(bus_id)
        return count
