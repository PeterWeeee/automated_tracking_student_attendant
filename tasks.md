# Kế hoạch Tái cấu trúc Dự án & Cập nhật Tài liệu

File này liệt kê các nhiệm vụ cần thực hiện để tổ chức lại dự án Hệ thống điểm danh sinh viên tự động. Các AI agent / model có thể đọc file này và tuần tự thực hiện từng bước dưới đây.

## 1. Cấu trúc lại thư mục
Mục tiêu: Đưa các file rải rác ở thư mục gốc vào các thư mục con tương ứng cho gọn gàng, nhưng **giữ nguyên hoặc đặt tên lại cho chuyên nghiệp** các thư mục quan trọng (`BAK`, `scripts`, `codeIOTdo`).

- [x] Tạo thư mục `src/` (hoặc `app/`) chứa mã nguồn Python chính:
  - Di chuyển `main_system.py` vào `src/`.
  - Di chuyển `face_tracker.py` vào `src/`.
  - Di chuyển `import_excel.py` vào `src/`.
  - Di chuyển thư mục `templates/` vào trong `src/`.
- [x] Tạo thư mục `data/` để chứa dữ liệu mẫu:
  - Di chuyển `danh_sach.xls` vào `data/`.
  - Di chuyển `minh.jpg` vào `data/`.
- [x] **KHÔNG XÓA** các thư mục sau (vì chứa code SQL/Arduino cần thiết cho phần cứng và Database):
  - `BAK/`: Chứa Database Backup.
  - `scripts/`: Chứa các script liên quan.
  - `codeIOTdo/`: Chứa code cho Arduino / ESP32.

## 2. Tạo file `requirements.txt`
Dự án cần file quản lý thư viện Python để cài đặt dễ dàng.
- [x] Tạo file `requirements.txt` tại thư mục gốc với nội dung:
```txt
Flask
pyodbc
face_recognition
numpy
opencv-python
requests
pandas
```

## 3. Cập nhật file `README.md`
- [x] Viết lại nội dung file `README.md` tại thư mục gốc để hướng dẫn người mới cách khởi chạy dự án:
  - **Giới thiệu:** Hệ thống điểm danh với AI + ESP32.
  - **Yêu cầu môi trường:** Python 3.8+, SQL Server, C++ Build Tools (cho dlib/face_recognition).
  - **Hướng dẫn cài đặt:** Lệnh tạo môi trường ảo, lệnh chạy `pip install -r requirements.txt`.
  - **Database & ESP32:** 
    - Khôi phục (restore) DB từ thư mục `BAK/`.
    - Chạy script trong `scripts/` (nếu có).
    - Nạp code Arduino từ thư mục `codeIOTdo/` vào ESP32.
    - Chạy file `src/import_excel.py` để nạp dữ liệu sinh viên.
  - **Hướng dẫn khởi chạy:** Chạy `python src/main_system.py` và truy cập `http://localhost:5000`.

## Lưu ý cho AI Agent thực thi
- Vui lòng đổi lại đường dẫn import và file data trong code Python (ví dụ trong `import_excel.py` phải trỏ đúng đến `data/danh_sach.xls`) sau khi cấu trúc lại thư mục.
