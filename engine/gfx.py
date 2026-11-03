"""Shared drawing helpers for LowPolyLab shorts (PIL frames -> ffmpeg)."""
import math
import subprocess
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
FONT_BLACK = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
FONT_BOLD = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
_font_cache = {}


def font(size, bold=False):
    key = (size, bold)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(FONT_BOLD if bold else FONT_BLACK, size)
    return _font_cache[key]


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_back(x):
    x = clamp(x)
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


def prog(t, start, dur):
    return clamp((t - start) / dur)


def lerp(a, b, k):
    return a + (b - a) * k


def lerp_col(c1, c2, k):
    return tuple(int(lerp(a, b, k)) for a, b in zip(c1, c2))


def vgradient(top, bottom, w=W, h=H):
    img = Image.new("RGB", (1, h))
    for y in range(h):
        img.putpixel((0, y), lerp_col(top, bottom, y / (h - 1)))
    return img.resize((w, h))


def text(d, xy, s, size, fill=(255, 255, 255), anchor="mm", stroke=8,
         stroke_fill=(0, 0, 0), bold=False, alpha=1.0, img=None):
    """Draw outlined text. If alpha<1, draws on an overlay (needs img)."""
    if size < 6:
        return
    f = font(size, bold)
    if alpha >= 0.999 or img is None:
        d.text(xy, s, font=f, fill=fill, anchor=anchor, stroke_width=stroke,
               stroke_fill=stroke_fill)
        return
    if alpha <= 0.001:
        return
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    a = int(255 * alpha)
    od.text(xy, s, font=f, fill=fill + (a,), anchor=anchor, stroke_width=stroke,
            stroke_fill=stroke_fill + (a,))
    img.alpha_composite(ov) if img.mode == "RGBA" else img.paste(ov, (0, 0), ov)


def wrap_lines(s, size, max_w):
    f = font(size)
    words, lines, cur = s.split(), [], ""
    for w_ in words:
        test = (cur + " " + w_).strip()
        if f.getlength(test) <= max_w:
            cur = test
        else:
            lines.append(cur)
            cur = w_
    if cur:
        lines.append(cur)
    return lines


def text_block(d, cx, cy, s, size, max_w=960, line_gap=1.12, **kw):
    if size < 6:
        return
    lines = wrap_lines(s, size, max_w)
    total = len(lines) * size * line_gap
    y = cy - total / 2 + size * line_gap / 2
    for ln in lines:
        text(d, (cx, y), ln, size, **kw)
        y += size * line_gap


def block(d, x, y, s, top, side, front, edge=(0, 0, 0)):
    """Flat 'low-poly' cube: front square + darker right/top bevel."""
    b = int(s * 0.18)
    d.polygon([(x, y), (x + b, y - b), (x + s + b, y - b), (x + s, y)], fill=top)
    d.polygon([(x + s, y), (x + s + b, y - b), (x + s + b, y + s - b), (x + s, y + s)], fill=side)
    d.rectangle([x, y, x + s, y + s], fill=front)
    d.rectangle([x, y, x + s, y + s], outline=edge, width=int(max(2, s // 20)))


def grass_block(d, x, y, s):
    block(d, x, y, s, (120, 200, 80), (70, 110, 45), (134, 96, 67))
    d.rectangle([x, y, x + s, y + s * 0.28], fill=(106, 170, 64))
    d.rectangle([x, y, x + s, y + s], outline=(0, 0, 0), width=int(max(2, s // 20)))


def cube_guy(d, cx, cy, s, body=(80, 170, 230), face=(240, 200, 160)):
    """Generic blocky character (original design): head + body cube."""
    hs = s * 0.55
    block(d, cx - s / 2, cy - s / 2, s, lerp_col(body, (255, 255, 255), .3),
          lerp_col(body, (0, 0, 0), .35), body)
    block(d, cx - hs / 2, cy - s / 2 - hs - 4, hs, lerp_col(face, (255, 255, 255), .3),
          lerp_col(face, (0, 0, 0), .3), face)
    e = hs * 0.16
    ey = cy - s / 2 - hs * 0.55
    d.rectangle([cx - hs * 0.28, ey, cx - hs * 0.28 + e, ey + e], fill=(30, 30, 40))
    d.rectangle([cx + hs * 0.12, ey, cx + hs * 0.12 + e, ey + e], fill=(30, 30, 40))


HEART = [".XX.XX.", "XXXXXXX", "XXXXXXX", ".XXXXX.", "..XXX..", "...X..."]


def heart(d, cx, cy, px, fill=(230, 40, 50), empty=False):
    w = len(HEART[0]) * px
    h = len(HEART) * px
    x0, y0 = cx - w / 2, cy - h / 2
    for r, row in enumerate(HEART):
        for c, ch in enumerate(row):
            if ch == "X":
                col = (60, 20, 25) if empty else fill
                d.rectangle([x0 + c * px, y0 + r * px, x0 + (c + 1) * px - 1, y0 + (r + 1) * px - 1], fill=col)
    if not empty:
        d.rectangle([x0 + px, y0 + px, x0 + 2 * px - 1, y0 + 2 * px - 1], fill=(255, 160, 160))


def pill(d, cx, cy, s, size, fill, tcol, pad=34):
    if size < 6:
        return
    f = font(size)
    tw = f.getlength(s)
    h = size * 1.6
    d.rounded_rectangle([cx - tw / 2 - pad, cy - h / 2, cx + tw / 2 + pad, cy + h / 2],
                        radius=h / 2, fill=fill)
    d.text((cx, cy), s, font=f, fill=tcol, anchor="mm")


class Encoder:
    def __init__(self, path, audio=None):
        cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
               "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-"]
        if audio:
            cmd += ["-i", audio, "-c:a", "aac", "-b:a", "192k", "-shortest"]
        cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "20",
                "-pix_fmt", "yuv420p", "-movflags", "+faststart", path]
        self.p = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    def write(self, img):
        self.p.stdin.write(img.convert("RGB").tobytes())

    def close(self):
        self.p.stdin.close()
        self.p.wait()
