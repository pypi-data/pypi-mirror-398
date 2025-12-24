# btcontrol

**btcontrol** is a driver-based Bluetooth control framework that exposes
**only the actions a device explicitly supports** as validated API endpoints.

It works across **Bluetooth Classic and BLE**, automatically detecting
interfaces, mapping them to capabilities, and executing actions through
the correct control plane.

> No undocumented hacks. No vendor lock-in. No unsafe guessing.

---

## Features

- Automatic Bluetooth device discovery
- Interface-based capability detection
- Driver system for extensibility
- Safe, allow-listed actions only
- Auto-generated REST API (FastAPI)
- BLE control-plane support (custom devices)
- Audio device support (A2DP / AVRCP)
- Vendor-locked devices are intentionally excluded

---

## Supported Device Interfaces

| Interface               | Examples             | Actions                   |
| ----------------------- | -------------------- | ------------------------- |
| Bluetooth Audio (AVRCP) | Headphones, speakers | play, pause, next, volume |
| Bluetooth HID           | Keyboards, mice      | key events (planned)      |
| BLE GATT (standard)     | Sensors              | read, notify              |
| BLE GATT (custom)       | Your own devices     | command execution         |
| RFCOMM / SPP            | Serial devices       | byte I/O (planned)        |

Devices that hide actions behind proprietary protocols are **not supported by design**.

---

## Installation

```bash
pip install btcontrol
```
