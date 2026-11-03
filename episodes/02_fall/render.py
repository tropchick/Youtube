"""Short #2: falling from the top of a Minecraft world vs real life."""
import math
import random
import sys
import wave

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, __file__.rsplit("/episodes/", 1)[0] + "/engine")
from gfx import (W, H, FPS, Encoder, text, text_block, block, grass_block, cube_guy,
                 heart, pill, prog, ease_out, ease_back, lerp, lerp_col, vgradient, clamp)

OUT = sys.argv[1]
VO = sys.argv[2]
DUR = 40.6

SKY = vgradient((92, 160, 235), (190, 225, 250))
NIGHT = vgradient((12, 18, 38), (40, 30, 70))
DARK = vgradient((14, 30, 20), (30, 70, 40))
random.seed(7)
STARS = [(random.randint(0, W), random.randint(0, H), random.randint(2, 5)) for _ in range(80)]

# --- timing (seconds, from voice pauses) ---
T_HEIGHT = 5.1
T_RACE = 10.26
FALL_START = 10.6
MC_FALL, REAL_FALL = 7.25, 10.75
T_DMG = 22.6
T_HP = 30.58
T_DIE = 32.25
T_WATER = 35.5
T_END = 37.64


def mc_y(t):
    """Distance fallen (blocks) after t seconds in Minecraft physics."""
    v = y = 0.0
    for _ in range(int(t * 20)):
        v = (v + 0.08) * 0.98
        y += v
    return min(y, 384), v * 20 * 3.6


def real_y(t):
    vt, g = 55.0, 9.81
    y = (vt ** 2 / g) * math.log(math.cosh(g * t / vt))
    return min(y, 384), vt * math.tanh(g * t / vt) * 3.6


MC_TAB = [mc_y(i / FPS) for i in range(int(12 * FPS))]


def scene_hook(img, d, t):
    img.paste(SKY)
    # tall pillar going down, camera at top
    s = 120
    for i in range(12):
        grass_block(d, W / 2 - s / 2, 1000 + i * s, s) if i == 0 else \
            block(d, W / 2 - s / 2, 1000 + i * s, s, (150, 150, 150), (90, 90, 90), (125, 125, 125))
    bob = math.sin(t * 4) * 6
    cube_guy(d, W / 2, 1000 - 70 + bob, 110)
    k = ease_back(prog(t, 0.1, 0.5))
    text_block(d, W / 2, 420, "ЧТО БУДЕТ, ЕСЛИ ПРЫГНУТЬ", int(86 * max(k, .01)), max_w=980)
    k2 = ease_back(prog(t, 1.2, 0.5))
    if k2 > 0.02:
        text_block(d, W / 2, 640, "С САМОГО ВЕРХА МИРА?", int(100 * max(k2, .01)),
                   fill=(255, 230, 80), max_w=1000)
    pill(d, W / 2, 1780, "Y = 320", 56, (20, 20, 30), (255, 255, 255))


def scene_height(img, d, t):
    lt = t - T_HEIGHT
    img.paste(SKY)
    # scale bar
    x0, top, bot = 260, 380, 1720
    d.rectangle([x0 - 30, top, x0 + 30, bot], fill=(40, 40, 50))
    k = ease_out(prog(lt, 0.2, 2.0))
    fill_top = lerp(bot, top, k)
    d.rectangle([x0 - 30, fill_top, x0 + 30, bot], fill=(95, 191, 58))
    n = int(384 * k)
    text(d, (x0 + 70, fill_top), f"{n}", 90, anchor="lm")
    text(d, (x0 + 70, fill_top + 80), "блоков", 50, anchor="lm", bold=True)
    # Eiffel tower silhouette 330/384 of bar
    kt = ease_out(prog(lt, 2.9, 0.8))
    if kt > 0:
        th = (bot - top) * 330 / 384
        cx, base = 760, bot
        tip = base - th * kt
        col = (70, 60, 55)
        h = th * kt
        pts = [(cx - 200, base), (cx - 70, base - .35 * h), (cx - 26, base - .75 * h), (cx - 7, base - h + 50),
               (cx + 7, base - h + 50), (cx + 26, base - .75 * h), (cx + 70, base - .35 * h), (cx + 200, base),
               (cx + 115, base), (cx + 60, base - .14 * h), (cx, base - .19 * h), (cx - 60, base - .14 * h),
               (cx - 115, base)]
        d.polygon(pts, fill=col)
        d.rectangle([cx - 4, base - h, cx + 4, base - h + 60], fill=col)
        d.rectangle([cx - 150, base - .2 * h, cx + 150, base - .2 * h + 20], fill=col)
        d.rectangle([cx - 85, base - .42 * h, cx + 85, base - .42 * h + 16], fill=col)
        text(d, (cx, tip - 70), "Эйфелева башня", 52, alpha=kt, img=img)
        text(d, (cx, tip - 15), "330 м", 46, fill=(255, 230, 80), alpha=kt, img=img, bold=True)
    text(d, (W / 2, 200), "ВЫСОТА МИРА", 96)


