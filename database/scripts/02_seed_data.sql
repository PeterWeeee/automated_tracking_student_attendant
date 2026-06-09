USE IOT_QUANLYSINHVIEN;
GO

-- =========================================================
-- DỮ LIỆU MẦM (SEED DATA)
-- =========================================================

-- 1. GIẢNG VIÊN
INSERT INTO NguoiDung (MaNguoiDung, MatKhau, HoTen, VaiTro) VALUES
('GV01', '123456', N'Đinh Công Đoan',   'GiangVien'),
('GV02', '123456', N'Võ Lê Phúc Hậu',  'GiangVien'),
('GV03', '123456', N'Huỳnh Hạnh Dung', 'GiangVien'),
('GV04', '123456', N'Bùi Mạnh Quân',   'GiangVien');
GO

-- 2. LỚP HỌC PHẦN
INSERT INTO LopHocPhan (MaLop, TenMonHoc, MaMon, SoTC, NamHoc, HocKy, MaGV) VALUES
('241102B',   N'Vạn Vật Kết Nối',         'INOT231780', 3, '2024-2025', 1, 'GV01'),
('241104B',   N'An toàn thông tin',       'INSE330380', 3, '2024-2025', 1, 'GV02'),
('241101C',   N'Tiếng Anh Chuyên ngành',  'ENGL330001', 2, '2024-2025', 1, 'GV03'),
('24110CTNA', N'Trí tuệ nhân tạo',        'ARIN330585', 3, '2024-2025', 2, 'GV04');
GO

-- 3. BUỔI HỌC
SET IDENTITY_INSERT BuoiHoc ON;
INSERT INTO BuoiHoc (MaBuoiHoc, MaLop, NgayHoc, ThuTrongTuan, Ca, TietBatDau, TietKetThuc, Phong) VALUES
(1, '241102B',   CAST(GETDATE() AS DATE), 2, 'Sang',  1, 4,  'A113'),
(2, '241104B',   CAST(GETDATE() AS DATE), 2, 'Chieu', 7, 10, 'A2-401'),
(3, '241101C',   CAST(GETDATE() AS DATE), 3, 'Sang',  1, 5,  'A123'),
(4, '24110CTNA', CAST(GETDATE() AS DATE), 3, 'Chieu', 7, 10, 'A2-502'),
(5, '241102B',   CAST(GETDATE() AS DATE), 4, 'Sang',  1, 4,  'A113'),
(6, '241104B',   CAST(GETDATE() AS DATE), 4, 'Chieu', 7, 10, 'E4-102'),
(7, '24110CTNA', CAST(GETDATE() AS DATE), 5, 'Chieu', 7, 10, 'A2-502');
SET IDENTITY_INSERT BuoiHoc OFF;
GO