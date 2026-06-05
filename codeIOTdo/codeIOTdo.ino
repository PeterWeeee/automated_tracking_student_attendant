#include "esp_camera.h"
#include <WiFi.h>
#include "esp_http_server.h"
#include <Wire.h>
#include <LiquidCrystal_I2C.h> 

// ================= CẤU HÌNH HỆ THỐNG =================
const char* ssid = "Phong46";
const char* password = "53350596";

String ROOM_ID = "A113"; // <-- ĐỊNH DANH PHÒNG HỌC ĐỂ GỬI VỀ SERVER

int buzzerPin = 12; 
LiquidCrystal_I2C lcd(0x27, 16, 2); 
// ====================================================

#define PWDN_GPIO_NUM 32
#define RESET_GPIO_NUM -1
#define XCLK_GPIO_NUM 0
#define SIOD_GPIO_NUM 26
#define SIOC_GPIO_NUM 27
#define Y9_GPIO_NUM 35
#define Y8_GPIO_NUM 34
#define Y7_GPIO_NUM 39
#define Y6_GPIO_NUM 36
#define Y5_GPIO_NUM 21
#define Y4_GPIO_NUM 19
#define Y3_GPIO_NUM 18
#define Y2_GPIO_NUM 5
#define VSYNC_GPIO_NUM 25
#define HREF_GPIO_NUM 23
#define PCLK_GPIO_NUM 22

httpd_handle_t camera_httpd = NULL;

// CHẾ ĐỘ 1: CHỤP 1 TẤM ẢNH
static esp_err_t capture_handler(httpd_req_t *req) {
    camera_fb_t * fb = esp_camera_fb_get();
    if (!fb) return ESP_FAIL;
    
    // Thêm header chứa tên phòng học để Python biết ảnh này từ phòng nào gửi tới
    httpd_resp_set_hdr(req, "Room-ID", ROOM_ID.c_str());
    httpd_resp_set_type(req, "image/jpeg");
    
    esp_err_t res = httpd_resp_send(req, (const char *)fb->buf, fb->len);
    esp_camera_fb_return(fb);
    return res;
}

// CHẾ ĐỘ 2: MỞ CỬA & KÊU CÒI
static esp_err_t trigger_handler(httpd_req_t *req) {
    httpd_resp_send(req, "OK", HTTPD_RESP_USE_STRLEN); 
    
    lcd.clear();
    lcd.setCursor(0, 0); lcd.print("DIEM DANH HOP LE");
    lcd.setCursor(0, 1); lcd.print(" Xin moi vao!");

    for(int i = 0; i < 2; i++) {
        digitalWrite(buzzerPin, HIGH); delay(150);
        digitalWrite(buzzerPin, LOW);  delay(150);
    }
    
    delay(2500); 
    
    lcd.clear();
    lcd.setCursor(0, 0); lcd.print("PHONG HOC: " + ROOM_ID);
    lcd.setCursor(0, 1); lcd.print(" Vui long soi mat");
    
    return ESP_OK;
}

void setup() {
    Serial.begin(115200);
    Wire.begin(14, 15);
    
    lcd.init(); lcd.backlight();
    lcd.setCursor(0, 0); lcd.print(" Dang khoi dong");
    pinMode(buzzerPin, OUTPUT); digitalWrite(buzzerPin, LOW);

    camera_config_t config;
    config.ledc_channel = LEDC_CHANNEL_0; config.ledc_timer = LEDC_TIMER_0;
    config.pin_d0 = Y2_GPIO_NUM; config.pin_d1 = Y3_GPIO_NUM; config.pin_d2 = Y4_GPIO_NUM; config.pin_d3 = Y5_GPIO_NUM;
    config.pin_d4 = Y6_GPIO_NUM; config.pin_d5 = Y7_GPIO_NUM; config.pin_d6 = Y8_GPIO_NUM; config.pin_d7 = Y9_GPIO_NUM;
    config.pin_xclk = XCLK_GPIO_NUM; config.pin_pclk = PCLK_GPIO_NUM; config.pin_vsync = VSYNC_GPIO_NUM; config.pin_href = HREF_GPIO_NUM;
    config.pin_sscb_sda = SIOD_GPIO_NUM; config.pin_sscb_scl = SIOC_GPIO_NUM; config.pin_pwdn = PWDN_GPIO_NUM; config.pin_reset = RESET_GPIO_NUM;
    config.xclk_freq_hz = 20000000; config.frame_size = FRAMESIZE_QVGA; config.pixel_format = PIXFORMAT_JPEG; 
    config.grab_mode = CAMERA_GRAB_LATEST; config.fb_location = CAMERA_FB_IN_PSRAM; config.jpeg_quality = 12; config.fb_count = 2;

    esp_camera_init(&config);
    sensor_t * s = esp_camera_sensor_get();
    if (s != NULL) { s->set_vflip(s, 1); s->set_hmirror(s, 0); }
  
    // Đang kết nối Wi-Fi
    lcd.clear();
    lcd.setCursor(0, 0); lcd.print("Dang ket noi...");
    lcd.setCursor(0, 1); lcd.print(ssid);

    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) { delay(500); }

    // ========================================================
    // BÁO HIỆU THÀNH CÔNG: KÊU 2 TIẾNG BÍP BÍP
    // ========================================================
    for(int i = 0; i < 2; i++) {
        digitalWrite(buzzerPin, HIGH); delay(100);
        digitalWrite(buzzerPin, LOW);  delay(100);
    }

    Serial.println("\n=============================================");
    Serial.print("👉 KET NOI THANH CONG! COPY LINK NAY VAO PYTHON:\n");
    Serial.print("http://");
    Serial.println(WiFi.localIP());
    Serial.println("=============================================\n");

    httpd_config_t http_config = HTTPD_DEFAULT_CONFIG();
    http_config.server_port = 80; 
    
    httpd_uri_t cam_uri = { .uri = "/cam", .method = HTTP_GET, .handler = capture_handler, .user_ctx = NULL };
    httpd_uri_t open_uri = { .uri = "/open", .method = HTTP_GET, .handler = trigger_handler, .user_ctx = NULL };
    
    if (httpd_start(&camera_httpd, &http_config) == ESP_OK) {
        httpd_register_uri_handler(camera_httpd, &cam_uri);
        httpd_register_uri_handler(camera_httpd, &open_uri);
    }
    
    lcd.clear();
    lcd.setCursor(0, 0); lcd.print("PHONG HOC: " + ROOM_ID);
    lcd.setCursor(0, 1); lcd.print(" Vui long soi mat");
}

void loop() { delay(10000); }