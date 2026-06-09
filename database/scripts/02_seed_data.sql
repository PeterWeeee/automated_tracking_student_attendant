USE IOT_QUANLYSINHVIEN;
GO

-- =========================================================
-- DỮ LIỆU MẦM (SEED DATA)
-- =========================================================

-- 1. NGƯỜI DÙNG (Giảng viên)
INSERT INTO NguoiDung (MaNguoiDung, MatKhau, TenDangNhap, VaiTro) VALUES
('GV01', '123456', 'GV01', 'GiangVien'),
('GV02', '123456', 'GV02', 'GiangVien'),
('GV03', '123456', 'GV03', 'GiangVien'),
('GV04', '123456', 'GV04', 'GiangVien');
GO

-- 2. GIẢNG VIÊN (Thông tin chi tiết)
INSERT INTO GiangVien (MaGiangVien, HoTen, Khoa, ChuyenNganh, Email, SDT, HocVi) VALUES
('GV01', N'Đinh Công Đoan',   N'CNTT', NULL, 'GV01@hcmute.edu.vn', '098*******', N'Thạc Sĩ'),
('GV02', N'Võ Lê Phúc Hậu',  N'CNTT', NULL, 'GV02@hcmute.edu.vn', '098*******', N'Thạc Sĩ'),
('GV03', N'Huỳnh Hạnh Dung', N'CNTT', NULL, 'GV03@hcmute.edu.vn', '098*******', N'Thạc Sĩ'),
('GV04', N'Bùi Mạnh Quân',   N'CNTT', NULL, 'GV04@hcmute.edu.vn', '098*******', N'Thạc Sĩ');
GO

-- 3. MÔN HỌC
INSERT INTO MonHoc (MaMon, TenMon, SoTC) VALUES
('INOT231780', N'Vạn Vật Kết Nối', 3),
('INSE330380', N'An toàn thông tin', 3),
('ENGL330001', N'Tiếng Anh Chuyên ngành', 3),
('ARIN330585', N'Trí tuệ nhân tạo', 3);
GO

-- 4. PHÒNG HỌC
INSERT INTO PhongHoc (MaPhong, TenPhong) VALUES
('A113', N'Phòng A113'),
('A2-401', N'Phòng A2-401'),
('A123', N'Phòng A123'),
('A2-502', N'Phòng A2-502'),
('E4-102', N'Phòng E4-102');
GO

-- 5. BUỔI HỌC
SET IDENTITY_INSERT BuoiHoc ON;
INSERT INTO BuoiHoc (MaBuoiHoc, MaPhong, MaMon, MaGiangVien, NgayHoc, ThuTrongTuan, Ca, TietBatDau, TietKetThuc) VALUES
(1, 'A113',   'INOT231780', 'GV01', CAST(GETDATE() AS DATE), 2, 'Sang',  1, 4),
(2, 'A2-401', 'INSE330380', 'GV02', CAST(GETDATE() AS DATE), 2, 'Chieu', 7, 10),
(3, 'A123',   'ENGL330001', 'GV03', CAST(GETDATE() AS DATE), 3, 'Sang',  1, 5),
(4, 'A2-502', 'ARIN330585', 'GV04', CAST(GETDATE() AS DATE), 3, 'Chieu', 7, 10),
(5, 'A113',   'INOT231780', 'GV01', CAST(GETDATE() AS DATE), 4, 'Sang',  1, 4),
(6, 'E4-102', 'INSE330380', 'GV02', CAST(GETDATE() AS DATE), 4, 'Chieu', 7, 10),
(7, 'A2-502', 'ARIN330585', 'GV04', CAST(GETDATE() AS DATE), 5, 'Chieu', 7, 10);
SET IDENTITY_INSERT BuoiHoc OFF;
GO