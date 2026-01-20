
import os
import glob
import re

def natural_sort_key(s):
    """Hàm giúp sắp xếp file theo số tự nhiên: 1.zip -> 2.zip -> 10.zip"""
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split('([0-9]+)', s)]

def get_file_batches(assets_dir, srt_dir, batch_size=8):
    """
    Trả về danh sách các gói (batch) để upload.
    Mỗi gói gồm: 8 file zip + sentences.srt + words.srt
    """
    # 1. Lấy đường dẫn tuyệt đối của SRT
    srt_files = [
        os.path.abspath(os.path.join(srt_dir, "sentences.srt")),
        os.path.abspath(os.path.join(srt_dir, "words.srt"))
    ]
    
    # Kiểm tra SRT có tồn tại không
    for f in srt_files:
        if not os.path.exists(f):
            print(f"❌ Thiếu file: {f}")
            return []

    # 2. Quét toàn bộ file zip
    zip_pattern = os.path.join(assets_dir, "*.zip")
    all_zips = glob.glob(zip_pattern)
    
    # Sắp xếp zip theo số (quan trọng)
    all_zips.sort(key=natural_sort_key)
    
    if not all_zips:
        print(f"❌ Không tìm thấy file .zip nào trong {assets_dir}")
        return []

    print(f"✅ Tìm thấy {len(all_zips)} file zip. Đang chia nhóm {batch_size}...")

    # 3. Chia thành từng chunk và gộp với SRT
    batches = []
    for i in range(0, len(all_zips), batch_size):
        # Lấy 8 file zip
        chunk_zips = all_zips[i : i + batch_size]
        # Chuyển sang đường dẫn tuyệt đối
        chunk_zips = [os.path.abspath(p) for p in chunk_zips]
        
        # Gộp: Zips + SRTs
        batch_files = chunk_zips + srt_files
        batches.append(batch_files)
        
    return batches