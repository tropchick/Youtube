"""Short #3 (3D): digging down like in Minecraft vs real life.
python3 scene3d.py OUTDIR [start end step]"""
import math
import os
import random
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "engine"))
from blocky import reset, mat, srgb, cube, character, look_at, setup_render

FPS, DUR = 30, 40.6
OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
F0 = int(sys.argv[2]) if len(sys.argv) > 2 else 0
F1 = int(sys.argv[3]) if len(sys.argv) > 3 else int(DUR * FPS)
STEP = int(sys.argv[4]) if len(sys.argv) > 4 else 1

T_SHAFT, T_PICK, T_KOLA, T_DIVE, T_HOUR, T_EARTH, T_HEAT, T_END = 3.6, 7.6, 12.4, 16.6, 21.0, 24.9, 32.1, 37.4

sc = reset(FPS)
setup_render(sc, samples=int(os.environ.get("SAMPLES", "10")))
w = bpy.data.worlds.new("sky")
w.use_nodes = True
bgn = w.node_tree.nodes["Background"]
sc.world = w

bpy.ops.object.light_add(type="SUN")
sun = bpy.context.object
sun.data.energy = 3.5
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


GRASS = mat("grass_top", srgb("#6cbf48"))
DIRT = mat("dirt", srgb("#8a6142"))
STONE = mat("stone", srgb("#8d8d8d"))
DEEP = mat("deepslate", srgb("#4a4a52"))
BED = mat("bedrock", srgb("#2a2a2a"))
DIA = mat("diamond", srgb("#5fe0e0"), emit=0.3)
WOOD = mat("wood", srgb("#6b4a2b"))
LAVA = mat("lava", srgb("#ff6a10"), emit=1.6)
CORE = mat("core", srgb("#ffd040"), emit=10.0)
MANTLE = mat("mantle", srgb("#c8401a"), emit=2.5)
CRUST = mat("crust", srgb("#7a5a40"))
OCEAN = mat("ocean", srgb("#2f6fd0"))
IRON = mat("iron", srgb("#c9c9c9"))
WATER = mat("water", srgb("#3c8cff"), rough=0.1)
STEAM = mat("steam", srgb("#ffffff"), rough=1)


def pickaxe(parent=None):
    root = bpy.data.objects.new("pick", None)
    sc.collection.objects.link(root)
    cube((0, 0, 0), (0.08, 0.08, 0.9), WOOD, "handle", 0.01, root)
    cube((0, 0, 0.42), (0.7, 0.1, 0.12), DIA, "head", 0.01, root)
    for s in (-1, 1):
        cube((s * 0.38, 0, 0.36), (0.12, 0.1, 0.16), DIA, "tip", 0.01, root)
    if parent:
        root.parent = parent
    return root


# ---------- group 1: surface + shaft cross-section ----------
g_dig = group("dig")
LAYERS = [(GRASS, 1), (DIRT, 3), (STONE, 10), (DEEP, 8), (BED, 1)]
z = 0
for m_, n in LAYERS:
    # left and right halves around a 1-wide shaft, depth 3 (cross-section)
    for side in (-1, 1):
        o = cube((side * 4.5, 0, z - n / 2), (8, 3, n), m_, "layer", 0.0)
        put(o, g_dig)
    z -= n
SHAFT_BOTTOM = z + 1  # standing on bedrock
# blocks inside the shaft that get mined
shaft_blocks = []
zz = 0
for m_, n in LAYERS[:-1]:
    for i in range(n):
        o = cube((0, 0, zz - 0.5 - i), (1, 3, 1), m_, "sb", 0.02)
        put(o, g_dig)
        shaft_blocks.append(o)
    zz -= n
put(cube((0, 0, SHAFT_BOTTOM - 1.5), (1, 3, 1), BED, "bedrock_c"), g_dig)
digger = put(character("dig", "#4fb83a"), g_dig)
dpick = pickaxe(digger)
dpick.location = (0.45, -0.2, 1.1)
put(dpick, g_dig)
random.seed(4)
for _ in range(10):  # ores
    x, zz2 = random.choice([-1, 1]) * random.uniform(1.5, 7), random.uniform(-20, -6)
    put(cube((round(x) + .0, -1.45, round(zz2)), (1, 0.12, 1), DIA if zz2 < -14 else IRON, "ore"), g_dig)
parts = [put(cube((0, 0, -999), 0.15, STONE, "p"), g_dig) for _ in range(14)]

# ---------- group 2: pickaxe close-up ----------
g_pick = group("pickclose")
for i in range(5):
    for j in range(3):
        put(cube((i - 2, 1, j - 1), 1, STONE, "wall", 0.02), g_pick)
target = put(cube((0, 0, 0), 1, STONE, "target", 0.03), g_pick)
cpick = put(pickaxe(), g_pick)

