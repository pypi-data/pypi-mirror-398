import asyncio
from btcontrol.discovery.ble import discover_ble
from btcontrol.discovery.classic import discover_classic
from btcontrol.core.registry import REGISTRY
from btcontrol.drivers import DRIVERS

async def init():
    devices = []

    devices.extend(discover_classic())
    devices.extend(await discover_ble())

    for info in devices:
        for driver in DRIVERS:
            if driver.match(info):
                device = driver.build_device(info)
                REGISTRY.register(device)
                break  # one driver per device

if __name__ == "__main__":
    asyncio.run(init())
