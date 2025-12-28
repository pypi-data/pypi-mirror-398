import argparse
import socket
import time

from luci import LUCI
from luci.utils import load_ip, save_ip

DEFAULT_PORT = 50001


def rtsp_reachable(ip: str, port: int, timeout: float = 2.0) -> bool:
    try:
        with socket.create_connection((ip, port), timeout=timeout):
            return True
    except OSError:
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Record LUCI RTSP stream (cached IP → ADB fallback)"
    )
    parser.add_argument("--duration", type=int, default=10)
    parser.add_argument("--segment-time", type=int, default=5)
    parser.add_argument("--save-dir", default="recordings")
    parser.add_argument("--ffmpeg", default="ffmpeg")
    args = parser.parse_args()

    # --------------------------------------------------
    # Always create LUCI instance
    # --------------------------------------------------
    luci = None
    ip = None

    cached_ip = load_ip()
    if cached_ip and rtsp_reachable(cached_ip, DEFAULT_PORT):
        print(f"[INFO] Using cached IP: {cached_ip}")
        luci = LUCI(device_id="cached")
        luci._ip_address = cached_ip
        ip = cached_ip

    # --------------------------------------------------
    # Fallback to ADB
    # --------------------------------------------------
    if not ip:
        print("[INFO] Trying ADB connection...")
        luci = LUCI.connect_via_adb()
        ip = luci.ip_address

        if not ip or not rtsp_reachable(ip, DEFAULT_PORT):
            print("[INFO] Attempting hotspot connection...")
            ssid = input("Hotspot SSID: ").strip()
            password = input("Hotspot Password: ").strip()
            luci.join_hotspot(ssid, password)
            ip = luci.ip_address

        if not ip:
            raise RuntimeError("RTSP stream not reachable")

        save_ip(ip)

    # --------------------------------------------------
    # Record using wrapper
    # --------------------------------------------------
    print(f"[INFO] Recording from {ip}")

    luci.video.start(
        save_dir=args.save_dir,
        segment_time=args.segment_time,
        ffmpeg_path=args.ffmpeg,
    )

    try:
        time.sleep(args.duration)
    except KeyboardInterrupt:
        print("[WARN] Interrupted")
    finally:
        luci.video.stop()
        print("[SUCCESS] Recording finished")


if __name__ == "__main__":
    main()
