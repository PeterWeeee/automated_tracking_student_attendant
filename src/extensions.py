import threading

# Global variables to share state across modules
camera_is_running = False
current_buoi_hoc_id = 1
ai_memory = []
lock = threading.Lock()

global_latest_frame = b''
latest_scan_data = {
    "masv": "--",
    "hoten": "Đang chờ quét...",
    "time": "--:--:--",
    "status": "waiting"
}
