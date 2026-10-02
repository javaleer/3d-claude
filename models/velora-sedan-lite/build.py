import bmesh
from lowpoly import *

NAME = "Velora Sedan Lite"
CATEGORY = "vehicle"
DESCRIPTION = "Game-budget (under 3k tris) version of the smooth silver Velora sedan."
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
# where it's high it's the greenhouse.
SECTIONS = [
    (-2.45, 0.30, 0.50, 0.70, 0.72, 0.60, 0.68, 0.60, 0.44),
    (-2.39, 0.22, 0.50, 0.77, 0.80, 0.78, 0.84, 0.76, 0.60),
    (-2.22, 0.20, 0.52, 0.84, 0.87, 0.84, 0.90, 0.82, 0.68),
    (-1.90, 0.20, 0.56, 0.88, 0.92, 0.86, 0.915, 0.84, 0.71),
    (-1.50, 0.20, 0.58, 0.91, 0.95, 0.87, 0.92, 0.85, 0.72),
    (-1.10, 0.20, 0.60, 0.94, 0.98, 0.87, 0.92, 0.85, 0.74),
    (-0.80, 0.20, 0.60, 0.96, 1.00, 0.87, 0.92, 0.85, 0.76),  # cowl
    (-0.45, 0.20, 0.60, 0.97, 1.22, 0.87, 0.92, 0.85, 0.74),
    (-0.10, 0.20, 0.60, 0.97, 1.42, 0.87, 0.92, 0.85, 0.70),
    (0.05, 0.20, 0.60, 0.97, 1.47, 0.87, 0.92, 0.85, 0.68),  # roof
    (0.50, 0.20, 0.60, 0.97, 1.475, 0.87, 0.92, 0.85, 0.68),   # B-pillar
    (0.62, 0.20, 0.60, 0.97, 1.475, 0.87, 0.92, 0.85, 0.68),
    (1.00, 0.20, 0.60, 0.98, 1.44, 0.87, 0.92, 0.85, 0.67),   # rear window
    (1.40, 0.20, 0.60, 1.00, 1.24, 0.87, 0.92, 0.85, 0.70),
    (1.80, 0.20, 0.60, 1.02, 1.06, 0.87, 0.92, 0.85, 0.72),   # trunk
    (2.10, 0.21, 0.61, 1.03, 1.06, 0.86, 0.91, 0.84, 0.70),
    (2.33, 0.26, 0.62, 1.01, 1.03, 0.83, 0.89, 0.80, 0.64),
    (2.45, 0.38, 0.62, 0.96, 0.97, 0.72, 0.82, 0.70, 0.54),
]
# Material slots per interval (index of the section it starts at).
WINDSHIELD = {6, 7, 8}
REAR_GLASS = {12, 13}
SIDE_GLASS = {7, 8, 9, 11, 12}
B_PILLAR = {10}
PAINT, GLASS, TRIM = 0, 1, 2


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


def build_body(paint, glass, trim):
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
                m = GLASS if i in SIDE_GLASS else TRIM if i in B_PILLAR else PAINT
            elif j in (6, 7, 8) and (i in WINDSHIELD or i in REAR_GLASS):
                m = GLASS
            f.material_index = m
    bm.faces.new(rings[0])
    bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    body = _link("Body", bm)
    for m in (paint, glass, trim):
        body.data.materials.append(m)

    sub = body.modifiers.new("Sub", "SUBSURF")
    sub.levels = 2
    _apply(body, sub)

    # Wheel arches: cut with cylinders; the well walls take the Trim material.
    for y in WHEEL_Y:
        for s in (1, -1):
            c = cylinder("ArchCut", radius=0.415, depth=0.40, verts=40,
                         loc=(s * 0.98, y, WHEEL_R), rot=(0, 90, 0), material=trim)
            bpy.context.view_layer.update()
            mod = body.modifiers.new("Arch", "BOOLEAN")
            mod.operation = "DIFFERENCE"
            mod.solver = "EXACT"
            mod.material_mode = "TRANSFER"
            mod.object = c
            _apply(body, mod)
            bpy.data.objects.remove(c)
    # Game budget: collapse-decimate the smooth shell; flat panels lose the
    # most triangles, curves keep theirs.
    body.data.calc_loop_triangles()
    dec = body.modifiers.new("Dec", "DECIMATE")
    dec.ratio = BODY_TRIS / len(body.data.loop_triangles)
    _apply(body, dec)
    return mark_sharp(body, 45)


