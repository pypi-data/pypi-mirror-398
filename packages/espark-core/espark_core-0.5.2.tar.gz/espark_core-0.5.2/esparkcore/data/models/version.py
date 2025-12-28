from sqlmodel import SQLModel, Field


class AppVersion(SQLModel, table=True):
    id      : str = Field(primary_key=True, description='The app name, which is a unique identifier for the app version')
    version : str = Field(description='Version of the application')
