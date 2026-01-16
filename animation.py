import numpy as np
import pytweening
from moviepy.editor import ImageClip


# ===============================
# UTILS
# ===============================

def clamp01(x):
    return max(0.0, min(1.0, x))


def clamp(v, lo=0.01, hi=10):
    return max(lo, min(hi, v))


# ===============================
# EASING
# ===============================

def ease_out(p):
    return pytweening.easeOutBack(p)


def ease_in(p):
    return pytweening.easeInBack(p)


def ease_elastic(p):
    return pytweening.easeOutElastic(p)


# ===============================
# SCALE FUNC (SAFE)
# ===============================

def scale_func(t, total, effect, intro, outro):
    # clamp time
    if t < 0:
        t = 0
    if t > total:
        t = total

    s = 1.0

    # ---- INTRO ----
    if t < intro:
        p = clamp01(t / intro)

        if effect in ["pop", "pulse", "jello"]:
            s = 0.6 + 0.4 * ease_elastic(p)
        else:
            s = ease_out(p)

    # ---- OUTRO ----
    elif t > total - outro:
        p = clamp01((t - (total - outro)) / outro)
        s = ease_in(1 - p)

    # ---- SAFE GUARD ----
    if not np.isfinite(s):
        s = 0.05

    return max(0.05, float(s))


# ===============================
# MAIN
# ===============================

def apply_animation(clip, effect_name, target_x, target_y, duration, hand_img_path=None):
    target_x, target_y = int(target_x), int(target_y)

    total = clip.duration
    intro = min(duration, total * 0.4)
    outro = min(duration * 0.8, total * 0.4)

    # ---- SCALE SAFE ----
    animated = clip.resize(lambda t: scale_func(min(t, total), total, effect_name, intro, outro))

    slide_dist = animated.w * 1.2
    drop_dist = animated.h * 1.2
    fly_dist = animated.w * 2.0

    def pos_func(t):
        x, y = target_x, target_y

        # ---- INTRO ----
        if t < intro:
            p = clamp01(t / intro)

            if effect_name == "slide":
                x = target_x - slide_dist + slide_dist * ease_out(p)

            elif effect_name == "slide_up":
                y = target_y + drop_dist - drop_dist * ease_out(p)

            elif effect_name in ["drop", "swing"]:
                y = target_y - drop_dist + drop_dist * pytweening.easeOutBounce(p)

        # ---- FLOAT LOOP ----
        if effect_name == "float":
            y += 8 * np.sin(t * 1.6)
            x += 4 * np.cos(t * 1.2)

        # ---- OUTRO ----
        if t > total - outro:
            p = clamp01((t - (total - outro)) / outro)
            x = target_x + fly_dist * ease_in(p)

        return (int(x), int(y))

    animated = animated.set_position(pos_func)

    # ---- DRAW HAND ----
    if effect_name == "draw" and hand_img_path:
        w, h = clip.size
        try:
            hand_clip = ImageClip(hand_img_path).resize(height=150)

            def hand_pos(t):
                if t >= intro:
                    return (target_x + w, target_y + h + 3000)

                p = clamp01(t / intro)
                cur_x = target_x + w * p
                cur_y = target_y + h * 0.6 + 20 * np.sin(18 * t)
                return (int(cur_x), int(cur_y))

            hand_anim = (
                hand_clip
                .set_start(clip.start)
                .set_duration(intro)
                .set_position(hand_pos)
            )

            return animated, hand_anim
        except:
            return animated, None

    return animated, None
