"""Overlay text + sfx + voice on the 3D frames of short #4. Usage:
python3 compose3d.py FRAMES_DIR VOICE.mp3 OUT.mp4 [preview_times]"""
import os
import subprocess
import sys
import wave

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "engine"))
from gfx import W, H, FPS, Encoder, text, text_block, pill, prog, ease_back, ease_out

FR, VO, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
DUR = 42.4
T_CUBE, T_STONE, T_INV, T_2304, T_SCALE, T_GOLD, T_X7, T_ALL, T_RUN, T_WATER, T_END = (
    3.08, 6.39, 8.86, 12.9, 15.66, 21.18, 23.91, 26.58, 33.43, 36.15, 39.57)
T_FIFTH = 28.33
GOLDC = (255, 200, 60)
YEL = (255, 230, 80)
RED = (255, 90, 90)
CYAN = (110, 235, 235)
CUTS = (T_CUBE, T_INV, T_SCALE, T_GOLD, T_X7, T_ALL, T_RUN, T_WATER, T_END)


def base(f):
    return Image.open(os.path.join(FR, f"f_{f:05d}.png")).convert("RGB").resize((W, H), Image.LANCZOS)


def pop(t, s, d=0.45):
    return max(ease_back(prog(t, s, d)), 0.0)


def overlay(img, t):
    d = ImageDraw.Draw(img)
    if t < T_CUBE:
        text_block(d, W / 2, 280, "СКОЛЬКО ВЕСИТ ТВОЙ ИНВЕНТАРЬ", int(92 * pop(t, 0.1)), max_w=1000)
        text(d, (W / 2, 1720), "в реальной жизни?", int(90 * pop(t, 1.3)), fill=YEL)
    elif t < T_STONE:
        lt = t - T_CUBE
        text(d, (W / 2, 220), "1 БЛОК", int(120 * pop(lt, 0)))
        text(d, (W / 2, 380), "= 1 м × 1 м × 1 м", int(84 * pop(lt, 0.9)), fill=YEL)
    elif t < T_INV:
        lt = t - T_STONE
        text(d, (W / 2, 220), "БЛОК КАМНЯ", 110)
        text(d, (W / 2, 390), "≈ 2,7 т", int(170 * pop(lt, 0.9)), fill=YEL)
    elif t < T_SCALE:
        lt = t - T_INV
        k = pop(lt, 0)
        text(d, (W / 2, 220), "36 ячеек × 64", int(110 * k))
        n = int(2304 * ease_out(prog(t, T_INV + 0.3, 5.0)))
        text(d, (W / 2, 390), f"{n:,} блока".replace(",", " "), int(130 * pop(t, T_2304 - 3.6)), fill=YEL)
    elif t < T_GOLD:
        lt = t - T_SCALE
        text(d, (W / 2, 220), "≈ 6 200 т КАМНЯ", int(100 * pop(lt, 0)), fill=YEL)
        k = pop(t, 18.4, 0.5)
        text(d, (W / 2, 1560), "почти как весь металл", int(70 * k))
        text(d, (W / 2, 1680), "Эйфелевой башни", int(84 * k))
        text(d, (W / 2, 1800), "(≈ 7 300 т)", int(64 * k), fill=YEL)
    elif t < T_X7:
        lt = t - T_GOLD
        text_block(d, W / 2, 300, "А ТЕПЕРЬ ЗОЛОТЫЕ БЛОКИ", int(100 * pop(lt, 0)), fill=GOLDC, max_w=1000)
    elif t < T_ALL:
        lt = t - T_X7
        text(d, (W / 2, 260), "×7", int(260 * pop(lt, 0.3)), fill=GOLDC)
        text(d, (W / 2, 450), "тяжелее камня", int(90 * pop(lt, 0.6)))
    elif t < T_RUN:
        lt = t - T_ALL
        n = int(44500 * ease_out(prog(lt, 0, 1.4)))
        text(d, (W / 2, 220), f"≈ {n:,} т".replace(",", " "), 140, fill=GOLDC)
        k = pop(t, T_FIFTH, 0.5)
        text(d, (W / 2, 1560), "1/5 всего золота,", int(96 * k), fill=YEL)
        text(d, (W / 2, 1700), "добытого людьми", int(80 * k))
        text(d, (W / 2, 1800), "за всю историю", int(64 * k))
    elif t < T_WATER:
        lt = t - T_RUN
        text_block(d, W / 2, 300, "А ТЫ С ЭТИМ БЕГАЕШЬ И ПРЫГАЕШЬ", int(90 * pop(lt, 0)), max_w=1000)
    elif t < T_END:
        lt = t - T_WATER
        text(d, (W / 2, 220), "ВЕДРО ВОДЫ", int(120 * pop(lt, 0)), fill=(110, 180, 255))
        text(d, (W / 2, 380), "= 1 м³ = 1000 л", int(90 * pop(lt, 0.8)))
        text(d, (W / 2, 1640), "= 1 ТОННА", int(150 * pop(t, 37.6, 0.5)), fill=YEL)
    else:
        text_block(d, W / 2, 320, "ЧТО БЫ ТЫ СЛОЖИЛ В ИНВЕНТАРЬ?", int(96 * pop(t, T_END)), fill=YEL, max_w=1000)
        pill(d, W / 2, 1700, "Пиши в комментах", int(70 * pop(t, T_END + 1.2)), (95, 191, 58), (14, 42, 23))
    text(d, (W / 2, H - 50), "LowPolyLab", 38, stroke=5, bold=True)
    for s in CUTS:
        if 0 <= t - s < 0.12:
            img = Image.blend(img, Image.new("RGB", (W, H), (255, 255, 255)), (1 - (t - s) / 0.12) * 0.45)
    return img


