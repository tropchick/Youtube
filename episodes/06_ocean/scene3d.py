"""Short #6 (3D): diving to the ocean floor, Minecraft vs real life.
python3 scene3d.py OUTDIR [start end step]"""
import math
import os
import random
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "engine"))
from blocky import reset, mat, srgb, cube, character, look_at, setup_render

FPS, DUR = 30, 40.96
OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
F0 = int(sys.argv[2]) if len(sys.argv) > 2 else 0
F1 = int(sys.argv[3]) if len(sys.argv) > 3 else int(DUR * FPS)
STEP = int(sys.argv[4]) if len(sys.argv) > 4 else 1

T_MC, T_AIR, T_HUMAN, T_REC, T_TRENCH, T_11, T_EV, T_EV2, T_PRESS, T_POT, T_END = (
    3.29, 8.78, 13.22, 16.24, 19.03, 22.58, 25.53, 27.56, 31.18, 34.97, 38.83)

sc = reset(FPS)
setup_render(sc, samples=int(os.environ.get("SAMPLES", "10")))
w = bpy.data.worlds.new("sky")
w.use_nodes = True
bgn = w.node_tree.nodes["Background"]
sc.world = w

bpy.ops.object.light_add(type="SUN")
sun = bpy.context.object
sun.data.energy = 3.0
sun.data.angle = math.radians(3)
sun.rotation_euler = (math.radians(40), math.radians(15), math.radians(30))

GROUPS = {}


def group(name):
    c = bpy.data.collections.new(name)
    sc.collection.children.link(c)
    GROUPS[name] = c
    return c


def put(obj, coll):
    for c in obj.users_collection:
        c.objects.unlink(obj)
    coll.objects.link(obj)
    for ch in obj.children:
        put(ch, coll)
    return obj


def show(name):
    for n, c in GROUPS.items():
        c.hide_render = n != name


def sky(h, s=1.0):
    bgn.inputs["Color"].default_value = (*srgb(h), 1)
    bgn.inputs["Strength"].default_value = s


def ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def lerp(a, b, k):
    return Vector(a).lerp(Vector(b), k)


SAND = mat("sand", srgb("#e0d090"))
WOOD = mat("wood", srgb("#8a6a40"))
WATER = mat("water_top", srgb("#2f7fd8"), rough=0.15)
GRASSW = mat("seagrass", srgb("#3aa860"))
STONE = mat("stone", srgb("#8d8d8d"))
RULER_A = mat("ruler_a", srgb("#ffe14d"), emit=0.5)
RULER_B = mat("ruler_b", srgb("#ffffff"), emit=0.5)
BUBBLE = mat("bubble", srgb("#bfe8ff"), emit=0.8)
SPECK = mat("speck", srgb("#cfe6ff"), emit=1.5)
ROCK = mat("rock", srgb("#3c4250"))
SNOW = mat("snow", srgb("#f4f8ff"), emit=0.2)
MOUNT = mat("mount", srgb("#7d7468"))
GAP = mat("gap", srgb("#ffe14d"), emit=2.0)
CLOCK = mat("clock", srgb("#f2f2f2"), emit=0.4)
HAND = mat("hand", srgb("#e03030"), emit=0.8)
GLASS = mat("glass", srgb("#b060ff"), emit=1.2)
CORK = mat("cork", srgb("#a07850"))

g_surf = group("surf")
g_under = group("under")
g_trench = group("trench")

# ---------------- surface: dock over the ocean ----------------
for i in range(-20, 21, 2):
    for j in range(-6, 40, 2):
        put(cube((i, j, -0.5), (2, 2, 1), WATER, "sea"), g_surf)
for i in range(-1, 2):
    for j in range(-8, -1):
        put(cube((i, j, 0.15), (1, 1, 0.3), WOOD, "dock", 0.02), g_surf)

hero = character("hero", "#4caf50")
legs = [c for c in hero.children if c.name.startswith("hero_leg")]
arms = [c for c in hero.children if c.name.startswith("hero_arm")]
for p in legs + arms:
    z = p.location.z
    p.data = p.data.copy()
    for v in p.data.vertices:
        v.co.z -= 0.5
    p.location.z = z + 0.3

# ---------------- underwater (minecraft ocean) ----------------
FLOOR = -30
for i in range(-9, 10):
    for j in range(-4, 14):
        put(cube((i, j, FLOOR - 0.5 + 0.2 * ((i * 7 + j * 3) % 3 == 0)), 1, SAND, "sand"), g_under)
rnd = random.Random(2)
for _ in range(40):
    x, y = rnd.randint(-8, 8), rnd.randint(0, 12)
    h = rnd.uniform(0.6, 2.4)
    put(cube((x, y, FLOOR + h / 2), (0.15, 0.15, h), GRASSW, "kelp"), g_under)
