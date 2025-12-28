import subprocess
import os
import signal
import platform


class RtspRecorder:
    def __init__(self, rtsp_url, ffmpeg_path="ffmpeg", save_dir="recording", segment_time=60):
        self.rtsp_url = rtsp_url
        self.ffmpeg_path = ffmpeg_path
        self.save_dir = save_dir
        self.segment_time = segment_time
        self.proc = None

        os.makedirs(save_dir, exist_ok=True)

    def start(self):
        """start recording"""
        if self.proc is not None:
            raise RuntimeError("Recorder already running!")

        output_pattern = os.path.join(self.save_dir, "output_%Y-%m-%d_%H-%M-%S.h264")

        command = [
            self.ffmpeg_path,
            "-i", self.rtsp_url,
            "-c", "copy",
            "-an",                       # get rid of the voice
            "-f", "segment",
            "-segment_time", str(self.segment_time),
            "-reset_timestamps", "1",
            "-strftime", "1",
            output_pattern
        ]

        self.proc = subprocess.Popen(command)
        print(f"[Recorder] Started recording RTSP stream to {self.save_dir}")

    def stop(self):
        """stop recording safely， save the file """
        if self.proc is None:
            print("[Recorder] Not running.")
            return

        print("[Recorder] Stopping...")

        try:
            if platform.system() == "Windows":
                self.proc.terminate()  # In the Windows system, terminate can trigger ffmpeg flush
            else:
                self.proc.send_signal(signal.SIGINT)  # Linux/macOS  SIGINT
            self.proc.wait()
        except Exception as e:
            print(f"[Recorder] Error stopping process: {e}")
        finally:
            self.proc = None

            print("[Recorder] Recording stopped and files saved.")
