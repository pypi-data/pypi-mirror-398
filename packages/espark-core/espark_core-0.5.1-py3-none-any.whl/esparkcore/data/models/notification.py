from typing import Dict

from sqlalchemy import Column
from sqlmodel import SQLModel, Field, JSON


class Notification(SQLModel, table=True):
    id       : int            = Field(primary_key=True, description='Unique identifier for the notification')
    name     : str            = Field(index=True, unique=True, description='Name of the notification')
    provider : str            = Field(index=True, description='Notification provider (e.g., Slack, Twilio)')
    config   : Dict[str, str] = Field(default_factory=dict, sa_column=Column(JSON), description='JSON string of provider-specific configuration parameters')
