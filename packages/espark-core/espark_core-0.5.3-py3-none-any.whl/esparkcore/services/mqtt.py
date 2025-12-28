from asyncio import create_task, gather, Queue, sleep
from datetime import datetime, timezone
from json import dumps, JSONDecodeError, loads
from os import getenv
from uuid import getnode

from aiomqtt import Client, MqttError
from packaging.version import Version

from ..constants import ENV_MQTT_HOST, ENV_MQTT_PORT, TOPIC_CRASH, TOPIC_OTA, TOPIC_REGISTRATION, TOPIC_TELEMETRY
from ..data import async_session
from ..data.models import AppVersion, Device, Telemetry
from ..data.repositories import AppVersionRepository, DeviceRepository, NotificationRepository, TelemetryRepository, TriggerRepository
from ..notifications import SlackNotifier
from ..utils import log_debug, log_error

MQTT_RETRY_DELAY: int = 5


class MQTTManager:
    def __init__(self, version_repo: AppVersionRepository = None, device_repo: DeviceRepository = None, notification_repo: NotificationRepository = None, telemetry_repo: TelemetryRepository = None, trigger_repo: TriggerRepository = None) -> None:
        self.mqtt_host         : str                  = getenv(ENV_MQTT_HOST, 'localhost')
        self.mqtt_port         : int                  = int(getenv(ENV_MQTT_PORT, '1883'))
        self.version_repo      : AppVersionRepository = version_repo if version_repo else AppVersionRepository()
        self.device_repo       : DeviceRepository     = device_repo if device_repo else DeviceRepository()
        self.notification_repo : NotificationRepository = notification_repo if notification_repo else NotificationRepository()
        self.telemetry_repo    : TelemetryRepository  = telemetry_repo if telemetry_repo else TelemetryRepository()
        self.trigger_repo      : TriggerRepository    = trigger_repo if trigger_repo else TriggerRepository()
        self.queue             : Queue                = Queue()

    async def _handle_registration(self, device_id: str, payload: dict) -> None:
        try:
            log_debug(f'Registering device: {device_id}')

            async with async_session() as session:
                device = await self.device_repo.get(session, Device.id == device_id)
                if device:
                    device.last_seen = datetime.now(timezone.utc)

                    await self.device_repo.update(session, device, last_seen=datetime.now(timezone.utc))
                else:
                    device = Device()

                    device.id           = device_id
                    device.display_name = None
                    device.app_name     = payload['app_name']
                    device.app_version  = payload['app_version']
                    device.capabilities = payload['capabilities']
                    device.last_seen    = datetime.now(timezone.utc)

                    await self.device_repo.add(session, device)

                latest_version = await self.version_repo.get(session, AppVersion.id == payload['app_name'])
                if not latest_version:
                    latest_version = AppVersion()
                    latest_version.id      = payload['app_name']
                    latest_version.version = payload['app_version']

                    await self.version_repo.add(session, latest_version)

                current_version = Version(payload['app_version'])

                if Version(latest_version.version) > current_version:
                    log_debug(f'Device {device_id} is running an outdated version ({current_version} < {latest_version.version})')

                    async with Client(self.mqtt_host, self.mqtt_port, identifier=f'espark-core-{hex(getnode())}') as client:
                        await client.publish(f'{TOPIC_OTA}/{device_id}', dumps({
                            'device_id'    : device_id,
                            'app_name'     : payload['app_name'],
                            'app_version'  : latest_version.version,
                            'download_url' : f'/downloads/{payload["app_name"]}/{latest_version.version}',
                        }), qos=1)
        # pylint: disable=broad-exception-caught
        except Exception as e:
            log_error(e)

    async def _handle_telemetry(self, device_id: str, payload: dict) -> None:
        try:
            log_debug(f'Receiving telemetry from device: {device_id} - Payload: {payload}')

            async with async_session() as session:
                telemetry = Telemetry()

                telemetry.device_id = device_id
                telemetry.timestamp = datetime.now(timezone.utc)
                telemetry.data_type = payload.get('data_type')
                telemetry.value     = payload.get('value')

                await self.telemetry_repo.add(session, telemetry)
        # pylint: disable=broad-exception-caught
        except Exception as e:
            log_error(e)

        await self._handle_triggers(device_id, payload.get('data_type'), payload.get('value'))

    async def _handle_triggers(self, device_id: str, data_type: str, value: int) -> None:
        async with async_session() as session:
            triggers = await self.trigger_repo.list(session)
            for trigger in triggers:
                matched_device_id = trigger.device_id is None or trigger.device_id == device_id
                matched_data_type = trigger.data_type is None or trigger.data_type == data_type
                if matched_device_id and matched_data_type:
                    condition_met = False
                    if trigger.condition is None:
                        condition_met = True
                    elif trigger.condition == '==' and value == trigger.value:
                        condition_met = True
                    elif trigger.condition == '>' and value > trigger.value:
                        condition_met = True
                    elif trigger.condition == '>=' and value >= trigger.value:
                        condition_met = True
                    elif trigger.condition == '<' and value < trigger.value:
                        condition_met = True
                    elif trigger.condition == '<=' and value <= trigger.value:
                        condition_met = True

                    if condition_met:
                        log_debug(f'Trigger {trigger.name} activated for device {device_id} with data type {data_type} and value {value}')

                        notifications = await self.notification_repo.list(session)
                        for notification in notifications:
                            if trigger.notification_ids.index(str(notification.id)) != -1:
                                log_debug(f'Sending notification {notification.name} for trigger {trigger.name}')

                                if notification.provider == 'Slack':
                                    await SlackNotifier(notification.config['slack_token'], notification.config['slack_channel']).notify(device_id, data_type, value)

    async def _process_queue(self) -> None:
        while True:
            topic, payload = await self.queue.get()

            topic_parts: list[str] = str(topic).split('/')
            if len(topic_parts) != 3:
                log_error(Exception('Invalid topic format, skipping message'))
                continue

            app_type, message_type, device_id = topic_parts
            if app_type != 'espark':
                log_debug('Invalid app type, skipping message')
                continue

            try:
                payload = loads(payload.decode())
            except JSONDecodeError as e:
                log_error(e)
                continue

            if message_type == TOPIC_REGISTRATION.split('/')[1]:
                await self._handle_registration(device_id, payload)
            elif message_type == TOPIC_TELEMETRY.split('/')[1]:
                await self._handle_telemetry(device_id, payload)
            elif message_type == TOPIC_CRASH.split('/')[1]:
                log_debug(f'Received crash report from device {device_id}: {payload}')
            else:
                log_debug(f'Unknown message type "{message_type}", skipping message')

            self.queue.task_done()

    async def _process_messages(self) -> None:
        while True:
            try:
                async with Client(self.mqtt_host, self.mqtt_port, identifier=f'espark-core-{hex(getnode())}') as client:
                    await client.subscribe(f'{TOPIC_REGISTRATION}/+')
                    await client.subscribe(f'{TOPIC_TELEMETRY}/+')
                    await client.subscribe(f'{TOPIC_CRASH}/+')

                    async for message in client.messages:
                        log_debug(f'Received MQTT message on topic {message.topic}')

                        self.queue.put_nowait((message.topic, message.payload))
            except MqttError as e:
                log_error(e)

                await sleep(MQTT_RETRY_DELAY)

    async def start(self) -> None:
        await gather(create_task(self._process_queue()), create_task(self._process_messages()))
