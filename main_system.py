from flask import Flask, render_template, request, redirect, url_for, session, jsonify, Response
import pyodbc
import face_recognition
import numpy as np
import json
import threading
import time
import requests
import cv2

app = Flask(__name__)
app.secret_key = 'ute_iot_secret_key'

# =========================================================
# CẤU HÌNH HỆ THỐNG
# =========================================================
conn_str = (
    r'DRIVER={SQL Server};'
    r'SERVER=localhost;'
    r'DATABASE=IOT_QUANLYSINHVIEN;'
    r'Trusted_Connection=yes;'
)
IP_ESP32 = "192.168.46.103"

camera_is_running = False
current_buoi_hoc_id = 1  # Sẽ được web cập nhật linh hoạt
ai_memory = []
lock = threading.Lock()

global_latest_frame = b''
latest_scan_data = {
    "masv": "--",
    "hoten": "Đang chờ quét...",
    "time": "--:--:--",
    "status": "waiting"
}


# =========================================================
# LUỒNG AI XỬ LÝ (CHẠY NGẦM)
# =========================================================
def load_ai_data_from_db():
    global ai_memory
    print("[HỆ THỐNG] Đang nạp dữ liệu khuôn mặt...")
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute("SELECT MaNguoiDung, HoTen, KhuonMatData FROM NguoiDung WHERE KhuonMatData IS NOT NULL")
        temp_mem = []
        for row in cursor.fetchall():
            temp_mem.append({
                "masv": row.MaNguoiDung,
                "hoten": row.HoTen,
                "encoding": np.array(json.loads(row.KhuonMatData))
            })
        with lock:
            ai_memory = temp_mem
        print(f"[HỆ THỐNG] Đã nạp {len(temp_mem)} khuôn mặt!")
        conn.close()
    except Exception as e:
        print("Lỗi nạp DB:", e)


def ai_camera_worker():
    global camera_is_running, ai_memory, latest_scan_data, global_latest_frame, current_buoi_hoc_id
    last_recognized = {}

    while True:
        if not camera_is_running:
            time.sleep(1)
            continue

        try:
            res = requests.get(f"http://{IP_ESP32}/cam", timeout=3)
            if res.status_code == 200:
                global_latest_frame = res.content

                img_arr = np.frombuffer(res.content, np.uint8)
                frame = cv2.imdecode(img_arr, cv2.IMREAD_COLOR)
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                locations = face_recognition.face_locations(rgb_frame)
                encodings = face_recognition.face_encodings(rgb_frame, locations)

                with lock:
                    local_memory = ai_memory.copy()

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
                                    conn = pyodbc.connect(conn_str)
                                    cursor = conn.cursor()
                                    cursor.execute("SELECT COUNT(*) FROM DiemDanh WHERE MaSV=? AND MaBuoiHoc=?",
                                                   (ma_sv, current_buoi_hoc_id))
                                    if cursor.fetchone()[0] == 0:
                                        cursor.execute("""
                                            INSERT INTO DiemDanh (MaBuoiHoc, MaSV, ThoiGianQuet, TrangThai, GhiChu)
                                            VALUES (?, ?, GETDATE(), N'Đúng giờ', N'AI')
                                        """, (current_buoi_hoc_id, ma_sv))
                                        conn.commit()
                                    conn.close()
                                except Exception as db_e:
                                    print(f"[SQL LỖI]: {db_e}")

                                latest_scan_data = {
                                    "masv": ma_sv,
                                    "hoten": ho_ten,
                                    "time": time.strftime('%H:%M:%S'),
                                    "status": "success"
                                }

                                requests.get(f"http://{IP_ESP32}/open", timeout=2)
                                last_recognized[ma_sv] = time.time()
                                time.sleep(2)
        except Exception:
            pass
        time.sleep(0.1)


threading.Thread(target=ai_camera_worker, daemon=True).start()


# =========================================================
# API CHO WEB HOẠT ĐỘNG
# =========================================================
@app.route('/api/get_attendance')
def get_attendance():
    """Lấy FULL danh sách sinh viên của lớp, kể cả người vắng mặt"""
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        query = """
            SELECT 
                n.MaNguoiDung AS MaSV, 
                n.HoTen, 
                CASE WHEN n.KhuonMatData IS NULL THEN 0 ELSE 1 END AS CoDuLieuMat,
                FORMAT(dd.ThoiGianQuet, 'HH:mm:ss') AS GioQuet, 
                ISNULL(dd.TrangThai, N'Vắng') AS TrangThai
            FROM BuoiHoc bh
            JOIN DanhSachLop dsl ON bh.MaLop = dsl.MaLop
            JOIN NguoiDung n ON dsl.MaSV = n.MaNguoiDung
            LEFT JOIN DiemDanh dd ON bh.MaBuoiHoc = dd.MaBuoiHoc AND dd.MaSV = n.MaNguoiDung
            WHERE bh.MaBuoiHoc = ?
            ORDER BY n.HoTen
        """
        cursor.execute(query, (current_buoi_hoc_id,))
        data = []
        for i, r in enumerate(cursor.fetchall()):
            data.append({
                "stt": i + 1,
                "masv": r.MaSV,
                "hoten": r.HoTen,
                "co_mat_ai": r.CoDuLieuMat,
                "gioquet": r.GioQuet if r.GioQuet else "--:--",
                "trangthai": r.TrangThai
            })
        conn.close()
        return jsonify({"status": "ok", "data": data})
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)})


