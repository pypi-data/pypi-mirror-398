from btcontrol.drivers.audio_driver import AudioDriver
from btcontrol.drivers.ble_control_driver import BLEControlPlaneDriver
from btcontrol.drivers.ble_standard_driver import BLEStandardDriver

DRIVERS = [
    AudioDriver(),
    BLEControlPlaneDriver(),
    BLEStandardDriver(),
]
