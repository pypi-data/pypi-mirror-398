from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class Telemetry(SQLModel, table=True):
    id        : Optional[int] = Field(primary_key=True, default=None)
    device_id : str           = Field(foreign_key='device.id', ondelete='CASCADE', description='Device that sent this data')
    timestamp : datetime      = Field(index=True, description='Timestamp of the data')
    data_type : str           = Field(index=True, description='Type of the data (e.g., motion, temperature)')
    value     : int           = Field(description='Value of the data (e.g., temperature, human presence detected or not)')
