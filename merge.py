import os
import subprocess
import re

# ==========================================
# 📂 CẤU HÌNH ĐƯỜNG DẪN (CHỈNH TẠI ĐÂY)
# ==========================================
PATHS = {
    # Sử dụng 'r' để tránh lỗi đường dẫn Windows
    'ffmpeg_bin': r'G:\Vinh\test\i_c\bin\ffmpeg.exe', 
    'scene_dir': 'data/scenes', 
    'audio_input': 'data/input/tc2.mp3',      
    'final_output': 'data/video_output/FINAL_MOVIE_FAST.mp4'
}

def merge_ffmpeg_pure():
    print("\n🚀 --- BẮT ĐẦU NỐI VIDEO TỐC ĐỘ CAO (FFMPEG ONLY) ---")
    
    if not os.path.exists(PATHS['scene_dir']):
        print(f"❌ Không thấy thư mục: {PATHS['scene_dir']}")
        return

    # 1. Sắp xếp danh sách file theo số thứ tự
    def sort_key(f):
        nums = re.findall(r'\d+', f)
        return int(nums[0]) if nums else 0

    video_files = sorted(
        [f for f in os.listdir(PATHS['scene_dir']) if f.endswith('.mp4')],
        key=sort_key
    )

    if not video_files:
        print("❌ Không có video để nối.")
        return

    # 2. Tạo file tạm list.txt cho FFmpeg
    list_file = 'data/scenes/concat.txt'
    with open(list_file, 'w', encoding='utf-8') as f:
        for v in video_files:
            # Dùng đường dẫn tuyệt đối để tránh lỗi
            abs_path = os.path.abspath(os.path.join(PATHS['scene_dir'], v)).replace('\\', '/')
            f.write(f"file '{abs_path}'\n")

    # 3. Bước 1: Nối các video lại (không render lại - c copy)
    temp_merged = "temp_merged.mp4"
    print("🔗 Đang ghép các cảnh...")
    cmd_merge = [
        PATHS['ffmpeg_bin'], '-y', '-f', 'concat', '-safe', '0',
        '-i', list_file, '-c', 'copy', temp_merged
    ]
    subprocess.run(cmd_merge, check=True)

    # 4. Bước 2: Ghép âm thanh mới vào video đã nối
    print(f"🎵 Đang lồng nhạc: {PATHS['audio_input']}")
    # -map 0:v : Lấy video từ file thứ nhất (video đã nối)
    # -map 1:a : Lấy audio từ file thứ hai (file mp3)
    # -shortest: Kết thúc video khi nhạc hoặc hình hết trước
    cmd_final = [
        PATHS['ffmpeg_bin'], '-y', '-i', temp_merged, '-i', PATHS['audio_input'],
        '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', 
        '-shortest', PATHS['final_output']
    ]
    
    try:
        subprocess.run(cmd_final, check=True)
        print(f"🎉 THÀNH CÔNG: {PATHS['final_output']}")
    except Exception as e:
        print(f"❌ Lỗi: {e}")
    finally:
        # Dọn dẹp file tạm
        for tmp in [list_file, temp_merged]:
            if os.path.exists(tmp): os.remove(tmp)

if __name__ == "__main__":
    merge_ffmpeg_pure()