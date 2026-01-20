import numpy as np
import pytweening
from moviepy.editor import ImageClip


# ===============================
# UTILS
# ===============================

def clamp01(x):
    return max(0.0, min(1.0, x))


# ===============================
# EASING
# ===============================

def ease_out(p):
    return pytweening.easeOutCubic(p)


def ease_in(p):
    return pytweening.easeInCubic(p)


def ease_elastic(p):
    return pytweening.easeOutElastic(p)


def ease_smooth(p):
    return p * p * (3 - 2 * p)


# ===============================
# SCALE FUNC
# ===============================

def scale_func(t, total, effect, intro, outro, is_hero=False):
    t = max(0, min(total, t))
    s = 1.0

    # ---- INTRO ----
    if t < intro:
        p = clamp01(t / intro)

        if effect in ["pop", "pulse", "jello"]:
            s = 0.75 + 0.25 * ease_elastic(p)
        else:
            s = 0.85 + 0.15 * ease_out(p)

    # ---- OUTRO ----
    elif t > total - outro:
        p = clamp01((t - (total - outro)) / outro)

        if is_hero:
            s = 1.0 - 0.35 * ease_smooth(p)
        else:
            s = 1.0 - 0.25 * ease_in(p)

    return max(0.25, float(s))


# ===============================
# MAIN
# ===============================

def apply_animation(clip, effect_name, target_x, target_y, duration, hand_img_path=None):
    target_x, target_y = int(target_x), int(target_y)

    total = clip.duration
    intro = min(duration, total * 0.35)
    outro = min(duration * 0.8, total * 0.35)

    # ---- HERO DETECT ----
    hero_effects = ["pop", "jello", "pulse", "swing"]
    is_hero = effect_name in hero_effects

    # ---- SCALE ----
    animated = clip.resize(lambda t: scale_func(t, total, effect_name, intro, outro, is_hero))

    # ---- RANDOM OUT VECTOR (SATELLITE ONLY) ----
    angle = np.random.uniform(0, np.pi * 2)
    out_dx = np.cos(angle) * animated.w * 2.2
    out_dy = np.sin(angle) * animated.h * 2.2

    slide_dist = animated.w * 0.8
    drop_dist = animated.h * 0.8

    def pos_func(t):
        x, y = target_x, target_y

        # ---- INTRO ----
        if t < intro:
            p = clamp01(t / intro)

            if effect_name == "slide":
                x = target_x - slide_dist * (1 - ease_out(p))

            elif effect_name == "slide_up":
                y = target_y + drop_dist * (1 - ease_out(p))

            elif effect_name in ["drop", "swing"]:
                y = target_y - drop_dist * (1 - pytweening.easeOutBounce(p))

        # ---- MICRO MOTION ----
        if effect_name in ["float", "pop", "jello"]:
            y += 3 * np.sin(t * 2.0)
            x += 2 * np.cos(t * 1.4)

        # ---- OUTRO ----
        if t > total - outro:
            p = clamp01((t - (total - outro)) / outro)
            k = ease_in(p)

            if not is_hero:
                x = target_x + out_dx * k
                y = target_y + out_dy * k

        return (int(x), int(y))

    animated = animated.set_position(pos_func)

    # ---- OPACITY ----
    if is_hero:
        animated = animated.crossfadein(0.25).crossfadeout(0.45)
    else:
        animated = animated.crossfadein(0.25).crossfadeout(0.25)

    # ---- DRAW HAND ----
    if effect_name == "draw" and hand_img_path:
        w, h = clip.size
        try:
            hand_clip = ImageClip(hand_img_path).resize(height=150)

            def hand_pos(t):
                if t >= intro:
                    return (target_x + w, target_y + h + 5000)

                p = clamp01(t / intro)
                cur_x = target_x + w * p
                cur_y = target_y + h * 0.6 + 15 * np.sin(18 * t)
                return (int(cur_x), int(cur_y))

            hand_anim = (
                hand_clip
                .set_start(clip.start)
                .set_duration(intro)
                .set_position(hand_pos)
                .crossfadeout(0.2)
            )

            return animated, hand_anim
        except:
            return animated, None

    return animated, None
