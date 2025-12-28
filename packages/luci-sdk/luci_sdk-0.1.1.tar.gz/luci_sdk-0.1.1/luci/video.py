# luci/video.py

import time
from sdk_save_video.luci_sdk import RtspRecorder


class VideoAPI:
    """
    Disk-based RTSP video recording API.
    """

    def __init__(self, luci):
        self._luci = luci
        self._recorder = None

    def start(
        self,
        save_dir="recordings",
        segment_time=60,
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
            segment_time=segment_time,
        )
        self._recorder.start()

    def stop(self):
        if self._recorder:
            self._recorder.stop()
            self._recorder = None

    def record(
        self,
        duration: int,
        save_dir="recordings",
        segment_time=60,
        ffmpeg_path="ffmpeg",
    ):
        """
        Record for a fixed duration (blocking).
        """
        self.start(
            save_dir=save_dir,
            segment_time=segment_time,
            ffmpeg_path=ffmpeg_path,
        )
        try:
            time.sleep(duration)
        finally:
            self.stop()
