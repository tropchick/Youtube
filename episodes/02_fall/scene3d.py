"""3D version of short #2. Usage:
python3 scene3d.py OUTDIR [start_frame end_frame step]
Renders PNG frames OUTDIR/f_00000.png (540x960, Cycles CPU)."""
import math
import os
import random
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "engine"))
from blocky import (reset, mat, srgb, cube, character, look_at, setup_render)

FPS = 30
DUR = 40.6
OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
F0 = int(sys.argv[2]) if len(sys.argv) > 2 else 0
F1 = int(sys.argv[3]) if len(sys.argv) > 3 else int(DUR * FPS)
STEP = int(sys.argv[4]) if len(sys.argv) > 4 else 1
SAMPLES = int(os.environ.get("SAMPLES", "10"))

T_HEIGHT, T_RACE, FALL_START = 5.1, 10.26, 10.6
MC_FALL, REAL_FALL = 7.25, 10.75
T_DMG, T_HP, T_DIE, T_WATER, T_END = 22.6, 30.58, 32.25, 35.5, 37.64
PH = 40.0  # visual pillar height (represents 384 blocks)
X_MC, X_RL = -2.5, 2.5
FY = -1.5  # characters jump off the front of the pillars

sc = reset(FPS)
setup_render(sc, samples=SAMPLES)

# --- world ---
w = bpy.data.worlds.new("sky")
w.use_nodes = True
bg = w.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (*srgb("#9fd0ff"), 1)
bg.inputs["Strength"].default_value = 1.0
sc.world = w

bpy.ops.object.light_add(type="SUN", location=(10, -10, 30))
sun = bpy.context.object
sun.data.energy = 3.5
sun.data.angle = math.radians(3)
sun.rotation_euler = (math.radians(50), math.radians(10), math.radians(35))


def arr(obj, axis, n, rel=1.0):
    m = obj.modifiers.new("a" + str(axis), "ARRAY")
    m.count = n
    m.relative_offset_displace = [rel if i == axis else 0 for i in range(3)]
    return m


# ground: grass grid via arrays
gt = cube((-30, -30, -0.1), (1, 1, 0.2), mat("grass_top", srgb("#6cbf48")), "ground_top", 0.02)
arr(gt, 0, 61)
arr(gt, 1, 61)
gd = cube((0, 0, -10.2), (61, 61, 20), mat("dirt", srgb("#8a6142")), "ground_dirt")

stone = mat("stone", srgb("#8d8d8d"))
stone_dark = mat("stone_dark", srgb("#6f6f6f"))
for x, m_ in ((X_MC, stone), (X_RL, mat("concrete", srgb("#b9a58a")))):
    p = cube((x, 0, 0.5), 1, m_, "pillar", 0.03)
    arr(p, 2, int(PH))
    top = cube((x, 0, PH + 0.4), (1, 1, 0.2), mat("grass_top", srgb("#6cbf48")), "ptop", 0.02)

# water block (hidden until the end)
water = cube((X_MC, FY, 0.5), (1.6, 1.6, 0.8), mat("water", srgb("#3c8cff"), rough=0.1), "water", 0.04)
water.scale = (0.001, 0.001, 0.001)

# Eiffel-like lattice tower (low-poly), height 330/384 of pillar
TH = PH * 330 / 384
tw_m = mat("iron", srgb("#9a7a5e"))
TX = -14
for sx in (-1, 1):
    for sy in (-1, 1):
        b = cube((TX + sx * 2.2, sy * 2.2, TH * 0.17), (0.7, 0.7, TH * 0.38), tw_m, "leg", 0.02)
        b.rotation_euler = (sy * math.radians(14), -sx * math.radians(14), 0)
cube((TX, 0, TH * 0.34), (4.2, 4.2, 0.5), tw_m, "deck1")
cube((TX, 0, TH * 0.62), (1.8, 1.8, TH * 0.56), tw_m, "upper", 0.02)
cube((TX, 0, TH * 0.6), (2.6, 2.6, 0.4), tw_m, "deck2")
cube((TX, 0, TH * 0.95), (0.25, 0.25, TH * 0.12), tw_m, "spire")

# trees + clouds for depth
random.seed(3)
leaf = mat("leaf", srgb("#3f8f3a"))
wood = mat("wood", srgb("#6b4a2b"))
for _ in range(26):
    x, y = random.uniform(-28, 28), random.uniform(-6, 28)
    if abs(x) < 6 and y < 6:
        continue
    h = random.randint(2, 4)
    cube((x, y, h / 2), (0.5, 0.5, h), wood, "trunk")
    cube((x, y, h + 0.6), 1.8, leaf, "leaves", 0.05)