# ---------- group 3: Kola rig + long shaft ----------
g_kola = group("kola")
put(cube((0, 0, -0.5), (60, 60, 1), GRASS, "ground"), g_kola)
put(cube((0, 0, -60.5), (60, 60, 119), mat("rock", srgb("#6d6258")), "rock"), g_kola)
rig = []
H = 14
for sx in (-1, 1):
    for sy in (-1, 1):
        o = cube((sx * 1.4, sy * 1.4, H / 2), (0.25, 0.25, H + 0.6), mat("rig", srgb("#d04030")), "rigleg", 0.01)
        o.rotation_euler = (sy * math.radians(5), -sx * math.radians(5), 0)
        put(o, g_kola)
for k in range(1, 6):
    s_ = 3.2 * (1 - k / 7)
    put(cube((0, 0, k * H / 6), (s_, s_, 0.15), mat("rig2", srgb("#e8e8e8")), "rigbar"), g_kola)
put(cube((4, 0, 1.2), (3, 2.2, 2.4), mat("hut", srgb("#d9c27a")), "hut", 0.04), g_kola)
kola_shaft = put(cube((0, -29.95, -55), (0.5, 0.2, 110), mat("hole", srgb("#111111")), "shaft"), g_kola)
for zz3, m_ in ((-8, DIRT), (-30, STONE), (-70, DEEP)):
    put(cube((0, -30, zz3), (60, 0.05, 0.3), m_, "band"), g_kola)
kola_guy = put(character("kd", "#4fb83a"), g_kola)
kpick = pickaxe(kola_guy)
kpick.location = (0.45, -0.2, 1.1)
put(kpick, g_kola)

# ---------- group 4: planet ----------
g_earth = group("earth")
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=10)
crust = put(bpy.context.object, g_earth)
crust.data.materials.append(OCEAN)
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=9.2)
mantle = put(bpy.context.object, g_earth)
mantle.data.materials.append(MANTLE)
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=4.5)
core = put(bpy.context.object, g_earth)
core.data.materials.append(CORE)
# cut away a quarter wedge with boolean
cutter = cube((5.5, -5.5, 6), (11, 11, 12), STONE, "cutter")
for o in (crust, mantle):
    b = o.modifiers.new("cut", "BOOLEAN")
    b.object = cutter
    b.operation = "DIFFERENCE"
cutter.hide_render = True
put(cutter, g_earth)
random.seed(8)
for _ in range(16):  # continents
    v = Vector((random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1))).normalized()
    if v.x > 0.2 and v.y < -0.2 and v.z > -0.6:
        continue
    o = cube(tuple(v * 9.9), (random.uniform(2, 4), random.uniform(2, 4), 0.6), GRASS, "land", 0.1)
    o.rotation_euler = v.to_track_quat("Z", "Y").to_euler()
    put(o, g_earth)
shaft_line = put(cube((0, 0, 7.2), (0.12, 0.12, 5.6), mat("hole", srgb("#111111")), "eshaft"), g_earth)

# ---------- group 5: lava / heat ----------
g_heat = group("heat")
for i in range(-4, 5):
    for j in range(-4, 5):
        put(cube((i, j, -0.5 + 0.15 * math.sin(i * 1.3 + j)), 1, LAVA, "lava"), g_heat)
for i in range(-2, 3):
    put(cube((i, 3, 0.5), 1, DEEP, "ledge"), g_heat)
heat_guy = put(character("hg", "#4fb83a"), g_heat)
heat_guy.location = (0, 3, 1.0)
bucket = put(cube((0.5, 2.2, 1.6), (0.35, 0.35, 0.4), IRON, "bucket", 0.02), g_heat)
water_blob = put(cube((0.5, 1.5, 1.2), 0.5, WATER, "wblob", 0.05), g_heat)
steam = [put(cube((0, 0, -99), 0.3, STEAM, "steam", 0.05), g_heat) for _ in range(16)]

bpy.ops.object.camera_add()
cam = bpy.context.object
cam.data.lens = 28
sc.camera = cam
cutter.hide_render = True


def ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def show(name):
    for n, c in GROUPS.items():
        c.hide_render = n != name
    cutter.hide_render = True


def sky(rgb_hex, strength=1.0):
    bgn.inputs["Color"].default_value = (*srgb(rgb_hex), 1)
    bgn.inputs["Strength"].default_value = strength


def swing(ch, t, rate=3.3):
    """arm+pickaxe swing (pickaxe is parented to root; rotate root's pickaxe child)."""
    for c in ch.children:
        if c.name.startswith("pick"):
            c.rotation_euler = (math.radians(-60) + math.sin(t * rate * 2 * math.pi) * 0.9, 0, 0)


def burst(objs, origin, t, life=0.5, seed=1, material=None):
    rnd = random.Random(seed)
    for o in objs:
        dx, dz = rnd.uniform(-1, 1), rnd.uniform(0.2, 1)
        if t < 0 or t > life:
            o.location = (0, 0, -999)
            continue
        if material:
            o.data.materials[0] = material
        o.location = (origin[0] + dx * 2.5 * t, origin[1] - 1.6, origin[2] + dz * 3 * t - 5 * t * t)
        s = 0.15 * (1 - t / life)
        o.scale = (s, s, s)


