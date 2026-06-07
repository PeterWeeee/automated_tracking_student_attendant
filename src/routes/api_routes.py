from flask import Blueprint, request, session, jsonify, Response
import pyodbc
from src.config import Config
import src.extensions as ext
from src.services.ai_worker import load_ai_data_from_db

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/get_attendance')
def get_attendance():
    """Lấy FULL danh sách sinh viên của lớp, kể cả người vắng mặt."""
    buoi_id = request.args.get('buoi_id', type=int)
    if buoi_id is None:
        buoi_id = ext.current_buoi_hoc_id
    try:
        conn = pyodbc.connect(Config.CONN_STR)
        cursor = conn.cursor()
        query = """
            SELECT
                n.MaNguoiDung AS MaSV,
                n.HoTen,
                CASE WHEN n.KhuonMatData IS NULL THEN 0 ELSE 1 END AS CoDuLieuMat,
                FORMAT(dd.ThoiGianQuet, 'HH:mm:ss') AS GioQuet,
                ISNULL(dd.TrangThai, N'Vắng') AS TrangThai,
                ISNULL(dd.GhiChu, '') AS GhiChu
            FROM BuoiHoc bh
            JOIN DanhSachLop dsl ON bh.MaLop = dsl.MaLop
            JOIN NguoiDung n ON dsl.MaSV = n.MaNguoiDung
            LEFT JOIN DiemDanh dd ON bh.MaBuoiHoc = dd.MaBuoiHoc AND dd.MaSV = n.MaNguoiDung
            WHERE bh.MaBuoiHoc = ?
            ORDER BY n.HoTen
        """
        cursor.execute(query, (buoi_id,))
        data = []
        for i, r in enumerate(cursor.fetchall()):
            data.append({
                "stt": i + 1,
                "masv": r.MaSV,
                "hoten": r.HoTen,
                "co_mat_ai": r.CoDuLieuMat,
                "gioquet": r.GioQuet if r.GioQuet else "--:--",
                "trangthai": r.TrangThai,
                "phuongthuc": r.GhiChu
            })
        conn.close()
        return jsonify({"status": "ok", "data": data})
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)})


@api_bp.route('/get_teacher_schedule')
def get_teacher_schedule():
    """Lấy lịch giảng dạy của giảng viên đang đăng nhập."""
    if not session.get('user_id'):
        return jsonify({"status": "error", "msg": "Chưa đăng nhập"})
    try:
        conn = pyodbc.connect(Config.CONN_STR)
        cursor = conn.cursor()
        query = """
            SELECT bh.MaBuoiHoc, bh.NgayHoc, bh.ThuTrongTuan, bh.Ca,
                   bh.TietBatDau, bh.TietKetThuc, bh.Phong,
                   lhp.MaLop, lhp.TenMonHoc, lhp.MaMon
            FROM BuoiHoc bh
            JOIN LopHocPhan lhp ON bh.MaLop = lhp.MaLop
            WHERE lhp.MaGV = ?
            ORDER BY bh.ThuTrongTuan, bh.TietBatDau
        """
        cursor.execute(query, (session['user_id'],))
        data = []
        for r in cursor.fetchall():
            data.append({
                "mabuoi": r.MaBuoiHoc,
                "ngayhoc": str(r.NgayHoc) if r.NgayHoc else "",
                "thu": r.ThuTrongTuan,
                "ca": r.Ca if r.Ca else "Sang",
                "tiet_bd": r.TietBatDau,
                "tiet_kt": r.TietKetThuc,
                "phong": r.Phong if r.Phong else "",
                "malop": r.MaLop,
                "tenmon": r.TenMonHoc,
                "mamon": r.MaMon if r.MaMon else ""
            })
        conn.close()
        return jsonify({"status": "ok", "data": data})
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)})


@api_bp.route('/update_status', methods=['POST'])
def update_status():
    """API để Giảng viên sửa điểm danh thủ công"""
    masv = request.form.get('masv')
    status = request.form.get('status')
    try:
        conn = pyodbc.connect(Config.CONN_STR)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM DiemDanh WHERE MaBuoiHoc=? AND MaSV=?", (ext.current_buoi_hoc_id, masv))
        row = cursor.fetchone()
        exists = (row[0] > 0) if row else False

        if exists:
            cursor.execute("""
                UPDATE DiemDanh
                SET TrangThai=?, ThoiGianQuet=GETDATE(), GhiChu=N'GV Sửa tay'
                WHERE MaBuoiHoc=? AND MaSV=?""",
                           (status, ext.current_buoi_hoc_id, masv))
        else:
            if status != 'Vắng':
                cursor.execute("""
                    INSERT INTO DiemDanh (MaBuoiHoc, MaSV, ThoiGianQuet, TrangThai, GhiChu)
                    VALUES (?, ?, GETDATE(), ?, N'GV Sửa tay')
                """, (ext.current_buoi_hoc_id, masv, status))
        conn.commit()
        conn.close()
        return jsonify({"status": "ok", "msg": "Cập nhật thành công!"})
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)})


