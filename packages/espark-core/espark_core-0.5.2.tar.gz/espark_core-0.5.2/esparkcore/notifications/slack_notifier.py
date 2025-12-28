from slack_sdk import WebClient

from ..utils import log_debug
from .notifier import BaseNotifier


class SlackNotifier(BaseNotifier):
    def __init__(self, slack_token: str, slack_channel: str) -> None:
        self.slack_token   = slack_token
        self.slack_channel = slack_channel

    async def notify(self, device_id: str, event_type: str, value: int) -> None:
        client = WebClient(token=self.slack_token)

        log_debug(f'Posting {event_type} event to Slack for device {device_id}: {value}')

        client.chat_postMessage(channel=self.slack_channel, text=f'Device {device_id} reported {event_type} with value {value}.')
