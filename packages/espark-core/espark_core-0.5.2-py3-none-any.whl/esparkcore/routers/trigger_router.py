from ..data.models import Trigger
from ..data.repositories import TriggerRepository
from .base_router import BaseRouter


class TriggerRouter(BaseRouter):
    def __init__(self, repo: TriggerRepository = None) -> None:
        self.repo : TriggerRepository = repo or TriggerRepository()

        super().__init__(Trigger, self.repo, '/api/v1/triggers', ['trigger'])
