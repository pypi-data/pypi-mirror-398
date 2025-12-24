import asyncio
from bleak import BleakScanner

async def discover_ble(timeout=4):
    results = []

    def callback(device, adv):
        results.append({
            "id": device.address,
            "name": device.name or "BLE Device",
            "transport": "ble",
            "services": adv.service_uuids or []
        })

    scanner = BleakScanner(callback)
    await scanner.start()
    await asyncio.sleep(timeout)
    await scanner.stop()

    return results
