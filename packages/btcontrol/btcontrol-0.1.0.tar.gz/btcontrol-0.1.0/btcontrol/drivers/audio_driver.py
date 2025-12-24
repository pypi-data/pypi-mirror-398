from btcontrol.drivers.base import Driver
from btcontrol.core.device import Device
from btcontrol.core.action import Action
from btcontrol.executors.media_exec_windows import MediaExecutor

class AudioDriver(Driver):
    def match(self, device_info):
        return (
            device_info.get("transport") == "classic"
            and "AVRCP" in device_info.get("profiles", [])
        )

    def build_device(self, device_info):
        exec = MediaExecutor()

        actions = {
            "play": Action("play", exec.play),
            "pause": Action("pause", exec.pause),
            "next": Action("next", exec.next),
            "previous": Action("previous", exec.previous),
            "volume_up": Action("volume_up", exec.volume_up),
            "volume_down": Action("volume_down", exec.volume_down),
            "mute": Action("mute", exec.mute),
        }

        return Device(
            device_id=device_info["id"],
            name=device_info["name"],
            device_type="audio_output",
            capabilities=["media_control"],
            actions=actions
        )
