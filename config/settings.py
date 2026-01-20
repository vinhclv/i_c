# config/settings.py
import os

# Đường dẫn gốc
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) 

# 👇 1. TẮT ORBITA
USE_ORBITA = False 

# 👇 2. CẤU HÌNH CHROME THẬT CỦA BẠN (Sửa lại tên User chỗ 'Admin' nhé)
# Đường dẫn Profile dữ liệu (QUAN TRỌNG)
LOCAL_PROFILE_PATH = r"C:\Users\Admin\AppData\Local\Google\Chrome\User Data\Profile 24"

# Đường dẫn file chạy Chrome (Thường là cố định thế này)
CHROME_EXE_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

# Link Gem
GEMINI_URL = "https://gemini.google.com/gem/1jugt5zshMZ6XtssXY5fgBL0tJne3HIT2?usp=sharing"

# Giữ lại mấy cái cũ để tránh lỗi import (dù ko dùng tới)
PROFILES_DIR = os.path.join(BASE_DIR, "profiles")
ORBITA_PATH = "" 
DRIVER_PATH = ""