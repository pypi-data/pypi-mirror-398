class DeviceRegistry:
    def __init__(self):
        self._devices = {}

    def register(self, device):
        self._devices[device.id] = device

    def get(self, device_id):
        if device_id not in self._devices:
            raise KeyError("Device not found")
        return self._devices[device_id]

    def all(self):
        return list(self._devices.values())


REGISTRY = DeviceRegistry()
