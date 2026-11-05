"""Short #4 (3D): how much would a full Minecraft inventory weigh in real life.
python3 scene3d.py OUTDIR [start end step]"""
import math
import os
import random
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "engine"))
from blocky import reset, mat, srgb, cube, character, look_at, setup_render

FPS, DUR = 30, 42.4
OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
F0 = int(sys.argv[2]) if len(sys.argv) > 2 else 0
F1 = int(sys.argv[3]) if len(sys.argv) > 3 else int(DUR * FPS)
STEP = int(sys.argv[4]) if len(sys.argv) > 4 else 1

# voice timings (s)
T_CUBE, T_STONE, T_INV, T_2304, T_SCALE, T_GOLD, T_X7, T_ALL, T_RUN, T_WATER, T_END = (
    3.08, 6.39, 8.86, 12.9, 15.66, 21.18, 23.91, 26.58, 33.43, 36.15, 39.57)

sc = reset(FPS)
setup_render(sc, samples=int(os.environ.get("SAMPLES", "10")))
w = bpy.data.worlds.new("sky")
w.use_nodes = True
bgn = w.node_tree.nodes["Background"]
bgn.inputs["Color"].default_value = (*srgb("#9fd0ff"), 1)
sc.world = w

bpy.ops.object.light_add(type="SUN")
sun = bpy.context.object
sun.data.energy = 3.5
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


def ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def gold_mat(name, emit=0.0):
    m = mat(name, srgb("#f5b52a"), emit=emit, rough=0.3)
    m.node_tree.nodes["Principled BSDF"].inputs["Metallic"].default_value = 0.6
    return m


GRASS = mat("grass_top", srgb("#6cbf48"))
DIRT = mat("dirt", srgb("#8a6142"))
STONE = mat("stone", srgb("#8d8d8d"))
DIA = mat("diamond", srgb("#5fe0e0"), emit=0.3)
WOOD = mat("wood", srgb("#6b4a2b"))
LEAF = mat("leaf", srgb("#3f8f3a"))
GOLD = gold_mat("gold")
GOLD2 = gold_mat("gold_other")
IRON = mat("iron", srgb("#c9c9c9"))
WATER = mat("water", srgb("#3c8cff"), rough=0.1)
SLOT = mat("slot", srgb("#2b2b33"))
YEL = mat("yel", srgb("#ffe14d"), emit=0.6)
TOWER = mat("tower", srgb("#9a7a5e"))
BEAM = mat("beam", srgb("#5a4632"))

g_field = group("field")
g_scale = group("scale")

# ---------------- field ----------------
put(cube((10, 10, -0.5), (140, 140, 1), GRASS, "ground"), g_field)
rnd = random.Random(4)
for _ in range(30):
    x, y = rnd.uniform(-60, 70), rnd.uniform(25, 70)
    h = rnd.uniform(2, 4)
    put(cube((x, y, h / 2), (0.6, 0.6, h), WOOD, "trunk"), g_field)
    put(cube((x, y, h + 1), 2.6, LEAF, "crown", 0.05), g_field)

hero = put(character("hero", "#4caf50"), g_field)
legs = [c for c in hero.children if c.name.startswith("hero_leg")]
arms = [c for c in hero.children if c.name.startswith("hero_arm")]
for p in legs + arms:  # pivot at the top of the limb
    z = p.location.z
    p.data = p.data.copy()
    for v in p.data.vertices:
        v.co.z -= 0.5
    p.location.z = z + 0.3

# hotbar above the head (hook)
hot = []
for i, m_ in enumerate((STONE, DIRT, GRASS, WOOD, GOLD, DIA, IRON, LEAF, WATER)):
    x = (i - 4) * 0.42
    s = put(cube((x, 0.05, 2.6), (0.46, 0.05, 0.46), SLOT, "slot"), g_field)
    b = put(cube((x, -0.05, 2.6), 0.3, m_, "hb", 0.02), g_field)
    hot.append((s, b, Vector((x, 0, 2.6))))

# 1 m stone block + measuring bars
one = put(cube((1.4, 0, 0.5), 1, STONE, "one", 0.02), g_field)
bars = [put(cube((1.4, -0.56, 0.02), (1, 0.04, 0.04), YEL, "barx"), g_field),
        put(cube((0.86, -0.56, 0.5), (0.04, 0.04, 1), YEL, "barz"), g_field)]
dust = [put(cube((0, 0, -99), 0.15, DIRT, "dust"), g_field) for _ in range(14)]