cloud = mat("cloud", srgb("#ffffff"), rough=1)
for _ in range(14):
    cube((random.uniform(-40, 40), random.uniform(-10, 40), random.uniform(22, 34)),
         (random.uniform(3, 7), random.uniform(2, 4), 0.8), cloud, "cloud")

mc = character("mc", "#4fb83a")
rl = character("rl", "#3a8fe0")

# particles pool
part_m = mat("part", srgb("#ffffff"))
red_m = mat("heart", srgb("#e0283a"), emit=0.4)
dark_m = mat("heart_dark", srgb("#3a1418"))
water_p = mat("water_p", srgb("#7cc0ff"))
parts = [cube((0, 0, -50), 0.18, part_m, "p") for _ in range(24)]

HEART = [".XX.XX.", "XXXXXXX", "XXXXXXX", ".XXXXX.", "..XXX..", "...X..."]
hearts = []
for i in range(10):
    cubes = []
    for r, row in enumerate(HEART):
        for c, ch in enumerate(row):
            if ch == "X":
                cubes.append(cube((0, 0, -50), 0.1, red_m, "h"))
    hearts.append(cubes)

bpy.ops.object.camera_add()
cam = bpy.context.object
cam.data.lens = 28
sc.camera = cam


def mc_y(t):
    v = y = 0.0
    for _ in range(int(t * 20)):
        v = (v + 0.08) * 0.98
        y += v
    return min(y, 384.0)


def real_y(t):
    vt, g = 55.0, 9.81
    return min((vt ** 2 / g) * math.log(math.cosh(g * t / vt)), 384.0)


def ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def lerpv(a, b, k):
    return Vector(a).lerp(Vector(b), k)


def pose(ch, z, x, falling=False, t=0.0, lying=False, scale=1.0, y=FY):
    ch.location = (x, y, z)
    ch.scale = (scale, scale, scale)
    if lying:
        ch.rotation_euler = (math.radians(90), 0, 0)
    elif falling:
        ch.rotation_euler = (math.sin(t * 3) * 0.25, math.sin(t * 2.3) * 0.2, t * 0.8)
    else:
        ch.rotation_euler = (0, 0, 0)
    for an in ch["arms"]:
        a = bpy.data.objects[an]
        a.rotation_euler = (0, 0, 0)
        if falling:
            a.rotation_euler = (math.radians(180) + math.sin(t * 9) * 0.3, 0, 0)
            a.location.z = 1.4
        else:
            a.location.z = 1.0


def burst(objs, origin, t, material, spread=2.0, up=4.0, life=1.2, seed=1):
    rnd = random.Random(seed)
    for o in objs:
        dx, dy, dz = rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(0.4, 1)
        if t < 0 or t > life:
            o.location = (0, 0, -50)
            continue
        o.data.materials[0] = material
        o.location = (origin[0] + dx * spread * t, origin[1] + dy * spread * t,
                      origin[2] + dz * up * t - 4.9 * t * t)
        s = 0.18 * (1 - t / life)
        o.scale = (s, s, s)


def place_heart(cubes, center, px, material, drop=0.0):
    k = 0
    for r, row in enumerate(HEART):
        for c, ch in enumerate(row):
            if ch == "X":
                o = cubes[k]
                k += 1
                o.data.materials[0] = material
                o.location = (center[0] + (c - 3) * px, center[1], center[2] - r * px - drop)
                o.scale = (px * 0.95,) * 3


def hide_hearts():
    for h in hearts:
        for o in h:
            o.location = (0, 0, -50)


