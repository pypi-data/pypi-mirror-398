import asyncio
import signal

import ts_sdk_connectors_python.logger as logging
from ts_sdk_connectors_python.config import TdpApiConfig
from ts_sdk_connectors_python.openapi_codegen.connectors_api_client.models import (
    UpdateConnectorHealthRequest,
    UpdateConnectorHealthRequestStatus,
)
from ts_sdk_connectors_python.tdp_api import TdpApi


async def heartbeat(api: TdpApi, config: TdpApiConfig):
    while True:
        try:
            await api.heartbeat(config.connector_id)
            await asyncio.sleep(60)
        except asyncio.CancelledError:
            return


async def main():
    config = TdpApiConfig(artifact_type="data-app")
    api = TdpApi(config)
    await api.init_client()

    logger = logging.get_root_connector_sdk_logger()
    logger.debug("Sending HEALTHY health status to API", {"app": "heartbeat"})

    await api.update_health(
        config.connector_id,
        UpdateConnectorHealthRequest(UpdateConnectorHealthRequestStatus.HEALTHY),
    )
    logger.debug("Health status sent", {"app": "heartbeat"})

    heartbeat_task = asyncio.create_task(heartbeat(api, config))
    loop = asyncio.get_running_loop()
    # cancel task on SIGINT
    loop.add_signal_handler(signal.SIGTERM, lambda: heartbeat_task.cancel())
    loop.add_signal_handler(signal.SIGINT, lambda: heartbeat_task.cancel())

    try:
        await heartbeat_task
    except asyncio.CancelledError:
        pass
    finally:
        logger.info("Cleanup completed")


if __name__ == "__main__":
    asyncio.run(main())
