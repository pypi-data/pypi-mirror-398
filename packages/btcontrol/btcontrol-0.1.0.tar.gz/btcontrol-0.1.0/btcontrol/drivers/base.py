from abc import ABC, abstractmethod

class Driver(ABC):
    @abstractmethod
    def match(self, device_info) -> bool:
        pass

    @abstractmethod
    def build_device(self, device_info):
        pass