def race_column(img, d, cx, label, col, y_blocks, kmh, done, landed_t, lt):
    top, bot = 430, 1540
    d.rounded_rectangle([cx - 230, top - 20, cx + 230, bot + 120], radius=40, fill=(24, 26, 56),
                        outline=(255, 255, 255), width=4)
    text(d, (cx, top - 80), label, 64, fill=col)
    y = lerp(top + 60, bot - 40, y_blocks / 384)
    # speed streaks
    if not done and y_blocks > 5:
        for i in range(5):
            sx = cx - 120 + i * 60
            d.line([sx, y - 120 - (i % 2) * 40, sx, y - 60], fill=(255, 255, 255), width=5)
    cube_guy(d, cx, y, 90, body=col)
    for i in range(4):
        grass_block(d, cx - 230 + i * 115, bot + 60 - 115 + 60, 115) if False else None
    d.rectangle([cx - 226, bot + 40, cx + 226, bot + 116], fill=(106, 170, 64))
    text(d, (cx, bot + 190), f"{kmh:.0f} км/ч", 64)
    if done:
        k = ease_back(prog(lt, landed_t, 0.4))
        text(d, (cx, 380 + 0 * k), "", 10)
        pill(d, cx, (top + bot) / 2, f"{landed_t:.1f} с".replace(".", ","), int(80 * max(k, .01)),
             (255, 230, 80), (20, 20, 30))


def scene_race(img, d, t):
    img.paste(NIGHT)
    for x, y, r in STARS:
        d.ellipse([x, y, x + r, y + r], fill=(220, 220, 255))
    lt = t - T_RACE
    ft = max(0.0, t - FALL_START)
    text(d, (W / 2, 150), "КТО БЫСТРЕЕ?", 100)
    timer = min(ft, REAL_FALL)
    text(d, (W / 2, 260), f"{timer:4.1f} с".replace(".", ","), 70, fill=(255, 230, 80))
    # minecraft
    mi = min(int(ft * FPS), len(MC_TAB) - 1)
    my, mk = MC_TAB[mi]
    mdone = ft >= MC_FALL
    if mdone:
        my, mk = 384, MC_TAB[int(MC_FALL * FPS)][1]
    ry, rk = real_y(ft)
    rdone = ft >= REAL_FALL
    if rdone:
        ry, rk = 384, real_y(REAL_FALL)[1]
    race_column(img, d, 280, "Майнкрафт", (95, 191, 58), my, mk, mdone, MC_FALL, ft)
    race_column(img, d, 800, "Реальность", (90, 180, 240), ry, rk, rdone, REAL_FALL, ft)


def scene_damage(img, d, t):
    lt = t - T_DMG
    img.paste(DARK)
    k = ease_back(prog(lt, 0, 0.4))
    text(d, (W / 2, 360), "УРОН", int(150 * max(k, .01)), fill=(255, 90, 90))
    k1 = ease_out(prog(lt, 1.2, 0.5))
    text(d, (W / 2, 640), "каждый блок после 3-го", 66, alpha=k1, img=img)
    text(d, (W / 2, 740), "= 1 очко урона", 66, alpha=k1, img=img, fill=(255, 230, 80))
    k2 = ease_back(prog(lt, 5.2, 0.5))
    if k2 > 0.02:
        text(d, (W / 2, 1050), "384 − 3", int(130 * max(k2, .01)))
        text(d, (W / 2, 1230), "≈ 380 урона", int(120 * max(k2, .01)), fill=(255, 90, 90))
    for i in range(10):
        heart(d, 120 + i * 93, 1600, 11, empty=lt > 6.0)


def scene_hp(img, d, t):
    lt = t - T_HP
    img.paste(DARK)
    text(d, (W / 2, 360), "У ТЕБЯ ВСЕГО", 90)
    text(d, (W / 2, 520), "20 HP", 170, fill=(255, 90, 90))
    for i in range(10):
        heart(d, 120 + i * 93, 760, 11)
    if t >= T_DIE:
        dk = ease_back(prog(t, T_DIE, 0.5))
        n = min(19, int(1 + (t - T_DIE) / 1.6 * 18))
        text(d, (W / 2, 1150), f"×{n}", int(260 * max(dk, .01)), fill=(255, 230, 80))
        text(d, (W / 2, 1380), "СМЕРТЕЙ ПОДРЯД", int(90 * max(dk, .01)))


