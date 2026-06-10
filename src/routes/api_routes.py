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
                sv.MaSinhVien AS MaSV,
                sv.HoTen,
                CASE WHEN sv.KhuonMatData IS NULL THEN 0 ELSE 1 END AS CoDuLieuMat,
                CASE WHEN sv.MaTheRFID IS NULL THEN 0 ELSE 1 END AS CoDuLieuThe,
                FORMAT(dd.ThoiGianQuet, 'HH:mm:ss') AS GioQuet,
                ISNULL(dd.TrangThai, N'Trống') AS TrangThai,
                ISNULL(dd.GhiChu, '') AS GhiChu
            FROM BuoiHoc bh
            JOIN DanhSachMon dsm ON bh.MaMon = dsm.MaMon
            JOIN SinhVien sv ON dsm.MaSV = sv.MaSinhVien
            LEFT JOIN DiemDanh dd ON bh.MaBuoiHoc = dd.MaBuoiHoc AND dd.MaSV = sv.MaSinhVien
            WHERE bh.MaBuoiHoc = ?
            ORDER BY sv.HoTen
        """
        cursor.execute(query, (buoi_id,))
        data = []
        for i, r in enumerate(cursor.fetchall()):
            data.append({
                "stt": i + 1,
                "masv": r.MaSV,
                "hoten": r.HoTen,
                "co_mat_ai": r.CoDuLieuMat,
                "co_the_rfid": getattr(r, 'CoDuLieuThe', 0),
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
                   bh.TietBatDau, bh.TietKetThuc, bh.MaPhong AS Phong,
                   mh.MaMon, mh.TenMon AS TenMonHoc
            FROM BuoiHoc bh
            JOIN MonHoc mh ON bh.MaMon = mh.MaMon
            WHERE bh.MaGiangVien = ?
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
                "mamon": r.MaMon,
                "tenmon": r.TenMonHoc
            })
        conn.close()
        return jsonify({"status": "ok", "data": data})
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)})


@api_bp.route('/get_student_schedule')
def get_student_schedule():
    """Lấy lịch học của sinh viên đang đăng nhập."""
    if not session.get('user_id'):
        return jsonify({"status": "error", "msg": "Chưa đăng nhập"})
    try:
        conn = pyodbc.connect(Config.CONN_STR)
        cursor = conn.cursor()
        query = """
            SELECT bh.MaBuoiHoc, bh.NgayHoc, bh.ThuTrongTuan, bh.Ca,
                   bh.TietBatDau, bh.TietKetThuc, bh.MaPhong AS Phong,
                   mh.MaMon, mh.TenMon AS TenMonHoc
            FROM BuoiHoc bh
            JOIN MonHoc mh ON bh.MaMon = mh.MaMon
            JOIN DanhSachMon dsm ON bh.MaMon = dsm.MaMon
            WHERE dsm.MaSV = ?
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
                "mamon": r.MaMon,
                "tenmon": r.TenMonHoc
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
    buoi_id = request.form.get('buoi_id', type=int)
    
    if not buoi_id:
        buoi_id = ext.current_buoi_hoc_id

    try:
        conn = pyodbc.connect(Config.CONN_STR)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM DiemDanh WHERE MaBuoiHoc=? AND MaSV=?", (buoi_id, masv))
        row = cursor.fetchone()
        exists = (row[0] > 0) if row else False

        if exists:
            cursor.execute("""
                UPDATE DiemDanh
                SET TrangThai=?, ThoiGianQuet=GETDATE(), GhiChu=N'GV Sửa tay'
                WHERE MaBuoiHoc=? AND MaSV=?""",
                           (status, buoi_id, masv))
        else:
            if status != 'Vắng':
                cursor.execute("""
                    INSERT INTO DiemDanh (MaBuoiHoc, MaSV, ThoiGianQuet, TrangThai, GhiChu)
                    VALUES (?, ?, GETDATE(), ?, N'GV Sửa tay')
                """, (buoi_id, masv, status))
        conn.commit()
        conn.close()
        return jsonify({"status": "ok", "msg": "Cập nhật thành công!"})
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)})


