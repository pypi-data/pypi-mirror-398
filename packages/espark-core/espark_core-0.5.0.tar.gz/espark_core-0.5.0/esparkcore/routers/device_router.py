from json import dumps
from os import getenv

from aiomqtt import Client
from fastapi import Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from ..constants import ENV_MQTT_HOST, ENV_MQTT_PORT, TOPIC_DEVICE
from ..data.models import Device
from ..data.repositories import DeviceRepository, TelemetryRepository
from ..utils import log_debug
from .base_router import BaseRouter


class DeviceRouter(BaseRouter):
    def __init__(self, repo: DeviceRepository = None) -> None:
        self.repo : DeviceRepository = repo or DeviceRepository()

        super().__init__(Device, self.repo, '/api/v1/devices', ['device'])

    async def _publish_update(self, entity: Device) -> None:
        log_debug(f'Publishing parameters update for device {entity.id}: {entity.parameters}')

        async with Client(getenv(ENV_MQTT_HOST, 'localhost'), int(getenv(ENV_MQTT_PORT, '1883'))) as client:
            await client.publish(f'{TOPIC_DEVICE}/{entity.id}', payload=dumps(entity.parameters) if entity.parameters else None, qos=1, retain=True)

    async def _after_update(self, entity: Device, session: AsyncSession) -> None:
        await super()._after_update(entity, session)

        await self._publish_update(entity)

    def _setup_routes(self) -> None:
        @self.router.get('/all')
        async def list_all(response: Response, session: AsyncSession = Depends(BaseRouter._get_session), offset: int = Query(None, ge=0), limit: int = Query(None, ge=1, le=100)):
            response.headers['X-Total-Count'] = str(await self.repo.count(session))

            devices                = await self.repo.list(session, offset=offset, limit=limit)
            devices_with_telemetry = []
            telemetry_repo         = TelemetryRepository()

            for device in devices:
                battery = await telemetry_repo.get_latest_for_device(session, device.id, 'battery')

                devices_with_telemetry.append({
                    'id'           : device.id,
                    'display_name' : device.display_name,
                    'app_name'     : device.app_name,
                    'app_version'  : device.app_version,
                    'capabilities' : device.capabilities,
                    'parameters'   : device.parameters,
                    'last_seen'    : device.last_seen,
                    'battery'      : battery.value if battery else None,
                })

            return devices_with_telemetry

        super()._setup_routes()
