"""AddressRepository."""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.address import Address


class AddressRepository:

    def __init__(self, session: AsyncSession):
        self._session = session

    async def find_by_id(self, address_id: int) -> Optional[Address]:
        result = await self._session.execute(
            select(Address).where(Address.id == address_id)
        )
        return result.scalar_one_or_none()

    async def find_by_user_id(self, user_id: int) -> List[Address]:
        result = await self._session.execute(
            select(Address).where(Address.user_id == user_id).order_by(Address.is_default.desc())
        )
        return list(result.scalars().all())

    async def save(self, address: Address) -> Address:
        self._session.add(address)
        await self._session.flush()
        await self._session.refresh(address)
        return address

    async def delete(self, address: Address) -> None:
        await self._session.delete(address)
        await self._session.flush()