def surface_x(body, y, z, side):
    """X of the body surface at (y, z) on one side, via ray cast."""
    hit, loc, *_ = body.ray_cast(Vector((side * 2.0, y, z)), Vector((-side, 0, 0)))
    return loc.x if hit else side * 0.9


# ---------------------------------------------------------------- build

WHEEL_Y = (-1.50, 1.38)
WHEEL_R = 0.36
BODY_TRIS = 1820


def build():
    paint = mat("Paint", "#a4a6a9", roughness=0.3, metallic=0.55)
    glass = mat("Glass", "#2c3034", roughness=0.08)
    trim = mat("Trim", "#1b1c1e", roughness=0.6)
    tire = mat("Tire", "#262628", roughness=0.9)
    rim = mat("Rim", "#a9acb0", roughness=0.3, metallic=0.75)
    head = mat("Headlight", "#e4eaee", roughness=0.1, emission="#cfd8de")
    tail = mat("Taillight", "#b3141c", roughness=0.2)

    body = build_body(paint, glass, trim)

    # Front: slim upper grille, big trapezoid lower intake (buried in the nose
    # so only the part that breaks the surface shows).
    box("UpperGrille", (0.70, 0.20, 0.09), loc=(0, -2.36, 0.64), material=trim)
    poly_extrude("LowerGrille", [(-0.64, 0.34), (0.64, 0.34), (0.50, 0.58), (-0.50, 0.58)],
                 0.20, loc=(0, -2.27, 0), rot=(90, 0, 0), material=trim)

    for s in (1, -1):
        # Swept headlights and wraparound taillights, also partly buried.
        box("Headlight", (0.52, 0.34, 0.085), loc=(s * 0.50, -2.26, 0.75),
            rot=(-8, 0, s * 18), material=head)
        box("Taillight", (0.46, 0.30, 0.13), loc=(s * 0.56, 2.33, 0.89),
            rot=(0, 0, s * -18), material=tail)

        # Mirrors on short stalks.
        box("MirrorStalk", (0.12, 0.06, 0.04), loc=(s * 0.86, -0.62, 1.02), material=trim)
        m = box("Mirror", (0.20, 0.11, 0.12), loc=(s * 0.96, -0.60, 1.06),
                rot=(0, 0, s * -8), material=paint)
        mark_sharp(m, 50)

        # Black side sill.
        box("Sill", (0.05, 2.10, 0.08), loc=(s * (surface_x(body, -0.05, 0.27, s) - s * 0.01),
                                              -0.05, 0.27), material=trim)

    box("RearDiffuser", (1.20, 0.10, 0.10), loc=(0, 2.42, 0.42), material=trim)

    # Wheels: round tires, rim lip, dark dish, five spokes and a center cap.
    tire_prof = [(0.25, -0.10), (WHEEL_R, -0.08), (WHEEL_R, 0.08), (0.34, 0.112), (0.25, 0.10)]
    lip_prof = [(0.25, 0.10), (0.225, 0.085)]
    dish_prof = [(0.226, 0.085), (0.0, 0.06)]
    cap_prof = [(0.06, 0.11), (0.0, 0.122)]
    for y in WHEEL_Y:
        for s in (1, -1):
            cx = s * 0.835
            loc = (cx, y, WHEEL_R)
            lathe("Tire", tire_prof, 16, loc, s, tire)
            lathe("RimLip", lip_prof, 16, loc, s, rim)
            lathe("RimDish", dish_prof, 16, loc, s, trim)
            lathe("HubCap", cap_prof, 8, loc, s, rim)
            for k in range(5):
                a = math.radians(72 * k + 18)
                # Spoke runs along its local Z; rotating by `a` about X points it
                # at (0, -sin a, cos a), so centre it 0.13 m out along that line.
                box("Spoke", (0.03, 0.06, 0.18),
                    loc=(cx + s * 0.088, y - 0.13 * math.sin(a), WHEEL_R + 0.13 * math.cos(a)),
                    rot=(math.degrees(a), 0, 0), material=rim)