# the inventory stack: 2304 blocks = 12 x 12 x 16
stack = bpy.data.objects.new("stack", None)
g_field.objects.link(stack)
stack.location = (3, 1, 0)
base = cube((0, 0, -99), 1, STONE, "blk", 0.03)
base.data.materials.clear()
base.data.materials.append(STONE)
base.material_slots[0].link = "OBJECT"
blocks = []
for k in range(16):
    for j in range(12):
        for i in range(12):
            o = base.copy()
            o.location = (i + 0.5, j + 0.5, k + 0.5)
            o.parent = stack
            o.material_slots[0].material = STONE
            g_field.objects.link(o)
            blocks.append(o)
bpy.data.objects.remove(base)
others = []
for n in range(4):
    o = put(cube((9, 7, 8 + 16 * (n + 1)), (12, 12, 16), GOLD2, "goldall", 0.05), g_field)
    others.append(o)

bucket = put(cube((0, -0.45, 0.75), (0.3, 0.3, 0.32), IRON, "bucket", 0.02), g_field)
bucket_water = put(cube((0, -0.45, 0.88), (0.24, 0.24, 0.05), WATER, "bwater"), g_field)
water_cube = put(cube((-1.5, 0, 0.5), 1, WATER, "wcube", 0.03), g_field)

# ---------------- balance scale ----------------
SX = 0
put(cube((SX, 200, -0.5), (80, 80, 1), GRASS, "ground2"), g_scale)
put(cube((SX, 200, 1.6), (0.6, 0.6, 3.2), BEAM, "post", 0.03), g_scale)
pivot = put(bpy.data.objects.new("pivot", None), g_scale)
pivot.location = (SX, 200, 3.3)
beam = cube((0, 0, 0), (7.4, 0.4, 0.3), BEAM, "beam", 0.03, pivot)
put(beam, g_scale)
pans = []
for side in (-1, 1):
    p = bpy.data.objects.new("pan", None)
    g_scale.objects.link(p)
    put(cube((0, 0, 0), (2.6, 2.6, 0.15), IRON, "pan_plate", 0.02, p), g_scale)
    pans.append(p)
load_stone = put(cube((0, 0, 1.1), (1.7, 1.7, 2.1), STONE, "load", 0.04, pans[0]), g_scale)
load_gold = put(cube((0, 0, 1.1), (1.7, 1.7, 2.1), GOLD, "loadg", 0.04, pans[0]), g_scale)
tower = bpy.data.objects.new("tower", None)
g_scale.objects.link(tower)
tower.parent = pans[1]
TH = 4.4
for sx in (-1, 1):
    for sy in (-1, 1):
        b = cube((sx * 0.45, sy * 0.45, TH * 0.17), (0.16, 0.16, TH * 0.38), TOWER, "tleg", 0.01, tower)
        b.rotation_euler = (sy * math.radians(14), -sx * math.radians(14), 0)
        put(b, g_scale)
for loc, size in (((0, 0, TH * 0.34), (0.9, 0.9, 0.1)), ((0, 0, TH * 0.62), (0.38, 0.38, TH * 0.56)),
                  ((0, 0, TH * 0.6), (0.55, 0.55, 0.08)), ((0, 0, TH * 0.95), (0.06, 0.06, TH * 0.12))):
    put(cube(loc, size, TOWER, "tpart", 0.01, tower), g_scale)

cam_data = bpy.data.cameras.new("cam")
cam_data.lens = 30
cam = bpy.data.objects.new("cam", cam_data)
sc.collection.objects.link(cam)
sc.camera = cam


def set_scale(angle, gold=False):
    pivot.rotation_euler = (0, angle, 0)
    for side, p in zip((-1, 1), pans):
        x = side * 3.4 * math.cos(angle)
        z = -side * 3.4 * math.sin(angle)
        p.location = (SX + x, 200, 3.3 + z - 0.9)
    load_stone.hide_render = gold
    load_gold.hide_render = not gold


def pose(ch, t, run=0.0, wave=0.0):
    a = math.sin(t * 2 * math.pi * 2.2) * 0.9 * run
    for i, l in enumerate(legs):
        l.rotation_euler = ((a if i else -a), 0, 0)
    for i, ar in enumerate(arms):
        ar.rotation_euler = ((-a if i else a), 0, 0)
    if wave:
        arms[1].rotation_euler = (0, math.radians(-150 + 20 * math.sin(t * 12)), 0)