@api_bp.route('/student_history')
def student_history():
    """Sinh viên xem lịch sử điểm danh của mình theo Lớp"""
    mamon = request.args.get('mamon')
    masv = session.get('user_id')
    try:
        conn = pyodbc.connect(Config.CONN_STR)
        cursor = conn.cursor()
        query = """
            SELECT 
                bh.NgayHoc, 
                FORMAT(dd.ThoiGianQuet, 'HH:mm:ss') as GioQuet, 
                ISNULL(dd.TrangThai, N'Trống') as TrangThai
            FROM BuoiHoc bh
            LEFT JOIN DiemDanh dd ON bh.MaBuoiHoc = dd.MaBuoiHoc AND dd.MaSV = ?
            WHERE bh.MaMon = ?
            ORDER BY bh.NgayHoc DESC
        """
        cursor.execute(query, (masv, mamon))
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

        duration = request.form.get('duration')
        if duration:
            ext.scan_duration_seconds = int(duration) * 60
        else:
            ext.scan_duration_seconds = 30 * 60 # Default 30 mins

        import time
        ext.session_start_time = time.time()

        load_ai_data_from_db()
        ext.camera_is_running = True
        ext.latest_scan_data = {"masv": "--", "hoten": "Đang chờ quét...", "time": "--:--:--", "status": "waiting"}
        return jsonify({"msg": f"Đã BẬT Camera AI tại phòng học!"})
    else:
        ext.camera_is_running = False
        
        buoi_id = request.form.get('buoi_id')
        if not buoi_id:
            buoi_id = getattr(ext, 'current_buoi_hoc_id', None)
            
        if buoi_id:
            try:
                conn = pyodbc.connect(Config.CONN_STR)
                cursor = conn.cursor()
                
                # Get all students for this class
                cursor.execute("""
                    SELECT dsm.MaSV
                    FROM BuoiHoc bh
                    JOIN DanhSachMon dsm ON bh.MaMon = dsm.MaMon
                    WHERE bh.MaBuoiHoc = ?
                """, (buoi_id,))
                all_students = set(r[0] for r in cursor.fetchall())
                
                # Get students already attended
                cursor.execute("SELECT MaSV FROM DiemDanh WHERE MaBuoiHoc=?", (buoi_id,))
                attended_students = set(r[0] for r in cursor.fetchall())
                
                absent_students = all_students - attended_students
                
                for sv in absent_students:
                    cursor.execute("""
                        INSERT INTO DiemDanh (MaBuoiHoc, MaSV, ThoiGianQuet, TrangThai, GhiChu)
                        VALUES (?, ?, GETDATE(), N'Vắng', N'Hệ thống tự đánh vắng')
                    """, (buoi_id, sv))
                
                conn.commit()
                conn.close()
            except Exception as e:
                print(f"Lỗi tự đánh vắng: {e}")
                
        return jsonify({"msg": "Đã TẮT Camera AI và chốt điểm danh!"})


@api_bp.route('/latest_scan')
def get_latest_scan():
    return jsonify(ext.latest_scan_data)