@api_bp.route('/student_history')
def student_history():
    """Sinh viên xem lịch sử điểm danh của mình theo Lớp"""
    malop = request.args.get('malop')
    masv = session.get('user_id')
    try:
        conn = pyodbc.connect(Config.CONN_STR)
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


@api_bp.route('/toggle_camera', methods=['POST'])
def toggle_camera():
    action = request.form.get('action')

    if action == 'start':
        buoi_id = request.form.get('buoi_id')
        if buoi_id:
            ext.current_buoi_hoc_id = int(buoi_id)

        load_ai_data_from_db()
        ext.camera_is_running = True
        ext.latest_scan_data = {"masv": "--", "hoten": "Đang chờ quét...", "time": "--:--:--", "status": "waiting"}
        return jsonify({"msg": f"Đã BẬT Camera AI tại phòng học!"})
    else:
        ext.camera_is_running = False
        return jsonify({"msg": "Đã TẮT Camera AI"})


@api_bp.route('/latest_scan')
def get_latest_scan():
    return jsonify(ext.latest_scan_data)


@api_bp.route('/cam_proxy')
def cam_proxy():
    def generate_frames():
        import time
        while True:
            if ext.global_latest_frame:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + ext.global_latest_frame + b'\r\n')
            time.sleep(0.06)
            
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@api_bp.route('/upload_excel', methods=['POST'])
def upload_excel():
    if 'file' not in request.files:
        return jsonify({"status": "error", "msg": "Không tìm thấy file!"})
    
    file = request.files['file']
    malop = request.form.get('malop')
    
    if file.filename == '' or not malop:
        return jsonify({"status": "error", "msg": "Dữ liệu không hợp lệ!"})
        
    try:
        import pandas as pd
        
        # Đọc Excel
        if file.filename and file.filename.endswith('.csv'):
            df = pd.read_csv(file.stream, skiprows=8) # type: ignore
        else:
            df = pd.read_excel(file.stream, skiprows=8) # type: ignore

        # Nhận diện cột thông minh
        col_masv = None
        col_holot = None
        col_ten = None
        
        # Thử tìm theo tên cột (nếu có header)
        for i, col in enumerate(df.columns):
            col_lower = col.lower().strip() if isinstance(col, str) else str(col).lower().strip()
            if col_lower == 'mã sv' or col_lower == 'mssv' or col_lower == 'mã số sinh viên':
                col_masv = i
            elif col_lower == 'họ và tên lót' or col_lower == 'họ lót' or 'họ' in col_lower and 'tên' not in col_lower:
                if col_holot is None: # Tránh lấy nhầm cột khác có chữ họ
                    col_holot = i
            elif col_lower == 'tên':
                col_ten = i
                
        # Fallback về index tĩnh nếu không nhận diện được
        if col_masv is None: col_masv = 1
        if col_holot is None: col_holot = 3
        # col_ten: KHÔNG fallback – nếu Excel có cột "Họ và tên" gộp thì dùng col_holot là đủ

        conn = pyodbc.connect(Config.CONN_STR)
        cursor = conn.cursor()
        
        count = 0
        for index, row in df.iterrows():
            try:
                raw_ma_sv = str(row.iloc[col_masv]).strip()
                try:
                    ma_sv = str(int(float(raw_ma_sv)))
                except (ValueError, OverflowError):
                    ma_sv = raw_ma_sv
                    
                ho_lot = str(row.iloc[col_holot]).strip()

                if ma_sv == 'nan' or not ma_sv or ma_sv == 'None':
                    continue

                if col_ten is not None:
                    ten = str(row.iloc[col_ten]).strip()
                    ho_ten = f"{ho_lot} {ten}"
                else:
                    ho_ten = ho_lot  # Tên đầy đủ đã gộp trong 1 cột

                # 1. Thêm user nếu chưa có
                cursor.execute("SELECT COUNT(*) FROM NguoiDung WHERE MaNguoiDung=?", (ma_sv,))
                user_row = cursor.fetchone()
                if user_row and user_row[0] == 0:
                    cursor.execute(
                        "INSERT INTO NguoiDung (MaNguoiDung, MatKhau, HoTen, VaiTro) VALUES (?, '123456', ?, 'SinhVien')",
                        (ma_sv, ho_ten))

                # 2. Map vào lớp học
                cursor.execute("SELECT COUNT(*) FROM DanhSachLop WHERE MaLop=? AND MaSV=?", (malop, ma_sv))
                class_row = cursor.fetchone()
                if class_row and class_row[0] == 0:
                    cursor.execute("INSERT INTO DanhSachLop (MaLop, MaSV) VALUES (?, ?)", (malop, ma_sv))
                    
                count += 1
            except Exception as e:
                print(f"Bỏ qua dòng lỗi: {e}")
                continue

        conn.commit()
        conn.close()
        return jsonify({"status": "ok", "msg": f"Đã nạp {count} sinh viên vào lớp {malop} thành công!"})
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)})


