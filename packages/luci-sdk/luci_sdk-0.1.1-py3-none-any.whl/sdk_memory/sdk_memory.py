import subprocess
import threading
import collections
import os
import platform
import signal
import time


class RtspRecorder:
    def __init__(self, rtsp_url, ffmpeg_path="ffmpeg",
                 save_dir="recording", segment_time=60,
                 mode="disk", buffer_size=30):
        self.rtsp_url = rtsp_url
        self.ffmpeg_path = ffmpeg_path
        self.save_dir = save_dir
        self.segment_time = segment_time
        self.mode = mode
        self.buffer_size = buffer_size   # memory length
        self.proc = None
        self.buffer = collections.deque(maxlen=buffer_size * 30)  # buffer size
        self.timestamps = collections.deque(maxlen=buffer_size * 30)  # timestamps
        self.thread = None

        os.makedirs(save_dir, exist_ok=True)

    def start(self):
        if self.mode == "disk":
            self._start_disk()
        else:
            self._start_memory()

    def stop(self):
        if self.proc:
            if platform.system() == "Windows":
                self.proc.terminate()
            else:
                self.proc.send_signal(signal.SIGINT)
            self.proc.wait()
            self.proc = None

    def _start_disk(self):
        output_pattern = os.path.join(self.save_dir, "output_%Y-%m-%d_%H-%M-%S.h264")
        cmd = [self.ffmpeg_path, "-i", self.rtsp_url,
               "-c", "copy", "-an",
               "-f", "segment", "-segment_time", str(self.segment_time),
               "-reset_timestamps", "1", "-strftime", "1", output_pattern]
        self.proc = subprocess.Popen(cmd)

    def _start_memory(self):
        cmd = [self.ffmpeg_path, "-i", self.rtsp_url,
               "-c", "copy", "-an", "-f", "mpegts", "pipe:1"]
        self.proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=10**7
        )
        self.thread = threading.Thread(target=self._reader, daemon=True)
        self.thread.start()

    def _reader(self):
        """ ffmpeg output to memory"""
        while True:
            data = self.proc.stdout.read(4096)
            if not data:
                break
            now = time.time()
            self.buffer.append(data)
            self.timestamps.append(now)

    def dump(self, filename, start=-30, end=0):
        """
        output the video of the memory to the disk
        parameters:
          filename: 
          start: start second
          end: end second
        examples:
          dump("last10s.ts", start=-10, end=0) → latest 10s
          dump("clip.ts", start=-30, end=-15) → 
        """
        if self.mode != "memory":
            raise RuntimeError("dump only in (mode='memory')")

        t_now = time.time()
        t_start = t_now + start
        t_end = t_now + end

        with open(os.path.join(self.save_dir, filename), "wb") as f:
            for ts, chunk in zip(self.timestamps, self.buffer):
                if t_start <= ts <= t_end:
                    f.write(chunk)

        print(f"[Recorder] Dumped buffer to {filename} ({start}..{end} sec)")