def update(t):
    if t < T_PICK:
        show("dig")
        sky("#9fd0ff")
        # depth progress: 0 for hook, then descend to bottom
        if t < T_SHAFT:
            depth = min(1.0, max(0.0, (t - 1.6) / 1.4))  # mine first block in the hook
        else:
            depth = 1 + (len(shaft_blocks) - 1) * ease((t - T_SHAFT) / 3.4)
        n_mined = int(depth)
        for i, o in enumerate(shaft_blocks):
            o.hide_render = i < n_mined
        z_feet = 0.0 if depth < 1 else -depth + 0.0
        z_feet = max(z_feet, SHAFT_BOTTOM - 1)
        digger.location = (0, 0, z_feet)
        swing(digger, t)
        frac = depth - n_mined
        burst(parts, (0, 0, z_feet - 0.5), frac * 0.5, seed=n_mined, material=shaft_blocks[min(n_mined, len(shaft_blocks) - 1)].data.materials[0])
        if t < T_SHAFT:
            cam.location = (2.2, -4.5, 2.3)
            look_at(cam, (0, 0, 1.0))
        else:
            k = ease((t - T_SHAFT) / 1.2)
            cam.location = Vector((2.2, -4.5, 2.3)).lerp(Vector((0, -26, -9)), k)
            look_at(cam, Vector((0, 0, 1)).lerp(Vector((0, 0, -10)), k))
    elif t < T_KOLA:
        show("pickclose")
        sky("#2a2a35", 0.6)
        lt = t - T_PICK
        cyc = (lt % 1.2)
        hit = min(cyc / 0.3, 1.0)  # 0.3 s break
        target.scale = (1.0,) * 3 if cyc < 0.3 else (0.001,) * 3
        if cyc >= 0.3 and cyc < 0.6:
            target.scale = (0.001,) * 3
        if cyc >= 0.6:
            target.scale = (ease((cyc - 0.6) / 0.3),) * 3
        cpick.location = (0.9, -1.3, 0.6)
        cpick.rotation_euler = (math.radians(-90 + 70 * math.sin(min(cyc, 0.3) / 0.3 * math.pi)), math.radians(-20), 0)
        cam.location = (2.6, -4.0, 1.4)
        look_at(cam, (0, 0, 0.2))
    elif t < T_EARTH:
        show("kola")
        sky("#9fd0ff")
        if t < T_DIVE:
            lt = t - T_KOLA
            a = -1.9 + lt * 0.18
            cam.location = (math.cos(a) * 22, math.sin(a) * 22, 6 + lt * 0.8)
            look_at(cam, (0, 0, 6))
            kola_guy.location = (-6, -3, 0)
        elif t < T_HOUR:
            k = ease((t - T_DIVE) / 4.2)
            cam.location = (0, -48, 8 - k * 100)
            look_at(cam, (0, -30, 6 - k * 100))
            kola_guy.location = (-6, -3, 0)
        else:
            lt = t - T_HOUR
            kz = -2 - lt * 20
            kola_guy.location = (0, -30.6, kz)
            swing(kola_guy, t, rate=5)
            cam.location = (2.5, -36, kz + 1.5)
            look_at(cam, (0, -30.6, kz + 0.8))
    elif t < T_HEAT:
        show("earth")
        sky("#05060f", 0.3)
        lt = t - T_EARTH
        crust.rotation_euler = mantle.rotation_euler = (0, 0, 0)
        shaft_line.scale = (0.12, 0.12, 5.6 * ease(lt / 3.0))
        shaft_line.location = (0, 0, 10 - 2.8 * ease(lt / 3.0))
        a = -0.9 + lt * 0.06
        r = 34 - lt * 1.2
        cam.location = (math.cos(a) * r * 0.9, math.sin(a) * r, 12)
        look_at(cam, (0, 0, 1))
    else:
        show("heat")
        sky("#200805", 0.3)
        lt = t - T_HEAT
        heat_guy.location = (0, 3, 1.0)
        # pour water at ~4s -> evaporates
        pour = ease((lt - 3.2) / 0.6)
        water_blob.location = (0.5, 1.6 - pour * 1.2, 1.3 - pour * 1.3)
        water_blob.scale = (max(0.001, 0.5 * (1 - ease((lt - 3.8) / 0.4))),) * 3
        rnd = random.Random(5)
        for i, o in enumerate(steam):
            st = lt - 3.8 - i * 0.06
            if st < 0:
                o.location = (0, 0, -99)
                continue
            o.location = (0.5 + rnd.uniform(-1, 1) * st, 0.4 + rnd.uniform(-0.5, 0.5), 0.3 + st * 2.2)
            s = 0.3 + st * 0.4
            o.scale = (s, s, s)
        cam.location = (3.5, -4.5, 3.2 + lt * 0.1)
        look_at(cam, (0.2, 1.5, 1.0))


for f in range(F0, F1, STEP):
    path = os.path.join(OUT, f"f_{f:05d}.png")
    if os.path.exists(path):
        continue
    update(f / FPS)
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
