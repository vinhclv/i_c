import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

# Import các biến từ settings
from config.settings import (
    USE_ORBITA, 
    ORBITA_PATH, 
    DRIVER_PATH, 
    LOCAL_PROFILE_PATH, 
    CHROME_EXE_PATH
)

def init_driver(user_data_dir=None):
    print("🔧 Đang khởi tạo trình duyệt...")
    
    options = Options()
    
    # Các setting giúp chạy mượt, tránh bị Google phát hiện tool
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("--start-maximized")

    # ==================================================
    # TRƯỜNG HỢP 1: DÙNG CHROME THẬT CỦA BẠN
    # ==================================================
    if not USE_ORBITA:
        print("🌐 MODE: CHROME THẬT (Local Browser)")
        print("⚠️  LƯU Ý: Vui lòng TẮT HẾT cửa sổ Chrome trước khi chạy!")
        
        # Trỏ vào file exe Chrome thật
        options.binary_location = CHROME_EXE_PATH
        
        # Trỏ vào Profile thật (để lấy cookie đã login)
        # Lưu ý: Chrome thật dùng folder 'Default' bên trong User Data, 
        # nên ta trỏ đến folder cha là 'User Data' thôi.
        options.add_argument(f"--user-data-dir={LOCAL_PROFILE_PATH}")
        options.add_argument("--profile-directory=Default") # Dùng profile chính
        
        try:
            # Chrome thường thì Selenium tự tải driver, không cần Service cứng
            driver = webdriver.Chrome(options=options)
            return driver
        except Exception as e:
            print(f"❌ Lỗi mở Chrome thật: {e}")
            print("👉 Bạn đã tắt hết cửa sổ Chrome chưa?")
            return None

    # ==================================================
    # TRƯỜNG HỢP 2: DÙNG ORBITA (Code cũ)
    # ==================================================
    else:
        print("🚀 MODE: ORBITA Browser")
        options.binary_location = ORBITA_PATH
        if user_data_dir:
            options.add_argument(f"--user-data-dir={user_data_dir}")
        
        try:
            service = Service(executable_path=DRIVER_PATH)
            driver = webdriver.Chrome(service=service, options=options)
            return driver
        except Exception as e:
            print(f"❌ Lỗi mở Orbita: {e}")
            return None