def burst(t, origin, seed=1, life=0.7):
    r = random.Random(seed)
    for o in dust:
        dx, dy, dz = r.uniform(-1, 1), r.uniform(-1, 1), r.uniform(0.5, 1.5)
        if t < 0 or t > life:
            o.location = (0, 0, -99)
            continue
        o.location = (origin[0] + dx * 2.2 * t, origin[1] + dy * 2.2 * t, origin[2] + dz * 3 * t - 5 * t * t)
        s = 0.18 * (1 - t / life)
        o.scale = (s, s, s)


def cam_to(loc, target):
    cam.location = Vector(loc)
    look_at(cam, Vector(target))


def lerp(a, b, k):
    return Vector(a).lerp(Vector(b), k)


HIDE = (0, 0, -99)


def update(t):
    # defaults
    hero.location = (0, 0, 0)
    hero.rotation_euler = (0, 0, 0)
    pose(hero, t)
    for s, b, p in hot:
        s.location = b.location = HIDE
    one.location = HIDE
    for b in bars:
        b.hide_render = True
    burst(-1, (0, 0, 0))
    stack.location = (3, 1, 0)
    stack.hide_render = False
    for o in others:
        o.location.z = -200
    bucket.hide_render = bucket_water.hide_render = water_cube.hide_render = True
    GOLD.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 0.0
    n_vis = 0
    gold_upto = -1

    if t < T_SCALE or (T_GOLD <= t < T_X7) or t >= T_ALL:
        show("field")
    else:
        show("scale")

    if t < T_CUBE:  # hook: hotbar floating over the hero
        for i, (s, b, p) in enumerate(hot):
            k = ease((t - 0.2 - i * 0.08) / 0.4)
            off = Vector((0, 0, 0.08 * math.sin(t * 3 + i)))
            s.location = p + off
            b.location = p + off + Vector((0, -0.1, 0))
            s.scale = (0.46 * k + 0.001, 0.05, 0.46 * k + 0.001)
            b.scale = (0.3 * k + 0.001,) * 3
            b.rotation_euler = (0, 0, t * 1.5 + i)
        a = -1.75 + t * 0.12
        cam_to((math.cos(a) * 6.8, math.sin(a) * 6.8, 2.3), (0, 0, 1.75))
    elif t < T_STONE:  # 1 m block next to a person
        lt = t - T_CUBE
        one.location = (1.4, 0, 0.5 + 3 * (1 - ease(lt / 0.5)))
        for b in bars:
            b.hide_render = lt < 0.9
        bars[0].scale.x = ease((lt - 0.9) / 0.5) + 0.001
        bars[1].scale.z = ease((lt - 1.3) / 0.5) + 0.001
        a = -1.7 + lt * 0.08
        cam_to((0.7 + math.cos(a) * 5, math.sin(a) * 5, 1.6), (0.7, 0, 0.9))
        burst(lt - 0.5, (1.4, -0.5, 0.1), seed=2)
    elif t < T_INV:  # stone is heavy: lift and slam
        lt = t - T_STONE
        up = ease(lt / 0.5)
        fall = max(0.0, lt - 0.9)
        z = 0.5 + 2.5 * up if lt < 0.9 else max(0.5, 3.0 - 9.8 * fall * fall * 2)
        one.location = (1.4, 0, z)
        land = 0.9 + math.sqrt(2.5 / 19.6)
        burst(lt - land, (1.4, -0.5, 0.1), seed=3)
        shake = 0.06 * math.sin(lt * 80) * max(0, 1 - (lt - land) / 0.4) if lt > land else 0
        cam_to((3.2 + shake, -4.6, 1.8 + shake), (0.9, 0, 1.0))
    elif t < T_SCALE:  # 2304 blocks rain in, camera pulls back
        lt = t - T_INV
        n_vis = int(2304 * ease(lt / 5.6))
        k = ease(lt / 5.0)
        cam_to(lerp((2.0, -5.5, 2.0), (-14, -30, 14), k), lerp((1.5, 0, 1.2), (8, 6, 6), k))
    elif t < T_GOLD:  # balance: stone stack vs Eiffel tower metal
        lt = t - T_SCALE
        set_scale(math.radians(6) * ease(lt / 1.5) + 0.02 * math.sin(lt * 3) * math.exp(-lt))
        cam_to((SX + 1.0 - lt * 0.15, 200 - 16, 4.8), (SX, 200, 3.4))
    elif t < T_X7:  # stack turns to gold, bottom-up
        lt = t - T_GOLD
        n_vis = 2304
        gold_upto = int(2304 * ease(lt / 2.2))
        a = -2.0 + lt * 0.1
        cam_to((9 + math.cos(a) * 30, 7 + math.sin(a) * 30, 14), (9, 7, 7))
    elif t < T_ALL:  # gold on the scale slams it down
        lt = t - T_X7
        k = min(1.0, (lt / 0.35) ** 2)
        bounce = 0.05 * math.sin(lt * 25) * math.exp(-lt * 4) if lt > 0.35 else 0
        set_scale(math.radians(6) - math.radians(24) * k + bounce, gold=True)
        # the tower gets tossed up a little
        tower.location = (0, 0, max(0.0, 2.5 * (lt - 0.35) - 4.9 * (lt - 0.35) ** 2) if lt > 0.35 else 0)
        cam_to((SX - 1.0, 200 - 16, 4.8), (SX, 200, 3.2))
    elif t < T_RUN:  # all the gold ever mined = 5 stacks
        lt = t - T_ALL
        n_vis = gold_upto = 2304
        for i, o in enumerate(others):
            d = ease((t - 28.4 - i * 0.35) / 0.4)
            o.location.z = 8 + 16 * (i + 1) + 120 * (1 - d) if d > 0 else -200
        pulse = 0.5 + 0.5 * math.sin(lt * 5)
        GOLD.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = (
            0.2 * pulse if t > 29.5 else 0.0)
        k = ease(lt / 3.0)
        k = ease((t - 28.0) / 1.6)
        cam_to(lerp((9, -32, 10), (9, -72, 40), k), lerp((9, 7, 8), (9, 7, 40), k))
    elif t < T_WATER:  # running and jumping with 44 000 t over your head
        lt = t - T_RUN
        n_vis = gold_upto = 2304
        x = -10 + lt * 6.5
        jump = abs(math.sin(lt * math.pi / 0.7)) * 1.2 if lt > 1.0 else 0
        hero.location = (x, -10, jump)
        hero.rotation_euler = (0, 0, math.radians(90))
        pose(hero, t, run=1.0)
        stack.location = (x - 6, -16, 2.3 + jump)
        cam_to((x + 3, -30, 1.6), (x + 0.5, -10, 5.5))
    elif t < T_END:  # a bucket of water = 1 m3 = 1 t
        lt = t - T_WATER
        bucket.hide_render = bucket_water.hide_render = water_cube.hide_render = False
        n_vis = gold_upto = 2304
        stack.hide_render = True
        water_cube.scale = (ease(lt / 0.5) + 0.001,) * 3
        arms[0].rotation_euler = (math.radians(-30), 0, 0)
        bucket.location = (-0.36, -0.45, 0.62)
        bucket_water.location = (-0.36, -0.45, 0.75)
        a = -1.85 + lt * 0.06
        cam_to((-0.6 + math.cos(a) * 4.6, math.sin(a) * 4.6, 1.7), (-0.6, 0, 0.9))
    else:  # CTA: standing on top of the gold stack
        lt = t - T_END
        n_vis = gold_upto = 2304
        hero.location = (9, 7, 16)
        pose(hero, t, wave=1.0)
        a = -1.6 + lt * 0.15
        cam_to((9 + math.cos(a) * 6, 7 + math.sin(a) * 6, 18.0), (9, 7, 17.1))

    # stack blocks: visibility, falling-in, material
    for idx, o in enumerate(blocks):
        vis = idx < n_vis
        o.hide_render = not vis or stack.hide_render
        if not vis:
            continue
        i, j, k = idx % 12, (idx // 12) % 12, idx // 144
        z = k + 0.5
        if T_INV <= t < T_SCALE:
            lt = t - T_INV
            # time this block appeared: invert n_vis(t)
            appear = idx / 2304.0
            # solve ease(x) = appear for x by bisection (cheap: 12 iterations)
            lo, hi = 0.0, 1.0
            for _ in range(12):
                mid = (lo + hi) / 2
                if ease(mid) < appear:
                    lo = mid
                else:
                    hi = mid
            age = lt - lo * 5.6
            z += 4 * max(0.0, 1 - age / 0.3)
        o.location = (i + 0.5, j + 0.5, z)
        want = GOLD if idx < gold_upto else STONE
        if o.material_slots[0].material != want:
            o.material_slots[0].material = want


for f in range(F0, F1, STEP):
    path = os.path.join(OUT, f"f_{f:05d}.png")
    if os.path.exists(path):
        continue
    update(f / FPS)
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
