from ..models import AppVersion
from .base_repository import AsyncRepository


class AppVersionRepository(AsyncRepository[AppVersion]):
    def __init__(self):
        super().__init__(AppVersion)

    async def get_by_app_name(self, session, app_name: str) -> AppVersion | None:
        # pylint: disable=unexpected-keyword-arg
        return await self.get(session, AppVersion.id == app_name)
