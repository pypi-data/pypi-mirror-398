import asyncio
import time
import btcontrol

async def main():
    await btcontrol.init()

    device = btcontrol.REGISTRY.get("default_audio")

    print("Play / Pause")
    device.actions["play"].execute()
    time.sleep(5)

    print("Next track")
    device.actions["next"].execute()
    time.sleep(5)

    print("Volume down")
    device.actions["volume_down"].execute()
    time.sleep(5)

    print("Mute")
    device.actions["mute"].execute()

    print("Done.")

if __name__ == "__main__":
    asyncio.run(main())
