"""Overlay text + audio on the 3D frames. Usage:
python3 compose3d.py FRAMES_DIR VOICE.mp3 OUT.mp4 [preview_times]"""
import math
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "engine"))
from gfx import W, H, FPS, Encoder, text, text_block, pill, prog, ease_back, ease_out

FR, VO, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
DUR = 40.6
T_HEIGHT, T_RACE, FALL_START = 5.1, 10.26, 10.6
MC_FALL, REAL_FALL = 7.25, 10.75
T_DMG, T_HP, T_DIE, T_WATER, T_END = 22.6, 30.58, 32.25, 35.5, 37.64
T_SPLIT0 = T_RACE + 0.6
YEL = (255, 230, 80)
RED = (255, 90, 90)


def mc_kmh(t):
    v = 0.0
    for _ in range(int(t * 20)):
        v = (v + 0.08) * 0.98
    return v * 20 * 3.6


def real_kmh(t):
    return 55 * math.tanh(9.81 * t / 55) * 3.6


def base(f):
    p = os.path.join(FR, f"f_{f:05d}.png")
    a = p[:-4] + "_a.png"
    if os.path.exists(a):
        im = Image.new("RGB", (540, 960))
        im.paste(Image.open(a), (0, 0))
        im.paste(Image.open(p[:-4] + "_b.png"), (270, 0))
    else:
        im = Image.open(p).convert("RGB")
    return im.resize((W, H), Image.LANCZOS)


def pop(t, s, d=0.45):
    return max(ease_back(prog(t, s, d)), 0.0)


def overlay(img, t):
    d = ImageDraw.Draw(img)
    if t < T_HEIGHT:
        text_block(d, W / 2, 300, "ЧТО БУДЕТ, ЕСЛИ ПРЫГНУТЬ", int(90 * pop(t, 0.1)), max_w=980)
        text_block(d, W / 2, 500, "С САМОГО ВЕРХА МИРА?", int(104 * pop(t, 1.2)), fill=YEL, max_w=1000)
        pill(d, W / 2, 1700, "Y = 320", int(60 * pop(t, 2.0)), (20, 20, 30), (255, 255, 255))
    elif t < T_RACE:
        lt = t - T_HEIGHT
        text(d, (W / 2, 220), "ВЫСОТА МИРА", 100)
        n = int(384 * ease_out(prog(lt, 0.2, 2.0)))
        text(d, (W / 2, 380), f"{n} блока", 120, fill=YEL)
        k = pop(lt, 2.9)
        text(d, (W / 2, 1640), "Эйфелева башня — 330 м", int(70 * k))
        text(d, (W / 2, 1740), "мир Майнкрафта выше", int(60 * k), fill=YEL)
    elif t < T_DMG:
        ft = max(0.0, t - FALL_START)
        text(d, (W / 2, 120), "КТО БЫСТРЕЕ?", 96)
        text(d, (W / 2, 240), f"{min(ft, REAL_FALL):4.1f} с".replace(".", ","), 80, fill=YEL)
        if t >= T_SPLIT0:
            d.rectangle([W / 2 - 4, 320, W / 2 + 4, H], fill=(255, 255, 255))
            for cx, label, col, fall, fn in ((W / 4, "Майнкрафт", (120, 220, 90), MC_FALL, mc_kmh),
                                             (3 * W / 4, "Реальность", (110, 190, 255), REAL_FALL, real_kmh)):
                text(d, (cx, 360), label, 66, fill=col)
                landed = ft >= fall
                v = fn(min(ft, fall))
                text(d, (cx, 1760), f"{v:.0f} км/ч", 70)
                if landed:
                    pill(d, cx, 1000, f"{fall:.1f} с".replace(".", ","), int(84 * pop(ft, fall, 0.4)),
                         YEL, (20, 20, 30))
    elif t < T_HP:
        lt = t - T_DMG
        text(d, (W / 2, 220), "УРОН", int(150 * pop(lt, 0)), fill=RED)
        k1 = ease_out(prog(lt, 1.2, 0.5))
        text(d, (W / 2, 380), "каждый блок после 3-го", 66, alpha=k1, img=img)
        text(d, (W / 2, 470), "= 1 очко урона", 66, alpha=k1, img=img, fill=YEL)
        k2 = pop(lt, 5.2, 0.5)
        text(d, (W / 2, 1560), "384 − 3", int(120 * k2))
        text(d, (W / 2, 1720), "≈ 380 урона", int(110 * k2), fill=RED)
    elif t < T_WATER:
        text(d, (W / 2, 220), "У ТЕБЯ ВСЕГО", 90)
        text(d, (W / 2, 380), "20 HP", 160, fill=RED)
        if t >= T_DIE:
            k = pop(t, T_DIE, 0.5)
            n = min(19, int(1 + (t - T_DIE) / 1.6 * 18))
            text(d, (W / 2, 1500), f"×{n}", int(240 * k), fill=YEL)
            text(d, (W / 2, 1720), "СМЕРТЕЙ ПОДРЯД", int(90 * k))
    else:
        text_block(d, W / 2, 300, "ИЛИ ПРОСТО ПОСТАВЬ ВОДУ", 96, max_w=980)
        if t >= T_END:
            k = pop(t, T_END, 0.4)
            text(d, (W / 2, 1560), "А ты бы успел?", int(100 * k), fill=YEL)
            pill(d, W / 2, 1720, "Пиши в комментах", int(62 * k), (95, 191, 58), (14, 42, 23))
    text(d, (W / 2, H - 50), "LowPolyLab", 38, stroke=5, bold=True)
    for s in (T_HEIGHT, T_RACE, T_DMG, T_HP, T_WATER):
        if 0 <= t - s < 0.12:
            img = Image.blend(img, Image.new("RGB", (W, H), (255, 255, 255)), (1 - (t - s) / 0.12) * 0.45)
    return img


if __name__ == "__main__":
    if len(sys.argv) > 4:
        for ts in map(float, sys.argv[4].split(",")):
            f = int(ts * FPS)
            overlay(base(f), f / FPS).save(f"{OUT}.{ts:05.1f}.png")
        sys.exit()
    enc = Encoder(OUT, sys.argv[2])
    for f in range(int(DUR * FPS)):
        enc.write(overlay(base(f), f / FPS))
    enc.close()