@api_bp.route('/rfid-check', methods=['POST'])
def rfid_check():
    data = request.json
    if not data:
        return jsonify({"status": "error", "msg": "No data provided"}), 400
        
    uid = data.get('uid')
    room_id = data.get('room_id')
    
    if not uid:
        return jsonify({"status": "error", "msg": "Missing UID"}), 400

    # Chỉ xử lý khi GV đã nhấn "Điểm danh / Bắt đầu"
    if not ext.camera_is_running:
        return jsonify({"status": "ignored", "msg": "Chua mo diem danh"}), 200

    try:
        conn = pyodbc.connect(Config.CONN_STR)
        cursor = conn.cursor()
        
        # Tìm sinh viên qua MaTheRFID
        cursor.execute("SELECT MaNguoiDung, HoTen FROM NguoiDung WHERE MaTheRFID=?", (uid,))
        user = cursor.fetchone()
        
        if not user:
            print(f"==================================================")
            print(f"👉 [RFID LẠ] Phát hiện mã thẻ chưa đăng ký: {uid}")
            print(f"==================================================")
            conn.close()
            return jsonify({"status": "error", "msg": "Thẻ không hợp lệ hoặc chưa được đăng ký"}), 404
            
        ma_sv = user.MaNguoiDung
        ho_ten = user.HoTen
        
        import time
        # Kiểm tra debounce 30 giây
        if ma_sv in ext.last_recognized_time and (time.time() - ext.last_recognized_time[ma_sv] < 30):
            conn.close()
            return jsonify({"status": "ignored", "msg": "Đã điểm danh gần đây"})
            
        print(f"[RFID] 👉 NHẬN DIỆN: {ho_ten} ({ma_sv})")
        
        # Ghi nhận điểm danh
        current_buoi_id = ext.current_buoi_hoc_id
        cursor.execute("SELECT COUNT(*) FROM DiemDanh WHERE MaSV=? AND MaBuoiHoc=?", (ma_sv, current_buoi_id))
        row = cursor.fetchone()
        if row and row[0] == 0:
            cursor.execute("""
                INSERT INTO DiemDanh (MaBuoiHoc, MaSV, ThoiGianQuet, TrangThai, GhiChu)
                VALUES (?, ?, GETDATE(), N'Đúng giờ', N'rfid')
            """, (current_buoi_id, ma_sv))
            conn.commit()
            
        conn.close()
        
        # Cập nhật state hiển thị
        ext.latest_scan_data = {
            "masv": ma_sv,
            "hoten": ho_ten,
            "time": time.strftime('%H:%M:%S'),
            "status": "success",
            "method": "rfid"
        }
        
        ext.last_recognized_time[ma_sv] = time.time()
        
        # Gọi ngược lại ESP32-S để mở cửa/kêu còi (dùng luồng riêng để không bị đơ)
        import requests
        import threading
        
        def trigger_door_open_rfid():
            try:
                requests.get(f"http://{Config.IP_ESP32_S}/open?method=rfid&masv={ma_sv}", timeout=2)
            except Exception as req_e:
                print(f"[LỖI KẾT NỐI ESP32-S TỪ RFID]: {req_e}")
                
        threading.Thread(target=trigger_door_open_rfid).start()

        return jsonify({"status": "ok", "msg": "Điểm danh thành công"})

    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)}), 500
