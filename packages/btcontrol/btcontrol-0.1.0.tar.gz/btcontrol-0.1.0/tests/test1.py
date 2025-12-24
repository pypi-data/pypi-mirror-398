import asyncio
import btcontrol

async def main():
    await btcontrol.init()

    from btcontrol import REGISTRY

    devices = REGISTRY.all()

    print("\nDiscovered devices:")
    for d in devices:
        print(d.describe())

if __name__ == "__main__":
    asyncio.run(main())
