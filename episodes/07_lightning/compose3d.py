"""Overlay text + sfx + voice on the 3D frames of short #7. Usage:
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
DUR = 44.8
T_MC, T_STEAK, T_HOT, T_SUN, T_VOLT, T_SOCK, T_SURV, T_NINE, T_ROY, T_EARTH, T_END = (
    3.4, 7.0, 8.9, 13.9, 16.9, 19.8, 22.45, 24.0, 27.0, 32.95, 37.35)
STRIKE0 = 1.9
ROY_HITS = [29.9 + 0.42 * i for i in range(7)]
HEAT_HITS = [T_HOT + s for s in (0.0, 1.1, 2.3, 3.4)]
VOLT_HITS = [T_VOLT + s for s in (0.0, 0.8, 1.7, 2.5, 3.6, 4.6)]
ORANGE = (255, 150, 40)
GREEN = (120, 220, 90)
BLUE = (110, 190, 255)
YEL = (255, 230, 80)
RED = (255, 90, 90)
CYAN = (110, 235, 235)
CUTS = (T_HOT, T_VOLT, T_SURV, T_ROY, T_EARTH, T_END)


def base(f):
    return Image.open(os.path.join(FR, f"f_{f:05d}.png")).convert("RGB").resize((W, H), Image.LANCZOS)


def pop(t, s, d=0.45):
    return max(ease_back(prog(t, s, d)), 0.0)


def overlay(img, t):
    d = ImageDraw.Draw(img)
    if t < T_MC:
        text(d, (W / 2, 230), "ЧТО ЕСЛИ В ТЕБЯ", int(96 * pop(t, 0.1)))
        text_block(d, W / 2, 450, "УДАРИТ МОЛНИЯ?", int(110 * pop(t, 1.2)), fill=YEL, max_w=1000)
        text(d, (W / 2, 1720), "как в Майнкрафте", int(80 * pop(t, 2.3)), fill=GREEN)
    elif t < T_HOT:
        lt = t - T_MC
        text(d, (W / 2, 220), "В МАЙНКРАФТЕ", int(110 * pop(lt, 0)), fill=GREEN)
        text(d, (W / 2, 1560), "−2,5 сердца", int(130 * pop(t, 4.3)), fill=RED)
        text(d, (W / 2, 1700), "+ немного огня", int(80 * pop(t, 6.0)), fill=ORANGE)
        text(d, (W / 2, 1820), "съел стейк — и дальше", int(64 * pop(t, T_STEAK + 0.1)))
    elif t < T_VOLT:
        lt = t - T_HOT
        text(d, (W / 2, 210), "В РЕАЛЬНОСТИ", int(110 * pop(lt, 0)))
        n = int(30000 * ease_out(prog(t, T_HOT + 0.6, 3.6)))
        if t >= T_HOT + 0.6:
            text(d, (W / 2, 370), f"{n:,} °C".replace(",", " "), 140, fill=CYAN)
        k = pop(t, T_SUN, 0.5)
        text(d, (W / 2, 1560), "×5", int(200 * k), fill=ORANGE)
        text(d, (W / 2, 1730), "горячее поверхности Солнца", int(62 * k))
    elif t < T_SURV:
        lt = t - T_VOLT
        text(d, (W / 2, 210), "НАПРЯЖЕНИЕ", int(110 * pop(lt, 0)))
        n = int(300e6 * ease_out(prog(t, 17.9, 1.8)))
        if t >= 17.9:
            text(d, (W / 2, 370), f"{n:,} В".replace(",", " "), 120, fill=YEL)
        k = pop(t, T_SOCK + 0.3, 0.5)
        text(d, (W / 2, 1560), "×1 000 000", int(150 * k), fill=RED)
        text(d, (W / 2, 1720), "больше, чем в розетке (220 В)", int(60 * k))
    elif t < T_ROY:
        text(d, (W / 2, 230), "НО...", int(120 * pop(t, T_SURV)))
        text(d, (W / 2, 420), "9 из 10", int(190 * pop(t, T_NINE)), fill=GREEN)
        text(d, (W / 2, 1700), "выживают", int(110 * pop(t, 26.08)), fill=GREEN)
    elif t < T_EARTH:
        text(d, (W / 2, 210), "РОЙ САЛЛИВАН", int(100 * pop(t, 28.72)), fill=YEL)
        text(d, (W / 2, 330), "смотритель парка, США", int(60 * pop(t, 27.84)))
        hits = sum(1 for h in ROY_HITS if t >= h)
        if hits:
            text(d, (W / 2, 1560), f"УДАРОВ: {hits}", int(130 * pop(t, ROY_HITS[hits - 1], 0.25)), fill=CYAN)
        text(d, (W / 2, 1740), "рекорд Гиннесса", int(84 * pop(t, 31.68)), fill=ORANGE)
    elif t < T_END:
        text(d, (W / 2, 210), "НА ЗЕМЛЕ", int(110 * pop(t, T_EARTH + 0.1)))
        text(d, (W / 2, 380), "40+ ударов", int(150 * pop(t, 34.44)), fill=YEL)
        text(d, (W / 2, 1680), "КАЖДУЮ СЕКУНДУ", int(100 * pop(t, 35.9)), fill=CYAN)
    else:
        text_block(d, W / 2, 320, "А ТЕБЯ БИЛО МОЛНИЕЙ?", int(104 * pop(t, T_END)), fill=YEL, max_w=1000)
        if t < 41.0:
            pill(d, W / 2, 1700, "Пиши в комментах", int(70 * pop(t, 39.36)), (95, 191, 58), (14, 42, 23))
        else:
            pill(d, W / 2, 1700, "Подпишись на LowPolyLab", int(66 * pop(t, 41.0)), (230, 60, 60), (255, 255, 255))
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

    def pop_(vol):
        m = int(0.12 * sr)
        tt = np.arange(m) / sr
        return np.sin(2 * np.pi * 880 * tt) * np.exp(-tt * 40) * vol

    def crack(vol):  # sharp lightning crack
        m = int(0.25 * sr)
        tt = np.arange(m) / sr
        return noise(0.25, 3) * np.exp(-tt * 18) * vol

    def rumble(dur, vol):
        m = int(dur * sr)
        env = np.exp(-np.linspace(0, 3, m)) * np.minimum(1, np.linspace(0, 8, m))
        return noise(dur, 300) * 6 * env * vol

    def thunder(t0, vol):
        add(t0, crack(vol * 0.5))
        add(t0 + 0.05, rumble(2.2, vol))

    def crackle(t0, dur, vol):  # fire
        for x in np.arange(t0, t0 + dur, 0.07):
            add(x + rng.uniform(0, 0.05), crack(vol * rng.uniform(0.2, 1.0))[: int(0.03 * sr)])

    def bite(vol):
        m = int(0.08 * sr)
        tt = np.arange(m) / sr
        return noise(0.08, 6) * np.exp(-tt * 50) * vol

    rain_n = noise(DUR, 6) * 0.05
    out += rain_n * np.array([0 if (T_HOT <= i / sr < T_VOLT or T_EARTH <= i / sr < T_END) else 1 for i in range(0, n)])
    for s in CUTS:
        add(s - 0.15, whoosh(0.4, 0.2))
    thunder(STRIKE0, 0.9)
    crackle(STRIKE0 + 0.4, 1.0, 0.25)
    crackle(T_MC, T_STEAK - T_MC + 0.4, 0.25)
    add(4.3, pop_(0.35))
    for k in range(3):
        add(T_STEAK + 0.3 + k * 0.18, bite(0.5))
    for h in HEAT_HITS:
        add(h, crack(0.4))
    add(T_HOT + 0.1, rumble(4.0, 0.5))
    add(T_SUN, pop_(0.4))
    for h in VOLT_HITS:
        thunder(h, 0.6)
    add(T_SOCK + 0.3, pop_(0.4))
    add(T_SOCK + 0.5, crack(0.15))
    thunder(T_NINE - 0.6, 0.8)
    add(T_NINE, pop_(0.4))
    for h in ROY_HITS:
        add(h, crack(0.5))
    add(ROY_HITS[0], rumble(3.5, 0.5))
    add(31.68, pop_(0.4))
    for x in np.arange(T_EARTH + 0.5, T_END, 0.23):
        add(x + rng.uniform(0, 0.1), crack(0.12))
    thunder(T_END + 1.2, 0.5)
    add(41.0, pop_(0.4))
    thunder(42.0, 0.7)
    thunder(43.6, 0.5)
    add(39.36, pop_(0.4))
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
                    ("[0:a]apad,asplit[v][key];[1:a]volume=0.6[fx];[fx][key]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=300[duck];"
                     "[v][duck]amix=inputs=2:duration=longest:normalize=0,atrim=0:%s" % DUR),
                    OUT + ".audio.m4a"], check=True)
    enc = Encoder(OUT, OUT + ".audio.m4a")
    for f in range(int(DUR * FPS)):
        enc.write(overlay(base(f), f / FPS))
    enc.close()
