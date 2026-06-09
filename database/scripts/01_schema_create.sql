-- =========================================================
-- IOT_QUANLYSINHVIEN — SCHEMA
-- Xóa Database cũ và thiết kế lại theo yêu cầu mới
-- =========================================================

-- 1. XOÁ VÀ TẠO MỚI CƠ SỞ DỮ LIỆU
USE master;
GO

IF EXISTS (SELECT name FROM sys.databases WHERE name = N'IOT_QUANLYSINHVIEN')
BEGIN
    ALTER DATABASE IOT_QUANLYSINHVIEN SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE IOT_QUANLYSINHVIEN;
END
GO

CREATE DATABASE IOT_QUANLYSINHVIEN;
GO

USE IOT_QUANLYSINHVIEN;
GO

-- =========================================================
-- 2. BẢNG NGƯỜI DÙNG (CHUNG)
-- =========================================================
CREATE TABLE NguoiDung (
    MaNguoiDung VARCHAR(50)  PRIMARY KEY,     -- MSSV hoặc Mã GV (đóng vai trò ID/Username đăng nhập)
    MatKhau     VARCHAR(255) NOT NULL,         
    TenDangNhap NVARCHAR(255) NOT NULL,        -- Tên đăng nhập
    VaiTro      VARCHAR(20)  NOT NULL CHECK (VaiTro IN ('SinhVien', 'GiangVien'))
);
GO

-- =========================================================
-- 3. BẢNG GIẢNG VIÊN
-- =========================================================
CREATE TABLE GiangVien (
    MaGiangVien VARCHAR(50) PRIMARY KEY,
    HoTen       NVARCHAR(255) NOT NULL,
    Khoa        NVARCHAR(255) NULL,
    ChuyenNganh NVARCHAR(255) NULL,
    Email       VARCHAR(255)  NULL,
    SDT         VARCHAR(20)   NULL,
    HocVi       NVARCHAR(50)  NULL,
    CONSTRAINT FK_GiangVien_NguoiDung FOREIGN KEY (MaGiangVien) REFERENCES NguoiDung(MaNguoiDung) ON DELETE CASCADE
);
GO

-- =========================================================
-- 4. BẢNG SINH VIÊN
-- =========================================================
CREATE TABLE SinhVien (
    MaSinhVien  VARCHAR(50) PRIMARY KEY,
    HoTen       NVARCHAR(255) NOT NULL,
    MaTheRFID   VARCHAR(50)  NULL,
    KhuonMatData NVARCHAR(MAX) NULL,
    CONSTRAINT FK_SinhVien_NguoiDung FOREIGN KEY (MaSinhVien) REFERENCES NguoiDung(MaNguoiDung) ON DELETE CASCADE
);
GO

-- =========================================================
-- 5. BẢNG MÔN HỌC
-- =========================================================
CREATE TABLE MonHoc (
    MaMon     VARCHAR(50)   PRIMARY KEY,      
    TenMon    NVARCHAR(255) NOT NULL,          
    SoTC      INT           DEFAULT 3
);
GO

-- =========================================================
-- 6. BẢNG PHÒNG HỌC
-- =========================================================
CREATE TABLE PhongHoc (
    MaPhong   VARCHAR(50) PRIMARY KEY,
    TenPhong  NVARCHAR(255) NOT NULL
);
GO

-- =========================================================
-- 7. BẢNG DANH SÁCH MÔN HỌC (Sinh viên học môn nào với GV nào)
-- =========================================================
CREATE TABLE DanhSachMon (
    MaMon       VARCHAR(50) NOT NULL,
    MaSV        VARCHAR(50) NOT NULL,
    MaGiangVien VARCHAR(50) NULL,
    PRIMARY KEY (MaMon, MaSV),
    FOREIGN KEY (MaMon) REFERENCES MonHoc(MaMon) ON DELETE CASCADE,
    FOREIGN KEY (MaSV)  REFERENCES SinhVien(MaSinhVien) ON DELETE CASCADE,
    FOREIGN KEY (MaGiangVien) REFERENCES GiangVien(MaGiangVien)
);
GO

-- =========================================================
-- 8. BẢNG BUỔI HỌC
-- =========================================================
CREATE TABLE BuoiHoc (
    MaBuoiHoc   INT IDENTITY(1,1) PRIMARY KEY,
    MaPhong     VARCHAR(50)  NULL,
    MaMon       VARCHAR(50)  NOT NULL,
    MaGiangVien VARCHAR(50)  NOT NULL,
    NgayHoc     DATE         NOT NULL DEFAULT CAST(GETDATE() AS DATE),
    ThuTrongTuan TINYINT     NULL,  
    Ca          NVARCHAR(10) NULL,  
    TietBatDau  TINYINT      NULL,  
    TietKetThuc TINYINT      NULL,  
    FOREIGN KEY (MaMon) REFERENCES MonHoc(MaMon) ON DELETE CASCADE,
    FOREIGN KEY (MaPhong) REFERENCES PhongHoc(MaPhong) ON DELETE CASCADE,
    FOREIGN KEY (MaGiangVien) REFERENCES GiangVien(MaGiangVien) 
);
GO

-- =========================================================
-- 9. BẢNG ĐIỂM DANH
-- =========================================================
CREATE TABLE DiemDanh (
    MaDiemDanh  INT IDENTITY(1,1) PRIMARY KEY,
    MaBuoiHoc   INT          NOT NULL,
    MaSV        VARCHAR(50)  NOT NULL,
    ThoiGianQuet DATETIME    NOT NULL DEFAULT GETDATE(),
    TrangThai   NVARCHAR(50) NOT NULL,  
    GhiChu      NVARCHAR(255) NULL,     
    FOREIGN KEY (MaBuoiHoc) REFERENCES BuoiHoc(MaBuoiHoc) ON DELETE CASCADE,
    FOREIGN KEY (MaSV)      REFERENCES SinhVien(MaSinhVien) ON DELETE CASCADE
);
GO
