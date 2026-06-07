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

def trigger_door_open(method, ma_sv):
    try:
        requests.get(f"http://{Config.IP_ESP32_S}/open?method={method}&masv={ma_sv}", timeout=2)
    except Exception as req_e:
        print(f"[LỖI KẾT NỐI ESP32-S]: {req_e}")

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
    while True:
        if not ext.camera_is_running:
            time.sleep(1)
            continue

        cap = None
        try:
            # OpenCV kết nối trực tiếp đến luồng MJPEG của ESP32-CAM trên cổng 81
            stream_url = f"http://{Config.IP_ESP32_CAM}:81/stream"
            cap = cv2.VideoCapture(stream_url)
            
            if not cap.isOpened():
                if not getattr(ext, 'camera_error_printed', False):
                    print(f"\n[LỖI CAMERA] Không thể mở luồng Video từ: {stream_url}")
                    setattr(ext, 'camera_error_printed', True)
                time.sleep(2)
                continue

            setattr(ext, 'camera_error_printed', False)
            
            # Đọc khung hình liên tục mượt mà
            while ext.camera_is_running:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # frame là mảng BGR của OpenCV, lưu lại để AI xử lý luôn (không cần decode lại)
                ext.global_latest_bgr = frame
                
                # Mã hóa ra JPEG để phát qua Web Proxy cho giao diện
                ret_jpg, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                if ret_jpg:
                    ext.global_latest_frame = buffer.tobytes()
                    
        except Exception as e:
            print(f"[LỖI CAMERA] {e}")
            time.sleep(2)
        finally:
            if 'cap' in locals() and cap is not None:
                cap.release()


def ai_process_worker():
    last_processed_frame = None

    while True:
        if not ext.camera_is_running or not hasattr(ext, 'global_latest_bgr'):
            time.sleep(0.5)
            continue

        frame = getattr(ext, 'global_latest_bgr')
        # Tránh xử lý lại cùng một khung hình (dựa vào reference)
        if frame is last_processed_frame:
            time.sleep(0.1)
            continue

        last_processed_frame = frame

        try:
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

                        if ma_sv not in ext.last_recognized_time or (time.time() - ext.last_recognized_time[ma_sv] > 30):
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
                                        VALUES (?, ?, GETDATE(), N'Đúng giờ', N'face')
                                    """, (current_buoi_id, ma_sv))
                                    conn.commit()
                                conn.close()
                            except Exception as db_e:
                                print(f"[SQL LỖI]: {db_e}")

                            ext.latest_scan_data = {
                                "masv": ma_sv,
                                "hoten": ho_ten,
                                "time": time.strftime('%H:%M:%S'),
                                "status": "success",
                                "method": "face"
                            }

                            # Gọi hàm mở cửa không đồng bộ (không chờ)
                            threading.Thread(target=trigger_door_open, args=("face", ma_sv)).start()
                            ext.last_recognized_time[ma_sv] = time.time()
        except Exception as frame_e:
            print(f"[AI FRAME LỖI]: {frame_e}")
            
        time.sleep(0.01)

def start_ai_worker():
    threading.Thread(target=camera_fetch_worker, daemon=True).start()
    threading.Thread(target=ai_process_worker, daemon=True).start()
