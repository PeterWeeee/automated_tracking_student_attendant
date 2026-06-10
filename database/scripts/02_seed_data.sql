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

-- 5. BUỔI HỌC (4 TUẦN - TỪ 08/06/2026 ĐẾN 05/07/2026)
SET IDENTITY_INSERT BuoiHoc ON;
INSERT INTO BuoiHoc (MaBuoiHoc, MaPhong, MaMon, MaGiangVien, NgayHoc, ThuTrongTuan, Ca, TietBatDau, TietKetThuc) VALUES
-- Tuần 1 (08/06 - 14/06)
(1, 'A113',   'INOT231780', 'GV01', '2026-06-08', 2, 'Sang',  1, 4),
(2, 'A2-401', 'INSE330380', 'GV02', '2026-06-08', 2, 'Chieu', 7, 10),
(3, 'A123',   'ENGL330001', 'GV03', '2026-06-09', 3, 'Sang',  1, 5),
(4, 'A2-502', 'ARIN330585', 'GV04', '2026-06-09', 3, 'Chieu', 7, 10),
(5, 'A113',   'INOT231780', 'GV01', '2026-06-10', 4, 'Sang',  1, 4),
(6, 'E4-102', 'INSE330380', 'GV02', '2026-06-10', 4, 'Chieu', 7, 10),
(7, 'A2-502', 'ARIN330585', 'GV04', '2026-06-11', 5, 'Chieu', 7, 10),
-- Tuần 2 (15/06 - 21/06)
(8, 'A113',   'INOT231780', 'GV01', '2026-06-15', 2, 'Sang',  1, 4),
(9, 'A2-401', 'INSE330380', 'GV02', '2026-06-15', 2, 'Chieu', 7, 10),
(10, 'A123',   'ENGL330001', 'GV03', '2026-06-16', 3, 'Sang',  1, 5),
(11, 'A2-502', 'ARIN330585', 'GV04', '2026-06-16', 3, 'Chieu', 7, 10),
(12, 'A113',   'INOT231780', 'GV01', '2026-06-17', 4, 'Sang',  1, 4),
(13, 'E4-102', 'INSE330380', 'GV02', '2026-06-17', 4, 'Chieu', 7, 10),
(14, 'A2-502', 'ARIN330585', 'GV04', '2026-06-18', 5, 'Chieu', 7, 10),
-- Tuần 3 (22/06 - 28/06)
(15, 'A113',   'INOT231780', 'GV01', '2026-06-22', 2, 'Sang',  1, 4),
(16, 'A2-401', 'INSE330380', 'GV02', '2026-06-22', 2, 'Chieu', 7, 10),
(17, 'A123',   'ENGL330001', 'GV03', '2026-06-23', 3, 'Sang',  1, 5),
(18, 'A2-502', 'ARIN330585', 'GV04', '2026-06-23', 3, 'Chieu', 7, 10),
(19, 'A113',   'INOT231780', 'GV01', '2026-06-24', 4, 'Sang',  1, 4),
(20, 'E4-102', 'INSE330380', 'GV02', '2026-06-24', 4, 'Chieu', 7, 10),
(21, 'A2-502', 'ARIN330585', 'GV04', '2026-06-25', 5, 'Chieu', 7, 10),
-- Tuần 4 (29/06 - 05/07)
(22, 'A113',   'INOT231780', 'GV01', '2026-06-29', 2, 'Sang',  1, 4),
(23, 'A2-401', 'INSE330380', 'GV02', '2026-06-29', 2, 'Chieu', 7, 10),
(24, 'A123',   'ENGL330001', 'GV03', '2026-06-30', 3, 'Sang',  1, 5),
(25, 'A2-502', 'ARIN330585', 'GV04', '2026-06-30', 3, 'Chieu', 7, 10),
(26, 'A113',   'INOT231780', 'GV01', '2026-07-01', 4, 'Sang',  1, 4),
(27, 'E4-102', 'INSE330380', 'GV02', '2026-07-01', 4, 'Chieu', 7, 10),
(28, 'A2-502', 'ARIN330585', 'GV04', '2026-07-02', 5, 'Chieu', 7, 10);
SET IDENTITY_INSERT BuoiHoc OFF;
GO