from fastapi import FastAPI, HTTPException
import btcontrol
from btcontrol.core.registry import REGISTRY

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    await btcontrol.init()

@app.get("/devices")
def list_devices():
    return [d.describe() for d in REGISTRY.all()]

@app.post("/devices/{device_id}/{action}")
async def run_action(device_id: str, action: str):
    try:
        device = REGISTRY.get(device_id)

        if action not in device.actions:
            raise HTTPException(404, "Action not supported")

        await device.actions[action].run()
        return {"status": "ok"}

    except Exception as e:
        print("ERROR:", e)
        raise HTTPException(500, str(e))
