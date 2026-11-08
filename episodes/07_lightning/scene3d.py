"""Short #7 (3D): getting struck by lightning, Minecraft vs real life.
python3 scene3d.py OUTDIR [start end step]"""
import math
import os
import random
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "engine"))
from blocky import reset, mat, srgb, cube as ops_cube, character, look_at, setup_render

FPS, DUR = 30, 40.9
OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
F0 = int(sys.argv[2]) if len(sys.argv) > 2 else 0
F1 = int(sys.argv[3]) if len(sys.argv) > 3 else int(DUR * FPS)
STEP = int(sys.argv[4]) if len(sys.argv) > 4 else 1

T_MC, T_STEAK, T_HOT, T_SUN, T_VOLT, T_SOCK, T_SURV, T_NINE, T_ROY, T_EARTH, T_END = (
    3.4, 7.0, 8.9, 13.9, 16.9, 19.8, 22.45, 24.0, 27.0, 32.95, 37.35)
STRIKE0 = 1.9
ROY_HITS = [29.9 + 0.42 * i for i in range(7)]

sc = reset(FPS)
setup_render(sc, samples=int(os.environ.get("SAMPLES", "10")))
w = bpy.data.worlds.new("sky")
w.use_nodes = True
bgn = w.node_tree.nodes["Background"]
sc.world = w

bpy.ops.object.light_add(type="SUN")
sun = bpy.context.object
sun.data.energy = 1.2
sun.data.angle = math.radians(3)
sun.rotation_euler = (math.radians(40), math.radians(15), math.radians(30))
bpy.ops.object.light_add(type="POINT")
flash = bpy.context.object
flash.data.shadow_soft_size = 2.0
flash.data.color = (0.75, 0.85, 1.0)

GROUPS = {}
_meshes = {}


def cube(loc, size, material, name="c", bevel=0.0, parent=None):
    """Fast cube: shares one unit mesh per material (no bpy.ops per object)."""
    m = _meshes.get(material.name)
    if m is None:
        tmp = ops_cube((0, 0, 0), 1, material, "tmpl")
        m = tmp.data
        bpy.data.objects.remove(tmp)
        _meshes[material.name] = m
    o = bpy.data.objects.new(name, m)
    sc.collection.objects.link(o)
    o.location = loc
    o.scale = size if isinstance(size, (tuple, list)) else (size, size, size)
    if bevel:
        mod = o.modifiers.new("b", "BEVEL")
        mod.width = bevel
        mod.segments = 1
    if parent:
        o.parent = parent
    return o


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


def vis(obj, on):
    obj.hide_render = not on
    for ch in obj.children:
        vis(ch, on)


def sky(h, s=1.0):
    bgn.inputs["Color"].default_value = (*srgb(h), 1)
    bgn.inputs["Strength"].default_value = s


def ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


GRASS = mat("grass_top", srgb("#5aa83c"))
DIRT = mat("dirt", srgb("#7a5538"))
BOLT = mat("bolt", srgb("#dfeaff"), emit=25.0)
FIRE_A = mat("fire_a", srgb("#ff8a1e"), emit=6.0)
FIRE_B = mat("fire_b", srgb("#ffd23a"), emit=6.0)
HEART = mat("heart", srgb("#ff2a3a"), emit=1.5)
HEART_OFF = mat("heart_off", srgb("#3a2228"))
STEAK = mat("steak", srgb("#9a4a2a"))
RAIN = mat("rain", srgb("#9fb8e0"), emit=0.6)
LCOL = mat("l_col", srgb("#cfe0ff"), emit=4.0)
SCOL = mat("s_col", srgb("#ffa020"), emit=4.0)
SUNB = mat("sun_block", srgb("#ffc030"), emit=12.0)
GLASS = mat("tube", srgb("#3a4660"))
WALL = mat("wall", srgb("#c9b48a"))
PLATE = mat("plate", srgb("#f4f4f4"))
HOLE = mat("hole", srgb("#202020"))
SPARK = mat("spark", srgb("#fff2a0"), emit=10.0)
DEAD = mat("dead", srgb("#555555"))
LEAF = mat("leaf", srgb("#2f7a2f"))
LOG = mat("log", srgb("#6a4a2a"))
HAT = mat("hat", srgb("#8a6a3a"))
OCEAN = mat("ocean", srgb("#2a6fd0"))
LAND = mat("land", srgb("#4caf50"))
CLOUD = mat("cloud", srgb("#2a2e3a"))
SPOT = mat("spot", srgb("#ffffff"), emit=30.0)

