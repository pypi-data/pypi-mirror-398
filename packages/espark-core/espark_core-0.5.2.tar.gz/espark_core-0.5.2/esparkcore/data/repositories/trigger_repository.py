from ..models import Trigger
from .base_repository import AsyncRepository


class TriggerRepository(AsyncRepository[Trigger]):
    def __init__(self):
        super().__init__(Trigger)
