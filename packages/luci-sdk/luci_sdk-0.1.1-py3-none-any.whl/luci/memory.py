# luci/memory.py

from sdk_memory.sdk_memory import RtspRecorder


class MemoryAPI:
    """
    In-memory RTSP recording API with time-based dump.
    """

    def __init__(self, luci):
        self._luci = luci
        self._recorder = None

    def start(
        self,
        save_dir="recordings",
        buffer_size=60,
        ffmpeg_path="ffmpeg",
    ):
        ip = self._luci.ip_address
        if not ip:
            raise RuntimeError("Device IP unknown. Connect hotspot or ADB first.")

        rtsp_url = f"rtsp://{ip}:50001/live/0"

        self._recorder = RtspRecorder(
            rtsp_url=rtsp_url,
            ffmpeg_path=ffmpeg_path,
            save_dir=save_dir,
            mode="memory",
            buffer_size=buffer_size,
        )
        self._recorder.start()

    def dump(self, filename, start=-10, end=0):
        if not self._recorder:
            raise RuntimeError("Memory recorder not running")
        self._recorder.dump(filename, start=start, end=end)

    def stop(self):
        if self._recorder:
            self._recorder.stop()
            self._recorder = None
