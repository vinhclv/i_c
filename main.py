# run_local.py
import time
from utils.selenium_test import init_driver
from config.settings import GEMINI_URL

print("--- CHẠY TEST TRÊN CHROME CỦA TÔI ---")

# Gọi hàm init không cần tham số, nó sẽ tự lấy LOCAL_PROFILE_PATH trong settings
driver = init_driver()

if driver:
    print(f"🌍 Vào Gem: {GEMINI_URL}")
    driver.get(GEMINI_URL)
    
    print("\n✅ Đã mở trình duyệt!")
    print("Hãy kiểm tra xem nó có vào thẳng Gem mà không cần login không?")
    
    input("Bấm Enter để tắt...")
    driver.quit()
else:
    print("❌ Thất bại. Nhớ tắt hết Chrome trước khi chạy nhé!")