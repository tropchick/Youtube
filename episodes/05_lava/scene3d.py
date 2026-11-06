"""Short #5 (3D): jumping into lava in Minecraft vs real life.
python3 scene3d.py OUTDIR [start end step]"""
import math
import os
import random
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "engine"))
from blocky import reset, mat, srgb, cube, character, look_at, setup_render

FPS, DUR = 30, 40.64
OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
F0 = int(sys.argv[2]) if len(sys.argv) > 2 else 0
F1 = int(sys.argv[3]) if len(sys.argv) > 3 else int(DUR * FPS)
STEP = int(sys.argv[4]) if len(sys.argv) > 4 else 1

T_MC, T_REAL, T_DENS, T_LIE, T_HEAT, T_FLOW, T_YEAR, T_VOLC, T_BOLT, T_END = (
    3.29, 7.93, 11.16, 17.40, 20.81, 24.82, 29.0, 31.4, 34.96, 37.64)

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
sun.rotation_euler = (math.radians(45), math.radians(15), math.radians(30))

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


GRASS = mat("grass_top", srgb("#6cbf48"))
DIRT = mat("dirt", srgb("#8a6142"))
STONE = mat("stone", srgb("#8d8d8d"))
BASALT = mat("basalt", srgb("#3a3538"))
LAVA = mat("lava", srgb("#ff6a10"), emit=1.6)
LAVA2 = mat("lava_dark", srgb("#e04a08"), emit=1.2)
FIRE = mat("fire", srgb("#ffb030"), emit=4.0)
SMOKE = mat("smoke", srgb("#5a5a5a"), rough=1)
DIA = mat("diamond", srgb("#5fe0e0"), emit=0.3)
WOOD = mat("wood", srgb("#6b4a2b"))
LEAF = mat("leaf", srgb("#3f8f3a"))
CRATER = mat("crater", srgb("#ff4a10"), emit=6.0)

g_pool = group("pool")
g_field = group("field")
g_volc = group("volc")

# ---------------- pool: lava lake + stone ledge ----------------
lava_cells = []
for i in range(-7, 8):
    for j in range(-3, 12):
        m_ = LAVA if (i + j) % 3 else LAVA2
        lava_cells.append(put(cube((i, j, -0.5), 1, m_, "lava"), g_pool))
for i in range(-7, 8):
    for j in (-4, -5, -6):
        put(cube((i, j, -0.3 + (0.0 if j == -4 else 0.1 * (-4 - j))), 1, STONE, "ledge", 0.02), g_pool)
for i in range(-9, 10):
    for j in range(13, 16):
        put(cube((i, j, 1.0 + (j - 13) * 1.2), (1, 1, 3), BASALT, "wall", 0.02), g_pool)

hero = character("hero", "#4caf50")
put(hero, g_pool)
legs = [c for c in hero.children if c.name.startswith("hero_leg")]
arms = [c for c in hero.children if c.name.startswith("hero_arm")]
for p in legs + arms:
    z = p.location.z
    p.data = p.data.copy()
    for v in p.data.vertices:
        v.co.z -= 0.5
    p.location.z = z + 0.3
hero_mats = [bpy.data.materials["skin"], bpy.data.materials["hero_body"], bpy.data.materials["pants"]]
hero_cols = [tuple(m_.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value) for m_ in hero_mats]

pick = bpy.data.objects.new("pick", None)
sc.collection.objects.link(pick)
cube((0, 0, 0), (0.08, 0.08, 0.9), WOOD, "handle", 0.01, pick)
cube((0, 0, 0.42), (0.7, 0.1, 0.12), DIA, "head", 0.01, pick)
for s in (-1, 1):
    cube((s * 0.38, 0, 0.36), (0.12, 0.1, 0.16), DIA, "tip", 0.01, pick)
put(pick, g_pool)

fire = [put(cube((0, 0, -99), 0.2, FIRE, "fire"), g_pool) for _ in range(16)]
smoke = [put(cube((0, 0, -99), 0.4, SMOKE, "smoke"), g_pool) for _ in range(14)]