@app.route('/api/update_status', methods=['POST'])
def update_status():
    """API để Giảng viên sửa điểm danh thủ công"""
    masv = request.form.get('masv')
    status = request.form.get('status')  # 'Đúng giờ', 'Trễ', 'Vắng'
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM DiemDanh WHERE MaBuoiHoc=? AND MaSV=?", (current_buoi_hoc_id, masv))
        exists = cursor.fetchone()[0] > 0

        if exists:
            cursor.execute("UPDATE DiemDanh SET TrangThai=? WHERE MaBuoiHoc=? AND MaSV=?",
                           (status, current_buoi_hoc_id, masv))
        else:
            if status != 'Vắng':
                cursor.execute("""
                    INSERT INTO DiemDanh (MaBuoiHoc, MaSV, ThoiGianQuet, TrangThai, GhiChu)
                    VALUES (?, ?, GETDATE(), ?, N'GV Sửa tay')
                """, (current_buoi_hoc_id, masv, status))
        conn.commit()
        conn.close()
        return jsonify({"status": "ok", "msg": "Cập nhật thành công!"})
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)})


@app.route('/api/student_history')
def student_history():
    """Sinh viên xem lịch sử điểm danh của mình theo Lớp"""
    malop = request.args.get('malop')
    masv = session.get('user_id')
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        query = """
            SELECT 
                bh.NgayHoc, 
                FORMAT(dd.ThoiGianQuet, 'HH:mm:ss') as GioQuet, 
                ISNULL(dd.TrangThai, N'Vắng') as TrangThai
            FROM BuoiHoc bh
            LEFT JOIN DiemDanh dd ON bh.MaBuoiHoc = dd.MaBuoiHoc AND dd.MaSV = ?
            WHERE bh.MaLop = ?
            ORDER BY bh.NgayHoc DESC
        """
        cursor.execute(query, (masv, malop))
        data = []
        for r in cursor.fetchall():
            data.append({
                "ngayhoc": str(r.NgayHoc),
                "gioquet": r.GioQuet if r.GioQuet else "--:--",
                "trangthai": r.TrangThai
            })
        conn.close()
        return jsonify({"status": "ok", "data": data})
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)})


@app.route('/api/toggle_camera', methods=['POST'])
def toggle_camera():
    global camera_is_running, latest_scan_data, current_buoi_hoc_id
    action = request.form.get('action')

    if action == 'start':
        buoi_id = request.form.get('buoi_id')
        if buoi_id:
            current_buoi_hoc_id = int(buoi_id)

        load_ai_data_from_db()
        camera_is_running = True
        latest_scan_data = {"masv": "--", "hoten": "Đang chờ quét...", "time": "--:--:--", "status": "waiting"}
        return jsonify({"msg": f"Đã BẬT Camera AI tại phòng học!"})
    else:
        camera_is_running = False
        return jsonify({"msg": "Đã TẮT Camera AI"})


@app.route('/api/latest_scan')
def get_latest_scan():
    return jsonify(latest_scan_data)


@app.route('/cam_proxy')
def cam_proxy():
    if global_latest_frame: return Response(global_latest_frame, mimetype='image/jpeg')
    return "No frame", 404


# =========================================================
# ROUTE GIAO DIỆN HTML
# =========================================================
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        try:
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()
            cursor.execute("SELECT HoTen, VaiTro FROM NguoiDung WHERE MaNguoiDung = ? AND MatKhau = ?",
                           (username, password))
            user = cursor.fetchone()
            if user:
                session['user_id'] = username
                session['ho_ten'] = user.HoTen
                session['role'] = user.VaiTro
                if user.VaiTro == 'SinhVien': return redirect(url_for('student'))
                if user.VaiTro == 'GiangVien': return redirect(url_for('teacher'))
        except Exception:
            pass
    return render_template('login.html')


@app.route('/student')
def student(): return render_template('student_dashboard.html', hoten=session.get('ho_ten'),
                                      masv=session.get('user_id'))


@app.route('/teacher')
def teacher(): return render_template('teacher_dashboard.html', hoten=session.get('ho_ten'),
                                      masv=session.get('user_id'))


@app.route('/upload_face', methods=['POST'])
def upload_face():
    file = request.files['face_image']
    img = face_recognition.load_image_file(file)
    encs = face_recognition.face_encodings(img)
    if len(encs) == 1:
        vec_str = json.dumps(encs[0].tolist())
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute("UPDATE NguoiDung SET KhuonMatData = ? WHERE MaNguoiDung = ?", (vec_str, session['user_id']))
        conn.commit()
        load_ai_data_from_db()
        return "Cập nhật khuôn mặt AI thành công!", 200


@app.route('/door')
def door_display(): return render_template('door_display.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


if __name__ == '__main__':
    load_ai_data_from_db()
    app.run(host='0.0.0.0', port=5000, debug=False)