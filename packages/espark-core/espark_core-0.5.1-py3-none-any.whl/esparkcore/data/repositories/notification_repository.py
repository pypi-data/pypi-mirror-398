from ..models import Notification
from .base_repository import AsyncRepository


class NotificationRepository(AsyncRepository[Notification]):
    def __init__(self):
        super().__init__(Notification)
