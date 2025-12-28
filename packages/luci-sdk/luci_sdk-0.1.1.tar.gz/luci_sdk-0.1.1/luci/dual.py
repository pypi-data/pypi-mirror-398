# luci/dual.py

from dual_luci_capture.dual_eye_threaded import DualCameraCaptureThreaded


class DualCaptureAPI:
    """
    Dual-camera preview and paired capture.
    """

    def __init__(self, luci):
        self._luci = luci

    def preview(
        self,
        right_ip: str,
        save_dir="captures",
    ):
        """
        Preview and capture from two LUCI devices.
        Left camera = this LUCI instance
        Right camera = manually provided IP
        """
        left_ip = self._luci.ip_address
        if not left_ip:
            raise RuntimeError("Left device IP unknown")

        rtsp_left = f"rtsp://{left_ip}:50001/live/0"
        rtsp_right = f"rtsp://{right_ip}:50001/live/0"

        app = DualCameraCaptureThreaded(
            rtsp_left,
            rtsp_right,
            save_dir=save_dir,
        )
        app.run()