def sfx(path):
    sr = 44100
    n = int(DUR * sr)
    out = np.zeros(n)
    rng = np.random.default_rng(3)

    def add(t0, sig):
        i = int(t0 * sr)
        if i < n:
            out[i:i + len(sig)] += sig[:n - i]

    def noise(dur, smooth):
        m = int(dur * sr)
        return np.convolve(rng.standard_normal(m), np.ones(smooth) / smooth, mode="same")

    def whoosh(dur, vol):
        m = int(dur * sr)
        return noise(dur, 40) * np.sin(np.linspace(0, np.pi, m)) ** 2 * vol

    def hit(vol):  # stone pick hit: short noise click + low knock
        m = int(0.12 * sr)
        tt = np.arange(m) / sr
        return (noise(0.12, 4) * 0.6 + np.sin(2 * np.pi * 180 * tt)) * np.exp(-tt * 45) * vol

    def thud(vol):
        m = int(0.35 * sr)
        tt = np.arange(m) / sr
        return np.sin(2 * np.pi * (90 - 120 * tt) * tt) * np.exp(-tt * 14) * vol

    def pop_(vol):
        m = int(0.12 * sr)
        tt = np.arange(m) / sr
        return np.sin(2 * np.pi * 880 * tt) * np.exp(-tt * 40) * vol

    def sizzle(dur, vol):
        m = int(dur * sr)
        return noise(dur, 2) * np.exp(-np.linspace(0, 4, m)) * vol

    for s in CUTS:
        add(s - 0.15, whoosh(0.4, 0.25))
    add(T_CUBE + 0.5, thud(0.6))
    add(T_STONE + 0.9 + 0.357, thud(1.0))
    add(T_STONE + 0.9, pop_(0.3))
    for x in np.arange(T_INV + 0.3, T_SCALE - 0.6, 0.06):
        add(x + rng.uniform(0, 0.04), hit(0.12))
    add(T_2304, pop_(0.4))
    add(T_SCALE + 0.1, thud(0.5))
    add(18.4, pop_(0.35))
    for x in np.arange(T_GOLD + 0.1, T_GOLD + 2.3, 0.09):
        add(x, pop_(0.08))
    add(T_X7 + 0.35, thud(1.0))
    add(T_X7 + 0.4, hit(0.6))
    for i in range(4):
        add(28.4 + i * 0.35 + 0.4, thud(0.8))
    add(T_FIFTH, pop_(0.4))
    for x in np.arange(T_RUN + 0.2, T_RUN + 1.0, 0.25):
        add(x, hit(0.15))
    for x in np.arange(T_RUN + 1.7, T_WATER, 0.7):
        add(x, thud(0.7))
    add(T_WATER + 0.1, sizzle(0.6, 0.3))
    add(37.6, pop_(0.4))
    add(T_END + 1.2, pop_(0.4))
    out = np.clip(out, -1, 1)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((out * 32767 * 0.6).astype(np.int16).tobytes())


if __name__ == "__main__":
    if len(sys.argv) > 4:
        for ts in map(float, sys.argv[4].split(",")):
            f = int(ts * FPS)
            overlay(base(f), f / FPS).save(f"{OUT}.{ts:05.1f}.png")
        sys.exit()
    sfx(OUT + ".sfx.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", VO, "-i", OUT + ".sfx.wav",
                    "-filter_complex",
                    "[0:a]apad[v];[v][1:a]amix=inputs=2:duration=longest:normalize=0,atrim=0:%s" % DUR,
                    OUT + ".audio.m4a"], check=True)
    enc = Encoder(OUT, OUT + ".audio.m4a")
    for f in range(int(DUR * FPS)):
        enc.write(overlay(base(f), f / FPS))
    enc.close()
