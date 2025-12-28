from ..data.models import AppVersion
from ..data.repositories import AppVersionRepository
from .base_router import BaseRouter


class AppVersionRouter(BaseRouter):
    def __init__(self, repo: AppVersionRepository = None) -> None:
        self.repo : AppVersionRepository = repo or AppVersionRepository()

        super().__init__(AppVersion, self.repo, '/api/v1/apps', ['version'])