# ---------------- field: game lava creeping block by block ----------------
FY = 200
put(cube((0, FY + 10, -0.5), (60, 60, 1), GRASS, "ground", 0.0), g_field)
src = put(cube((-4, FY, 0.45), (1, 1, 0.9), LAVA, "src"), g_field)
flow = [put(cube((-4 + n, FY, 0.0), 1, LAVA, "flow"), g_field) for n in range(1, 6)]
rnd = random.Random(4)
for _ in range(24):
    x, y = rnd.uniform(-25, 25), rnd.uniform(FY + 8, FY + 35)
    h = rnd.uniform(2, 4)
    put(cube((x, y, h / 2), (0.6, 0.6, h), WOOD, "trunk"), g_field)
    put(cube((x, y, h + 1), 2.6, LEAF, "crown", 0.05), g_field)
walker = character("walker", "#4caf50")
put(walker, g_field)
wlegs = [c for c in walker.children if c.name.startswith("walker_leg")]
for p in wlegs:
    z = p.location.z
    p.data = p.data.copy()
    for v in p.data.vertices:
        v.co.z -= 0.5
    p.location.z = z + 0.3

# ---------------- volcano ----------------
VY = 400
put(cube((0, VY - 40, -0.5), (200, 200, 1), mat("ash", srgb("#6b6258")), "ground_v"), g_volc)
for k in range(10):
    s = 34 - k * 3.1
    put(cube((0, VY, 0.75 + k * 1.5), (s, s, 1.5), BASALT if k % 2 else mat("rock2", srgb("#4a4245")), "cone", 0.05), g_volc)
put(cube((0, VY, 15.3), (3.5, 3.5, 0.4), CRATER, "crater"), g_volc)
slope = put(cube((0, VY, 0), (2.4, 1, 0.5), LAVA, "slope"), g_volc)
river = put(cube((0, VY, 0), (3.0, 1, 0.5), LAVA, "river"), g_volc)
runner = character("runner", "#4caf50")
put(runner, g_volc)
rlegs = [c for c in runner.children if c.name.startswith("runner_leg")]
rarms = [c for c in runner.children if c.name.startswith("runner_arm")]
for p in rlegs + rarms:
    z = p.location.z
    p.data = p.data.copy()
    for v in p.data.vertices:
        v.co.z -= 0.5
    p.location.z = z + 0.3
plume = [put(cube((0, 0, -99), 1.6, SMOKE, "plume"), g_volc) for _ in range(12)]

cam_data = bpy.data.cameras.new("cam")
cam_data.lens = 24
cam = bpy.data.objects.new("cam", cam_data)
sc.collection.objects.link(cam)
sc.camera = cam


def cam_to(loc, target):
    cam.location = Vector(loc)
    look_at(cam, Vector(target))


def limbs(ls, as_, t, amt, rate=2.2):
    a = math.sin(t * 2 * math.pi * rate) * 0.9 * amt
    for i, l in enumerate(ls):
        l.rotation_euler = ((a if i else -a), 0, 0)
    for i, ar in enumerate(as_):
        ar.rotation_euler = ((-a if i else a), 0, 0)


def particles(objs, t, origin, seed, life=1.0, up=2.5, spread=0.8, size=0.2, loop=True):
    r = random.Random(seed)
    for n, o in enumerate(objs):
        off = r.uniform(0, life)
        dx, dy = r.uniform(-1, 1), r.uniform(-1, 1)
        if t < 0:
            o.location = (0, 0, -99)
            continue
        lt = ((t + off) % life) if loop else (t - off * 0.3)
        if lt < 0 or lt > life:
            o.location = (0, 0, -99)
            continue
        k = lt / life
        o.location = (origin[0] + dx * spread * k, origin[1] + dy * spread * k, origin[2] + up * k)
        s = size * (1 - k * 0.6) if objs is fire else size * (0.6 + k)
        o.scale = (s, s, s)


