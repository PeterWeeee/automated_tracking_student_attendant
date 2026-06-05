import os

class Config:
    SECRET_KEY = 'ute_iot_secret_key'
    
    # Database config
    CONN_STR = (
        r'DRIVER={ODBC Driver 17 for SQL Server};'
        r'SERVER=localhost;'
        r'DATABASE=IOT_QUANLYSINHVIEN;'
        r'Trusted_Connection=yes;'
    )
    
    # Hardware config
    IP_ESP32 = "192.168.46.103"
    
    # Paths
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
    STATIC_DIR = os.path.join(BASE_DIR, 'static')
