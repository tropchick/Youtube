"""Blender (bpy) helpers for low-poly block-world scenes."""
import math
import bpy

_mats = {}


def reset(fps=30):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.fps = fps
    return sc


def mat(name, rgb, emit=0.0, rough=0.8, alpha=1.0):
    key = name
    if key in _mats:
        return _mats[key]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = (*rgb, 1)
        b.inputs["Emission Strength"].default_value = emit
    if alpha < 1:
        b.inputs["Alpha"].default_value = alpha
    m.diffuse_color = (*rgb, alpha)  # used by Workbench
    _mats[key] = m
    return m


def srgb(h):
    """hex -> linear rgb tuple"""
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c)


def cube(loc, size, material, name="c", bevel=0.0, parent=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object
    o.name = name
    o.scale = size if isinstance(size, (tuple, list)) else (size, size, size)
    o.data.materials.append(material)
    if bevel:
        mod = o.modifiers.new("b", "BEVEL")
        mod.width = bevel
        mod.segments = 1
    if parent:
        o.parent = parent
    return o


def empty(name, loc=(0, 0, 0)):
    o = bpy.data.objects.new(name, None)
    o.location = loc
    bpy.context.scene.collection.objects.link(o)
    return o


def character(name, body_hex, loc=(0, 0, 0), s=1.0):
    """Original blocky character: head, torso, arms, legs under one empty."""
    root = empty(name, loc)
    skin = mat("skin", srgb("#f0c8a0"))
    body = mat(name + "_body", srgb(body_hex))
    pants = mat("pants", srgb("#3a3f6b"))
    eye = mat("eye", srgb("#1e1e28"))
    cube((0, 0, 1.55 * s), 0.5 * s, skin, name + "_head", 0.02, root)
    cube((-0.12 * s, -0.255 * s, 1.6 * s), 0.08 * s, eye, name + "_eyeL", 0, root)
    cube((0.12 * s, -0.255 * s, 1.6 * s), 0.08 * s, eye, name + "_eyeR", 0, root)
    cube((0, 0, 1.0 * s), (0.5 * s, 0.28 * s, 0.6 * s), body, name + "_torso", 0.02, root)
    arms = []
    for side in (-1, 1):
        a = cube((side * 0.36 * s, 0, 1.0 * s), (0.2 * s, 0.22 * s, 0.6 * s), body, name + "_arm", 0.02, root)
        arms.append(a)
    for side in (-1, 1):
        cube((side * 0.13 * s, 0, 0.4 * s), (0.23 * s, 0.25 * s, 0.6 * s), pants, name + "_leg", 0.02, root)
    root["arms"] = [a.name for a in arms]
    return root


def grass(loc, s=1.0, name="grass"):
    top = mat("grass_top", srgb("#6cbf48"))
    dirt = mat("dirt", srgb("#8a6142"))
    cube((loc[0], loc[1], loc[2] - 0.1 * s), (s, s, 0.8 * s), dirt, name + "_d")
    return cube((loc[0], loc[1], loc[2] + 0.4 * s), (s, s, 0.2 * s), top, name + "_t")


def key(obj, frame, **props):
    for k, v in props.items():
        setattr(obj, k, v)
        obj.keyframe_insert(data_path=k, frame=frame)


def look_at(cam, target):
    from mathutils import Vector
    d = Vector(target) - cam.location
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def linear_all():
    for a in bpy.data.actions:
        for layer in getattr(a, "layers", []):
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for fc in bag.fcurves:
                        for kp in fc.keyframe_points:
                            kp.interpolation = "LINEAR"
        for fc in getattr(a, "fcurves", []):
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"


def setup_render(sc, w=540, h=960, engine="CYCLES", samples=12):
    sc.render.resolution_x = w
    sc.render.resolution_y = h
    sc.render.engine = engine
    sc.render.image_settings.file_format = "PNG"
    if engine == "CYCLES":
        sc.cycles.samples = samples
        sc.cycles.device = "CPU"
        sc.cycles.use_denoising = True
        sc.cycles.max_bounces = 4
        sc.render.use_persistent_data = True
    sc.view_settings.view_transform = "Standard"
