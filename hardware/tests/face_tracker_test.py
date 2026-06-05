import cv2
import face_recognition
import numpy as np
import time
import pyodbc
import requests
import threading

print("Đang tải dữ liệu khuôn mặt...")

# ==============================================================
# 1. TẢI ẢNH KHUÔN MẶT (Tạm dùng ảnh cứng để test phần cứng trước)
# ==============================================================
try:
    minh_image = face_recognition.load_image_file("data/minh.jpg")
    minh_face_encoding = face_recognition.face_encodings(minh_image)[0]
    known_face_encodings = [minh_face_encoding]
    known_face_names = ["Minh - Sinh Vien CNTT"]
    print("Đã học xong khuôn mặt của Minh! Đang khởi động hệ thống...")
except Exception as e:
    print(f"Cảnh báo lỗi tải ảnh: {e}")
    known_face_encodings = []
    known_face_names = []

# ==============================================================
# 2. CẤU HÌNH BIẾN TOÀN CỤC & DATABASE
# ==============================================================
# ĐÃ CẬP NHẬT IP MỚI TỪ MÀN HÌNH LCD
IP_ESP32 = "192.168.46.103"

conn_str = (
    r'DRIVER={SQL Server};'
    r'SERVER=localhost;'
    r'DATABASE=IOT_QUANLYSINHVIEN;'
    r'Trusted_Connection=yes;'
)

global_frame = None
global_face_locations = []
global_face_names = []
lock = threading.Lock()

# BIẾN "ĐÈN GIAO THÔNG" ĐỂ CHỐNG KẸT MẠNG ESP32
pause_camera = False

# ==============================================================
# 3. HÀM GHI SQL
# ==============================================================
def ghi_diem_danh_sql(ma_sv):
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        query = """
            INSERT INTO DiemDanh (MaBuoiHoc, MaSV, ThoiGianQuet, TrangThai, GhiChu) 
            VALUES (1, ?, GETDATE(), N'Đúng giờ', N'Điểm danh qua Camera AI')
        """
        cursor.execute(query, (ma_sv,))
        conn.commit()
        print(f"[{time.strftime('%H:%M:%S')}] ĐÃ LƯU DATABASE THÀNH CÔNG!")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Lỗi SQL: {e}")


# ==============================================================
# LUỒNG 1: HÚT ẢNH TỪ ESP32
# ==============================================================
def luong_nhan_video():
    global global_frame, pause_camera
    while True:
        # NẾU ĐÈN ĐỎ -> DỪNG XIN ẢNH ĐỂ NHƯỜNG ĐƯỜNG CHO LỆNH MỞ CỬA
        if pause_camera:
            time.sleep(0.1)
            continue

        try:
            # GỌI LINK /cam ĐỂ LẤY 1 BỨC ẢNH MỚI NHẤT
            res = requests.get(f"http://{IP_ESP32}/cam", timeout=2)
            if res.status_code == 200:
                img_arr = np.frombuffer(res.content, np.uint8)
                frame = cv2.imdecode(img_arr, cv2.IMREAD_COLOR)
                if frame is not None:
                    with lock:
                        global_frame = frame
        except Exception as e:
            pass

        time.sleep(0.02)  # Cho ESP32 thở một nhịp


# ==============================================================
# LUỒNG 2: NÃO BỘ AI XỬ LÝ (TÍCH HỢP ĐIỀU PHỐI GIAO THÔNG)
# ==============================================================
def luong_xu_ly_ai():
    global global_frame, global_face_locations, global_face_names, pause_camera
    last_recognized_time = {}
    COOLDOWN_TIME = 10
    sticky_name = "Nguoi La"
    last_seen_time = 0

    while True:
        if global_frame is None or pause_camera:
            time.sleep(0.01)
            continue

        with lock:
            img_ai = global_frame.copy()

        rgb_frame = cv2.cvtColor(img_ai, cv2.COLOR_BGR2RGB)
        locations = face_recognition.face_locations(rgb_frame)
        encodings = face_recognition.face_encodings(rgb_frame, locations)

        names = []
        for encoding in encodings:
            name = "Nguoi La"
            if len(known_face_encodings) > 0:
                matches = face_recognition.compare_faces(known_face_encodings, encoding, tolerance=0.50)

                if True in matches:
                    first_match_index = matches.index(True)
                    name = known_face_names[first_match_index]
                    sticky_name = name
                    last_seen_time = time.time()
                    current_time = time.time()

                    if name not in last_recognized_time or (current_time - last_recognized_time[name]) > COOLDOWN_TIME:
                        print(f"\n--- [OK] PHÁT HIỆN THỰC TẾ: {name} ---")

                        # =====================================================
                        # KÍCH HOẠT QUY TRÌNH MỞ CỬA "ĐÈN GIAO THÔNG"
                        # =====================================================
                        pause_camera = True  # 1. Bật đèn đỏ (Dừng lấy ảnh)
                        time.sleep(0.3)      # 2. Đợi 0.3s cho mạng Wi-Fi dọn dẹp sạch sẽ

                        # 3. Ghi SQL
                        threading.Thread(target=ghi_diem_danh_sql, args=("24110200",)).start()

                        # 4. Gửi lệnh mở cửa (Lúc này ESP32 đang rảnh 100%, nhận là kêu ngay)
                        try:
                            print(f"[{time.strftime('%H:%M:%S')}] Đang gửi lệnh kích hoạt LCD + Còi...")
                            requests.get(f"http://{IP_ESP32}/open", timeout=3)
                        except Exception as e:
                            print(f"Lỗi gọi phần cứng: {e}")

                        # 5. Đợi 3 giây cho Còi kêu và LCD hiện chữ xong xuôi
                        time.sleep(3)

                        pause_camera = False  # 6. Bật lại đèn xanh (Tiếp tục gọi Camera)
                        # =====================================================

                        last_recognized_time[name] = time.time()
                else:
                    if time.time() - last_seen_time < 1.5:
                        name = sticky_name

            names.append(name)

        with lock:
            global_face_locations = locations
            global_face_names = names

        time.sleep(0.1)


# ==============================================================
# LUỒNG 3: HIỂN THỊ GIAO DIỆN CHÍNH
# ==============================================================
threading.Thread(target=luong_nhan_video, daemon=True).start()
threading.Thread(target=luong_xu_ly_ai, daemon=True).start()

while True:
    if global_frame is None:
        time.sleep(0.01)
        continue

    with lock:
        frame_display = global_frame.copy()
        locations = list(global_face_locations)
        names = list(global_face_names)

    for (top, right, bottom, left), name in zip(locations, names):
        color = (0, 255, 0) if name != "Nguoi La" else (0, 0, 255)
        cv2.rectangle(frame_display, (left, top), (right, bottom), color, 2)
        cv2.putText(frame_display, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

    # Nếu đang mở cửa thì báo lên màn hình cho sinh viên biết
    if pause_camera:
        cv2.putText(frame_display, "DANG MO CUA...", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

    cv2.imshow('He Thong Diem Danh IoT', frame_display)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()