for _ in range(14):
    x, y = rnd.uniform(-8, 8), rnd.uniform(3, 12)
    put(cube((x, y, FLOOR + 0.5), rnd.uniform(0.8, 1.8), STONE, "rock", 0.05), g_under)
ruler = []
for k in range(30):
    ruler.append(put(cube((-3.2, 1.0, -k - 0.5), (0.5, 0.5, 0.96), RULER_A if k % 2 else RULER_B, "ruler"), g_under))
surface_under = put(cube((0, 5, 0.05), (60, 60, 0.1), mat("surf_under", srgb("#7fc8ff"), emit=0.6), "surface"), g_under)
specks = [put(cube((0, 0, -99), 0.06, SPECK, "speck"), g_under) for _ in range(60)]
bubbles = [put(cube((0, 0, -99), 0.22, BUBBLE, "bub", 0.03), g_under) for _ in range(10)]
clock = bpy.data.objects.new("clock", None)
g_under.objects.link(clock)
put(cube((0, 0, 0), (1.6, 0.12, 1.6), CLOCK, "clock_face", 0.2, clock), g_under)
hand_pivot = bpy.data.objects.new("hand_pivot", None)
g_under.objects.link(hand_pivot)
hand_pivot.parent = clock
hand_pivot.location = (0, -0.1, 0)
put(cube((0, 0, 0.32), (0.08, 0.04, 0.64), HAND, "hand", 0, hand_pivot), g_under)
bottle = bpy.data.objects.new("bottle", None)
g_under.objects.link(bottle)
put(cube((0, 0, 0), (0.3, 0.3, 0.36), GLASS, "glass", 0.03, bottle), g_under)
put(cube((0, 0, 0.24), (0.12, 0.12, 0.12), CORK, "neck", 0.01, bottle), g_under)
shards = [put(cube((0, 0, -99), 0.08, GLASS, "shard"), g_under) for _ in range(10)]

# ---------------- trench cross-section (1 unit = 100 m) ----------------
TX = 400
put(cube((TX, 0, 0.3), (400, 4, 0.6), mat("sea_line", srgb("#6fc0ff"), emit=1.0), "surfline"), g_trench)
put(cube((TX, 1.5, -55), (400, 1, 110), mat("deep", srgb("#0c2a5a"), emit=0.25), "water_bg"), g_trench)
# sea floor at -40 with a V-shaped trench down to -110
for x in range(-150, 151, 2):
    ax = abs(x)
    depth = 40 if ax > 30 else 40 + (110 - 40) * (1 - ax / 30)
    h = 140 - depth
    put(cube((TX + x, 0, -depth - h / 2), (2.02, 3, h), ROCK, "floor"), g_trench)
everest = bpy.data.objects.new("everest", None)
g_trench.objects.link(everest)
for k in range(12):
    hh = 88.5 / 12
    s = 26 * (1 - k / 12)
    m_ = SNOW if k >= 10 else MOUNT
    put(cube((0, -0.4, hh * (k + 0.5)), (s, 2, hh), m_, "ev", 0.05, everest), g_trench)
gapbar = put(cube((TX, -1.0, -10.75), (2.5, 0.6, 21.5), GAP, "gap"), g_trench)
diver = put(cube((TX, -1.0, 0), (1.6, 1.0, 1.6), mat("diver", srgb("#ffd040"), emit=3.0), "diver", 0.2), g_trench)

cam_data = bpy.data.cameras.new("cam")
cam_data.lens = 24
cam_data.clip_end = 1000
cam = bpy.data.objects.new("cam", cam_data)
sc.collection.objects.link(cam)
sc.camera = cam


def cam_to(loc, target):
    cam.location = Vector(loc)
    look_at(cam, Vector(target))


def limbs(t, amt, rate=2.0):
    a = math.sin(t * 2 * math.pi * rate) * 0.9 * amt
    for i, l in enumerate(legs):
        l.rotation_euler = ((a if i else -a), 0, 0)
    for i, ar in enumerate(arms):
        ar.rotation_euler = ((-a if i else a), 0, 0)


def drift_specks(t, center):
    r = random.Random(6)
    for o in specks:
        x, y, z = r.uniform(-6, 6), r.uniform(-4, 8), r.uniform(-8, 8)
        o.location = (center[0] + x + 0.2 * math.sin(t + z), center[1] + y, center[2] + (z + t * 0.3) % 16 - 8)


