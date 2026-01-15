import os
import json
import pysrt
import re
from moviepy.editor import *
from moviepy.config import change_settings

# 👇 Gọi file animation chứa hiệu ứng hiện đại
from animation import apply_animation 

# Cấu hình ImageMagick
change_settings({"IMAGEMAGICK_BINARY": r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"})

# --- CẤU HÌNH ---
PATHS = {
    'audio_file': 'data/input/tc2.mp3',
    'image_srt_file': 'images.srt',
    'sentences_srt_file': 'sentences.srt', 
    'output_video': 'data/video_output/FINAL_VIDEO.mp4',
    'hand_icon': 'data/input/hand.png' # Đường dẫn ảnh cái tay (nếu dùng hiệu ứng draw)
}

SETTINGS = {
    'anim_duration': 0.8, # Tăng thời gian animation lên xíu cho mượt
    'bg_color': (255, 255, 255),
    'video_fps': 24,
    'default_size': (1366, 768),
    'font': 'Arial-Bold',
    'fontsize': 42,
    'font_color': 'yellow',
    'stroke_color': 'black',
    'stroke_width': 1.8,
    'sub_bottom_margin': 60
}

# Hàm tiện ích: Đảm bảo số luôn chẵn
def make_even(n):
    return int(n) if int(n) % 2 == 0 else int(n) + 1

def create_balanced_subtitle(txt, start, end, v_width, v_height):
    txt_clip = TextClip(txt, font=SETTINGS['font'], fontsize=SETTINGS['fontsize'],
                        color=SETTINGS['font_color'], stroke_color=SETTINGS['stroke_color'],
                        stroke_width=SETTINGS['stroke_width'], method='caption', align='Center',
                        size=(v_width * 0.85, None))
    y_pos = v_height - txt_clip.h - SETTINGS['sub_bottom_margin']
    return txt_clip.set_start(start).set_end(end).set_position(('center', y_pos))

# --- HÀM RENDER CHÍNH ---
def render_video():
    print("\n🎞️ --- ĐANG TỔNG HỢP VIDEO ---")
    
    # 0. CHUẨN BỊ
    audio_clip = AudioFileClip(PATHS['audio_file'])
    total_duration = audio_clip.duration + 1.0
    
    # 👇 KHỞI TẠO BIẾN QUAN TRỌNG (Fix lỗi NameError)
    layout_caches = {} 
    video_size = SETTINGS['default_size']
    
    # 1. ĐỌC VÀ SỬA LỖI ĐỊNH DẠNG SRT
# 1. ĐỌC VÀ SỬA LỖI ĐỊNH DẠNG SRT
    if not os.path.exists(PATHS['image_srt_file']):
        print(f"❌ Không tìm thấy file {PATHS['image_srt_file']}")
        return

    with open(PATHS['image_srt_file'], 'r', encoding='utf-8') as f:
        content = f.read().strip()

    # --- BỔ SUNG LOGIC XỬ LÝ ĐỊNH DẠNG MỘT DÒNG ---
    # Kiểm tra xem có phải định dạng: [ID] [Time] [Text] trên cùng 1 dòng không
    # Ví dụ: 1 00:00:00,031 --> 00:00:11,227 data/output/1/5.png | pop
    line_format_pattern = r'^(\d+)\s+(\d{2}:\d{2}:\d{2},\d{3}\s+-->\s+\d{2}:\d{2}:\d{2},\d{3})\s+(.+)$'
    
    lines = content.split('\n')
    fixed_lines = []
    
    for line in lines:
        line = line.strip()
        if not line: continue
        
        match = re.match(line_format_pattern, line)
        if match:
            # Nếu khớp định dạng một dòng, tách ra làm 3 dòng chuẩn SRT
            fixed_lines.append(match.group(1)) # ID
            fixed_lines.append(match.group(2)) # Time
            fixed_lines.append(match.group(3)) # Text
            fixed_lines.append("")             # Dòng trống phân cách
        else:
            # Nếu không khớp, có thể nó đã là định dạng chuẩn hoặc định dạng lỗi khác
            fixed_lines.append(line)

    # Gộp lại thành nội dung SRT chuẩn
    final_content = "\n".join(fixed_lines)
    
    # Sử dụng pysrt để parse nội dung đã được chuẩn hóa
    raw_subs = pysrt.from_string(final_content)
    scenes = [] 
    current_folder = None
    current_scene_items = []

    # Gom nhóm các ảnh theo folder (Scene)
    for sub in raw_subs:
        content = sub.text.strip().split('|')
        path_raw = content[0].strip()
        effect_type = content[1].strip().lower() if len(content) > 1 else 'pop'
        
        if not os.path.exists(path_raw): continue
        
        sub.img_path = path_raw
        sub.anim_effect = effect_type 
        
        folder = os.path.dirname(path_raw)
        if folder != current_folder:
            if current_folder is not None:
                scenes.append({'folder': current_folder, 'items': current_scene_items})
            current_folder = folder
            current_scene_items = []
        current_scene_items.append(sub)
    
    if current_folder is not None:
        scenes.append({'folder': current_folder, 'items': current_scene_items})

    # 2. XỬ LÝ ẢNH & ANIMATION
    image_layers = []
    
    for i, scene in enumerate(scenes):
        folder_path = scene['folder']
        items = scene['items']
        
        # Tính thời gian kết thúc của Scene
        if i < len(scenes) - 1:
            next_scene_start = scenes[i+1]['items'][0].start.ordinal / 1000.0
            scene_end_time = next_scene_start
        else:
            scene_end_time = total_duration

        # Load Layout JSON
        if folder_path not in layout_caches:
            json_path = os.path.join(folder_path, 'layout.json')
            if os.path.exists(json_path):
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    w = make_even(data['original_size']['w'])
                    h = make_even(data['original_size']['h'])
                    layout_caches[folder_path] = {
                        'icons': {item['file']: item for item in data['icons']},
                        'size': (w, h)
                    }
                    video_size = layout_caches[folder_path]['size']
            else:
                layout_caches[folder_path] = None
        
        layout_data = layout_caches.get(folder_path)

        for item in items:
            filename = os.path.basename(item.img_path)
            start_time = item.start.ordinal / 1000.0
            duration = scene_end_time - start_time
            if duration <= 0: duration = 0.5 

            if layout_data and filename in layout_data['icons']:
                info = layout_data['icons'][filename]
                
                # Tạo clip ảnh gốc
                img_clip = ImageClip(item.img_path).set_start(start_time).set_duration(duration)
                
                # 👇 GỌI HÀM ANIMATION (QUAN TRỌNG: XỬ LÝ TUPLE TRẢ VỀ)
                # apply_animation bây giờ trả về (clip_đã_xử_lý, clip_cái_tay)
                result = apply_animation(
                    img_clip, 
                    item.anim_effect, 
                    info['x'], 
                    info['y'], 
                    SETTINGS['anim_duration'],
                    PATHS['hand_icon']
                )
                
                final_img_clip = None
                hand_clip = None

                # Kiểm tra xem kết quả là tuple hay clip đơn lẻ
                if isinstance(result, tuple):
                    final_img_clip, hand_clip = result
                else:
                    final_img_clip = result

                # Thêm hiệu ứng fade nhẹ cho ảnh chính để mượt hơn
                if final_img_clip:
                    # Lưu ý: Nếu dùng hiệu ứng draw, fade đã được xử lý bên trong animation.py rồi
                    # nên ta chỉ crossfadeout lúc biến mất
                    final_img_clip = final_img_clip.crossfadeout(0.3)
                    image_layers.append(final_img_clip)

                # Nếu có clip cái tay (hiệu ứng draw), thêm vào layer trên cùng
                if hand_clip:
                    image_layers.append(hand_clip)

    # 3. XỬ LÝ PHỤ ĐỀ
    subtitle_layers = []
    if os.path.exists(PATHS['sentences_srt_file']):
        subs_data = pysrt.open(PATHS['sentences_srt_file'], encoding='utf-8')
        for sub in subs_data:
            sub_clip = create_balanced_subtitle(
                sub.text, 
                sub.start.ordinal/1000.0, 
                sub.end.ordinal/1000.0, 
                video_size[0], 
                video_size[1]
            )
            subtitle_layers.append(sub_clip)

    # 4. TỔNG HỢP FINAL
    bg_clip = ColorClip(size=video_size, color=SETTINGS['bg_color'], duration=total_duration)
    
    final_video = CompositeVideoClip(
        [bg_clip] + image_layers + subtitle_layers, 
        size=video_size
    ).set_audio(audio_clip)
    
    final_video = final_video.set_duration(audio_clip.duration)

    final_video.write_videofile(
        PATHS['output_video'], 
        fps=SETTINGS['video_fps'], 
        codec='libx264', 
        audio_codec='aac',
        ffmpeg_params=['-pix_fmt', 'yuv420p']
    )
    print(f"\n🎉 HOÀN THÀNH: {PATHS['output_video']}")

if __name__ == "__main__":
    render_video()