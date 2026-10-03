import bmesh
from lowpoly import *

NAME = "Pearl Sedan"
CATEGORY = "vehicle"
DESCRIPTION = "Rounded pearl-white fastback sedan with a hexagonal black grille and five-spoke wheels."
SMOOTH = True  # sharp edges are marked per part below


# ---------------------------------------------------------------- helpers

def _link(name, bm):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(obj)
    return obj


def _apply(obj, mod):
    """Bake a modifier into the mesh (works with the pip bpy package)."""
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(obj.evaluated_get(dg))
    obj.modifiers.remove(mod)
    obj.data = me


def mark_sharp(obj, angle=40):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    lim = math.radians(angle)
    for e in bm.edges:
        if len(e.link_faces) == 2 and e.calc_face_angle(0) > lim:
            e.smooth = False
    bm.to_mesh(obj.data)
    bm.free()
    return obj


def lathe(name, profile, segs, loc, side, material):
    """Spin a (radius, x) profile around the X axis. `side` = +1/-1 mirrors x."""
    bm = bmesh.new()
    rings = []
    for r, x in profile:
        if r < 1e-6:
            rings.append([bm.verts.new((side * x, 0, 0))] * segs)
            continue
        rings.append([bm.verts.new((side * x, r * math.cos(2 * math.pi * k / segs),
                                    r * math.sin(2 * math.pi * k / segs)))
                      for k in range(segs)])
    for a, b in zip(rings, rings[1:]):
        for k in range(segs):
            q = [a[k], a[(k + 1) % segs], b[(k + 1) % segs], b[k]]
            uniq = list(dict.fromkeys(q))
            if len(uniq) >= 3:
                bm.faces.new(uniq)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    obj = _link(name, bm)
    obj.location = loc
    obj.data.materials.append(material)
    return mark_sharp(obj, 50)


# ---------------------------------------------------------------- body

# (y, z_bottom, z_widest, z_belt, z_crown, w_bottom, w_widest, w_belt, w_top)
# w_* are half-widths. Where z_crown is near z_belt the section is a hood/deck;
# where it's high it's the greenhouse. Fastback roof: long sloping rear glass.
SECTIONS = [
    (-2.42, 0.28, 0.48, 0.66, 0.68, 0.58, 0.66, 0.56, 0.40),
    (-2.36, 0.20, 0.50, 0.74, 0.77, 0.78, 0.84, 0.74, 0.58),
    (-2.18, 0.18, 0.52, 0.81, 0.84, 0.85, 0.90, 0.81, 0.66),
    (-1.85, 0.18, 0.56, 0.86, 0.90, 0.87, 0.92, 0.84, 0.70),
    (-1.45, 0.18, 0.58, 0.89, 0.93, 0.88, 0.93, 0.85, 0.72),
    (-1.05, 0.18, 0.60, 0.92, 0.96, 0.88, 0.93, 0.85, 0.74),
    (-0.80, 0.18, 0.60, 0.94, 0.98, 0.88, 0.93, 0.85, 0.76),  # cowl
    (-0.45, 0.18, 0.60, 0.95, 1.25, 0.88, 0.93, 0.85, 0.75),
    (-0.10, 0.18, 0.60, 0.95, 1.43, 0.88, 0.93, 0.85, 0.72),
    (0.30, 0.18, 0.60, 0.95, 1.47, 0.88, 0.93, 0.85, 0.71),  # roof
    (0.75, 0.18, 0.60, 0.96, 1.44, 0.88, 0.93, 0.85, 0.70),
    (1.15, 0.18, 0.60, 0.97, 1.33, 0.88, 0.93, 0.85, 0.70),   # rear glass
    (1.52, 0.18, 0.60, 0.99, 1.16, 0.88, 0.93, 0.85, 0.71),
    (1.85, 0.18, 0.60, 1.01, 1.05, 0.88, 0.93, 0.85, 0.72),   # trunk
    (2.12, 0.19, 0.61, 1.01, 1.04, 0.86, 0.91, 0.83, 0.69),
    (2.33, 0.24, 0.62, 0.98, 1.00, 0.82, 0.88, 0.79, 0.62),
    (2.43, 0.36, 0.62, 0.93, 0.94, 0.72, 0.80, 0.68, 0.52),
]
# Material slots per interval (index of the section it starts at).
WINDSHIELD = {6, 7}
REAR_GLASS = {11, 12}
SIDE_GLASS = {7, 8, 9, 10, 11}
PAINT, GLASS, BLACK = 0, 1, 2


def half_profile(zb, zm, zs, zr, wb, wm, ws, wt):
    g = zr - zs - 0.02
    return [
        (wb - 0.14, zb),
        (wb, zb + 0.06),
        (wm, zm),
        (ws, zs),
        (ws - 0.03, zs + 0.01),
        (wt, zs + 0.01 + g * 0.87),
        (wt * 0.94, zs + 0.01 + g * 0.96),
        (wt * 0.45, zr),
    ]


