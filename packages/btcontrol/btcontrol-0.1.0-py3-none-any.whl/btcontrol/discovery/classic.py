import platform

def discover_classic():
    system = platform.system()

    if system == "Windows":
        return [{
            "id": "default_audio",
            "name": "Active Audio Output",
            "transport": "classic",
            "profiles": ["A2DP", "AVRCP"]
        }]

    return []
