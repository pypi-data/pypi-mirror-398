from sdk_memory import RtspRecorder
import time

rec = RtspRecorder(
    rtsp_url="rtsp://192.168.137.99:50001/live/0",
    ffmpeg_path=r"C:\Users\vq24975\Downloads\ffmpeg-7.0.2-full_build\ffmpeg-7.0.2-full_build\bin\ffmpeg.exe", # use your own ffmpeg path
    save_dir="recording",
    mode="memory",
    buffer_size=60  # buffer save latest 60-second length video
)


rec.start()
time.sleep(20)

# output 10 last 10 seconds video
rec.dump("last10s.ts", start=-10, end=0)

# output video between the latest 30s and 15s
rec.dump("mid_clip.ts", start=-30, end=-15)

rec.stop()

