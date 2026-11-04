"""Overlay text + sfx + voice on the 3D frames of short #3. Usage:
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
DUR = 40.6
T_SHAFT, T_PICK, T_KOLA, T_DIVE, T_HOUR, T_EARTH, T_HEAT, T_END = 3.6, 7.6, 12.4, 16.6, 21.0, 24.9, 32.1, 37.4
T_KM, T_WEEKS, T_BUCKET = 26.0, 28.64, 35.26
YEL = (255, 230, 80)
RED = (255, 90, 90)
CYAN = (110, 235, 235)
CUTS = (T_SHAFT, T_PICK, T_KOLA, T_DIVE, T_HOUR, T_EARTH, T_HEAT, T_END)


def base(f):
    return Image.open(os.path.join(FR, f"f_{f:05d}.png")).convert("RGB").resize((W, H), Image.LANCZOS)


def pop(t, s, d=0.45):
    return max(ease_back(prog(t, s, d)), 0.0)


def overlay(img, t):
    d = ImageDraw.Draw(img)
    if t < T_SHAFT:
        text_block(d, W / 2, 280, "ЧТО ЕСЛИ КОПАТЬ ВНИЗ", int(96 * pop(t, 0.1)), max_w=980)
        text_block(d, W / 2, 470, "КАК В МАЙНКРАФТЕ?", int(104 * pop(t, 1.0)), fill=YEL, max_w=1000)
    elif t < T_PICK:
        lt = t - T_SHAFT
        text(d, (W / 2, 220), "ДНО МИРА", 110)
        n = int(127 * ease_out(prog(lt, 0.2, 3.2)))
        text(d, (W / 2, 380), f"−{n} блоков", 120, fill=YEL)
        text(d, (W / 2, 1740), "от уровня моря", int(66 * pop(lt, 0.6)))
    elif t < T_KOLA:
        lt = t - T_PICK
        text(d, (W / 2, 220), "АЛМАЗНАЯ КИРКА", int(100 * pop(lt, 0)), fill=CYAN)
        k = pop(lt, 3.1, 0.5)
        text(d, (W / 2, 1520), "0,3 с", int(200 * k), fill=YEL)
        text(d, (W / 2, 1700), "на блок камня", int(80 * k))
    elif t < T_DIVE:
        lt = t - T_KOLA
        text_block(d, W / 2, 260, "КОЛЬСКАЯ СВЕРХГЛУБОКАЯ СКВАЖИНА", int(80 * pop(lt, 0)), max_w=1000)
        k = pop(t, 16.1, 0.5)
        text(d, (W / 2, 1580), "12 262 м", int(170 * k), fill=YEL)
        text(d, (W / 2, 1740), "самая глубокая дыра на Земле", int(56 * k))
    elif t < T_HOUR:
        lt = t - T_DIVE
        m = int(12262 * ease_out(prog(lt, 0.1, 4.0)))
        text(d, (W / 2, 220), f"{m:,} м".replace(",", " "), 130, fill=YEL)
        k = pop(lt, 0.5)
        text(d, (W / 2, 1560), "≈ 20 ЛЕТ", int(170 * k), fill=RED)
        text(d, (W / 2, 1720), "бурения (1970–1989)", int(64 * k))
    elif t < T_EARTH:
        lt = t - T_HOUR
        text(d, (W / 2, 200), "АЛМАЗНОЙ КИРКОЙ:", int(84 * pop(lt, 0)), fill=CYAN)
        text(d, (W / 2, 360), "≈ 1 ЧАС", int(190 * pop(lt, 0.35)), fill=YEL)
        k = pop(lt, 1.4)
        text(d, (W / 2, 1640), "вместо 20 лет", int(84 * k))
        mm = min(61, int(61 * prog(lt, 0, 3.6)))
        text(d, (W / 2, 1780), f"{mm} мин", int(60 * k), fill=YEL)
    elif t < T_HEAT:
        text(d, (W / 2, 200), "ДО ЦЕНТРА ЗЕМЛИ", int(92 * pop(t, T_EARTH + 0.1)))
        n = int(6370 * ease_out(prog(t, T_KM, 2.2)))
        if t >= T_KM:
            text(d, (W / 2, 360), f"{n:,} км".replace(",", " "), 140, fill=YEL)
        k = pop(t, T_WEEKS, 0.5)
        text(d, (W / 2, 1560), "≈ 3 НЕДЕЛИ", int(140 * k), fill=YEL)
        text(d, (W / 2, 1720), "копать без перерыва", int(70 * k))
    elif t < T_END:
        lt = t - T_HEAT
        text(d, (W / 2, 210), "ВНИЗУ ПОЧТИ", int(90 * pop(lt, 0)))
        text(d, (W / 2, 380), "5000 °C", int(180 * pop(lt, 0.8)), fill=RED)
        k = pop(t, T_BUCKET, 0.5)
        text(d, (W / 2, 1600), "ведро воды", int(90 * k), fill=CYAN)
        text(d, (W / 2, 1730), "не поможет", int(90 * k), fill=RED)
    else:
        text_block(d, W / 2, 330, "А ТЫ КАК ГЛУБОКО КОПАЛ?", int(100 * pop(t, T_END)), fill=YEL, max_w=980)
        pill(d, W / 2, 1700, "Пиши в комментах", int(70 * pop(t, T_END + 0.5)), (95, 191, 58), (14, 42, 23))
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
    for x in np.arange(1.6, 3.0, 0.3):  # first block in the hook
        add(x, hit(0.35))
    add(3.0, thud(0.5))
    for x in np.arange(T_SHAFT + 0.3, T_SHAFT + 3.4, 0.17):  # fast descent
        add(x, hit(0.25))
    for c in np.arange(T_PICK, T_KOLA, 1.2):  # 0.3 s break cycle
        add(c + 0.05, hit(0.4))
        add(c + 0.15, hit(0.4))
        add(c + 0.3, thud(0.6))
    add(16.1, pop_(0.4))
    add(T_DIVE, whoosh(4.2, 0.12))
    for x in np.arange(T_HOUR, T_EARTH, 0.1):
        add(x, hit(0.18))
    add(T_HOUR + 0.35, pop_(0.4))
    add(T_KM, pop_(0.35))
    add(T_WEEKS, pop_(0.4))
    add(T_HEAT + 0.8, thud(0.6))
    add(T_HEAT + 3.8, sizzle(1.6, 0.5))
    add(T_END + 0.5, pop_(0.4))
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