g_hill = group("hill")
g_heat = group("heat")
g_volt = group("volt")
g_crowd = group("crowd")
g_roy = group("roy")
g_earth = group("earth")


def bolt(seed, top, bottom, n=10, thick=0.35, coll=None, branches=2):
    """Zigzag lightning made of stretched cubes under one empty (positions relative)."""
    r = random.Random(seed)
    root = bpy.data.objects.new("bolt", None)
    (coll or sc.collection).objects.link(root)
    top, bottom = Vector(top), Vector(bottom)
    pts = [top]
    for i in range(1, n):
        p = top.lerp(bottom, i / n)
        span = (top - bottom).length / n
        pts.append(p + Vector((r.uniform(-0.6, 0.6) * span, r.uniform(-0.2, 0.2) * span, 0)))
    pts.append(bottom)

    def seg(a, b, th):
        d = b - a
        o = cube((a + b) / 2, (th, th, d.length + th * 0.6), BOLT, "bseg", 0, root)
        o.rotation_mode = "QUATERNION"
        o.rotation_quaternion = d.to_track_quat("Z", "Y")
        put(o, coll or sc.collection)

    for a, b in zip(pts, pts[1:]):
        seg(a, b, thick)
    for k in range(branches):
        i = r.randint(1, n - 3)
        a = pts[i]
        b = a + Vector((r.choice((-1, 1)) * r.uniform(0.5, 1.0), 0, -r.uniform(0.8, 1.4))) * (top - bottom).length / n * 2
        seg(a, b, thick * 0.6)
    return root


def strike(b, t, t0, dur=0.35, base_energy=5000, loc=None):
    """Show bolt b with flicker between t0 and t0+dur; return flash level 0..1."""
    starts = t0 if isinstance(t0, (list, tuple)) else [t0]
    on = any(0 <= t - s0 < dur and (int((t - s0) * FPS) % 3 != 1) for s0 in starts)
    vis(b, on)
    if on:
        flash.location = loc or (b.location + Vector((0, -2, 6)))
        flash.data.energy = base_energy
        return 1.0
    return 0.0


# ---------------- hill (hook, minecraft, end) ----------------
for i in range(-7, 8):
    for j in range(-6, 12):
        h = 0.0 if abs(i) < 3 and abs(j - 1) < 3 else -0.5 * ((i * 5 + j * 3) % 2)
        put(cube((i, j, h - 0.6), (1, 1, 0.2), GRASS, "g"), g_hill)
        put(cube((i, j, h - 1.2), (1, 1, 1.0), DIRT, "d"), g_hill)
hero = character("hero", "#3f8fe0")
legs = [c for c in hero.children if c.name.startswith("hero_leg")]
arms = [c for c in hero.children if c.name.startswith("hero_arm")]
for p in legs + arms:
    z = p.location.z
    p.data = p.data.copy()
    for v in p.data.vertices:
        v.co.z -= 0.5
    p.location.z = z + 0.3
hero.location = (0, 0, -0.5)
put(hero, g_hill)
b_hill = bolt(1, (0, 0, 30), (0, 0, 1.3), n=12, coll=g_hill)
b_far = bolt(5, (9, 18, 30), (9, 18, -1), n=10, thick=0.6, coll=g_hill)
fire = [put(cube((0, 0, -99), 0.18, FIRE_A if k % 2 else FIRE_B, "fire"), g_hill) for k in range(16)]
hearts = []
for k in range(10):
    o = put(cube((0, 0, -99), (0.22, 0.08, 0.2), HEART, "heart", 0.02), g_hill)
    o.material_slots[0].link = "OBJECT"
    hearts.append(o)
steak = put(cube((0, 0, -99), (0.32, 0.12, 0.22), STEAK, "steak", 0.03), g_hill)

# ---------------- heat: thermometer columns ----------------
HX = 200
put(cube((HX, 3, 0), (60, 1, 60), mat("heat_bg", srgb("#141a2e")), "bg"), g_heat)
put(cube((HX, 0, -0.5), (20, 6, 1), mat("heat_floor", srgb("#262c40")), "floor"), g_heat)
for x in (-2.5, 2.5):
    put(cube((HX + x, 0.4, 7.5), (1.6, 0.4, 15.2), GLASS, "tube"), g_heat)
col_l = put(cube((HX + 2.5, 0, 0), (1.2, 1.2, 1), LCOL, "col_l"), g_heat)
col_s = put(cube((HX - 2.5, 0, 0), (1.2, 1.2, 1), SCOL, "col_s"), g_heat)
sun_block = put(cube((HX - 2.5, 0, -99), 1.6, SUNB, "sunb", 0.05), g_heat)
b_heat = bolt(7, (HX + 6.5, -0.5, 26), (HX + 6.5, -0.5, 0), n=12, thick=0.5, coll=g_heat)