@api_bp.route('/camera_status')
def get_camera_status():
    return jsonify({
        "is_running": ext.camera_is_running,
        "buoi_id": getattr(ext, 'current_buoi_hoc_id', None),
        "start_time": getattr(ext, 'session_start_time', 0),
        "duration": getattr(ext, 'scan_duration_seconds', 0)
    })


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
    mamon = request.form.get('mamon')
    
    if file.filename == '' or not mamon:
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
                        "INSERT INTO NguoiDung (MaNguoiDung, MatKhau, TenDangNhap, VaiTro) VALUES (?, '123456', ?, 'SinhVien')",
                        (ma_sv, ma_sv))
                    cursor.execute(
                        "INSERT INTO SinhVien (MaSinhVien, HoTen) VALUES (?, ?)",
                        (ma_sv, ho_ten))

                # 2. Map vào danh sách môn
                cursor.execute("SELECT COUNT(*) FROM DanhSachMon WHERE MaMon=? AND MaSV=?", (mamon, ma_sv))
                class_row = cursor.fetchone()
                if class_row and class_row[0] == 0:
                    cursor.execute("INSERT INTO DanhSachMon (MaMon, MaSV, MaGiangVien) VALUES (?, ?, ?)", (mamon, ma_sv, session.get('user_id')))
                    
                count += 1
            except Exception as e:
                print(f"Bỏ qua dòng lỗi: {e}")
                continue

        conn.commit()
        conn.close()
        return jsonify({"status": "ok", "msg": f"Đã nạp {count} sinh viên vào môn {mamon} thành công!"})
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
        cursor.execute("SELECT MaSinhVien, HoTen FROM SinhVien WHERE MaTheRFID=?", (uid,))
        user = cursor.fetchone()
        
        if not user:
            print(f"==================================================")
            print(f"👉 [RFID LẠ] Phát hiện mã thẻ chưa đăng ký: {uid}")
            print(f"==================================================")
            conn.close()
            return jsonify({"status": "error", "msg": "Thẻ không hợp lệ hoặc chưa được đăng ký"}), 404
            
        ma_sv = user.MaSinhVien
        ho_ten = user.HoTen
        
        import time
        # Kiểm tra debounce 30 giây
        if ma_sv in ext.last_recognized_time and (time.time() - ext.last_recognized_time[ma_sv] < 30):
            conn.close()
            return jsonify({"status": "ignored", "msg": "Đã điểm danh gần đây"})
            
        print(f"[RFID] 👉 NHẬN DIỆN: {ho_ten} ({ma_sv})")
        
        # Xác định trạng thái Đúng giờ hay Trễ
        elapsed = time.time() - ext.session_start_time
        scan_status = 'Đúng giờ' if elapsed <= ext.scan_duration_seconds else 'Trễ'

        # Ghi nhận điểm danh
        current_buoi_id = ext.current_buoi_hoc_id
        cursor.execute("SELECT TrangThai FROM DiemDanh WHERE MaSV=? AND MaBuoiHoc=?", (ma_sv, current_buoi_id))
        row = cursor.fetchone()
        if not row:
            cursor.execute("""
                INSERT INTO DiemDanh (MaBuoiHoc, MaSV, ThoiGianQuet, TrangThai, GhiChu)
                VALUES (?, ?, GETDATE(), ?, N'rfid')
            """, (current_buoi_id, ma_sv, scan_status))
            conn.commit()
        elif row[0] == 'Vắng':
            cursor.execute("""
                UPDATE DiemDanh 
                SET TrangThai=?, ThoiGianQuet=GETDATE(), GhiChu=N'rfid'
                WHERE MaBuoiHoc=? AND MaSV=?
            """, (scan_status, current_buoi_id, ma_sv))
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

