-- 1. TẠO CƠ SỞ DỮ LIỆU MỚI
CREATE DATABASE IOT_QUANLYSINHVIEN;
GO

USE IOT_QUANLYSINHVIEN;
GO

-- 2. BẢNG NGƯỜI DÙNG (Chứa cả Sinh viên và Giảng viên)
CREATE TABLE NguoiDung (
    MaNguoiDung VARCHAR(50) PRIMARY KEY,     -- MSSV của Sinh viên hoặc Mã GV của Giảng viên
    MatKhau VARCHAR(255) NOT NULL,            -- Mật khẩu đăng nhập portal
    HoTen NVARCHAR(255) NOT NULL,             -- Họ và tên đầy đủ
    VaiTro VARCHAR(20) CHECK (VaiTro IN ('SinhVien', 'GiangVien')), -- Phân quyền truy cập
    KhuonMatData NVARCHAR(MAX) NULL           -- Chuỗi JSON lưu mã hóa 128 số khuôn mặt AI
);
GO

-- 3. BẢNG LỚP HỌC PHẦN (Thông tin môn học & mã lớp của UTE)
CREATE TABLE LopHocPhan (
    MaLop VARCHAR(50) PRIMARY KEY,           -- Ví dụ: 241102B, 24110CTNA
    TenMonHoc NVARCHAR(255) NOT NULL         -- Ví dụ: Vạn Vật Kết Nối, Trí tuệ nhân tạo
);
GO

-- 4. BẢNG DANH SÁCH LỚP (Bảng trung gian kết nối Sinh viên vào từng Lớp học phần)
CREATE TABLE DanhSachLop (
    MaLop VARCHAR(50),
    MaSV VARCHAR(50),
    PRIMARY KEY (MaLop, MaSV),
    FOREIGN KEY (MaLop) REFERENCES LopHocPhan(MaLop) ON DELETE CASCADE,
    FOREIGN KEY (MaSV) REFERENCES NguoiDung(MaNguoiDung) ON DELETE CASCADE
);
GO

-- 5. BẢNG BUỔI HỌC DỰA TRÊN TKB (Để quản lý điểm danh theo từng ngày, từng ca riêng biệt)
CREATE TABLE BuoiHoc (
    MaBuoiHoc INT IDENTITY(1,1) PRIMARY KEY, -- ID tự tăng của buổi học đó (1, 2, 3...)
    MaLop VARCHAR(50) NOT NULL,              -- Buổi học này thuộc lớp nào
    NgayHoc DATE NOT NULL DEFAULT GETDATE(), -- Ngày diễn ra buổi học
    FOREIGN KEY (MaLop) REFERENCES LopHocPhan(MaLop) ON DELETE CASCADE
);
GO

-- 6. BẢNG ĐIỂM DANH (Lưu kết quả quét mặt thực tế hoặc giảng viên sửa tay)
CREATE TABLE DiemDanh (
    MaDiemDanh INT IDENTITY(1,1) PRIMARY KEY,
    MaBuoiHoc INT NOT NULL,
    MaSV VARCHAR(50) NOT NULL,
    ThoiGianQuet DATETIME NOT NULL DEFAULT GETDATE(), -- Giờ chính xác lúc quẹt mặt hoặc sửa tay
    TrangThai NVARCHAR(50) NOT NULL,                  -- 'Đúng giờ', 'Trễ', 'Vắng'
    GhiChu NVARCHAR(255) NULL,                        -- 'Quét qua ESP32 AI' hoặc 'GV Sửa tay'
    FOREIGN KEY (MaBuoiHoc) REFERENCES BuoiHoc(MaBuoiHoc) ON DELETE CASCADE,
    FOREIGN KEY (MaSV) REFERENCES NguoiDung(MaNguoiDung) ON DELETE CASCADE
);
GO

-- =========================================================
-- ĐỔ DỮ LIỆU MỒI (DATA TEST) ĐỂ ĐĂNG NHẬP THỬ WEB
-- =========================================================

-- Nạp tài khoản admin demo cho bro (Sinh viên Minh) và thầy giáo Đoan
INSERT INTO NguoiDung (MaNguoiDung, MatKhau, HoTen, VaiTro, KhuonMatData) VALUES
('24110200', '123456', N'Nguyễn Tất Đô', 'SinhVien', NULL),
('GV01', '123456', N'Đinh Công Đoan', 'GiangVien', NULL);
GO
