# run_local.py
import time
import os,sys
import pyautogui
import pyperclip
import platform
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.selenium_test import init_driver
from utils.file_loader import get_file_batches
from config.settings import GEMINI_URL

# --- CẤU HÌNH ĐƯỜNG DẪN DỮ LIỆU ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_ASSETS_DIR = os.path.join(BASE_DIR, "data", "outputzip") # Chỗ để zip
DATA_SRT_DIR = os.path.join(BASE_DIR,"srt")              # Chỗ để srt
IMAGES_SRT_PATH = os.path.join(DATA_SRT_DIR, "images.srt")

# Selector của Gemini (Cập nhật mới nhất)
# SELECTORS = {
#     "FILE_INPUT": "input[type='file']",
#     "PLUS_BUTTON": "button[aria-label*='Upload'], button[aria-label*='Thêm'], mat-icon[data-mat-icon-name='add']",
#     # Chọn phần tử hiển thị file đã upload (để chờ nó load xong)
#     "UPLOAD_PREVIEW": "div[aria-label*='Preview'], img[src*='blob:'], button[aria-label*='Remove file']",
#     "INPUT_BOX": "div[contenteditable='true'], div[role='textbox']",
#     "SEND_BUTTON": "button.send-button, button[aria-label='Gửi tin nhắn']",
#     "RESPONSE": "model-response" # Thẻ chứa câu trả lời
# }

# Trong file core/imgsrt_prc.py (hoặc run_local.py)

def wait_until_all_files_uploaded(driver, expected, timeout=180):
    wait = WebDriverWait(driver, timeout)

    def _enough(drv):
        items = drv.find_elements(By.CSS_SELECTOR,
            "button[aria-label*='Remove'], button[aria-label*='Xóa'], div.file-preview, img[src^='blob:']"
        )
        return len(items) >= expected

    wait.until(_enough)
    print(f"✅ Detected {expected} uploaded files on UI")

def append_images_srt(text):
    os.makedirs(os.path.dirname(IMAGES_SRT_PATH), exist_ok=True)

    blocks = []
    for line in text.splitlines():
        l = line.strip()
        if not l:
            continue
        blocks.append(l)

    formatted = "\n\n".join(blocks)

    with open(IMAGES_SRT_PATH, "a", encoding="utf-8") as f:
        f.write(formatted + "\n\n")


