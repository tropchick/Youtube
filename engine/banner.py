"""Insert the 5 s sponsor banner into a finished 1080x1920 video.
The main video pauses at AT seconds (pick a voice pause near the middle): its last frame is held,
dimmed, and the banner plays centered with its own audio. Then the video continues.
If AT is past the middle, the end is extended by holding the last frame so the banner sits exactly
in the middle of the final video.
python3 banner.py IN.mp4 BANNER.mp4 AT OUT.mp4 [height_px]
height_px default 360 = full screen width edge to edge, nothing cropped (user wants this)."""
import json
import subprocess
import sys

IN, BAN, AT, OUT = sys.argv[1], sys.argv[2], float(sys.argv[3]), sys.argv[4]
BH = int(sys.argv[5]) if len(sys.argv) > 5 else 360


def dur(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", p],
                       capture_output=True, text=True, check=True)
    return float(json.loads(r.stdout)["format"]["duration"])


L, B = dur(IN), dur(BAN)
pad = max(0.0, 2 * AT - L)  # hold the last frame so the banner is centered
BW = round(BH * 3 / 2) * 2  # banner is 3:1
fc = (
    f"[0:v]trim=0:{AT},setpts=PTS-STARTPTS[v1];"
    f"[0:v]trim={AT}:{L},setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration={pad}[v2];"
    f"[0:v]trim={AT - 0.04}:{AT},setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration={B},"
    f"trim=0:{B},eq=brightness=-0.25,boxblur=6[hold];"
    f"[1:v]scale={BW}:{BH},crop=min(iw\\,1080):ih,fps=30[ban];"
    f"[hold][ban]overlay=(W-w)/2:(H-h)/2,setpts=PTS-STARTPTS[vb];"
    f"[0:a]atrim=0:{AT},asetpts=PTS-STARTPTS[a1];"
    f"[0:a]atrim={AT}:{L},asetpts=PTS-STARTPTS,apad=pad_dur={pad}[a2];"
    f"[1:a]aresample=44100,atrim=0:{B},asetpts=PTS-STARTPTS[ab];"
    f"[0:a]aresample=44100[x];[x]anullsink;"
    f"[v1][a1][vb][ab][v2][a2]concat=n=3:v=1:a=1[v][a]"
)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", IN, "-i", BAN, "-filter_complex", fc,
                "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", OUT], check=True)
T = dur(OUT)
print(f"total {T:.2f}s, banner {AT:.2f}-{AT + B:.2f}, middle {T / 2:.2f}, banner center {AT + B / 2:.2f}, "
      f"area {1080 * BH / (1080 * 1920) * 100:.1f}%" if BW >= 1080 else f"area {BW * BH / (1080 * 1920) * 100:.1f}%")