def build_body(paint, glass, black):
    bm = bmesh.new()
    rings = []
    for y, *p in SECTIONS:
        h = half_profile(*p)
        pts = [(x, y, z) for x, z in h] + [(-x, y, z) for x, z in reversed(h)]
        rings.append([bm.verts.new(p) for p in pts])
    n = len(rings[0])  # 16: right 0-7, left 8-15
    for i in range(len(rings) - 1):
        for j in range(n):
            k = (j + 1) % n
            f = bm.faces.new((rings[i][j], rings[i][k], rings[i + 1][k], rings[i + 1][j]))
            m = PAINT
            if j in (4, 5, 9, 10):  # side window strips
                m = GLASS if i in SIDE_GLASS else PAINT
            elif j in (6, 7, 8) and (i in WINDSHIELD or i in REAR_GLASS):
                m = GLASS
            f.material_index = m
    bm.faces.new(rings[0])
    bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    body = _link("Body", bm)
    for m in (paint, glass, black):
        body.data.materials.append(m)

    sub = body.modifiers.new("Sub", "SUBSURF")
    sub.levels = 1
    _apply(body, sub)

    # Wheel arches: cut with cylinders; the well walls take the Black material.
    for y in WHEEL_Y:
        for s in (1, -1):
            c = cylinder("ArchCut", radius=0.42, depth=0.40, verts=24,
                         loc=(s * 0.99, y, WHEEL_R), rot=(0, 90, 0), material=black)
            bpy.context.view_layer.update()
            mod = body.modifiers.new("Arch", "BOOLEAN")
            mod.operation = "DIFFERENCE"
            mod.solver = "EXACT"
            mod.material_mode = "TRANSFER"
            mod.object = c
            _apply(body, mod)
            bpy.data.objects.remove(c)
    # Game budget: merge near-flat faces, never across material borders, so
    # the window outlines stay clean.
    dec = body.modifiers.new("Dec", "DECIMATE")
    dec.decimate_type = "DISSOLVE"
    dec.angle_limit = math.radians(DISSOLVE_DEG)
    dec.delimit = {"MATERIAL"}
    _apply(body, dec)
    return mark_sharp(body, 45)


# ---------------------------------------------------------------- build

WHEEL_Y = (-1.48, 1.40)
WHEEL_R = 0.36
DISSOLVE_DEG = 3


def build():
    paint = mat("Paint", "#e7e1d8", roughness=0.35, metallic=0.2)
    glass = mat("Glass", "#3a3c3e", roughness=0.08)
    black = mat("Black", "#262728", roughness=0.8)  # grille, tires, arches
    rim = mat("Rim", "#6b6c6f", roughness=0.35, metallic=0.6)
    head = mat("Headlight", "#c9ced3", roughness=0.1, emission="#b8c0c8")
    tail = mat("Taillight", "#a3161f", roughness=0.2)

    build_body(paint, glass, black)

    # Front: big hexagonal grille and a slim lower intake, buried in the nose
    # so only the part that breaks the surface shows.
    poly_extrude("Grille", [(-0.30, 0.38), (0.30, 0.38), (0.48, 0.52), (0.42, 0.70),
                            (-0.42, 0.70), (-0.48, 0.52)],
                 0.22, loc=(0, -2.25, 0), rot=(90, 0, 0), material=black)
    poly_extrude("LowerIntake", [(-0.42, 0.26), (0.42, 0.26), (0.36, 0.33), (-0.36, 0.33)],
                 0.20, loc=(0, -2.25, 0), rot=(90, 0, 0), material=black)

    for s in (1, -1):
        # Thin swept headlights and wraparound taillights, partly buried.
        box("Headlight", (0.42, 0.34, 0.06), loc=(s * 0.62, -2.20, 0.74),
            rot=(-6, 0, s * 22), material=head)
        box("Taillight", (0.40, 0.30, 0.11), loc=(s * 0.60, 2.32, 0.88),
            rot=(0, 0, s * -18), material=tail)

        # Body-colour mirrors on short stalks.
        box("MirrorStalk", (0.10, 0.05, 0.04), loc=(s * 0.86, -0.58, 1.00), material=paint)
        m = box("Mirror", (0.15, 0.10, 0.10), loc=(s * 0.94, -0.56, 1.04),
                rot=(0, 0, s * -8), material=paint)
        mark_sharp(m, 50)

    # Wheels: round tires, grey rim lip, dark dish, five wide spokes and a cap.
    tire_prof = [(0.25, -0.10), (WHEEL_R, -0.08), (WHEEL_R, 0.08), (0.34, 0.112), (0.25, 0.10)]
    lip_prof = [(0.25, 0.10), (0.225, 0.085)]
    dish_prof = [(0.226, 0.085), (0.0, 0.06)]
    cap_prof = [(0.05, 0.11), (0.0, 0.122)]
    for y in WHEEL_Y:
        for s in (1, -1):
            cx = s * 0.835
            loc = (cx, y, WHEEL_R)
            lathe("Tire", tire_prof, 24, loc, s, black)
            lathe("RimLip", lip_prof, 24, loc, s, rim)
            lathe("RimDish", dish_prof, 24, loc, s, black)
            lathe("HubCap", cap_prof, 8, loc, s, rim)
            for k in range(5):
                a = math.radians(72 * k + 18)
                box("Spoke", (0.03, 0.08, 0.18),
                    loc=(cx + s * 0.088, y - 0.13 * math.sin(a), WHEEL_R + 0.13 * math.cos(a)),
                    rot=(math.degrees(a), 0, 0), material=rim)