def update(t):
    hero.scale = (1, 1, 1)
    hero.rotation_euler = (0, 0, math.radians(180))
    limbs(t, 0)
    for o in bubbles + shards:
        o.location = (0, 0, -99)
    clock.location = (0, 0, -99)
    bottle.location = (0, 0, -99)
    for o in specks:
        o.location = (0, 0, -99)

    if t < T_MC or t >= T_END:  # surface: dock
        show("surf")
        sky("#9fd0ff")
        put(hero, g_surf)
        if t < T_MC:
            if t < 2.2:
                hero.location = (0, -2.6, 0.3)
            else:
                k = (t - 2.2) / 0.9
                hero.location = (0, -2.6 + 2.5 * k, 0.3 + 1.6 * k - 3.0 * k * k)
                hero.rotation_euler = (math.radians(-60 * k), 0, math.radians(180))
            a = -1.15 + t * 0.1
            cam_to((math.cos(a) * 7, -2 + math.sin(a) * 7, 2.6), (0, 0, 0.6))
        else:
            lt = t - T_END
            hero.location = (0, -2.6, 0.3)
            hero.rotation_euler = (0, 0, math.radians(200))
            cam_to((2.8, -7.4, 2.0), (0, -1.5, 0.9))
    elif t < T_TRENCH or t >= T_PRESS:
        show("under")
        put(hero, g_under)
        if t < T_AIR:  # sinking 30 blocks
            sky("#1f5fae", 0.9)
            lt = t - T_MC
            z = -1 - 29 * ease(lt / 4.6)
            hero.location = (0, 1.0, z)
            hero.rotation_euler = (math.radians(-10), 0, math.radians(180))
            limbs(t, 0.5, rate=1.2)
            drift_specks(t, (0, 2, z))
            cam_to((3.8, -6.5, z + 1.6), (0, 1.0, z + 0.4))
        elif t < T_PRESS:  # on the floor: air bubbles, then the clock
            sky("#1a4f96", 0.85)
            hero.location = (0, 1.0, FLOOR)
            drift_specks(t, (0, 2, FLOOR + 3))
            lt = t - T_AIR
            if t < T_HUMAN:
                n_left = max(0, 10 - int(lt / 0.42))
                for i, o in enumerate(bubbles):
                    if i < n_left:
                        o.location = (-0.99 + i * 0.22, 1.0, FLOOR + 2.25 + 0.03 * math.sin(t * 4 + i))
                cam_to((1.6, -3.6, FLOOR + 2.0), (0, 1.0, FLOOR + 1.5))
            else:
                lt = t - T_HUMAN
                clock.location = (1.5, 0.6, FLOOR + 1.6)
                spin = (lt / 3.0) * 2 * math.pi if t < T_REC else 2 * math.pi + (t - T_REC) * 9
                hand_pivot.rotation_euler = (0, spin, 0)
                cam_to((2.2, -4.2, FLOOR + 1.8), (0.8, 0.8, FLOOR + 1.3))
        else:  # pressure / potion at the real bottom
            sky("#04101f", 0.6)
            hero.location = (0, 1.0, FLOOR)
            drift_specks(t, (0, 2, FLOOR + 3))
            if t < T_POT:
                lt = t - T_PRESS
                k = ease((lt - 0.4) / 1.2)
                hero.scale = (1 + 0.5 * k, 1 + 0.5 * k, 1 - 0.65 * k)
                cam_to((2.0, -4.0, FLOOR + 1.3), (0, 1.0, FLOOR + 0.6))
            else:
                lt = t - T_POT
                hero.scale = (1.5, 1.5, 0.35)
                if lt < 1.6:
                    bottle.location = (0.55, 0.6, FLOOR + 0.95 + 0.05 * math.sin(t * 5))
                    bottle.rotation_euler = (0, 0, t)
                else:
                    r = random.Random(3)
                    k = lt - 1.6
                    for o in shards:
                        dx, dy, dz = r.uniform(-1, 1), r.uniform(-1, 1), r.uniform(0, 1)
                        o.location = (0.55 + dx * 1.2 * k, 0.6 + dy * 1.2 * k, FLOOR + 0.95 + dz * 1.5 * k - 0.6 * k * k)
                cam_to((1.8, -3.4, FLOOR + 1.2), (0.3, 0.8, FLOOR + 0.7))
    else:  # trench cross-section
        show("trench")
        sky("#05070f", 0.4)
        if t < T_11:  # diver descends
            k = ease((t - T_TRENCH) / 3.4)
            diver.location = (TX, -1.0, -k * 108)
            cam_to((TX + 10, -80, 8 - k * 70), (TX, 0, -10 - k * 60))
        else:
            diver.location = (TX, -1.0, -108)
            cam_to((TX + 6, -150, -45), (TX, 0, -50))
        ev_k = ease((t - T_EV) / 1.4)
        everest.location = (TX, 0, -110)
        everest.scale = (1, 1, ev_k + 0.001)
        for ch in everest.children:
            ch.hide_render = t < T_EV
        gk = ease((t - T_EV2) / 0.8)
        gapbar.hide_render = t < T_EV2
        gapbar.scale = (2.5, 0.6, 21.5 * gk + 0.001)
        gapbar.location = (TX + 13, -1.0, -21.5 * gk / 2)


for f in range(F0, F1, STEP):
    path = os.path.join(OUT, f"f_{f:05d}.png")
    if os.path.exists(path):
        continue
    update(f / FPS)
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
