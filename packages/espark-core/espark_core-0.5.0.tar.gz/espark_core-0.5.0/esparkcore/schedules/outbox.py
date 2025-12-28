from json import dumps
from os import getenv

from aiomqtt import Client

from ..constants import ENV_MQTT_HOST, ENV_MQTT_PORT, TOPIC_ACTION
from ..data import async_session
from ..data.repositories import OutboxRepository


async def consume_outbox(device_id: str, event_type: str) -> None:
    outbox_repo = OutboxRepository()

    async with async_session() as session:
        event = await outbox_repo.get_next(session, device_id, event_type)
        if not event:
            return

        await outbox_repo.delete_pending(session, device_id, event_type)

        async with Client(getenv(ENV_MQTT_HOST, 'localhost'), int(getenv(ENV_MQTT_PORT, '1883'))) as client:
            await client.publish(f'{TOPIC_ACTION}/{device_id}', dumps(event.payload), qos=1, retain=True)

        await session.commit()
