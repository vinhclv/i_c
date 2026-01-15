import cv2
import numpy as np
import os
import json
import shutil  # Thêm thư viện để nén zip

# --- CẤU HÌNH ---
INPUT_DIR = 'data/input'
OUTPUT_DIR = 'data/output'
OUTPUT_ZIP_DIR = 'data/outputzip'  # Thư mục lưu trữ file zip mới

# Ngưỡng lọc rác
MIN_AREA = 1000 
PADDING = 15 
MORPH_KERNEL_SIZE = (20, 20) 
VALID_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.bmp', '.webp')

def process_images():
    # Tạo các thư mục cần thiết nếu chưa có
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    if not os.path.exists(OUTPUT_ZIP_DIR):
        os.makedirs(OUTPUT_ZIP_DIR)

    files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith(VALID_EXTENSIONS)]
    print(f"Tìm thấy {len(files)} ảnh. Bắt đầu xử lý...")

    for filename in files:
        print(f"\n>>> Đang xử lý: {filename}")
        file_path = os.path.join(INPUT_DIR, filename)
        
        original_img = cv2.imread(file_path)
        if original_img is None: continue

        border_size = 20
        img = cv2.copyMakeBorder(original_img, border_size, border_size, border_size, border_size, 
                                 cv2.BORDER_CONSTANT, value=(255, 255, 255))
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 230, 255, cv2.THRESH_BINARY_INV)

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, MORPH_KERNEL_SIZE)
        closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=2)

        contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            print("   [!] Không tìm thấy đối tượng nào.")
            continue
            
        bounding_boxes = [cv2.boundingRect(c) for c in contours]
        (contours, bounding_boxes) = zip(*sorted(zip(contours, bounding_boxes),
                                                 key=lambda b: b[1][1] * img.shape[1] + b[1][0]))

        name_no_ext = os.path.splitext(filename)[0]
        save_dir = os.path.join(OUTPUT_DIR, name_no_ext)
        if not os.path.exists(save_dir): os.makedirs(save_dir)

        layout_data = []
        count = 0

        for i, cnt in enumerate(contours):
            area = cv2.contourArea(cnt)
            if area < MIN_AREA: continue 

            x, y, w, h = cv2.boundingRect(cnt)
            x_new = max(0, x - PADDING)
            y_new = max(0, y - PADDING)
            w_new = min(img.shape[1] - x_new, w + 2*PADDING)
            h_new = min(img.shape[0] - y_new, h + 2*PADDING)

            mask_full = np.zeros_like(gray)
            cv2.drawContours(mask_full, [cnt], -1, 255, cv2.FILLED)

            roi_img = img[y_new : y_new+h_new, x_new : x_new+w_new]
            roi_mask = mask_full[y_new : y_new+h_new, x_new : x_new+w_new]

            b, g, r = cv2.split(roi_img)
            final_icon = cv2.merge([b, g, r, roi_mask])

            count += 1
            icon_filename = f'{count}.png'
            cv2.imwrite(os.path.join(save_dir, icon_filename), final_icon)

            layout_data.append({
                "id": count,
                "file": icon_filename,
                "x": x_new - border_size, 
                "y": y_new - border_size,
                "w": w_new,
                "h": h_new
            })

        json_path = os.path.join(save_dir, 'layout.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump({
                "original_size": {"w": original_img.shape[1], "h": original_img.shape[0]},
                "icons": layout_data
            }, f, indent=4)

        print(f"   --> Hoàn thành trích xuất icon tại '{name_no_ext}'")

        # --- BƯỚC MỚI: ĐÓNG GÓI ZIP ---
        # Đường dẫn file zip mục tiêu (không cần ghi đuôi .zip vì shutil sẽ tự thêm)
        zip_base_name = os.path.join(OUTPUT_ZIP_DIR, name_no_ext)
        
        # Nén toàn bộ thư mục save_dir thành file zip
        shutil.make_archive(zip_base_name, 'zip', save_dir)
        print(f"   --> Đã đóng gói zip: {name_no_ext}.zip tại '{OUTPUT_ZIP_DIR}'")

    print("\n---------------- DONE ----------------")

if __name__ == "__main__":
    process_images()