@api_bp.route('/teacher_statistics')
def teacher_statistics():
    if not session.get('user_id'):
        return jsonify({"status": "error", "msg": "Chưa đăng nhập"})
    try:
        mamon = request.args.get('mamon')
        time_range = request.args.get('time_range')
        thu_trong_tuan = request.args.get('thu') # e.g., '2', '3', '4' or 'all'
        
        conn = pyodbc.connect(Config.CONN_STR)
        cursor = conn.cursor()
        
        base_query = """
            FROM DanhSachMon dsm
            JOIN BuoiHoc bh ON dsm.MaMon = bh.MaMon AND dsm.MaGiangVien = bh.MaGiangVien
            LEFT JOIN DiemDanh dd ON bh.MaBuoiHoc = dd.MaBuoiHoc AND dsm.MaSV = dd.MaSV
            WHERE dsm.MaGiangVien = ?
        """
        params = [session['user_id']]
        
        if mamon and mamon != 'all':
            base_query += " AND dsm.MaMon = ?"
            params.append(mamon)

        if thu_trong_tuan and thu_trong_tuan != 'all':
            base_query += " AND bh.ThuTrongTuan = ?"
            params.append(int(thu_trong_tuan))
            
        if time_range == 'semester':
            pass # Removed HocKy filter as it's not in MonHoc, might add later
        elif time_range == 'week':
            base_query += " AND DATEPART(ww, bh.NgayHoc) = DATEPART(ww, GETDATE()) AND YEAR(bh.NgayHoc) = YEAR(GETDATE())"
        elif time_range == 'month':
            base_query += " AND MONTH(bh.NgayHoc) = MONTH(GETDATE()) AND YEAR(bh.NgayHoc) = YEAR(GETDATE())"

        # 1. TỔNG QUAN (Pie Chart)
        query_pie = "SELECT ISNULL(dd.TrangThai, N'Trống') AS TrangThai, COUNT(*) AS SoLuong " + base_query + " GROUP BY ISNULL(dd.TrangThai, N'Trống')"
        cursor.execute(query_pie, tuple(params))
        pie_data = {"Đúng giờ": 0, "Trễ": 0, "Vắng": 0, "Trống": 0}
        for r in cursor.fetchall():
            if r.TrangThai in pie_data:
                pie_data[r.TrangThai] = r.SoLuong
            else:
                pie_data[r.TrangThai] = r.SoLuong

        # 2. XU HƯỚNG THEO NGÀY (Bar Chart)
        query_bar = """
            SELECT bh.NgayHoc, ISNULL(dd.TrangThai, N'Trống') AS TrangThai, COUNT(*) AS SoLuong
            """ + base_query + """
            GROUP BY bh.NgayHoc, ISNULL(dd.TrangThai, N'Trống')
            ORDER BY bh.NgayHoc ASC
        """
        cursor.execute(query_bar, tuple(params))
        
        # Group by NgayHoc
        trend_dict = {}
        for r in cursor.fetchall():
            ngay = str(r.NgayHoc)
            if ngay not in trend_dict:
                trend_dict[ngay] = {"Đúng giờ": 0, "Trễ": 0, "Vắng": 0, "Trống": 0}
            status = r.TrangThai if r.TrangThai in trend_dict[ngay] else "Trống"
            trend_dict[ngay][status] += r.SoLuong
            
        # Convert to list for frontend
        bar_data = []
        for ngay in sorted(trend_dict.keys()):
            bar_data.append({
                "ngayhoc": ngay,
                "dunggio": trend_dict[ngay]["Đúng giờ"],
                "tre": trend_dict[ngay]["Trễ"],
                "vang": trend_dict[ngay]["Vắng"],
                "trong": trend_dict[ngay]["Trống"]
            })

        conn.close()
        return jsonify({
            "status": "ok", 
            "data": {
                "pie": pie_data,
                "bar": bar_data
            }
        })
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)})

@api_bp.route('/student_attendance_summary')
def student_attendance_summary():
    """Lấy danh sách các lớp và chi tiết từng buổi học cho sinh viên"""
    if not session.get('user_id'):
        return jsonify({"status": "error", "msg": "Chưa đăng nhập"})
    try:
        nam_hoc = request.args.get('nam_hoc', '2024-2025')
        hoc_ky = request.args.get('hoc_ky', '1', type=int)

        conn = pyodbc.connect(Config.CONN_STR)
        cursor = conn.cursor()
        
        query = """
            SELECT 
                mh.MaMon, 
                mh.TenMon, 
                mh.SoTC,
                bh.NgayHoc,
                bh.ThuTrongTuan,
                bh.MaPhong AS Phong,
                bh.TietBatDau,
                bh.TietKetThuc,
                ISNULL(dd.TrangThai, N'Trống') AS TrangThai
            FROM DanhSachMon dsm
            JOIN MonHoc mh ON dsm.MaMon = mh.MaMon
            JOIN BuoiHoc bh ON dsm.MaMon = bh.MaMon AND dsm.MaGiangVien = bh.MaGiangVien
            LEFT JOIN DiemDanh dd ON bh.MaBuoiHoc = dd.MaBuoiHoc AND dsm.MaSV = dd.MaSV
            WHERE dsm.MaSV = ? 
            ORDER BY mh.MaMon, bh.NgayHoc ASC
        """
        cursor.execute(query, (session['user_id'],))
        
        # Group data by MaMon
        grouped_data = {}
        for r in cursor.fetchall():
            mamon = r.MaMon
            if mamon not in grouped_data:
                grouped_data[mamon] = {
                    "mamon": mamon,
                    "tenmon": r.TenMon,
                    "sotc": r.SoTC if r.SoTC else 3,
                    "sessions": []
                }
            
            grouped_data[mamon]["sessions"].append({
                "ngay": str(r.NgayHoc),
                "thu": r.ThuTrongTuan,
                "phong": r.Phong,
                "tiet": f"{r.TietBatDau} - {r.TietKetThuc}",
                "trangthai": r.TrangThai
            })
            
        conn.close()
        return jsonify({"status": "ok", "data": list(grouped_data.values())})
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)})

