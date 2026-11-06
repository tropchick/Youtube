"""Overlay text + sfx + voice on the 3D frames of short #5. Usage:
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
DUR = 40.64
T_MC, T_REAL, T_DENS, T_LIE, T_HEAT, T_FLOW, T_YEAR, T_VOLC, T_BOLT, T_END = (
    3.29, 7.93, 11.16, 17.40, 20.81, 24.82, 29.0, 31.4, 34.96, 37.64)
ORANGE = (255, 150, 40)
GREEN = (120, 220, 90)
BLUE = (110, 190, 255)
YEL = (255, 230, 80)
RED = (255, 90, 90)
CYAN = (110, 235, 235)
CUTS = (T_MC, T_REAL, T_FLOW, T_YEAR, T_BOLT, T_END)


def base(f):
    return Image.open(os.path.join(FR, f"f_{f:05d}.png")).convert("RGB").resize((W, H), Image.LANCZOS)


def pop(t, s, d=0.45):
    return max(ease_back(prog(t, s, d)), 0.0)


def overlay(img, t):
    d = ImageDraw.Draw(img)
    if t < T_MC:
        text_block(d, W / 2, 280, "ЧТО ЕСЛИ ПРЫГНУТЬ В ЛАВУ", int(96 * pop(t, 0.1)), max_w=1000)
        text(d, (W / 2, 1720), "в реальной жизни?", int(90 * pop(t, 1.2)), fill=ORANGE)
    elif t < T_REAL:
        lt = t - T_MC
        text(d, (W / 2, 220), "МАЙНКРАФТ", int(120 * pop(lt, 0)), fill=GREEN)
        text(d, (W / 2, 370), "тонешь, как в воде", int(76 * pop(lt, 0.4)))
        k = pop(t, 5.7, 0.5)
        text(d, (W / 2, 1600), "≈ 2 секунды", int(140 * k), fill=YEL)
        text(d, (W / 2, 1750), "и ты сгорел", int(80 * k))
    elif t < T_LIE:
        lt = t - T_REAL
        text(d, (W / 2, 220), "РЕАЛЬНОСТЬ", int(120 * pop(lt, 0)), fill=BLUE)
        text(d, (W / 2, 370), "ты НЕ утонешь", int(90 * pop(lt, 0.5)), fill=YEL)
        k = pop(t, T_DENS, 0.5)
        text(d, (W / 2, 1480), "лава плотнее", int(76 * k))
        text(d, (W / 2, 1600), "человека в ×3", int(100 * k), fill=ORANGE)
        k2 = pop(t, 15.39, 0.5)
        text(d, (W / 2, 1740), "и в 100 000+ раз гуще воды", int(62 * k2))
    elif t < T_HEAT:
        text_block(d, W / 2, 300, "ПРОСТО ЛЕЖИШЬ СВЕРХУ", int(100 * pop(t, T_LIE)), max_w=1000)
    elif t < T_FLOW:
        lt = t - T_HEAT
        text(d, (W / 2, 220), "НО ТЕМПЕРАТУРА", int(96 * pop(lt, 0)))
        text(d, (W / 2, 400), "1000+ °C", int(190 * pop(t, 22.98, 0.5)), fill=RED)
    elif t < T_YEAR:
        lt = t - T_FLOW
        text(d, (W / 2, 220), "ЛАВА В ИГРЕ", int(110 * pop(lt, 0)), fill=GREEN)
        text(d, (W / 2, 380), "1 блок за 1,5 с", int(96 * pop(t, 26.49)), fill=YEL)
        k = pop(t, 27.6, 0.5)
        text(d, (W / 2, 1620), "≈ 2,4 км/ч", int(130 * k), fill=ORANGE)
        text(d, (W / 2, 1760), "медленнее, чем ты ходишь", int(64 * k))
    elif t < T_BOLT:
        lt = t - T_YEAR
        text(d, (W / 2, 220), "НЬИРАГОНГО, 1977", int(96 * pop(lt, 0)), fill=ORANGE)
        text(d, (W / 2, 360), "Африка", int(70 * pop(lt, 0.4)))
        text(d, (W / 2, 1620), "≈ 60 км/ч", int(180 * pop(t, 33.1, 0.5)), fill=RED)
    elif t < T_END:
        lt = t - T_BOLT
        text(d, (W / 2, 220), "БЫСТРЕЕ", int(110 * pop(lt, 0)))
        text(d, (W / 2, 380), "УСЭЙНА БОЛТА", int(110 * pop(lt, 0.3)), fill=YEL)
        k = pop(lt, 0.8)
        text(d, (W / 2, 1600), "Болт ≈ 44 км/ч", int(84 * k), fill=BLUE)
        text(d, (W / 2, 1720), "лава ≈ 60 км/ч", int(84 * k), fill=RED)
    else:
        text_block(d, W / 2, 320, "А ТЫ ТЕРЯЛ АЛМАЗКИ В ЛАВЕ?", int(96 * pop(t, T_END)), fill=YEL, max_w=1000)
        pill(d, W / 2, 1700, "Пиши в комментах", int(70 * pop(t, T_END + 1.6)), (95, 191, 58), (14, 42, 23))
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

    def rumble(dur, vol):
        m = int(dur * sr)
        return noise(dur, 300) * 6 * np.sin(np.linspace(0, np.pi, m)) * vol

    for s in CUTS:
        add(s - 0.15, whoosh(0.4, 0.25))
    add(1.6, whoosh(1.0, 0.2))
    add(2.75, thud(0.6))
    add(2.8, sizzle(1.5, 0.45))
    add(T_MC + 0.3, sizzle(3.5, 0.3))
    add(5.7, pop_(0.4))
    add(T_REAL + 1.0, thud(0.7))
    add(T_REAL + 1.0, sizzle(1.2, 0.3))
    add(T_DENS, pop_(0.35))
    add(15.39, pop_(0.35))
    add(T_HEAT, sizzle(4.0, 0.5))
    add(22.98, thud(0.5))
    for n in range(5):
        add(T_FLOW + n * 1.5, pop_(0.25))
    add(T_YEAR, rumble(6.0, 0.6))
    add(T_VOLC, whoosh(3.0, 0.35))
    add(33.1, pop_(0.4))
    add(T_BOLT, whoosh(2.5, 0.25))
    add(T_END + 0.8, whoosh(0.5, 0.2))
    add(T_END + 1.35, sizzle(1.0, 0.45))
    add(T_END + 1.6, pop_(0.4))
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
