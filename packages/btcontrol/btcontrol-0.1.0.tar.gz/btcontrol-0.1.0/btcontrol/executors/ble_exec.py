import asyncio
from bleak import BleakClient

class BLEExecutor:
    def __init__(self, address, char_uuid):
        self.address = address
        self.char_uuid = char_uuid

    async def send(self, opcode: int):
        async with BleakClient(self.address) as client:
            await client.write_gatt_char(
                self.char_uuid,
                bytes([opcode]),
                response=False
            )
