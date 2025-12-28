from ..data.models import Notification
from ..data.repositories import NotificationRepository
from .base_router import BaseRouter


class NotificationRouter(BaseRouter):
    def __init__(self, repo: NotificationRepository = None) -> None:
        self.repo : NotificationRepository = repo or NotificationRepository()

        super().__init__(Notification, self.repo, '/api/v1/notifications', ['notification'])
