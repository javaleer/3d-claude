import bmesh
from lowpoly import *

NAME = "Velora Sedan"
CATEGORY = "vehicle"
DESCRIPTION = "Silver mid-size four-door sedan with a black grille and five-spoke wheels."


def loft(name, rings, face_mats, cap_front=True, cap_back=True):
    """Connect equal-length closed rings of (x, y, z) points with quads.
    face_mats(i, j) -> material index for the quad between ring i and i+1, edge j."""
    me = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(obj)
    bm = bmesh.new()
    vs = [[bm.verts.new(p) for p in ring] for ring in rings]
    n = len(rings[0])
    for i in range(len(rings) - 1):
        for j in range(n):
            k = (j + 1) % n
            f = bm.faces.new((vs[i][j], vs[i][k], vs[i + 1][k], vs[i + 1][j]))
            f.material_index = face_mats(i, j)
    if cap_front:
        bm.faces.new(vs[0]).material_index = face_mats(0, -1)
    if cap_back:
        bm.faces.new(vs[-1]).material_index = face_mats(len(rings) - 2, -1)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(me)
    bm.free()
    return obj


def build():
    paint = mat("Paint", "#a4a6a9", roughness=0.35, metallic=0.5)
    glass = mat("Glass", "#2c3034", roughness=0.1)
    trim = mat("Trim", "#1b1c1e", roughness=0.6)
    tire = mat("Tire", "#262628", roughness=0.9)
    rim = mat("Rim", "#a9acb0", roughness=0.35, metallic=0.7)
    head = mat("Headlight", "#e4eaee", emission="#cfd8de")
    tail = mat("Taillight", "#b3141c", roughness=0.3)

    # Lower body: cross-sections along Y (front at -Y).
    # (y, z_bot, z_mid, z_top, w_bot, w_mid, w_top) — w are half-widths.
    secs = [
        (-2.44, 0.28, 0.52, 0.76, 0.68, 0.78, 0.66),
        (-2.30, 0.24, 0.54, 0.87, 0.80, 0.90, 0.80),
        (-1.60, 0.28, 0.62, 0.94, 0.82, 0.90, 0.85),
        (-0.85, 0.28, 0.64, 0.98, 0.82, 0.90, 0.85),
        (1.30, 0.28, 0.64, 0.99, 0.82, 0.90, 0.85),
        (1.95, 0.28, 0.64, 1.03, 0.82, 0.90, 0.84),
        (2.36, 0.30, 0.64, 1.02, 0.80, 0.88, 0.78),
        (2.46, 0.40, 0.64, 0.97, 0.74, 0.82, 0.72),
    ]
    rings = []
    for y, zb, zm, zt, wb, wm, wt in secs:
        rings.append([(wb, y, zb), (wm, y, zm), (wt, y, zt),
                      (-wt, y, zt), (-wm, y, zm), (-wb, y, zb)])
    body = loft("Body", rings, lambda i, j: 0)
    body.data.materials.append(paint)

    # Greenhouse: windshield, roof, rear window; sides are glass.
    # (y, z_belt, z_top, w_belt, w_top)
    cab = [
        (-0.85, 0.98, 1.00, 0.84, 0.80),
        (0.05, 0.98, 1.48, 0.84, 0.66),
        (0.95, 0.99, 1.48, 0.84, 0.66),
        (1.95, 1.03, 1.05, 0.83, 0.78),
    ]
    crings = [[(wb, y, zb), (wt, y, zt), (-wt, y, zt), (-wb, y, zb)]
              for y, zb, zt, wb, wt in cab]

    def cab_mat(i, j):
        if j == 1 and i == 1:
            return 0  # roof
        if j == 3:
            return 0  # hidden bottom
        return 1  # glass

    cabin = loft("Cabin", crings, cab_mat, cap_front=False, cap_back=False)
    cabin.data.materials.append(paint)
    cabin.data.materials.append(glass)

    # B-pillar and roof-edge trim.
    for s in (1, -1):
        box("BPillar", (0.04, 0.10, 0.40), loc=(s * 0.75, 0.50, 1.22),
            rot=(0, s * -22, 0), material=trim)

    # Front: grille + lower intake, headlights.
    box("Grille", (1.30, 0.06, 0.24), loc=(0, -2.43, 0.40), material=trim)
    box("UpperGrille", (0.80, 0.06, 0.08), loc=(0, -2.43, 0.66), material=trim)
    for s in (1, -1):
        box("Headlight", (0.46, 0.14, 0.09), loc=(s * 0.48, -2.38, 0.78),
            rot=(0, 0, s * 14), material=head)
        box("Taillight", (0.44, 0.12, 0.14), loc=(s * 0.52, 2.42, 0.88),
            rot=(0, 0, s * -10), material=tail)
        box("Mirror", (0.20, 0.10, 0.10), loc=(s * 0.95, -0.72, 1.06), material=paint)

    # Rear bumper shadow strip.
    box("RearDiffuser", (1.20, 0.06, 0.10), loc=(0, 2.44, 0.42), material=trim)

    # Wheels.
    for y in (-1.50, 1.38):
        for s in (1, -1):
            cylinder("Tire", radius=0.36, depth=0.22, verts=12,
                     loc=(s * 0.86, y, 0.36), rot=(0, 90, 0), material=tire)
            cylinder("Rim", radius=0.25, depth=0.04, verts=10,
                     loc=(s * 0.975, y, 0.36), rot=(0, 90, 0), material=rim)