# ---------------- volt: giant bolt and a wall socket ----------------
VX = 400
for i in range(-30, 31, 3):
    for j in range(-4, 40, 3):
        put(cube((VX + i, j, -0.5), (3, 3, 1), GRASS, "vg"), g_volt)
wall = put(cube((VX - 1.5, 1.0, 1.0), (2.0, 0.6, 2.0), WALL, "wall"), g_volt)
put(cube((VX - 1.5, 0.68, 1.1), (0.5, 0.06, 0.5), PLATE, "plate", 0.02), g_volt)
for dx in (-0.09, 0.09):
    put(cube((VX - 1.5 + dx, 0.64, 1.1), (0.06, 0.04, 0.06), HOLE, "hole"), g_volt)
spark = put(cube((0, 0, -99), 0.05, SPARK, "spark"), g_volt)
vhero = character("vhero", "#3f8fe0", (VX, 0.2, 0), 1.0)
vhero.rotation_euler = (0, 0, math.radians(200))
put(vhero, g_volt)
b_giant = bolt(11, (VX + 14, 30, 90), (VX + 14, 30, 0), n=14, thick=3.0, coll=g_volt, branches=4)

# ---------------- crowd: ten people ----------------
CX = 600
for i in range(-10, 11):
    for j in range(-4, 10):
        put(cube((CX + i, j, -0.5), (1, 1, 1), GRASS if (i + j) % 3 else mat("grass2", srgb("#4f9a34")), "cg"), g_crowd)
