"""Helpers for building flat-shaded low-poly game assets with Blender (bpy).

Model scripts (models/<slug>/build.py) do `from lowpoly import *` and call the
primitive helpers below. Everything is in meters, Z-up while modeling (Blender's
convention); the exporters convert to Y-up for Unity / glTF.

Works with Blender 3.6+ and the `bpy` pip package (4.x).
"""

import math
import os

import bmesh
import bpy
from mathutils import Matrix, Vector

__all__ = [
    "mat", "box", "cylinder", "cone", "sphere", "ico", "wedge", "torus", "poly_extrude",
    "group_rotate", "mirror_x", "jitter",
    "Vector", "math", "bpy",
]

_materials = {}


# ---------------------------------------------------------------- scene setup

def reset_scene():
    """Empty the scene completely (objects, meshes, materials)."""
    _materials.clear()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0


# ---------------------------------------------------------------- materials

def _hex_to_linear(hex_color):
    h = hex_color.lstrip("#")
    srgb = [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]

    def to_lin(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    return [to_lin(c) for c in srgb]


def mat(name, hex_color, roughness=0.85, metallic=0.0, emission=None):
    """Get or create a flat-colored material. `hex_color` like "#a0522d"."""
    if name in _materials:
        return _materials[name]
    m = bpy.data.materials.new(name)
    rgb = _hex_to_linear(hex_color)
    m.diffuse_color = (*rgb, 1.0)  # used by the workbench thumbnail render
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if emission:
        erg = _hex_to_linear(emission)
        key = "Emission Color" if "Emission Color" in bsdf.inputs else "Emission"
        bsdf.inputs[key].default_value = (*erg, 1.0)
        if "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = 1.0
    m.metallic = metallic
    m.roughness = roughness
    _materials[name] = m
    return m


# ---------------------------------------------------------------- primitives

def _finish(obj, name, material, loc, rot, scale):
    obj.name = name
    obj.data.name = name
    if material is not None:
        obj.data.materials.clear()
        obj.data.materials.append(material)
    obj.location = loc
    obj.rotation_euler = [math.radians(a) for a in rot]
    obj.scale = scale
    return obj


def _from_bmesh(name, bm):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def box(name, size=(1, 1, 1), loc=(0, 0, 0), rot=(0, 0, 0), material=None, bevel=0.0):
    """Axis-aligned box. `size` = (x, y, z) full extents; `loc` = center.
    `bevel` > 0 chamfers the edges (1 segment, stays low-poly)."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    if bevel > 0:
        bmesh.ops.bevel(bm, geom=bm.edges[:], offset=bevel, segments=1, affect="EDGES")
    return _finish(_from_bmesh(name, bm), name, material, loc, rot, (1, 1, 1))


def cylinder(name, radius=0.5, depth=1.0, verts=8, loc=(0, 0, 0), rot=(0, 0, 0),
             material=None, radius_top=None):
    """Z-aligned cylinder centered on `loc`. `radius_top` makes a tapered frustum."""
    bm = bmesh.new()
    r2 = radius if radius_top is None else radius_top
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=verts,
                          radius1=radius, radius2=r2, depth=depth)
    return _finish(_from_bmesh(name, bm), name, material, loc, rot, (1, 1, 1))


def cone(name, radius=0.5, depth=1.0, verts=8, loc=(0, 0, 0), rot=(0, 0, 0), material=None):
    """Z-aligned cone, base at loc.z - depth/2, tip at loc.z + depth/2."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=verts,
                          radius1=radius, radius2=0.0, depth=depth)
    return _finish(_from_bmesh(name, bm), name, material, loc, rot, (1, 1, 1))


def sphere(name, radius=0.5, segments=8, rings=6, loc=(0, 0, 0), rot=(0, 0, 0),
           scale=(1, 1, 1), material=None):
    """UV sphere (low segment counts look faceted/low-poly)."""
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=rings, radius=radius)
    return _finish(_from_bmesh(name, bm), name, material, loc, rot, scale)


def ico(name, radius=0.5, subdivisions=1, loc=(0, 0, 0), rot=(0, 0, 0),
        scale=(1, 1, 1), material=None):
    """Icosphere — the classic low-poly rock/bush/cloud blob."""
    bm = bmesh.new()
    kw = {"radius": radius} if bpy.app.version >= (3, 0, 0) else {"diameter": radius}
    bmesh.ops.create_icosphere(bm, subdivisions=subdivisions, **kw)
    return _finish(_from_bmesh(name, bm), name, material, loc, rot, scale)


