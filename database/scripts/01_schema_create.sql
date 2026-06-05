-- =========================================================
-- IOT_QUANLYSINHVIEN — SCHEMA (Phiên bản 2.0)
-- Chỉ định nghĩa cấu trúc bảng
-- =========================================================

-- 1. TẠO CƠ SỞ DỮ LIỆU
IF NOT EXISTS (SELECT name FROM master.dbo.sysdatabases WHERE name = N'IOT_QUANLYSINHVIEN')
BEGIN
    CREATE DATABASE IOT_QUANLYSINHVIEN;
END
GO

USE IOT_QUANLYSINHVIEN;
GO

-- Xoá bảng cũ nếu tồn tại (để rebuild)
IF OBJECT_ID('DiemDanh', 'U') IS NOT NULL DROP TABLE DiemDanh;
IF OBJECT_ID('BuoiHoc', 'U') IS NOT NULL DROP TABLE BuoiHoc;
IF OBJECT_ID('DanhSachLop', 'U') IS NOT NULL DROP TABLE DanhSachLop;
IF OBJECT_ID('LopHocPhan', 'U') IS NOT NULL DROP TABLE LopHocPhan;
IF OBJECT_ID('NguoiDung', 'U') IS NOT NULL DROP TABLE NguoiDung;
GO

-- =========================================================
-- 2. BẢNG NGƯỜI DÙNG
-- =========================================================
CREATE TABLE NguoiDung (
    MaNguoiDung VARCHAR(50)  PRIMARY KEY,     -- MSSV hoặc Mã GV
    MatKhau     VARCHAR(255) NOT NULL,         
    HoTen       NVARCHAR(255) NOT NULL,        
    VaiTro      VARCHAR(20)  NOT NULL CHECK (VaiTro IN ('SinhVien', 'GiangVien')),
    KhuonMatData NVARCHAR(MAX) NULL            
);
GO

-- =========================================================
-- 3. BẢNG LỚP HỌC PHẦN
-- =========================================================
CREATE TABLE LopHocPhan (
    MaLop     VARCHAR(50)   PRIMARY KEY,      
    TenMonHoc NVARCHAR(255) NOT NULL,          
    MaMon     VARCHAR(50)   NULL,             
    MaGV      VARCHAR(50)   NULL,             
    CONSTRAINT FK_LopHocPhan_GV
        FOREIGN KEY (MaGV) REFERENCES NguoiDung(MaNguoiDung)
);
GO

-- =========================================================
-- 4. BẢNG DANH SÁCH LỚP
-- =========================================================
CREATE TABLE DanhSachLop (
    MaLop VARCHAR(50) NOT NULL,
    MaSV  VARCHAR(50) NOT NULL,
    PRIMARY KEY (MaLop, MaSV),
    FOREIGN KEY (MaLop) REFERENCES LopHocPhan(MaLop) ON DELETE CASCADE,
    FOREIGN KEY (MaSV)  REFERENCES NguoiDung(MaNguoiDung) ON DELETE CASCADE
);
GO

-- =========================================================
-- 5. BẢNG BUỔI HỌC
-- =========================================================
CREATE TABLE BuoiHoc (
    MaBuoiHoc   INT IDENTITY(1,1) PRIMARY KEY,
    MaLop       VARCHAR(50)  NOT NULL,
    NgayHoc     DATE         NOT NULL DEFAULT CAST(GETDATE() AS DATE),
    ThuTrongTuan TINYINT     NULL,  
    Ca          NVARCHAR(10) NULL,  
    TietBatDau  TINYINT      NULL,  
    TietKetThuc TINYINT      NULL,  
    Phong       NVARCHAR(50) NULL,  
    FOREIGN KEY (MaLop) REFERENCES LopHocPhan(MaLop) ON DELETE CASCADE
);
GO

-- =========================================================
-- 6. BẢNG ĐIỂM DANH
-- =========================================================
CREATE TABLE DiemDanh (
    MaDiemDanh  INT IDENTITY(1,1) PRIMARY KEY,
    MaBuoiHoc   INT          NOT NULL,
    MaSV        VARCHAR(50)  NOT NULL,
    ThoiGianQuet DATETIME    NOT NULL DEFAULT GETDATE(),
    TrangThai   NVARCHAR(50) NOT NULL,  
    GhiChu      NVARCHAR(255) NULL,     
    FOREIGN KEY (MaBuoiHoc) REFERENCES BuoiHoc(MaBuoiHoc) ON DELETE CASCADE,
    FOREIGN KEY (MaSV)      REFERENCES NguoiDung(MaNguoiDung) ON DELETE CASCADE
);
GO