def upload_and_run(driver, file_list, batch_index):
    wait = WebDriverWait(driver, 60)
    
    print(f"\n--- 📦 ĐANG XỬ LÝ BATCH {batch_index} ---")
    print(f"➡️ Số lượng file: {len(file_list)}")
    
    try:
        # 1. Đợi trang load ổn định
        print("⏳ Đang đợi trang web load...")
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[contenteditable='true']")))
        time.sleep(2) 

        print("📂 Kích hoạt upload UI...")

        # Đảm bảo không còn dialog OS nào
        pyautogui.press("esc")
        time.sleep(0.3)

        # Click dấu +
        plus_btn = wait.until(EC.element_to_be_clickable((
            By.CSS_SELECTOR,
            "button.upload-card-button, button[aria-label*='Upload'], mat-icon[data-mat-icon-name='add']"
        )))
        driver.execute_script("arguments[0].scrollIntoView(true);", plus_btn)
        plus_btn.click()

        # Đợi menu upload hiện
        upload_btn = wait.until(EC.element_to_be_clickable((
            By.XPATH,
                "//*[self::button or self::span][contains(normalize-space(.),'Tải') or contains(normalize-space(.),'Upload')]"
        )))

        # Click thật
        driver.execute_script("arguments[0].scrollIntoView(true);", upload_btn)
        upload_btn.click()

        # Đóng cửa sổ Windows Open
        time.sleep(0.4)
        pyautogui.press("esc")

        # Đợi input render xong
        file_input = wait.until(EC.presence_of_element_located((
            By.CSS_SELECTOR,
            "input[type='file']"
        )))


        # 3. Gửi đường dẫn file
        print(f"📤 Đang bắn {len(file_list)} file vào hệ thống...")
        all_paths = "\n".join(file_list) 
        file_input.send_keys(all_paths) # <--- CHÌA KHÓA LÀ Ở ĐÂY
        
        # 4. CHỜ FILE LOAD
        print("⏳ Đang chờ Gemini xử lý file...")
        # Đợi các thẻ đại diện cho file hiện lên (thường là mat-chip hoặc img preview)
        # Sửa selector để bắt dính chuẩn hơn
        wait_until_all_files_uploaded(driver, len(file_list))
        time.sleep(2)
        
        real = len(driver.find_elements(By.CSS_SELECTOR,
            "button[aria-label*='Remove'], button[aria-label*='Xóa'], div.file-preview, img[src^='blob:']"
        ))
        print("📊 UI file count:", real)

        print("✅ Upload thành công (đã thấy file trên UI)!")

        # 5. Gửi lệnh Prompt
        prompt_text = f"RUN GEM ENGINE - BATCH {batch_index}"
        
        input_box = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div[contenteditable='true']")))
        input_box.click() # Click để focus
        time.sleep(0.5)
        
        # Cách nhập liệu an toàn để trigger nút gửi sáng lên
        input_box.send_keys(prompt_text)
        time.sleep(1)
        
        old_count = len(driver.find_elements(
            By.CSS_SELECTOR,
            "div.markdown-main-panel[id^='model-response-message-content']"
        ))

        
        # 6. Bấm Gửi
        print("🚀 Đang bấm gửi...")
        
        # Tìm nút gửi (đôi khi nó disable nếu chưa nhận text, ta đợi nó enable)
        send_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.send-button, button[aria-label*='Submit'], button[aria-label*='Gửi']")))
        
        # Dùng JS click cho chắc chắn nếu bị overlay che
        driver.execute_script("arguments[0].click();", send_btn)
        
        print("⏳ Đã gửi lệnh. Đang đợi Gem trả lời...")
        
        # 7. Đợi trả lời xong
        # Logic: Đợi nút gửi biến mất (đang loading) rồi đợi nó hiện lại (đã xong)
        print("⏳ Đang đợi Gemini trả lời xong...")

        # 1. Đợi response mới xuất hiện
        WebDriverWait(driver, 120).until(lambda d: len(
            d.find_elements(By.CSS_SELECTOR, "div.markdown-main-panel[id^='model-response-message-content']")
        ) > old_count)

        # 2. Lấy response mới nhất
        responses = driver.find_elements(
            By.CSS_SELECTOR,
            "div.markdown-main-panel[id^='model-response-message-content']"
        )
        el = responses[-1]

        stable_time = 0
        last_text = ""

        while stable_time < 3:
            time.sleep(1)

            busy = el.get_attribute("aria-busy")
            current_text = el.text.strip()

            if busy == "false" and current_text == last_text and current_text != "":
                stable_time += 1
            else:
                stable_time = 0
                last_text = current_text

        print("✅ Gemini đã ngừng viết 3s, tiếp tục batch.")

        # --- SAVE RESULT ---
        raw_text = el.text.strip()

        clean_lines = []
        for line in raw_text.splitlines():
            l = line.strip()
            if not l:
                continue
            if l.lower().startswith("would you like"):
                break
            clean_lines.append(l)

        result_text = "\n".join(clean_lines)

        print("💾 Ghi kết quả vào srt/images.srt ...")
        append_images_srt(result_text)
        print("✅ Đã lưu batch", batch_index)

   
        print("🎉 Batch này đã xong!")
        return True

    except Exception as e:
        print(f"❌ Lỗi: {e}")
        # Chụp màn hình lỗi để debug nếu cần
        driver.save_screenshot(f"error_batch_{batch_index}.png")
        return False

def main():
    
    # 1. Chuẩn bị file
    batches = get_file_batches(DATA_ASSETS_DIR, DATA_SRT_DIR, batch_size=8)
    
    if not batches:
        print("Dừng chương trình do thiếu file.")
        return

    # 2. Mở trình duyệt (Profile thật)
    driver = init_driver()
    if not driver: return

    driver.get(GEMINI_URL)
    time.sleep(3) 

    # 3. Chạy vòng lặp từng batch
    for i, batch_files in enumerate(batches):
        success = upload_and_run(driver, batch_files, batch_index=i+1)
        
        if success:
            # Nghỉ một chút giữa các lần S để không bị spam
            print("zzZ Nghỉ 10 giây trước khi qua batch tiếp theo...")
            time.sleep(10)
        else:
            print("⚠️ Batch lỗi, dừng lại để kiểm tra.")
            break
            
    print("\n🏁 HOÀN TẤT TOÀN BỘ JOB.")
    input("Bấm Enter để đóng...")
    driver.quit()

if __name__ == "__main__":
    main()