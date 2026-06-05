import pandas as pd
import pyodbc

# CẤU HÌNH DATABASE
conn_str = (
    r'DRIVER={SQL Server};'
    r'SERVER=localhost;'
    r'DATABASE=IOT_QUANLYSINHVIEN;'
    r'Trusted_Connection=yes;'
)
file_path = 'danh_sach.xls'

try:
    print(f"Đang đọc dữ liệu từ: {file_path}...")
    # Bản chất file UTE là CSV nên dùng read_csv, chấp luôn đuôi xls
    try:
        df = pd.read_csv(file_path, skiprows=8)
    except:
        df = pd.read_excel(file_path, skiprows=8)

    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    print("1. Đang khởi tạo các Lớp và Buổi học (Tạo data mẫu)...")
    lops = [
        ('241102B', 'Vạn Vật Kết Nối'),
        ('241104B', 'An toàn thông tin'),
        ('241101C', 'Tiếng Anh Chuyên ngành'),
        ('24110CTNA', 'Trí tuệ nhân tạo')
    ]
    for malop, tenmon in lops:
        cursor.execute("SELECT COUNT(*) FROM LopHocPhan WHERE MaLop=?", (malop,))
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO LopHocPhan (MaLop, TenMonHoc) VALUES (?, ?)", (malop, tenmon))

    # Khởi tạo Buổi học (ID 1->7) để Web có cái mà Load danh sách
    buoi_map = {1: '241102B', 2: '241104B', 3: '241101C', 4: '24110CTNA', 5: '241102B', 6: '241104B', 7: '24110CTNA'}
    for mabuoi, malop in buoi_map.items():
        cursor.execute("SELECT COUNT(*) FROM BuoiHoc WHERE MaBuoiHoc=?", (mabuoi,))
        if cursor.fetchone()[0] == 0:
            try:
                cursor.execute("SET IDENTITY_INSERT BuoiHoc ON")
                cursor.execute("INSERT INTO BuoiHoc (MaBuoiHoc, MaLop, NgayHoc) VALUES (?, ?, GETDATE())",
                               (mabuoi, malop))
                cursor.execute("SET IDENTITY_INSERT BuoiHoc OFF")
            except:
                try:
                    cursor.execute("INSERT INTO BuoiHoc (MaBuoiHoc, MaLop, NgayHoc) VALUES (?, ?, GETDATE())",
                                   (mabuoi, malop))
                except:
                    pass

    print("2. Đang rải 60 sinh viên vào TẤT CẢ các lớp để Test Web...")
    count = 0
    for index, row in df.iterrows():
        # DÙNG ILOC (LẤY THEO VỊ TRÍ) ĐỂ TRÁNH LỖI TÊN CỘT BỊ KHOẢNG TRẮNG
        # index 1 = Mã SV, index 3 = Họ lót, index 4 = Tên
        ma_sv = str(row.iloc[1]).strip()
        ho_lot = str(row.iloc[3]).strip()
        ten = str(row.iloc[4]).strip()

        if ma_sv == 'nan' or not ma_sv or ma_sv == 'None':
            continue

        ho_ten = f"{ho_lot} {ten}"

        # Thêm tài khoản Sinh Viên
        cursor.execute("SELECT COUNT(*) FROM NguoiDung WHERE MaNguoiDung=?", (ma_sv,))
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                "INSERT INTO NguoiDung (MaNguoiDung, MatKhau, HoTen, VaiTro) VALUES (?, '123456', ?, 'SinhVien')",
                (ma_sv, ho_ten))

        # Rải danh sách vào 4 lớp luôn
        for malop, _ in lops:
            cursor.execute("SELECT COUNT(*) FROM DanhSachLop WHERE MaLop=? AND MaSV=?", (malop, ma_sv))
            if cursor.fetchone()[0] == 0:
                cursor.execute("INSERT INTO DanhSachLop (MaLop, MaSV) VALUES (?, ?)", (malop, ma_sv))

        count += 1

    conn.commit()
    conn.close()
    print(f"✅ HOÀN TẤT! Đã nạp {count} sinh viên. Giờ ông lên Web bấm môn nào cũng sẽ có danh sách!")

except Exception as e:
    print(f"❌ Lỗi: {e}")