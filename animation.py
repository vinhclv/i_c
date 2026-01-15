import numpy as np
import cv2
from moviepy.editor import ImageClip

# ==========================================
# 🧠 BỘ NÃO TOÁN HỌC (EASING FUNCTIONS)
# ==========================================

def ease_out_expo(t):
    return 1 if t >= 1 else 1 - pow(2, -10 * max(0, t))

def ease_out_back(t):
    c1 = 1.70158
    c3 = c1 + 1
    t_m = max(0, min(1, t)) - 1
    return 1 + c3 * pow(t_m, 3) + c1 * pow(t_m, 2)

def ease_out_elastic(t):
    if t <= 0: return 0
    if t >= 1: return 1
    c4 = (2 * np.pi) / 3
    return pow(2, -10 * t) * np.sin((t * 10 - 0.75) * c4) + 1

# ==========================================
# 🛠️ HELPER: THAY THẾ RESIZE CỦA MOVIEPY
# ==========================================

def manual_resize_frame(get_frame, t, duration, effect_type):
    frame = get_frame(t)
    h, w, c = frame.shape  # Lấy chính xác số kênh màu (3 hoặc 4)

    progress = min(1.0, max(0.0, t / duration)) if duration > 0 else 1.0
    
    # Tính toán scale dựa trên hiệu ứng
    if effect_type == 'pop':
        scale = ease_out_elastic(progress)
        scale_w, scale_h = scale, scale
    elif effect_type == 'flip':
        scale_w = ease_out_expo(progress)
        scale_h = 1.0
    elif effect_type == 'spin':
        scale = ease_out_expo(progress)
        scale_w, scale_h = scale, scale
    else:
        return frame

    # Bảo vệ: Không để scale <= 0
    scale_w = max(0.01, scale_w)
    scale_h = max(0.01, scale_h)

    new_w, new_h = int(w * scale_w), int(h * scale_h)
    
    # Nếu ảnh quá nhỏ, trả về frame trống cùng số kênh màu
    if new_w < 1 or new_h < 1: 
        return np.zeros((h, w, c), dtype="uint8")

    # Resize chất lượng cao
    resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
    
    # Khởi tạo canvas dựa trên số kênh màu thực tế (c) để tránh lỗi Broadcast
    canvas = np.zeros((h, w, c), dtype="uint8")
    
    y_off = (h - new_h) // 2
    x_off = (w - new_w) // 2
    
    # Tính toán vùng cắt dán an toàn
    y1, y2 = max(0, y_off), min(h, y_off + new_h)
    x1, x2 = max(0, x_off), min(w, x_off + new_w)
    
    ry1, ry2 = max(0, -y_off), max(0, -y_off) + (y2 - y1)
    rx1, rx2 = max(0, -x_off), max(0, -x_off) + (x2 - x1)
    
    # Dán phần đã resize vào giữa canvas
    canvas[y1:y2, x1:x2] = resized[ry1:ry2, rx1:rx2]
    return canvas

# ==========================================
# 🎬 TRÌNH QUẢN LÝ HIỆU ỨNG
# ==========================================

def apply_animation(clip, effect_name, target_x, target_y, duration, hand_img_path=None):
    target_x, target_y = int(target_x), int(target_y)
    
    # Thêm crossfadein nhẹ để tránh giật hình
    clip = clip.crossfadein(0.2)

    if effect_name in ['slide', 'slide_up']:
        def pos_func(t):
            prog = min(1.0, t / duration)
            val = ease_out_back(prog)
            start_y = target_y + 150 
            curr_y = start_y + (target_y - start_y) * val
            return (target_x, int(curr_y))
        return clip.set_position(pos_func), None

    elif effect_name == 'float':
        def float_pos(t):
            off_y = 8 * np.sin(1.5 * t) 
            off_x = 4 * np.cos(1.0 * t)
            return (target_x + int(off_x), target_y + int(off_y))
        return clip.set_position(float_pos), None

    elif effect_name in ['pop', 'flip', 'spin']:
        # fl xử lý biến đổi frame trực tiếp
        animated_clip = clip.fl(lambda gf, t: manual_resize_frame(gf, t, duration, effect_name))
        
        if effect_name == 'spin':
            # Xoay từ 360 về 0 độ
            animated_clip = animated_clip.rotate(lambda t: 360 * (1 - ease_out_expo(min(1, t/duration))) if t < duration else 0)
            
        return animated_clip.set_position((target_x, target_y)), None

    elif effect_name == 'draw' and hand_img_path:
        w, h = clip.size
        try:
            hand_clip = ImageClip(hand_img_path).resize(height=150)
            def hand_pos(t):
                if t >= duration: return (target_x + w, target_y + h + 2000) 
                prog = t / duration
                cur_x = target_x + (w * prog)
                cur_y = target_y + (h * 0.5) + 30 * np.sin(20 * t)
                return (int(cur_x), int(cur_y))
            
            hand_anim = hand_clip.set_start(clip.start).set_duration(duration).set_position(hand_pos)
            return clip.set_position((target_x, target_y)), hand_anim
        except:
            return clip.set_position((target_x, target_y)), None

    return clip.set_position((target_x, target_y)), None