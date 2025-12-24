class Device:
    def __init__(self, device_id, name, device_type, capabilities, actions):
        self.id = device_id
        self.name = name
        self.type = device_type
        self.capabilities = capabilities
        self.actions = actions  # dict[str, Action]

    def describe(self):
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "capabilities": self.capabilities,
            "actions": list(self.actions.keys()),
        }
