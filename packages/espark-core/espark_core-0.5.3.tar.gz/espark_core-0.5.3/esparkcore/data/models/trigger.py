from typing import Optional

from sqlmodel import Field, SQLModel


class Trigger(SQLModel, table=True):
    id               : Optional[int] = Field(primary_key=True, description='Unique identifier for the trigger')
    name             : str           = Field(index=True, unique=True, description='Name of the trigger')
    device_id        : Optional[str] = Field(index=True, default=None, description='Identifier of the associated device')
    data_type        : Optional[str] = Field(index=True, default=None, description='Type of telemetry data the trigger monitors (e.g., temperature, humidity)')
    condition        : str           = Field(description='Condition to evaluate (e.g., ">", "<=")')
    value            : int           = Field(description='Value to compare against for the trigger condition')
    notification_ids : Optional[str] = Field(default=None, description='Comma-separated list of associated notification IDs to be sent when the trigger condition is met')
