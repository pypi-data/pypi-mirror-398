from luci_sdk import RtspRecorder
import time

rec = RtspRecorder(
    rtsp_url="rtsp://192.168.137.28:50001/live/0",
    ffmpeg_path=r"C:\Users\junlo\OneDrive - University of Cambridge\Unity Projects\LUCI SDK\ffmpeg-8.0-essentials_build\bin\ffmpeg.exe",
    save_dir="recording",
    segment_time=60
)

rec.start()
time.sleep(120)   # record for 2 min== 120s

rec.stop()
