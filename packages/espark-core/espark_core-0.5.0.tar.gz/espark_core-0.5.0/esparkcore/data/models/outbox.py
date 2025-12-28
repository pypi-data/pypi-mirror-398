from datetime import datetime
from typing import Dict, Optional
from uuid import UUID, uuid4

from sqlalchemy import Column
from sqlmodel import SQLModel, Field, JSON, UniqueConstraint


class OutboxEvent(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint('device_id', 'event_type', 'is_processed', name='uq_device_event'),
    )

    id           : UUID               = Field(default_factory=uuid4, primary_key=True, description='Unique identifier for the outbox event')
    device_id    : str                = Field(foreign_key='device.id', ondelete='CASCADE', index=True, description='Identifier of the device associated with the event')
    event_type   : str                = Field(index=True, description='Type of the event')
    payload      : Dict[str, str]     = Field(default_factory=dict, sa_column=Column(JSON), description='JSON string of event-specific payload data')
    created_at   : datetime           = Field(default_factory=datetime.now, index=True, description='Timestamp when the event was created')
    processed_at : Optional[datetime] = Field(default=None, index=True, description='Timestamp when the event was processed')
    is_processed : bool               = Field(default=False, index=True, description='Flag indicating whether the event has been processed')
