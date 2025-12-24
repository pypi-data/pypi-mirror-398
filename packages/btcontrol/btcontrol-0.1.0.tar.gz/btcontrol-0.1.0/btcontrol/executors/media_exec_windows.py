import keyboard

class MediaExecutor:
    def play(self): keyboard.send("play/pause media")
    def pause(self): keyboard.send("play/pause media")
    def next(self): keyboard.send("next track")
    def previous(self): keyboard.send("previous track")
    def volume_up(self): keyboard.send("volume up")
    def volume_down(self): keyboard.send("volume down")
    def mute(self): keyboard.send("volume mute")
