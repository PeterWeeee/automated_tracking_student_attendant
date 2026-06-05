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
                ISNULL(dd.TrangThai, N'Vắng') AS TrangThai
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
                "trangthai": r.TrangThai
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
        row = cursor.fetchone()
        exists = (row[0] > 0) if row else False

        if exists:
            cursor.execute("UPDATE DiemDanh SET TrangThai=? WHERE MaBuoiHoc=? AND MaSV=?",
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
    if ext.global_latest_frame: 
        return Response(ext.global_latest_frame, mimetype='image/jpeg')
    return "No frame", 404


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
            col_lower = col.lower() if isinstance(col, str) else str(col).lower()
            if 'mã' in col_lower or 'mssv' in col_lower or 'id' in col_lower:
                col_masv = i
            elif 'họ' in col_lower:
                col_holot = i
            elif 'tên' in col_lower and 'họ' not in col_lower:
                col_ten = i
                
        # Fallback về index tĩnh nếu không nhận diện được
        if col_masv is None: col_masv = 1
        if col_holot is None: col_holot = 3
        if col_ten is None: col_ten = 4

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
                ten = str(row.iloc[col_ten]).strip()

                if ma_sv == 'nan' or not ma_sv or ma_sv == 'None':
                    continue

                ho_ten = f"{ho_lot} {ten}"

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

