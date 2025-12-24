from btcontrol.drivers.base import Driver
from btcontrol.core.device import Device
from btcontrol.core.action import Action

# Standard Battery Service UUID
BATTERY_SERVICE = "0000180f"

class BLEStandardDriver(Driver):
    def match(self, device_info):
        if device_info.get("transport") != "ble":
            return False

        return any(
            s.lower().startswith(BATTERY_SERVICE)
            for s in device_info.get("services", [])
        )

    def build_device(self, device_info):
        def read_battery():
            return "battery_read_not_implemented_yet"

        actions = {
            "read_battery": Action("read_battery", read_battery)
        }

        return Device(
            device_id=device_info["id"],
            name=device_info["name"],
            device_type="ble_standard",
            capabilities=["battery"],
            actions=actions
        )
