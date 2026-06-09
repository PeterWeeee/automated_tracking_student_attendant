#include <WiFi.h>
#include <HTTPClient.h>
#include <SPI.h>
#include <MFRC522.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <WebServer.h>

// ================= CẤU HÌNH HỆ THỐNG =================
const char* ssid     = "Host_Ute";
const char* password = "12345678";
String      ROOM_ID  = "A113";

const char* backend_url = "http://192.168.137.1:5000/api/rfid-check";

// ================= CHÂN KẾT NỐI (PINOUT) =================
// LCD 16x2 I2C: SDA -> GPIO 21, SCL -> GPIO 22
LiquidCrystal_I2C lcd(0x27, 16, 2);

// Buzzer (thụ động 2 chân)
const int BUZZER_PIN = 12;

// RFID RC522 (SPI mặc định ESP32: SCK=18, MISO=19, MOSI=23, SS=5)
#define RST_PIN 4
#define SS_PIN  5
MFRC522 mfrc522(SS_PIN, RST_PIN);

// Web Server (nhận lệnh từ Backend)
WebServer server(80);

// ================= BIẾN TRẠNG THÁI NON-BLOCKING =================
// --- Buzzer state machine ---
bool          buzzerActive  = false;
int           buzzerStep    = 0;       // 0..1 = 2 tiếng bíp
unsigned long buzzerNextMs  = 0;

// --- Auto-reset màn hình LCD ---
bool          displayActive = false;
unsigned long displayEndMs  = 0;

// --- Debounce RFID ---
unsigned long lastRfidMs    = 0;
const unsigned long RFID_DEBOUNCE_MS = 1500;

// ================= HÀM HIỂN THỊ =================
void resetDisplay() {
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("PHONG: " + ROOM_ID);   // VD: "PHONG: A113"
    lcd.setCursor(0, 1);
    lcd.print("Quet the/Soi mat");
}

// Hiện kết quả quét lên LCD và bắt đầu buzzer non-blocking
void showScanResult(String method, String masv) {
    lcd.clear();

    // Dòng 1: "Quet mat: OK" hoặc "Quet the: OK"  (12 ký tự, vừa trong 16)
    lcd.setCursor(0, 0);
    if (method == "face") {
        lcd.print("Quet mat: OK");
    } else {
        lcd.print("Quet the: OK");
    }

    // Dòng 2: "MSSV:" + mã số (tối đa 16 ký tự tổng)
    lcd.setCursor(0, 1);
    String line2 = "MSSV:" + masv;
    if (line2.length() > 16) line2 = line2.substring(0, 16);
    lcd.print(line2);

    // Khởi động buzzer non-blocking (2 tiếng bíp)
    buzzerStep   = 0;
    buzzerActive = true;
    buzzerNextMs = millis();  // Bắt đầu ngay

    // Hẹn reset màn hình sau 3 giây
    displayActive = true;
    displayEndMs  = millis() + 3000;
}

// ================= XỬ LÝ HTTP /open (từ Backend gọi vào) =================
void handleOpen() {
    // Phản hồi Backend ngay lập tức, không chờ LCD/Buzzer xong
    server.send(200, "text/plain", "OK");

    String method = server.arg("method");
    String masv   = server.arg("masv");

    Serial.printf("[OPEN] method=%s  masv=%s\n", method.c_str(), masv.c_str());
    showScanResult(method, masv);
}

