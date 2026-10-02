import math

import bmesh
import bpy
from lowpoly import *

NAME = "Velora Sedan"
CATEGORY = "vehicle"
DESCRIPTION = "Silver mid-size four-door sedan with a wide black grille and five-spoke rims."

L = 4.85            # overall length (Y), front at -Y
FRONT, REAR = -L / 2, L / 2
AXLE_F, AXLE_R = -1.47, 1.35
WHEEL_R = 0.35
ARCH = [(-0.42, 0.0), (-0.36, 0.52), (-0.2, 0.70), (0.0, 0.75), (0.2, 0.70), (0.36, 0.52), (0.42, 0.0)]


def deck(y):
    """Height of the hood / beltline / trunk lid at station y (piecewise linear)."""
    pts = [(FRONT, 0.72), (-2.25, 0.84), (-1.5, 0.91), (-0.95, 0.96), (0.4, 0.99),
           (1.6, 1.03), (2.25, 1.03), (REAR, 0.96)]
    for (y0, z0), (y1, z1) in zip(pts, pts[1:]):
        if y0 <= y <= y1:
            return z0 + (z1 - z0) * (y - y0) / (y1 - y0)
    return pts[-1][1]


def plan(y):
    """Half-width scale at station y: the nose and tail pinch in, sides stay full."""
    if y < -2.0:
        return 0.86 + 0.14 * (y - FRONT) / (-2.0 - FRONT)
    if y > 2.1:
        return 1.0 - 0.06 * (y - 2.1) / (REAR - 2.1)
    return 1.0


def _mesh_obj(name, bm):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def loft(name, rings, material):
    """Connect equal-length rings of 3D points into a closed tube with end caps."""
    bm = bmesh.new()
    vr = [[bm.verts.new(p) for p in r] for r in rings]
    n = len(rings[0])
    for a, b in zip(vr, vr[1:]):
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((a[i], a[j], b[j], b[i]))
    bm.faces.new(vr[0])
    bm.faces.new(list(reversed(vr[-1])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    obj = _mesh_obj(name, bm)
    obj.data.materials.append(material)
    return obj


def body_ring(y, bottom):
    s = plan(y)
    zt = deck(y)
    zm = max(0.60, bottom + 0.04)
    wb, wm, wt = 0.84 * s, 0.92 * s, 0.82 * s
    return [(-wb, y, bottom), (wb, y, bottom), (wm, y, zm), (wt, y, zt), (-wt, y, zt), (-wm, y, zm)]


def build():
    paint = mat("Paint", "#a8aaad", roughness=0.35, metallic=0.5)
    glass = mat("Glass", "#2e3236", roughness=0.1)
    black = mat("Black", "#1c1d1f", roughness=0.7)
    rim = mat("Rim", "#b9bcc0", roughness=0.35, metallic=0.7)
    head = mat("Headlight", "#eef3f7", emission="#dfe9f2")
    tail = mat("Taillight", "#b3141c", emission="#5a0508")

    # ---- lower body: lofted stations from nose to tail, with wheel-arch cut-outs
    stations = [(FRONT, 0.30), (-2.28, 0.20), (-2.05, 0.20)]
    for axle in (AXLE_F, AXLE_R):
        stations += [(axle + dy, 0.20 if h == 0 else 0.20 + h * 0.75) for dy, h in ARCH]
        if axle == AXLE_F:
            stations += [(0.0, 0.20)]
    stations += [(2.2, 0.22), (REAR, 0.36)]
    loft("Body", [body_ring(y, b) for y, b in stations], paint)

    # Dark underbody filler so the arches read as wheel wells, not holes.
    box("Underbody", (1.36, 3.9, 0.48), loc=(0, -0.05, 0.46), material=black)

    # ---- greenhouse: tapered prism, glass sides, painted roof
    prof = [(-0.95, 0.95), (-0.05, 1.46), (0.95, 1.44), (1.62, 1.02)]

    def half_w(z):
        return 0.81 - (z - 0.95) / 0.5 * 0.21

    bm = bmesh.new()
    R = [bm.verts.new((half_w(z), y, z)) for y, z in prof]
    Lv = [bm.verts.new((-half_w(z), y, z)) for y, z in prof]
    faces = [
        (R, glass),                                    # right side windows
        (list(reversed(Lv)), glass),                   # left side windows
        ((Lv[0], R[0], R[1], Lv[1]), glass),           # windshield
        ((Lv[1], R[1], R[2], Lv[2]), paint),           # roof
        ((Lv[2], R[2], R[3], Lv[3]), glass),           # rear window
    ]
    for verts, _ in faces:
        bm.faces.new(verts)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    for f, (_, m) in zip(bm.faces, faces):
        f.material_index = 0 if m is glass else 1
    cab = _mesh_obj("Cabin", bm)
    cab.data.materials.append(glass)
    cab.data.materials.append(paint)

    # ---- front: upper grille band, big lower grille, slim headlights
    box("GrilleUpper", (0.80, 0.06, 0.09), loc=(0, FRONT - 0.005, 0.64), material=black)
    poly = [(-0.46, 0.0), (0.46, 0.0), (0.56, 0.22), (-0.56, 0.22)]
    poly_extrude("GrilleLower", poly, 0.06, loc=(0, FRONT + 0.03, 0.32), rot=(90, 0, 0),
                 material=black)
    for sx in (-1, 1):
        box("Headlight", (0.30, 0.10, 0.06), loc=(sx * 0.50, FRONT + 0.03, 0.68),
            rot=(0, 0, sx * 12), material=head)
        box("Taillight", (0.36, 0.08, 0.09), loc=(sx * 0.60, REAR - 0.02, 0.88),
            material=tail)
        # Mirrors
        box("Mirror", (0.18, 0.08, 0.10), loc=(sx * 0.86, -0.72, 1.04), material=paint)

    # ---- wheels
    for y in (AXLE_F, AXLE_R):
        for sx in (-1, 1):
            cylinder("Tire", radius=WHEEL_R, depth=0.24, verts=10, loc=(sx * 0.78, y, WHEEL_R),
                     rot=(0, 90, 0), material=black)
            cylinder("Rim", radius=0.25, depth=0.02, verts=10, loc=(sx * 0.91, y, WHEEL_R),
                     rot=(0, 90, 0), material=rim)
