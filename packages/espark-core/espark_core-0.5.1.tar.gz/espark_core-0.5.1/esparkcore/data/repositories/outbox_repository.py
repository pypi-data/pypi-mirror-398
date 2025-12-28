from typing import Optional

from sqlmodel import and_

from ..models import OutboxEvent
from .base_repository import AsyncRepository


class OutboxRepository(AsyncRepository[OutboxEvent]):
    def __init__(self):
        super().__init__(OutboxEvent)

    async def get_next(self, session, device_id: str, event_type: str) -> Optional[OutboxEvent]:
        # pylint: disable=no-member,singleton-comparison
        events = await self.list(session, and_(OutboxEvent.device_id == device_id, OutboxEvent.event_type == event_type, OutboxEvent.is_processed == False), order_by=OutboxEvent.created_at.desc())
        return events[0] if events else None

    async def delete_pending(self, session, device_id: str, event_type: str) -> None:
        # pylint: disable=singleton-comparison
        events = await self.list(session, and_(OutboxEvent.device_id == device_id, OutboxEvent.event_type == event_type, OutboxEvent.is_processed == False))
        for event in events:
            await self.delete(session, event)