def scene_water(img, d, t):
    lt = t - T_WATER
    img.paste(SKY)
    # ground + water block
    s = 180
    for i in range(7):
        grass_block(d, -40 + i * s, 1500, s)
    wk = ease_back(prog(lt, 0.3, 0.5))
    ws = s * max(wk, 0.01)
    block(d, W / 2 - ws / 2, 1500 - ws, ws, (120, 180, 255), (30, 80, 170), (60, 120, 230))
    fall = ease_out(prog(lt, 0, 1.6))
    cube_guy(d, W / 2, lerp(300, 1500 - s - 60, fall), 110)
    text_block(d, W / 2, 330, "ИЛИ ПРОСТО ПОСТАВЬ ВОДУ", 92, max_w=980)
    if t >= T_END:
        k = ease_back(prog(t, T_END, 0.4))
        text(d, (W / 2, 700), "А ты бы успел?", int(100 * max(k, .01)), fill=(255, 230, 80))
        pill(d, W / 2, 860, "Пиши в комментах", int(60 * max(k, .01)), (95, 191, 58), (14, 42, 23))


SCENES = [(0, scene_hook), (T_HEIGHT, scene_height), (T_RACE, scene_race),
          (T_DMG, scene_damage), (T_HP, scene_hp), (T_WATER, scene_water)]


def frame(t):
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    fn = [f for s, f in SCENES if t >= s][-1]
    fn(img, d, t)
    # quick flash on scene change
    for s, _ in SCENES[1:]:
        if 0 <= t - s < 0.12:
            a = 1 - (t - s) / 0.12
            img = Image.blend(img, Image.new("RGB", (W, H), (255, 255, 255)), a * 0.5)
    # channel tag
    d2 = ImageDraw.Draw(img)
    text(d2, (W / 2, H - 60), "LowPolyLab", 40, fill=(255, 255, 255), stroke=5, bold=True)
    return img


def sfx(path):
    sr = 44100
    n = int(DUR * sr)
    out = np.zeros(n)
    rng = np.random.default_rng(1)

    def add(t0, sig):
        i = int(t0 * sr)
        out[i:i + len(sig)] += sig[:max(0, n - i)]

    def whoosh(dur, vol):
        m = int(dur * sr)
        noise = rng.standard_normal(m)
        k = np.ones(40) / 40
        noise = np.convolve(noise, k, mode="same")
        env = np.sin(np.linspace(0, np.pi, m)) ** 2
        return noise * env * vol

    def thud(vol):
        m = int(0.35 * sr)
        tt = np.arange(m) / sr
        return np.sin(2 * np.pi * (90 - 120 * tt) * tt) * np.exp(-tt * 14) * vol

    def pop(vol):
        m = int(0.12 * sr)
        tt = np.arange(m) / sr
        return np.sin(2 * np.pi * 880 * tt) * np.exp(-tt * 40) * vol

    for s, _ in SCENES[1:]:
        add(s, whoosh(0.4, 0.25))
    add(FALL_START, whoosh(MC_FALL, 0.12))
    add(FALL_START + MC_FALL, thud(0.8))
    add(FALL_START + REAL_FALL, thud(0.8))
    add(T_DIE, pop(0.4))
    add(T_WATER + 0.3, pop(0.4))
    add(T_END, pop(0.4))
    out = np.clip(out, -1, 1)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((out * 32767 * 0.6).astype(np.int16).tobytes())


if __name__ == "__main__":
    import subprocess
    sfx(OUT + ".sfx.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", VO, "-i", OUT + ".sfx.wav",
                    "-filter_complex", "[0:a]apad[v];[v][1:a]amix=inputs=2:duration=longest:normalize=0,atrim=0:%s" % DUR,
                    OUT + ".audio.m4a"], check=True)
    if len(sys.argv) > 3:  # preview stills
        for ts in map(float, sys.argv[3].split(",")):
            frame(ts).save(f"{OUT}.{ts:05.1f}.png")
        sys.exit()
    enc = Encoder(OUT, OUT + ".audio.m4a")
    for i in range(int(DUR * FPS)):
        enc.write(frame(i / FPS))
    enc.close()
