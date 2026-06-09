from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import pyodbc
import face_recognition
import json
from src.config import Config
from src.services.ai_worker import load_ai_data_from_db

web_bp = Blueprint('web', __name__)

@web_bp.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        try:
            conn = pyodbc.connect(Config.CONN_STR)
            cursor = conn.cursor()
            cursor.execute("SELECT VaiTro FROM NguoiDung WHERE MaNguoiDung = ? AND MatKhau = ?",
                           (username, password))
            user = cursor.fetchone()

            if user:
                vaitro = user.VaiTro
                ho_ten = username
                if vaitro == 'GiangVien':
                    cursor.execute("SELECT HoTen FROM GiangVien WHERE MaGiangVien = ?", (username,))
                    gv = cursor.fetchone()
                    if gv: ho_ten = gv.HoTen
                elif vaitro == 'SinhVien':
                    cursor.execute("SELECT HoTen FROM SinhVien WHERE MaSinhVien = ?", (username,))
                    sv = cursor.fetchone()
                    if sv: ho_ten = sv.HoTen
                conn.close()

                session['user_id'] = username
                session['ho_ten'] = ho_ten
                session['role'] = vaitro
                if vaitro == 'SinhVien':
                    return redirect(url_for('web.student'))
                elif vaitro == 'GiangVien':
                    return redirect(url_for('web.teacher'))
                else:
                    flash(f"Vai trò '{vaitro}' không được hỗ trợ.")
            else:
                flash("Sai mã người dùng hoặc mật khẩu!")
        except Exception as e:
            flash(f"Lỗi kết nối hệ thống: {e}")
    return render_template('login.html')


@web_bp.route('/student')
def student():
    if not session.get('user_id'):
        return redirect(url_for('web.login'))
        
    conn = pyodbc.connect(Config.CONN_STR)
    cursor = conn.cursor()
    cursor.execute("SELECT MaTheRFID, KhuonMatData FROM SinhVien WHERE MaSinhVien = ?", (session.get('user_id'),))
    user = cursor.fetchone()
    rfid = user.MaTheRFID if user and user.MaTheRFID else ""
    has_face = True if user and user.KhuonMatData else False
    conn.close()
    
    return render_template('student_dashboard.html', hoten=session.get('ho_ten'),
                           masv=session.get('user_id'), rfid=rfid, has_face=has_face)


@web_bp.route('/teacher')
def teacher():
    if not session.get('user_id'):
        return redirect(url_for('web.login'))
    return render_template('teacher_dashboard.html', hoten=session.get('ho_ten'),
                           masv=session.get('user_id'))


@web_bp.route('/upload_face', methods=['POST'])
def upload_face():
    file = request.files['face_image']
    img = face_recognition.load_image_file(file)
    encs = face_recognition.face_encodings(img)
    if len(encs) == 1:
        vec_str = json.dumps(encs[0].tolist())
        conn = pyodbc.connect(Config.CONN_STR)
        cursor = conn.cursor()
        cursor.execute("UPDATE SinhVien SET KhuonMatData = ? WHERE MaSinhVien = ?", (vec_str, session['user_id']))
        conn.commit()
        load_ai_data_from_db()
        return "Cập nhật khuôn mặt AI thành công!", 200
    return "Không nhận diện được khuôn mặt!", 400


@web_bp.route('/update_rfid', methods=['POST'])
def update_rfid():
    if not session.get('user_id'):
        return "Vui lòng đăng nhập!", 401
    
    rfid_code = request.form.get('rfid_code')
    if rfid_code:
        # Xóa khoảng trắng để mã thẻ chuẩn (ví dụ " F3 A2 " -> "F3A2")
        rfid_code = rfid_code.replace(" ", "").upper()
        try:
            conn = pyodbc.connect(Config.CONN_STR)
            cursor = conn.cursor()
            cursor.execute("UPDATE SinhVien SET MaTheRFID = ? WHERE MaSinhVien = ?", (rfid_code, session['user_id']))
            conn.commit()
            conn.close()
            return "Cập nhật mã thẻ RFID thành công!", 200
        except Exception as e:
            return f"Lỗi cập nhật mã thẻ: {e}", 500
    return "Mã thẻ không hợp lệ!", 400


@web_bp.route('/door')
def door_display(): 
    return render_template('door_display.html')


@web_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('web.login'))
