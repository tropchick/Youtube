"""Insert a sponsor banner into a finished 1080x1920 video.
The main video pauses at AT seconds (a voice pause): its frame is held, dimmed and blurred, and the
banner plays centered at full screen width (nothing cropped) with its own audio. Then the video goes on.
A green-screen background around the banner (corner pixel pure green) is keyed out automatically.
The banner sits exactly in the middle only if the input is exactly 2*AT long. The user does not want a
frozen picture at the end (2026-11-08), so a shorter input is refused: render/extend the real ending
to 2*AT seconds first (or pick another AT). --allow-pad overrides this.
python3 banner.py IN.mp4 BANNER.mp4 AT OUT.mp4 [--allow-pad]"""
import json
import subprocess
import sys

IN, BAN, AT, OUT = sys.argv[1], sys.argv[2], float(sys.argv[3]), sys.argv[4]
ALLOW_PAD = "--allow-pad" in sys.argv


def dur(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", p],
                       capture_output=True, text=True, check=True)
    return float(json.loads(r.stdout)["format"]["duration"])


L, B = dur(IN), dur(BAN)
if abs(2 * AT - L) > 0.1 and not ALLOW_PAD:
    sys.exit(f"input is {L:.2f}s; for a centered banner at AT={AT} it must be {2 * AT:.2f}s. "
             f"Extend/trim the real video, or use AT={L / 2:.2f}.")
pad = max(0.0, 2 * AT - L)
probe = json.loads(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                   "stream=width,height", "-of", "json", BAN],
                                  capture_output=True, text=True, check=True).stdout)["streams"][0]
BW = 1080
BH = round(BW * probe["height"] / probe["width"] / 2) * 2
corner = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(min(1.0, B / 2)), "-i", BAN, "-frames:v", "1",
                         "-vf", "crop=4:4:0:0", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                        capture_output=True, check=True).stdout[:3]
KEY = corner[1] > 200 and corner[0] < 60 and corner[2] < 60
import os
import tempfile

tmp = tempfile.mkdtemp()
# video: cut, hold+banner, rest (no audio in this pass)
fc = (
    f"[0:v]trim=0:{AT},setpts=PTS-STARTPTS[v1];"
    f"[0:v]trim={AT}:{L},setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration={pad}[v2];"
    f"[0:v]trim={AT - 0.04}:{AT},setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration={B},"
    f"trim=0:{B},eq=brightness=-0.25,boxblur=6[hold];"
    f"[1:v]scale={BW}:{BH},fps=30,trim=0:{B},setpts=PTS-STARTPTS"
    + (",format=rgba,colorkey=0x00FE00:0.35:0.08" if KEY else "") + "[ban];"
    f"[hold][ban]overlay=(W-w)/2:(H-h)/2:shortest=1,setpts=PTS-STARTPTS[vb];"
    f"[v1][vb][v2]concat=n=3:v=1:a=0,fps=30[v]"
)
vid = os.path.join(tmp, "v.mp4")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", IN, "-i", BAN, "-filter_complex", fc, "-map", "[v]",
                "-an", "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-r", "30", vid], check=True)
# audio: one continuous PCM track built sample-exactly
import numpy as np


def pcm(path, start=None, dur=None):
    cmd = ["ffmpeg", "-v", "error"]
    if start is not None:
        cmd += ["-ss", str(start)]
    cmd += ["-i", path]
    if dur is not None:
        cmd += ["-t", str(dur)]
    cmd += ["-vn", "-ac", "2", "-ar", "44100", "-f", "f32le", "-"]
    return np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.float32).reshape(-1, 2)


SR = 44100
main = pcm(IN)
ban = pcm(BAN)
n_at, n_b = int(round(AT * SR)), int(round(B * SR))
ban = np.pad(ban[:n_b], ((0, max(0, n_b - len(ban))), (0, 0)))
total = int(round((L + B + pad) * SR))
audio = np.concatenate([main[:n_at], ban, main[n_at:]])
audio = np.pad(audio[:total], ((0, max(0, total - len(audio))), (0, 0)))
wav = os.path.join(tmp, "a.f32")
audio.astype(np.float32).tofile(wav)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", vid, "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", wav,
                "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                "-movflags", "+faststart", OUT], check=True)
T = dur(OUT)
print(f"total {T:.2f}s, banner {AT:.2f}-{AT + B:.2f}, middle {T / 2:.2f}, banner center {AT + B / 2:.2f}, "
      f"banner {BW}x{BH}, area {BW * BH / (1080 * 1920) * 100:.1f}%, green key {KEY}")