def tint(k):
    """k: 0 normal, 1 charred."""
    for m_, c in zip(hero_mats, hero_cols):
        bc = m_.node_tree.nodes["Principled BSDF"].inputs["Base Color"]
        bc.default_value = (c[0] * (1 - k) + 0.03 * k, c[1] * (1 - k) + 0.03 * k, c[2] * (1 - k) + 0.03 * k, 1)


def update(t):
    for i, o in enumerate(lava_cells):
        x, y = o.location.x, o.location.y
        o.location.z = -0.5 + 0.06 * math.sin(t * 1.7 + x * 0.9 + y * 1.3)
    particles(fire, -1, (0, 0, 0), 1)
    particles(smoke, -1, (0, 0, 0), 2)
    particles(plume, -1, (0, 0, 0), 3)
    hero.rotation_euler = (0, 0, 0)
    limbs(legs, arms, t, 0)
    tint(0)
    pick.location = (0, 0, -99)

    if t < T_FLOW or t >= T_END:
        show("pool")
        sky("#1a0c0a", 0.35)
    elif t < T_YEAR:
        show("field")
        sky("#9fd0ff")
    else:
        show("volc")
        sky("#7a5a50", 0.6)

    if t < T_MC:  # hook: run-up and jump into the lava
        hero.rotation_euler = (0, 0, math.radians(180))
        if t < 1.6:
            hero.location = (0, -5.4, 0.2)
        else:
            k = (t - 1.6) / 1.2
            hero.location = (0, -5.4 + 4.0 * min(k, 1), 0.2 + 2.2 * k - 2.6 * k * k)
            limbs(legs, arms, t, 0.6)
        a = -1.2 + t * 0.12
        cam_to((math.cos(a) * 7.5, -3 + math.sin(a) * 7.5, 3.0), (0, -2.5, 0.8))
    elif t < T_REAL:  # minecraft: sink and burn in ~2 s
        lt = t - T_MC
        hero.location = (0, 0, -0.3 - 0.55 * lt)
        hero.rotation_euler = (0, 0, math.radians(180) + lt * 0.4)
        limbs(legs, arms, t, 1.0, rate=3)
        tint(min(0.7, lt / 3))
        particles(fire, lt, (0, 0, 0.1), 5, life=0.8, up=2.0, spread=1.0, size=0.25)
        cam_to((2.6, -4.2, 1.6), (0, 0, 0.2))
    elif t < T_HEAT:  # real: lands on top and lies there
        lt = t - T_REAL
        if lt < 1.0:
            k = lt / 1.0
            hero.location = (0, 1.0, 5 - 4.86 * k * k)
            hero.rotation_euler = (math.radians(70 * k), 0, math.radians(180))
        else:
            bob = 0.03 * math.sin(lt * 2)
            sink = 0.12 * (1 - math.exp(-(lt - 1) * 3))
            hero.location = (0, 1.0, 0.14 - sink + bob)
            hero.rotation_euler = (math.radians(90), 0, math.radians(180))
        if t < T_LIE:
            a = -1.9 + lt * 0.05
            cam_to((math.cos(a) * 4.6, 1 + math.sin(a) * 4.6, 2.2), (0, 1.5, 0.2))
        else:
            k = ease((t - T_LIE) / 2.5)
            cam_to(lerp((2.2, -2.6, 1.3), (1.4, -1.2, 2.4), k), (0, 1.4, 0.15))
    elif t < T_FLOW:  # 1000+ degrees: smoke, charring
        lt = t - T_HEAT
        hero.location = (0, 1.0, 0.02)
        hero.rotation_euler = (math.radians(90), 0, math.radians(180))
        tint(min(0.85, lt / 2.5))
        particles(smoke, lt, (0, 1.6, 0.3), 7, life=1.6, up=4.0, spread=1.5, size=0.35)
        particles(fire, lt, (0, 1.6, 0.2), 8, life=0.6, up=1.2, spread=1.4, size=0.2)
        k = ease(lt / 4.0)
        cam_to(lerp((2.5, -2.5, 1.6), (4.5, -5.5, 4.5), k), (0, 1.5, 0.6))
    elif t < T_YEAR:  # game lava creeps: 1 block per 1.5 s
        lt = t - T_FLOW
        for n, o in enumerate(flow):
            k = ease((lt - n * 1.5) / 0.4)
            hgt = max(0.15, 0.8 - n * 0.16)
            o.scale = (1, 1, hgt * k + 0.001)
            o.location.z = hgt * k / 2
            o.hide_render = k <= 0
        walker.location = (-4 + 1.4 * lt, FY - 1.6, 0)
        walker.rotation_euler = (0, 0, math.radians(90))
        limbs(wlegs, [], t, 0.7, rate=1.6)
        cx = -4 + 1.4 * lt - 0.8
        cam_to((cx, FY - 8, 2.4), (cx, FY, 0.5))
    elif t < T_END:  # volcano: lava races downhill
        lt = t - T_YEAR
        particles(plume, lt, (0, VY, 15.5), 9, life=3.0, up=14, spread=6, size=1.4)
        # lava front distance from the crater along the path (m)
        tv = max(0.0, t - T_VOLC)
        front = 16.7 * tv  # 60 km/h = 16.7 m/s
        # slope segment from crater (y=VY-2, z=15) down to the foot (y=VY-17, z=0)
        L1 = math.hypot(15, 15)
        s1 = min(front, L1) + 0.001
        ang = math.atan2(15, 15)
        slope.scale = (2.4, s1, 0.5)
        slope.rotation_euler = (ang, 0, 0)
        slope.location = (0, VY - 2 - (s1 / 2) * math.cos(ang), 15 - (s1 / 2) * math.sin(ang) + 0.3)
        s2 = max(0.001, front - L1)
        river.scale = (3.0, s2, 0.5)
        river.location = (0, VY - 17 - s2 / 2, 0.25)
        # runner: starts at the foot, runs at Bolt's top speed (12.3 m/s = 44 km/h)
        ry = VY - 22 - 12.3 * max(0.0, t - (T_VOLC + 0.8))
        runner.location = (2.3, ry, 0)
        runner.rotation_euler = (0, 0, 0)
        limbs(rlegs, rarms, t, 1.0 if t > T_VOLC + 0.8 else 0.0, rate=3.2)
        if t < T_BOLT:
            k = ease((t - T_YEAR) / 2.4)
            cam_to(lerp((40, VY - 70, 30), (28, VY - 60, 14), k), lerp((0, VY, 10), (0, VY - 22, 5), k))
        else:
            cam_to((14, ry - 6, 4.0), (1.5, ry - 3, 0.8))
    else:  # CTA: diamond pickaxe dropped into lava
        lt = t - T_END
        hero.location = (0, -4.4, 0.2)
        hero.rotation_euler = (0, 0, math.radians(180))
        arms[1].rotation_euler = (math.radians(-80), 0, 0)
        if lt < 0.8:
            pick.location = (0.36, -3.6, 1.2)
            pick.rotation_euler = (0, math.radians(20), 0)
        else:
            k = lt - 0.8
            pick.location = (0.36, -3.6 + 1.2 * k, 1.2 - 4.9 * k * k)
            pick.rotation_euler = (k * 6, math.radians(20), 0)
            if pick.location.z < -0.2:
                pick.location = (0, 0, -99)
                particles(fire, k - 0.55, (0.36, -2.9, 0.1), 11, life=0.7, up=1.6, spread=0.8, size=0.22, loop=True)
        cam_to((3.2, -7.6, 2.2), (0.2, -3.6, 0.8))


for f in range(F0, F1, STEP):
    path = os.path.join(OUT, f"f_{f:05d}.png")
    if os.path.exists(path):
        continue
    update(f / FPS)
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
