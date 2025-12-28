from abc import ABC, abstractmethod


class BaseNotifier(ABC):
    @abstractmethod
    async def notify(self, device_id: str, event_type: str, value: int) -> None:
        """
        Send a notification for an event.

        Args:
            device_id: ID of the device generating the event.
            event_type: Type of the event (human presence, door open, etc).
            value: An integer value associated with the event.
        """
