#include "esp_camera.h"
#include <WiFi.h>
#include "esp_http_server.h"

// ================= CẤU HÌNH HỆ THỐNG =================
const char* ssid = "Host_Ute";
const char* password = "12345678";

String ROOM_ID = "A113"; // <-- ĐỊNH DANH PHÒNG HỌC ĐỂ GỬI VỀ SERVER
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

static esp_err_t capture_handler(httpd_req_t *req) {
    camera_fb_t * fb = esp_camera_fb_get();
    if (!fb) {
        Serial.println("LỖI: Không thể chụp ảnh từ Camera!");
        httpd_resp_send_500(req);
        return ESP_FAIL;
    }
    
    // Thêm header chứa tên phòng học để Python biết ảnh này từ phòng nào gửi tới
    httpd_resp_set_hdr(req, "Room-ID", ROOM_ID.c_str());
    httpd_resp_set_type(req, "image/jpeg");
    
    esp_err_t res = httpd_resp_send(req, (const char *)fb->buf, fb->len);
    esp_camera_fb_return(fb);
    return res;
}

static esp_err_t stream_handler(httpd_req_t *req) {
    camera_fb_t * fb = NULL;
    esp_err_t res = ESP_OK;
    size_t _jpg_buf_len;
    uint8_t * _jpg_buf;
    char * part_buf[64];
    static const char* _STREAM_CONTENT_TYPE = "multipart/x-mixed-replace;boundary=123456789000000000000987654321";
    static const char* _STREAM_BOUNDARY = "\r\n--123456789000000000000987654321\r\n";
    static const char* _STREAM_PART = "Content-Type: image/jpeg\r\nContent-Length: %u\r\n\r\n";

    res = httpd_resp_set_type(req, _STREAM_CONTENT_TYPE);
    if(res != ESP_OK){ return res; }

    while(true){
        fb = esp_camera_fb_get();
        if (!fb) { res = ESP_FAIL; break; }
        _jpg_buf_len = fb->len;
        _jpg_buf = fb->buf;
        
        if(res == ESP_OK){
            res = httpd_resp_send_chunk(req, _STREAM_BOUNDARY, strlen(_STREAM_BOUNDARY));
        }
        if(res == ESP_OK){
            size_t hlen = snprintf((char *)part_buf, 64, _STREAM_PART, _jpg_buf_len);
            res = httpd_resp_send_chunk(req, (const char *)part_buf, hlen);
        }
        if(res == ESP_OK){
            res = httpd_resp_send_chunk(req, (const char *)_jpg_buf, _jpg_buf_len);
        }
        esp_camera_fb_return(fb);
        if(res != ESP_OK){ break; }
    }
    return res;
}

void setup() {
    Serial.begin(115200);

    camera_config_t config;
    config.ledc_channel = LEDC_CHANNEL_0; config.ledc_timer = LEDC_TIMER_0;
    config.pin_d0 = Y2_GPIO_NUM; config.pin_d1 = Y3_GPIO_NUM; config.pin_d2 = Y4_GPIO_NUM; config.pin_d3 = Y5_GPIO_NUM;
    config.pin_d4 = Y6_GPIO_NUM; config.pin_d5 = Y7_GPIO_NUM; config.pin_d6 = Y8_GPIO_NUM; config.pin_d7 = Y9_GPIO_NUM;
    config.pin_xclk = XCLK_GPIO_NUM; config.pin_pclk = PCLK_GPIO_NUM; config.pin_vsync = VSYNC_GPIO_NUM; config.pin_href = HREF_GPIO_NUM;
    config.pin_sscb_sda = SIOD_GPIO_NUM; config.pin_sscb_scl = SIOC_GPIO_NUM; config.pin_pwdn = PWDN_GPIO_NUM; config.pin_reset = RESET_GPIO_NUM;
    config.xclk_freq_hz = 20000000; config.frame_size = FRAMESIZE_QVGA; config.pixel_format = PIXFORMAT_JPEG; 
    config.grab_mode = CAMERA_GRAB_LATEST; config.fb_location = CAMERA_FB_IN_PSRAM; config.jpeg_quality = 10; config.fb_count = 2;

    esp_err_t err = esp_camera_init(&config);
    if (err != ESP_OK) {
        Serial.printf("LỖI KHỞI TẠO CAMERA: 0x%x\n", err);
        Serial.println("-> Kiem tra lai cap nguon hoac day cáp camera!");
        return;
    }
    Serial.println("Camera khoi tao thanh cong!");
    
    sensor_t * s = esp_camera_sensor_get();
    if (s != NULL) { s->set_vflip(s, 1); s->set_hmirror(s, 0); }
  
    Serial.println("Dang ket noi WiFi...");

    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) { delay(500); }

    Serial.println("\n=============================================");
    Serial.print("👉 ESP32-CAM KET NOI THANH CONG! COPY LINK NAY VAO PYTHON:\n");
    Serial.print("http://");
    Serial.println(WiFi.localIP());
    Serial.println("=============================================\n");

    httpd_config_t http_config = HTTPD_DEFAULT_CONFIG();
    http_config.server_port = 80; 
    
    httpd_uri_t cam_uri = { .uri = "/cam", .method = HTTP_GET, .handler = capture_handler, .user_ctx = NULL };
    
    if (httpd_start(&camera_httpd, &http_config) == ESP_OK) {
        httpd_register_uri_handler(camera_httpd, &cam_uri);
    }

    httpd_handle_t stream_httpd = NULL;
    httpd_config_t stream_config = HTTPD_DEFAULT_CONFIG();
    stream_config.server_port = 81;
    stream_config.ctrl_port += 1; // Sửa lỗi khởi tạo 2 HTTP server cùng lúc
    httpd_uri_t stream_uri = { .uri = "/stream", .method = HTTP_GET, .handler = stream_handler, .user_ctx = NULL };
    
    if (httpd_start(&stream_httpd, &stream_config) == ESP_OK) {
        httpd_register_uri_handler(stream_httpd, &stream_uri);
    }
}

void loop() { delay(10000); }
