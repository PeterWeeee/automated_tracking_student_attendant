# 🎓 Hệ thống Điểm danh Sinh viên Tự động (IoT + AI)

Hệ thống nhận diện khuôn mặt kết hợp thẻ RFID thông qua ESP32 để điểm danh sinh viên tự động trong môi trường lớp học. Giảng viên có thể theo dõi danh sách điểm danh trực tiếp qua giao diện web, trong khi sinh viên có thể xem lịch sử điểm danh của mình.

---

## 🗂️ Cấu trúc thư mục

```
automated_tracking_student_attendant/
├── src/                    # Mã nguồn Python chính
│   ├── app.py              # Flask web server (điểm khởi chạy)
│   ├── routes/             # Cấu hình Web và API
│   ├── services/           # Xử lý Logic (AI Worker)
│   └── templates/          # Giao diện HTML
├── data/                   # Dữ liệu mẫu
│   └── danh_sach.xls       # File danh sách sinh viên
├── database/               # Database Scripts
│   ├── scripts/            # Script tạo bảng và seed data
│   └── backups/            # Backup Database (nếu có)
├── hardware/               # Code Arduino/ESP32 cho phần cứng
│   └── esp32_rfid_firmware/
├── requirements.txt        # Danh sách thư viện Python
└── README.md
```

---

## 🔌 Yêu cầu Phần cứng & Sơ đồ nối dây

### Linh kiện cần thiết
1. **NodeMCU-32 (ESP32-S)**: Vi điều khiển chính xử lý thẻ RFID, xuất tín hiệu màn hình, còi bíp, và giao tiếp HTTP với Backend.
2. **ESP32-CAM**: Stream video liên tục (qua MJPEG port 81) về cho Server Python xử lý AI.
3. **Màn hình LCD 16x2 I2C**: Hiển thị thông báo trạng thái và mã sinh viên quét thành công.
4. **Module RFID RC522**: Đọc thẻ từ RFID của sinh viên.
5. **Còi Buzzer (Thụ động)**: Phát âm thanh thông báo "bíp" khi nhận diện thành công.

### Sơ đồ nối dây (Với ESP32-S / NodeMCU-32)
| Linh kiện | Chân trên Module | Chân trên ESP32 | Ghi chú |
|---|---|---|---|
| **LCD 16x2 I2C** | SDA | GPIO 21 | Cấp nguồn 5V/3.3V tùy theo module |
| | SCL | GPIO 22 | |
| **Buzzer** | Dương (+) | GPIO 12 | Tín hiệu PWM/Tone |
| | Âm (-) | GND | |
| **RFID RC522** | SCK | GPIO 18 | Giao tiếp SPI (Hardware) |
| | MISO | GPIO 19 | |
| | MOSI | GPIO 23 | |
| | SS / SDA | GPIO 5 | |
| | RST | GPIO 4 | |
| | 3.3V | 3.3V | **Tuyệt đối không cấp nguồn 5V cho RC522** |

*(ESP32-CAM hoạt động độc lập, chỉ cần cấp nguồn 5V, nạp code stream MJPEG và kết nối chung mạng Wi-Fi với ESP32-S và máy chủ AI).*

---

## ⚙️ Yêu cầu môi trường

| Thành phần | Phiên bản tối thiểu |
|---|---|
| Python | 3.8+ |
| SQL Server | 2017+ |
| Visual C++ Build Tools | 2019+ (cần để build thư viện `dlib` / `face_recognition`) |

> **Lưu ý:** Thư viện `face_recognition` yêu cầu cài đặt phần mềm **Microsoft C++ Build Tools** trước khi cài đặt. Tải tại: https://visualstudio.microsoft.com/visual-cpp-build-tools/

---

## 🚀 Hướng dẫn cài đặt và sử dụng

### 1. Cài đặt mã nguồn

```bash
git clone <URL_REPO>
cd automated_tracking_student_attendant
```

Tạo môi trường ảo và cài đặt thư viện:
```bash
python -m venv .venv

# Trên Windows
.venv\Scripts\activate
# Trên Linux/macOS
source .venv/bin/activate

# Cài đặt thư viện
pip install -r requirements.txt
```

### 2. Thiết lập Database
1. Mở **SQL Server Management Studio (SSMS)**.
2. Mở file `database/scripts/01_schema_create.sql` và chạy (Execute) để khởi tạo Database `IOT_QUANLYSINHVIEN` và các bảng.
3. Mở file `database/scripts/02_seed_data.sql` và chạy để đưa dữ liệu mẫu (hoặc tài khoản giáo viên) vào hệ thống.
4. Kiểm tra chuỗi kết nối `CONN_STR` trong `src/config.py` để đảm bảo kết nối đúng SQL Server cục bộ.

### 3. Nạp code và cấu hình Hardware
1. Mở **Arduino IDE**.
2. Nạp code cho ESP32-CAM và ghi nhớ IP của camera.
3. Nạp code `hardware/esp32_rfid_firmware/esp32_rfid_firmware.ino` vào mạch ESP32-S. 
   - Thay đổi thông tin wifi `ssid` và `password` trong code.
   - Thay đổi IP `backend_url` trỏ về IP của máy chủ chạy Python.
4. Sau khi nạp, ghi chú IP của ESP32-CAM và ESP32-S. Vào file `src/config.py`, cập nhật:
   ```python
   IP_ESP32_CAM = "192.168.x.x"
   IP_ESP32_S = "192.168.x.y"
   ```

### 4. Khởi chạy hệ thống Web Server và AI

Mở terminal ở thư mục gốc của project và chạy lệnh:
```bash
python -X utf8 -m src.app
```
*Ghi chú: Lệnh `-X utf8` giúp hiển thị Tiếng Việt trong console không bị lỗi font.*

Truy cập trang quản trị web:
```
http://localhost:5000
```
- **Tài khoản Giảng Viên**: Sử dụng tài khoản đã thêm trong `02_seed_data.sql` (VD: GV01 / 123456).
- **Tài khoản Sinh Viên**: Mã SV / 123456 (Sinh viên sẽ tự cập nhật ảnh khuôn mặt AI và mã thẻ RFID sau khi đăng nhập).

---

## 📖 Luồng hoạt động

```text
[ESP32-CAM] --(Stream MJPEG)--> [Flask Server (AI Thread)] <--(Giao diện Web Giảng Viên)
                                        |
                                 (So sánh Khuôn Mặt)
                                        v
                                 [SQL Server DB]
                                        ^
                                 (Truy vấn Thẻ)
                                        |
[MFRC522 RFID] --(Đọc Thẻ)--> [ESP32-S NodeMCU]
```

1. **AI Khuôn Mặt**: Giảng viên bấm "Bắt đầu" điểm danh trên web, hệ thống tự động kéo stream từ ESP32-CAM để nhận diện, điểm danh sinh viên tự động.
2. **Thẻ RFID**: Sinh viên quẹt thẻ vào module RC522. ESP32-S gửi mã thẻ về Backend để xác thực. Backend ghi nhận trạng thái điểm danh và gửi lệnh phản hồi lại cho ESP32-S kêu bíp và hiển thị LCD.
3. Sinh viên có thể đăng nhập trên Web để tải ảnh khuôn mặt của mình lên và xem lịch sử điểm danh các môn học.