def update(t):
    hide_hearts()
    for o in parts:
        o.location = (0, 0, -50)
    water.scale = (0.001,) * 3
    ft = max(0.0, t - FALL_START)
    z_mc = PH + 0.5 - PH * mc_y(ft) / 384
    z_rl = PH + 0.5 - PH * real_y(ft) / 384
    z_mc = max(z_mc, 0.0)
    z_rl = max(z_rl, 0.0)
    if t < FALL_START:
        pose(mc, PH + 0.5 + abs(math.sin(t * 3)) * 0.08, X_MC, y=0)
        pose(rl, PH + 0.5, X_RL, y=0)
    elif t < T_DMG:
        mc_landed = ft >= MC_FALL
        rl_landed = ft >= REAL_FALL
        pose(mc, 0.15 if mc_landed else z_mc, X_MC, falling=not mc_landed, t=ft, lying=mc_landed)
        pose(rl, 0.15 if rl_landed else z_rl, X_RL, falling=not rl_landed, t=ft, lying=rl_landed)
        if mc_landed:
            burst(parts[:12], (X_MC, FY, 0.3), ft - MC_FALL, part_m, seed=2)
        if rl_landed:
            burst(parts[12:], (X_RL, FY, 0.3), ft - REAL_FALL, part_m, seed=3)
    elif t < T_WATER:
        pose(mc, 0.15, X_MC, lying=True)
        pose(rl, 0.15, X_RL, lying=True)
        if t >= T_DIE:
            # repeated "deaths": pop + respawn
            k = ((t - T_DIE) * 4) % 1.0
            pose(mc, 0.0, X_MC, scale=max(0.05, 1 - k))
            burst(parts[:12], (X_MC, FY, 0.8), k * 0.6, red_m, spread=2.5, up=3, life=0.6,
                  seed=int((t - T_DIE) * 4))
    else:
        lt = t - T_WATER
        pose(rl, -5, X_RL)
        ws = ease(lt / 0.4)
        water.scale = (1.6 * max(ws, 0.001), 1.6 * max(ws, 0.001), 0.8 * max(ws, 0.001))
        fall = min(1.0, lt / 1.7)
        zz = lerpv((0, 0, 14), (0, 0, 0.25), fall * fall).z
        pose(mc, zz, X_MC, falling=fall < 1, t=lt)
        if fall >= 1:
            burst(parts, (X_MC, FY, 0.9), lt - 1.7, water_p, spread=2.5, up=5, life=1.0, seed=9)

    # hearts
    if T_DMG + 1.0 <= t < T_DIE:
        lt = t - T_DMG
        for i in range(10):
            pop = ease((lt - 1.0 - i * 0.08) / 0.3)
            if pop <= 0:
                continue
            empty = t < T_HP and lt > 6.0
            drop = max(0.0, (lt - 6.0 - i * 0.05)) * 3 if empty else 0
            place_heart(hearts[i], (X_MC + 0.6 - 1.44 + i * 0.32, FY - 0.6, 2.4), 0.04 * pop,
                        dark_m if empty else red_m, drop=min(drop, 3.0))
        if t >= T_HP:
            for i in range(10):
                place_heart(hearts[i], (X_MC + 0.6 - 1.44 + i * 0.32, FY - 0.6, 2.4), 0.04, red_m)

    # camera
    if t < T_HEIGHT:
        a = -math.pi / 2 + t * 0.25
        cam.location = (math.cos(a) * 10, math.sin(a) * 10, PH + 3.5 - t * 0.2)
        look_at(cam, (0, 0, PH + 1.0))
    elif t < T_RACE:
        k = ease((t - T_HEIGHT) / 2.2)
        cam.location = lerpv((0, -7, PH + 2.5), (-4, -62, 24), k)
        look_at(cam, lerpv((0, 0, PH + 1), (-6, 0, 19), k))
    elif t < T_DMG:
        lo, hi = min(z_mc, z_rl), max(z_mc, z_rl)
        if t < FALL_START:
            lo = hi = PH
        mid = (lo + hi) / 2 + 0.8
        span = hi - lo
        dist = 11 + span * 1.25
        k = ease((t - T_RACE) / 0.6)
        target = Vector((0, FY - dist, mid + 1.5))
        cam.location = lerpv((-4, -62, 24), target, k)
        look_at(cam, lerpv((-6, 0, 19), (0, 0, mid), k))
    elif t < T_WATER:
        k = ease((t - T_DMG) / 0.8)
        cam.location = lerpv((0, -14, 4), (X_MC + 1.4, FY - 5.0, 2.0), k)
        look_at(cam, (X_MC + 0.6, FY, 1.2))
    else:
        lt = t - T_WATER
        cam.location = (X_MC + 4, FY - 7, 1.5 + lt * 0.3)
        look_at(cam, (X_MC, FY, 3.5 - min(lt, 2) * 1.0))


T_SPLIT0, T_SPLIT1 = T_RACE + 0.6, T_DMG


def follow(ch_z, x, landed):
    z = max(ch_z, 0.0)
    cam.location = (x + 1.2, FY - 6.5, z + (2.5 if not landed else 1.6))
    look_at(cam, (x, FY, z + (0.2 if not landed else 0.4)))


for f in range(F0, F1, STEP):
    t = f / FPS
    path = os.path.join(OUT, f"f_{f:05d}.png")
    if T_SPLIT0 <= t < T_SPLIT1:
        pa, pb = path[:-4] + "_a.png", path[:-4] + "_b.png"
        if os.path.exists(pb):
            continue
        update(t)
        ft = max(0.0, t - FALL_START)
        sc.render.resolution_x = 270
        for ch, x, fl, pth in ((mc, X_MC, MC_FALL, pa), (rl, X_RL, REAL_FALL, pb)):
            follow(ch.location.z, x, ft >= fl)
            sc.render.filepath = pth
            bpy.ops.render.render(write_still=True)
        sc.render.resolution_x = 540
        continue
    if os.path.exists(path):
        continue
    update(t)
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
