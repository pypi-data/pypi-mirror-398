def infer_device(info):
    if info.get("transport") == "classic":
        if "AVRCP" in info.get("profiles", []):
            return {
                "type": "audio_output",
                "capabilities": ["media_control"]
            }

    if info.get("transport") == "ble":
        for s in info.get("services", []):
            if s.lower().startswith("12345678"):
                return {
                    "type": "control_plane",
                    "capabilities": ["ble_command"]
                }

    return None
