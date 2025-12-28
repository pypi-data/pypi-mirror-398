# luci/capture.py

from sdk_capture.capture_sdk import SingleCameraCapture


class CaptureAPI:
    """
    High-level capture API for LUCI.
    """

    def __init__(self, luci):
        self._luci = luci

    def preview(self, save_dir="captures", name="luci"):
        """
        Open a live RTSP preview and allow saving frames.
        Press:
          - 's' to save a frame
          - 'q' to quit
        """
        ip = self._luci.ip_address
        if not ip:
            raise RuntimeError("Device IP unknown. Connect hotspot or ADB first.")

        rtsp_url = f"rtsp://{ip}:50001/live/0"

        cap = SingleCameraCapture(
            rtsp_url=rtsp_url,
            save_dir=save_dir,
            name=name,
        )
        cap.run()

    def frame(self, save_dir="captures", name="luci"):
        """
        Alias for preview() for intuitive API naming.
        """
        self.preview(save_dir=save_dir, name=name)
