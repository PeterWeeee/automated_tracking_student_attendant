import threading
import time
import requests
import cv2
import numpy as np
import face_recognition
import pyodbc
import json

from src.config import Config
import src.extensions as ext

def load_ai_data_from_db():
    print("[HỆ THỐNG] Đang nạp dữ liệu khuôn mặt...")
    try:
        conn = pyodbc.connect(Config.CONN_STR)
        cursor = conn.cursor()
        cursor.execute("SELECT MaNguoiDung, HoTen, KhuonMatData FROM NguoiDung WHERE KhuonMatData IS NOT NULL")
        temp_mem = []
        for row in cursor.fetchall():
            temp_mem.append({
                "masv": row.MaNguoiDung,
                "hoten": row.HoTen,
                "encoding": np.array(json.loads(row.KhuonMatData))
            })
        with ext.lock:
            ext.ai_memory = temp_mem
        print(f"[HỆ THỐNG] Đã nạp {len(temp_mem)} khuôn mặt!")
        conn.close()
    except Exception as e:
        print("Lỗi nạp DB:", e)


def camera_fetch_worker():
    session = requests.Session()
    # Tối ưu hóa TCP Keep-Alive để lấy ảnh mượt hơn và giảm tải cho mạch ESP32
    while True:
        if not ext.camera_is_running:
            time.sleep(1)
            continue

        try:
            res = session.get(f"http://{Config.IP_ESP32}/cam", timeout=5)
            if res.status_code == 200:
                ext.global_latest_frame = res.content
                setattr(ext, 'camera_error_printed', False)
        except Exception as e:
            if not getattr(ext, 'camera_error_printed', False):
                print(f"\n[LỖI CAMERA] Không thể kết nối tới ESP32 tại địa chỉ IP: {Config.IP_ESP32}")
                print(f"Chi tiết lỗi: {e}")
                print("-> Hãy kiểm tra lại ESP32 đã bật nguồn chưa, hoặc xem IP thực tế của ESP32 trong Serial Monitor Arduino và cập nhật vào src/config.py\n")
                setattr(ext, 'camera_error_printed', True)
            time.sleep(2)
            continue
            
        # Nghỉ cực ngắn để vắt kiệt tối đa số khung hình ESP32 có thể gửi (Tối đa ~50 FPS)
        time.sleep(0.02)


def ai_process_worker():
    last_recognized = {}
    last_processed_frame = None

    while True:
        if not ext.camera_is_running or not ext.global_latest_frame:
            time.sleep(0.5)
            continue

        frame_data = ext.global_latest_frame
        # Tránh xử lý lại cùng một khung hình
        if frame_data == last_processed_frame:
            time.sleep(0.1)
            continue

        last_processed_frame = frame_data

        try:
            img_arr = np.frombuffer(frame_data, np.uint8)
            frame = cv2.imdecode(img_arr, cv2.IMREAD_COLOR)
            if frame is None:
                continue
            
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            locations = face_recognition.face_locations(rgb_frame)
            if not locations:
                continue
                
            encodings = face_recognition.face_encodings(rgb_frame, locations)

            with ext.lock:
                local_memory = ext.ai_memory.copy()
                current_buoi_id = ext.current_buoi_hoc_id

            for encoding in encodings:
                if len(local_memory) > 0:
                    known_encs = [m['encoding'] for m in local_memory]
                    matches = face_recognition.compare_faces(known_encs, encoding, tolerance=0.45)

                    if True in matches:
                        match_idx = matches.index(True)
                        matched_user = local_memory[match_idx]
                        ma_sv = matched_user['masv']
                        ho_ten = matched_user['hoten']

                        if ma_sv not in last_recognized or (time.time() - last_recognized[ma_sv] > 30):
                            print(f"[AI] 👉 NHẬN DIỆN: {ho_ten}")

                            try:
                                conn = pyodbc.connect(Config.CONN_STR)
                                cursor = conn.cursor()
                                cursor.execute("SELECT COUNT(*) FROM DiemDanh WHERE MaSV=? AND MaBuoiHoc=?",
                                               (ma_sv, current_buoi_id))
                                row = cursor.fetchone()
                                if row and row[0] == 0:
                                    cursor.execute("""
                                        INSERT INTO DiemDanh (MaBuoiHoc, MaSV, ThoiGianQuet, TrangThai, GhiChu)
                                        VALUES (?, ?, GETDATE(), N'Đúng giờ', N'AI')
                                    """, (current_buoi_id, ma_sv))
                                    conn.commit()
                                conn.close()
                            except Exception as db_e:
                                print(f"[SQL LỖI]: {db_e}")

                            ext.latest_scan_data = {
                                "masv": ma_sv,
                                "hoten": ho_ten,
                                "time": time.strftime('%H:%M:%S'),
                                "status": "success"
                            }

                            requests.get(f"http://{Config.IP_ESP32}/open", timeout=2)
                            last_recognized[ma_sv] = time.time()
        except Exception:
            pass
            
        time.sleep(0.01)

def start_ai_worker():
    threading.Thread(target=camera_fetch_worker, daemon=True).start()
    threading.Thread(target=ai_process_worker, daemon=True).start()
