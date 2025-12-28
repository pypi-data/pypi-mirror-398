from typing import Optional, Sequence

from sqlalchemy import ColumnElement
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import and_, select

from ..models import Telemetry
from .base_repository import AsyncRepository


class TelemetryRepository(AsyncRepository[Telemetry]):
    def __init__(self):
        super().__init__(Telemetry)

    async def get_latest_for_device(self, session: AsyncSession, device_id: str, data_type: str) -> Optional[Telemetry]:
        # pylint: disable=no-member
        results = await self.list(session, and_(Telemetry.device_id == device_id, Telemetry.data_type == data_type), order_by=Telemetry.timestamp.desc(), limit=1)
        return results[0] if results else None

    async def list(self, session: AsyncSession, *conditions: ColumnElement[bool], offset: Optional[int] = None, order_by=None, limit: Optional[int] = None) -> Sequence[Telemetry]:
        if order_by is None:
            # pylint: disable=no-member
            order_by = Telemetry.timestamp.desc()

        return await super().list(session, *conditions, offset=offset, order_by=order_by, limit=limit)

    async def search(self, session: AsyncSession, device_id: str = None, data_type: str = None, condition: str = None, value: int = None):
        query = select(self.model)

        if device_id is not None:
            query = query.where(Telemetry.device_id == device_id)

        if data_type is not None:
            query = query.where(Telemetry.data_type == data_type)

        if condition is not None and value is not None:
            if condition == '<':
                query = query.where(Telemetry.value < value)
            elif condition == '<=':
                query = query.where(Telemetry.value <= value)
            elif condition == '==':
                query = query.where(Telemetry.value == value)
            elif condition == '>=':
                query = query.where(Telemetry.value >= value)
            elif condition == '>':
                query = query.where(Telemetry.value > value)

        return (await session.execute(query)).scalars().all()