COLORS = ["#e04040", "#40a0e0", "#e0b030", "#40c070", "#a050e0", "#e07030", "#30c0c0", "#e050a0", "#8080e0", "#c0c040"]
crowd = []
for k in range(10):
    c = character(f"p{k}", COLORS[k], (CX - 3.0 + (k % 5) * 1.5, 1.8 * (k // 5), 0), 1.0)
    c.rotation_euler = (0, 0, math.radians((k - 4.5) * 3))
    put(c, g_crowd)
    crowd.append(c)
b_crowd = bolt(13, (CX + 3.0, 1.8, 30), (CX + 3.0, 1.8, 1.8), n=12, thick=0.4, coll=g_crowd)
dead_parts = [ch for ch in crowd[9].children]
for ch in dead_parts:
    ch.material_slots[0].link = "OBJECT"
    ch.material_slots[0].material = ch.data.materials[0]

# ---------------- roy: the ranger in the forest ----------------
RX = 800
rnd = random.Random(4)
for i in range(-10, 11):
    for j in range(-4, 16):
        put(cube((RX + i, j, -0.5), 1, GRASS, "rg"), g_roy)
for _ in range(14):
    x, y = rnd.choice([rnd.randint(-9, -3), rnd.randint(3, 9)]), rnd.randint(2, 14)
    h = rnd.randint(3, 5)
    put(cube((RX + x, y, h / 2), (0.8, 0.8, h), LOG, "log"), g_roy)
    put(cube((RX + x, y, h + 0.6), (2.6, 2.6, 2.0), LEAF, "leaf", 0.05), g_roy)
roy = character("roy", "#7a8a3a", (RX, 0, 0), 1.0)
roy.rotation_euler = (0, 0, 0)
put(cube((0, 0, 1.83), (0.85, 0.85, 0.06), HAT, "brim", 0.01, roy), g_roy)
put(cube((0, 0, 1.95), (0.5, 0.5, 0.22), HAT, "crown", 0.02, roy), g_roy)
put(roy, g_roy)
roy_bolts = [bolt(20 + k, (RX + (k - 3) * 0.6, 4, 32), (RX, 0, 2.0), n=12, thick=0.35, coll=g_roy) for k in range(7)]

# ---------------- earth: blocky globe ----------------
EX = 1000
globe = bpy.data.objects.new("globe", None)
g_earth.objects.link(globe)
globe.location = (EX, 0, 0)
R = 7.5
rg = random.Random(9)
blobs = [Vector((rg.uniform(-1, 1), rg.uniform(-1, 1), rg.uniform(-1, 1))).normalized() for _ in range(9)]
surface_pts = []
for x in range(-8, 9):
    for y in range(-8, 9):
        for z in range(-8, 9):
            d = math.sqrt(x * x + y * y + z * z)
            if R - 1.2 < d <= R:
                v = Vector((x, y, z)).normalized()
                land = max(b.dot(v) for b in blobs) > 0.82
                put(cube((x, y, z), 1.0, LAND if land else OCEAN, "gl", 0, globe), g_earth)
                surface_pts.append(Vector((x, y, z)) * 1.08)
put(cube((EX, 30, 0), (200, 1, 200), mat("space", srgb("#05060c")), "space"), g_earth)
stars = mat("star", srgb("#ffffff"), emit=3.0)
for _ in range(80):
    put(cube((EX + rg.uniform(-40, 40), 29, rg.uniform(-60, 60)), 0.12, stars, "star"), g_earth)
spots = []
for _ in range(14):
    s = cube((0, 0, 0), 1.0, SPOT, "spot", 0, globe)
    put(s, g_earth)
    spots.append(s)

# ---------------- rain (follows camera) ----------------
rain = [cube((0, 0, -999), (0.03, 0.03, 0.6), RAIN, "rain") for _ in range(140)]

cam_data = bpy.data.cameras.new("cam")
cam_data.lens = 24
cam_data.clip_end = 2000
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


def do_rain(t, center, on=True):
    r = random.Random(8)
    for o in rain:
        if not on:
            o.location = (0, 0, -999)
            continue
        x, y, z0 = r.uniform(-7, 7), r.uniform(-6, 9), r.uniform(0, 12)
        o.location = (center[0] + x, center[1] + y, center[2] + 10 - (z0 + t * 14) % 12)


def update(t):
    flash.data.energy = 0
    lvl = 0.0
    for b in [b_hill, b_far, b_heat, b_giant, b_crowd] + roy_bolts:
        vis(b, False)
    for o in fire + hearts:
        o.location = (0, 0, -99)
    steak.location = (0, 0, -99)
    spark.location = (0, 0, -99)
    limbs(t, 0)
    hero.rotation_euler = (0, 0, 0)
    hero.location = (0, 0, -0.5)

    if t < T_HOT or t >= T_END:
        show("hill")
        do_rain(t, (0, 2, 0))
        if t < T_MC:
            a = -1.3 + t * 0.12
            cam_to((math.cos(a) * 6.5, 1 + math.sin(a) * 6.5, 2.4), (0, 0, 1.4))
            lvl = strike(b_hill, t, STRIKE0, 0.45, base_energy=4000, loc=(0, -3, 5))
            if t > STRIKE0 + 0.45:
                for k, o in enumerate(fire):
                    r = random.Random(k * 31 + int(t * 12))
                    o.location = (r.uniform(-0.35, 0.35), r.uniform(-0.25, 0.25), -0.5 + r.uniform(0.2, 1.9))
        elif t < T_HOT:
            cam_to((1.6, -5.2, 2.1), (0, 0, 1.3))
            lost = 0.0
            if t >= T_MC + 1.1:
                lost = min(2.5, (t - T_MC - 1.1) / 0.6 * 2.5)
            if t >= T_STEAK + 0.5:
                lost = max(0.0, 2.5 - (t - T_STEAK - 0.5) / 0.5 * 2.5)
            for k, o in enumerate(hearts):
                x = -1.3 + k * 0.29
                full = 10 - lost
                o.location = (x, -0.3, 2.35)
                o.scale = (0.2, 0.08, 0.2)
                o.material_slots[0].material = HEART
                if k >= math.ceil(full):
                    o.material_slots[0].material = HEART_OFF
                elif k + 1 > full:  # half heart
                    o.scale = (0.1, 0.08, 0.2)
                    o.location = (x - 0.05, -0.3, 2.35)
            if t < T_STEAK + 0.4:
                for k, o in enumerate(fire):
                    r = random.Random(k * 31 + int(t * 12))
                    o.location = (r.uniform(-0.35, 0.35), r.uniform(-0.25, 0.25), -0.5 + r.uniform(0.2, 1.9))
            if T_STEAK - 0.2 <= t < T_STEAK + 0.6:
                k = ease((t - T_STEAK + 0.2) / 0.5)
                steak.location = (0.9 - 0.5 * k, -0.6, 0.4 + 1.0 * k)
                steak.rotation_euler = (0, t * 4, 0)
            if t >= T_STEAK + 0.8:
                lt = t - T_STEAK - 0.8
                hero.rotation_euler = (0, 0, math.radians(-90))
                hero.location = (-lt * 1.6, 0, -0.5)
                limbs(t, 0.8)
                for o in hearts:
                    o.location.x -= lt * 1.6
        else:  # end
            lt = t - T_END
            hero.rotation_euler = (0, 0, math.radians(15))
            cam_to((2.0, -5.6, 1.9), (0, 0, 1.3))
            lvl = strike(b_far, t, T_END + 1.2, 0.35, base_energy=60000, loc=(9, 12, 10))
    elif t < T_VOLT:  # heat columns
        show("heat")
        do_rain(t, (0, 0, 0), False)
        k = ease((t - T_HOT - 0.4) / 3.6)
        hl = 0.02 + 15 * k
        col_l.scale = (1.2, 1.2, hl)
        col_l.location = (HX + 2.5, 0, hl / 2)
        ks = ease((t - T_SUN) / 1.0)
        hs = 0.02 + 3 * ks
        col_s.scale = (1.2, 1.2, hs)
        col_s.location = (HX - 2.5, 0, hs / 2)
        sun_block.location = (HX - 2.5, 0, -99) if t < T_SUN else (HX - 2.5, 0, hs + 1.2)
        sun_block.rotation_euler = (0, 0, t * 0.8)
        if True:
            lvl = strike(b_heat, t, [T_HOT + s for s in (0.0, 1.1, 2.3, 3.4)], 0.25, base_energy=15000, loc=(HX + 6.5, -4, 12))
        z = 4 + 4 * ease((t - T_HOT) / 4)
        cam_to((HX + 0.5, -22 + 1.5 * (t - T_HOT) / 8, z + 2), (HX + 0.5, 0, z + 0.5))
    elif t < T_SURV:  # volt
        show("volt")
        do_rain(t, (VX, 2, 0))
        if True:
            lvl = strike(b_giant, t, [T_VOLT + s for s in (0.0, 0.8, 1.7, 2.5, 3.6, 4.6)], 0.55, base_energy=150000, loc=(VX + 10, 20, 30))
        if t < T_SOCK:
            cam_to((VX - 0.6, -5.2 + 0.3 * (t - T_VOLT), 0.9), (VX + 8, 30, 22))
        else:
            k = ease((t - T_SOCK) / 1.2)
            loc = Vector((VX - 0.6, -4.33, 0.9)).lerp(Vector((VX - 1.3, -0.6, 1.25)), k)
            tgt = Vector((VX + 8, 30, 22)).lerp(Vector((VX - 1.5, 0.7, 1.1)), k)
            cam_to(loc, tgt)
            if int(t * 10) % 4 == 0:
                spark.location = (VX - 1.5 + 0.09, 0.6, 1.12)
    elif t < T_ROY:  # crowd
        show("crowd")
        do_rain(t, (CX, 2, 0))
        lvl = strike(b_crowd, t, T_NINE - 0.6, 0.45, base_energy=8000, loc=(CX + 3, -3, 6))
        dead = t >= T_NINE - 0.15
        for ch in dead_parts:
            ch.material_slots[0].material = DEAD if dead else ch.data.materials[0]
        p = crowd[9]
        k = ease((t - T_NINE + 0.15) / 0.5)
        p.rotation_euler = (math.radians(-88 * k), 0, math.radians(4.5 * 3))
        p.location = (CX + 3.0, 1.8 + 0.9 * k, 0.15 * k)
        cam_to((CX + 0.6, -8.0 + 0.3 * (t - T_SURV), 3.6), (CX + 0.2, 1.0, 0.8))
    elif t < T_EARTH:  # roy
        show("roy")
        do_rain(t, (RX, 2, 0))
        for k, b in enumerate(roy_bolts):
            lvl = max(lvl, strike(b, t, ROY_HITS[k], 0.22, base_energy=6000, loc=(RX, -3, 5)))
        a = -1.57 + 0.35 * math.sin((t - T_ROY) * 0.4)
        cam_to((RX + math.cos(a) * 6, math.sin(a) * 6, 2.0), (RX, 0, 1.4))
    else:  # earth
        show("earth")
        do_rain(t, (0, 0, 0), False)
        globe.rotation_euler = (math.radians(20), 0, t * 0.35)
        r = random.Random(int(t * 15))
        for s in spots:
            p = surface_pts[r.randrange(len(surface_pts))]
            s.location = p
        cam_to((EX, -24 + 2 * ease((t - T_EARTH) / 4), 3), (EX, 0, 0))
    sky("#1c2233" if t < T_HOT or t >= T_END else "#141826", 0.5 + 1.0 * lvl)


for f in range(F0, F1, STEP):
    path = os.path.join(OUT, f"f_{f:05d}.png")
    if os.path.exists(path):
        continue
    update(f / FPS)
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
