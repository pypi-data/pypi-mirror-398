"""
btcontrol

Driver-based Bluetooth control framework.
"""

from btcontrol.core.device import Device
from btcontrol.core.action import Action
from btcontrol.core.registry import REGISTRY

from btcontrol.main import init

__all__ = [
    "Device",
    "Action",
    "REGISTRY",
    "init",
]

__version__ = "0.1.0"