// ================= SETUP =================
void setup() {
    Serial.begin(115200);

    // LCD
    Wire.begin(21, 22);
    lcd.init();
    lcd.backlight();
    lcd.setCursor(0, 0);
    lcd.print(" Dang khoi dong");

    // Buzzer
    pinMode(BUZZER_PIN, OUTPUT);
    digitalWrite(BUZZER_PIN, LOW);

    // RFID
    SPI.begin();
    mfrc522.PCD_Init();
    delay(10);
    mfrc522.PCD_DumpVersionToSerial();

    // WiFi
    lcd.clear();
    lcd.setCursor(0, 0); lcd.print("Dang ket noi...");
    lcd.setCursor(0, 1); lcd.print(ssid);

    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }

    Serial.println("\n=============================================");
    Serial.print("ESP32-S IP: ");
    Serial.println(WiFi.localIP());
    Serial.println("Cap nhat IP nay vao config.py cua Backend!");
    Serial.println("=============================================\n");

    // Đăng ký endpoint và khởi động Web Server
    server.on("/open", handleOpen);
    server.begin();

    resetDisplay();
}

// ================= LOOP (NON-BLOCKING) =================
void loop() {
    // [1] Luôn xử lý HTTP request từ Backend trước tiên
    server.handleClient();

    unsigned long now = millis();

    // [2] State machine buzzer – không dùng delay()
    if (buzzerActive && now >= buzzerNextMs) {
        if (buzzerStep < 2) {
            tone(BUZZER_PIN, 2000, 150);   // Kêu 150ms ở 2kHz
            buzzerNextMs = now + 300;      // Lần kêu tiếp sau 300ms
            buzzerStep++;
        } else {
            noTone(BUZZER_PIN);
            buzzerActive = false;
        }
    }

    // [3] Auto-reset LCD – không dùng delay()
    if (displayActive && now >= displayEndMs) {
        displayActive = false;
        resetDisplay();
    }

    // [4] Debounce RFID (tránh đọc nhiều lần liên tiếp)
    if (now - lastRfidMs < RFID_DEBOUNCE_MS) return;

    // [5] Kiểm tra có thẻ RFID mới không
    if (!mfrc522.PICC_IsNewCardPresent()) return;
    if (!mfrc522.PICC_ReadCardSerial())   return;

    lastRfidMs = now;  // Ghi nhận thời điểm quét

    // Đọc UID
    String uid = "";
    for (byte i = 0; i < mfrc522.uid.size; i++) {
        uid += (mfrc522.uid.uidByte[i] < 0x10 ? "0" : "");
        uid += String(mfrc522.uid.uidByte[i], HEX);
    }
    uid.toUpperCase();

    // Dừng giao tiếp với thẻ hiện tại
    mfrc522.PICC_HaltA();
    mfrc522.PCD_StopCrypto1();

    Serial.printf("[RFID] Da quet UID: %s\n", uid.c_str());

    // [6] Gửi UID lên Backend qua HTTP POST
    if (WiFi.status() == WL_CONNECTED) {
        WiFiClient client;
        HTTPClient http;
        http.begin(client, backend_url);
        http.addHeader("Content-Type", "application/json");

        String postData = "{\"uid\":\"" + uid + "\",\"room_id\":\"" + ROOM_ID + "\"}";
        int httpCode = http.POST(postData);
        String payload = http.getString();
        Serial.printf("[RFID] HTTP %d: %s\n", httpCode, payload.c_str());
        
        if (httpCode != 200) {
            lcd.clear();
            lcd.setCursor(0, 0);
            lcd.print("Quet the: LOI!");
            lcd.setCursor(0, 1);
            if (httpCode == 404) lcd.print("The chua dang ky");
            else lcd.print("Loi he thong");
            
            tone(BUZZER_PIN, 1000, 1000); // Bíp dài 1s báo lỗi
            displayActive = true;
            displayEndMs = millis() + 3000;
        } else if (payload.indexOf("\"ignored\"") > 0) {
            lcd.clear();
            lcd.setCursor(0, 0);
            lcd.print("Quet the: LOI!");
            lcd.setCursor(0, 1);
            lcd.print("Da quet/Chua mo");
            
            tone(BUZZER_PIN, 1500, 200); // Bíp nhẹ báo ignore
            displayActive = true;
            displayEndMs = millis() + 3000;
        }

        http.end();
    } else {
        Serial.println("[RFID] WiFi mat ket noi!");
    }
}
