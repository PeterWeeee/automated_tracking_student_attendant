import threading

# Global variables to share state across modules
camera_is_running = False
current_buoi_hoc_id = 1
ai_memory = []
lock = threading.Lock()

from typing import Any
global_latest_frame = b''
global_latest_bgr: Any = None
latest_scan_data = {
    "masv": "--",
    "hoten": "Đang chờ quét...",
    "time": "--:--:--",
    "status": "waiting"
}
last_recognized_time = {} # Cơ chế debounce chống trùng lặp (30s)