def wedge(name, size=(1, 1, 1), loc=(0, 0, 0), rot=(0, 0, 0), material=None):
    """Triangular prism (ramp / roof): full height at -Y, slopes down to +Y.
    `size` = (x, y, z) extents, `loc` = bounding-box center."""
    sx, sy, sz = (s / 2 for s in size)
    verts = [(-sx, -sy, -sz), (sx, -sy, -sz), (sx, sy, -sz), (-sx, sy, -sz),
             (-sx, -sy, sz), (sx, -sy, sz)]
    faces = [(0, 3, 2, 1), (0, 1, 5, 4), (1, 2, 5), (0, 4, 3), (4, 5, 2, 3)]
    bm = bmesh.new()
    bv = [bm.verts.new(v) for v in verts]
    for f in faces:
        bm.faces.new([bv[i] for i in f])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return _finish(_from_bmesh(name, bm), name, material, loc, rot, (1, 1, 1))


def torus(name, major=0.5, minor=0.1, major_segments=12, minor_segments=6,
          loc=(0, 0, 0), rot=(0, 0, 0), material=None):
    """Z-axis torus (ring, tire, handle)."""
    bm = bmesh.new()
    rings = []
    for i in range(major_segments):
        a = 2 * math.pi * i / major_segments
        ring = []
        for j in range(minor_segments):
            b = 2 * math.pi * j / minor_segments
            r = major + minor * math.cos(b)
            ring.append(bm.verts.new((r * math.cos(a), r * math.sin(a), minor * math.sin(b))))
        rings.append(ring)
    for i in range(major_segments):
        r0, r1 = rings[i], rings[(i + 1) % major_segments]
        for j in range(minor_segments):
            j1 = (j + 1) % minor_segments
            bm.faces.new((r0[j], r1[j], r1[j1], r0[j1]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return _finish(_from_bmesh(name, bm), name, material, loc, rot, (1, 1, 1))


def poly_extrude(name, points, height, loc=(0, 0, 0), rot=(0, 0, 0), material=None):
    """Extrude a 2D outline (list of (x, y), counter-clockwise) up along Z by `height`.
    Great for silhouettes: blades, signs, leaves, logos. Base sits at loc.z."""
    bm = bmesh.new()
    bottom = [bm.verts.new((x, y, 0)) for x, y in points]
    top = [bm.verts.new((x, y, height)) for x, y in points]
    bm.faces.new(list(reversed(bottom)))
    bm.faces.new(top)
    n = len(points)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((bottom[i], bottom[j], top[j], top[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return _finish(_from_bmesh(name, bm), name, material, loc, rot, (1, 1, 1))


# ---------------------------------------------------------------- modifiers

def jitter(obj, amount=0.05, seed=0):
    """Randomly offset vertices — makes rocks/trees look hand-made."""
    import random
    rnd = random.Random(seed)
    for v in obj.data.vertices:
        v.co += Vector((rnd.uniform(-amount, amount),
                        rnd.uniform(-amount, amount),
                        rnd.uniform(-amount, amount)))
    return obj


def mirror_x(obj, name=None):
    """Duplicate `obj` mirrored across the X=0 plane (for symmetric parts)."""
    dup = obj.copy()
    dup.data = obj.data.copy()
    dup.name = name or obj.name + "_R"
    bpy.context.scene.collection.objects.link(dup)
    dup.location.x = -obj.location.x
    dup.rotation_euler.y = -obj.rotation_euler.y
    dup.rotation_euler.z = -obj.rotation_euler.z
    dup.scale.x = -obj.scale.x
    return dup


def group_rotate(objs, angle_deg, axis="Z", pivot=(0, 0, 0)):
    """Rotate several objects together around a pivot point."""
    rot = Matrix.Rotation(math.radians(angle_deg), 4, axis)
    p = Matrix.Translation(Vector(pivot))
    m = p @ rot @ p.inverted()
    for o in objs:
        o.matrix_world = m @ o.matrix_world


# ---------------------------------------------------------------- finalize / export

def _mesh_objects():
    return [o for o in bpy.context.scene.objects if o.type == "MESH"]


def finalize(object_name, smooth=False):
    """Apply transforms, join all meshes into one object named `object_name`,
    put the pivot at the bottom center, flat shade, fix normals.
    Returns stats dict."""
    objs = _mesh_objects()
    if not objs:
        raise RuntimeError("build() created no mesh objects")
    bpy.context.view_layer.update()  # refresh matrix_world after loc/rot edits

    # Bake each object's transform into its mesh data. Negative scale (mirror_x)
    # flips winding, so flip normals back for those.
    for o in objs:
        neg = (o.scale.x * o.scale.y * o.scale.z) < 0
        o.data.transform(o.matrix_world)
        o.matrix_world = Matrix.Identity(4)
        if neg:
            o.data.flip_normals()

    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    if len(objs) > 1:
        bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    obj.name = object_name
    obj.data.name = object_name

    # Clean up: merge duplicate verts, consistent outward normals.
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(obj.data)
    bm.free()

    # Pivot at bottom center.
    xs = [v.co.x for v in obj.data.vertices]
    ys = [v.co.y for v in obj.data.vertices]
    zs = [v.co.z for v in obj.data.vertices]
    offset = Vector(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, min(zs)))
    obj.data.transform(Matrix.Translation(-offset))
    obj.location = (0, 0, 0)

    for p in obj.data.polygons:
        p.use_smooth = smooth
    _dedupe_materials(obj)
    obj.data.update()

    obj.data.calc_loop_triangles()
    mats = list(obj.data.materials)
    per_mat = [0] * len(mats)
    for t in obj.data.loop_triangles:
        per_mat[t.material_index] += 1
    return {
        "tris": len(obj.data.loop_triangles),
        "verts": len(obj.data.vertices),
        "materials": [
            {"name": m.name, "color": _linear_to_hex(m.diffuse_color), "tris": n}
            for m, n in zip(mats, per_mat)
        ],
        "size_m": [round(max(xs) - min(xs), 3), round(max(ys) - min(ys), 3),
                   round(max(zs) - min(zs), 3)],
    }


def _linear_to_hex(rgba):
    def to_srgb(c):
        c = max(0.0, min(1.0, c))
        return c * 12.92 if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055
    return "#" + "".join(f"{round(to_srgb(c) * 255):02x}" for c in rgba[:3])


def _dedupe_materials(obj):
    """Keep materials minimal: merge slots that share a material or an identical
    look (color/roughness/metallic), and drop slots no face uses."""
    me = obj.data
    old = list(me.materials)
    keys, unique, remap = {}, [], {}
    used = {p.material_index for p in me.polygons}
    for i, m in enumerate(old):
        if i not in used or m is None:
            continue
        key = (_linear_to_hex(m.diffuse_color), round(m.roughness, 2), round(m.metallic, 2))
        if key not in keys:
            keys[key] = len(unique)
            unique.append(m)
        remap[i] = keys[key]
    indices = [remap.get(p.material_index, 0) for p in me.polygons]
    me.materials.clear()
    for m in unique:
        me.materials.append(m)
    for p, idx in zip(me.polygons, indices):
        p.material_index = idx


def export(slug, out_dir):
    """Write <slug>.fbx (Unity) and <slug>.glb (web viewer / Godot / three.js)."""
    os.makedirs(out_dir, exist_ok=True)
    bpy.ops.object.select_all(action="SELECT")

    # Unity: Y-up, -Z forward, transform baked in, so it imports with rotation 0
    # and scale 1 (no -90° X rotation on the root).
    bpy.ops.export_scene.fbx(
        filepath=os.path.join(out_dir, f"{slug}.fbx"),
        use_selection=True,
        object_types={"MESH"},
        apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_ALL",
        axis_forward="-Z",
        axis_up="Y",
        bake_space_transform=True,
        mesh_smooth_type="FACE",
        use_mesh_modifiers=True,
        add_leaf_bones=False,
        bake_anim=False,
        path_mode="STRIP",
    )

    bpy.ops.export_scene.gltf(
        filepath=os.path.join(out_dir, f"{slug}.glb"),
        export_format="GLB",
        use_selection=True,
        export_yup=True,
        export_apply=True,
    )


def _look_at(cam, target):
    direction = Vector(target) - cam.location
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def render_views(obj_name, out_path, views=None, size=512):
    """Render a workbench (no GPU needed) image of the model.
    `views` = list of (azimuth_deg, elevation_deg); one image per view is
    written as out_path (first) and out_path with _<i> suffix (others)."""
    scene = bpy.context.scene
    obj = bpy.data.objects[obj_name]
    views = views or [(35, 25)]

    corners = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    center = sum(corners, Vector()) / 8
    radius = max((c - center).length for c in corners)

    scene.render.engine = "BLENDER_WORKBENCH"
    scene.render.resolution_x = size
    scene.render.resolution_y = size
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    shading = scene.display.shading
    shading.light = "STUDIO"
    shading.color_type = "MATERIAL"
    shading.show_cavity = False
    shading.show_shadows = False
    shading.show_object_outline = True
    shading.object_outline_color = (0.05, 0.05, 0.05)
    shading.show_specular_highlight = False
    try:
        scene.display_settings.display_device = "sRGB"
        scene.view_settings.view_transform = "Standard"
    except TypeError:
        pass

    cam_data = bpy.data.cameras.new("ThumbCam")
    cam_data.lens = 50
    cam = bpy.data.objects.new("ThumbCam", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    fov = cam_data.angle
    dist = radius / math.sin(fov / 2) * 1.08

    paths = []
    base, ext = os.path.splitext(out_path)
    for i, (az, el) in enumerate(views):
        a, e = math.radians(az), math.radians(el)
        offset = Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
        cam.location = center + offset * dist
        _look_at(cam, center)
        path = out_path if i == 0 else f"{base}_{i}{ext}"
        scene.render.filepath = path
        bpy.ops.render.render(write_still=True)
        paths.append(path)

    bpy.data.objects.remove(cam)
    return paths
