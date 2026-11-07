"""Overlay text + sfx + voice on the 3D frames of short #6. Usage:
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
DUR = 40.96
T_MC, T_AIR, T_HUMAN, T_REC, T_TRENCH, T_11, T_EV, T_EV2, T_PRESS, T_POT, T_END = (
    3.29, 8.78, 13.22, 16.24, 19.03, 22.58, 25.53, 27.56, 31.18, 34.97, 38.83)
ORANGE = (255, 150, 40)
GREEN = (120, 220, 90)
BLUE = (110, 190, 255)
YEL = (255, 230, 80)
RED = (255, 90, 90)
CYAN = (110, 235, 235)
CUTS = (T_MC, T_HUMAN, T_TRENCH, T_PRESS, T_END)


def base(f):
    return Image.open(os.path.join(FR, f"f_{f:05d}.png")).convert("RGB").resize((W, H), Image.LANCZOS)


def pop(t, s, d=0.45):
    return max(ease_back(prog(t, s, d)), 0.0)


def overlay(img, t):
    d = ImageDraw.Draw(img)
    if t < T_MC:
        text_block(d, W / 2, 280, "ЧТО ЕСЛИ НЫРНУТЬ НА САМОЕ ДНО", int(92 * pop(t, 0.1)), max_w=1000)
        text(d, (W / 2, 1720), "как в Майнкрафте?", int(90 * pop(t, 1.2)), fill=BLUE)
    elif t < T_AIR:
        lt = t - T_MC
        text(d, (W / 2, 220), "ОКЕАН В ИГРЕ", int(110 * pop(lt, 0)), fill=GREEN)
        n = int(30 * ease_out(prog(lt, 0.2, 4.4)))
        text(d, (W / 2, 380), f"−{n} блоков", 120, fill=YEL)
    elif t < T_HUMAN:
        lt = t - T_AIR
        text(d, (W / 2, 220), "ВОЗДУХ", int(110 * pop(lt, 0)), fill=BLUE)
        text(d, (W / 2, 390), "15 секунд", int(130 * pop(lt, 0.4)), fill=YEL)
        text(d, (W / 2, 1680), "потом теряешь сердечки", int(70 * pop(t, 10.9)), fill=RED)
    elif t < T_REC:
        lt = t - T_HUMAN
        text(d, (W / 2, 220), "ОБЫЧНЫЙ ЧЕЛОВЕК", int(100 * pop(lt, 0)))
        text(d, (W / 2, 390), "≈ 1 минута", int(140 * pop(lt, 1.2)), fill=YEL)
    elif t < T_TRENCH:
        lt = t - T_REC
        text(d, (W / 2, 220), "РЕКОРД", int(120 * pop(lt, 0)), fill=ORANGE)
        text(d, (W / 2, 400), "11 мин 35 с", int(140 * pop(lt, 0.7)), fill=YEL)
    elif t < T_EV:
        text_block(d, W / 2, 230, "МАРИАНСКАЯ ВПАДИНА", int(96 * pop(t, 20.9)), fill=BLUE, max_w=1000)
        m = int(10900 * ease_out(prog(t, T_TRENCH, 3.4)))
        text(d, (W / 2, 1640), f"−{m:,} м".replace(",", " "), 150, fill=YEL)
        text(d, (W / 2, 1790), "почти 11 км вниз", int(66 * pop(t, T_11)))
    elif t < T_PRESS:
        text(d, (W / 2, 210), "ЭВЕРЕСТ — 8 849 м", int(96 * pop(t, T_EV)), fill=(240, 240, 240))
        text(d, (W / 2, 350), "помещается целиком", int(70 * pop(t, T_EV + 0.6)))
        k = pop(t, T_EV2, 0.5)
        text(d, (W / 2, 1640), "+ 2 км воды", int(140 * k), fill=YEL)
        text(d, (W / 2, 1790), "над вершиной", int(80 * k))
    elif t < T_POT:
        lt = t - T_PRESS
        text(d, (W / 2, 220), "ДАВЛЕНИЕ", int(120 * pop(lt, 0)))
        text(d, (W / 2, 420), "×1000", int(220 * pop(t, 32.53, 0.5)), fill=RED)
    elif t < T_END:
        text_block(d, W / 2, 300, "ЗЕЛЬЕ ПОДВОДНОГО ДЫХАНИЯ НЕ СПАСЁТ", int(84 * pop(t, 35.6)), fill=(200, 140, 255), max_w=1000)
    else:
        text_block(d, W / 2, 320, "А ТЫ БЫ НЫРНУЛ?", int(110 * pop(t, T_END)), fill=YEL, max_w=1000)
        pill(d, W / 2, 1700, "Пиши в комментах", int(70 * pop(t, 40.0)), (95, 191, 58), (14, 42, 23))
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
        return noise(dur, 14) * np.exp(-np.linspace(0, 4, m)) * vol * 0.35

    def rumble(dur, vol):
        m = int(dur * sr)
        return noise(dur, 300) * 6 * np.sin(np.linspace(0, np.pi, m)) * vol

    for s in CUTS:
        add(s - 0.15, whoosh(0.4, 0.25))
    add(2.9, whoosh(0.6, 0.3))
    add(3.15, sizzle(0.8, 0.5))
    add(7.9, thud(0.5))
    for i in range(10):
        add(T_AIR + i * 0.42, pop_(0.18))
    for x in np.arange(T_HUMAN, T_TRENCH - 0.2, 0.5):
        add(x, hit(0.12))
    add(T_TRENCH, rumble(6.0, 0.5))
    add(T_EV, rumble(1.6, 0.6))
    add(T_EV2, pop_(0.35))
    add(T_PRESS + 0.5, thud(0.8))
    add(32.53, pop_(0.35))
    add(T_POT + 1.6, hit(0.6))
    add(T_POT + 1.62, sizzle(0.5, 0.4))
    add(T_END, whoosh(0.8, 0.2))
    add(40.0, pop_(0.4))
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
