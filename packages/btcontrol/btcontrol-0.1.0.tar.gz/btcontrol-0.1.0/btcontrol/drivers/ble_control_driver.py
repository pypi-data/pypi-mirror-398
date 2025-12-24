import asyncio
from btcontrol.drivers.base import Driver
from btcontrol.core.device import Device
from btcontrol.core.action import Action
from btcontrol.executors.ble_exec import BLEExecutor

CONTROL_PLANE_UUID_PREFIX = "12345678"
CHAR_UUID = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"

class BLEControlPlaneDriver(Driver):
    def match(self, device_info):
        if device_info.get("transport") != "ble":
            return False

        for s in device_info.get("services", []):
            if s.lower().startswith(CONTROL_PLANE_UUID_PREFIX):
                return True
        return False

    def build_device(self, device_info):
        exec = BLEExecutor(device_info["id"], CHAR_UUID)

        async def vibrate():
            await exec.send(0x01)

        actions = {
            "vibrate": Action("vibrate", vibrate)
        }

        return Device(
            device_id=device_info["id"],
            name=device_info["name"],
            device_type="control_plane",
            capabilities=["ble_command"],
            actions=actions
        )


