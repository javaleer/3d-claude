# Low-poly asset factory

This repo turns a reference image (usually sent from the Claude mobile app) into a
game-ready low-poly 3D model for a **Unity** game, and publishes it to a gallery site on
Vercel (`public/`) where it can be viewed, inspected per material, and downloaded.

Typical request: *[photo]* "make this" / "make this, call it mossy-rock".

## The user's words come first

Everything under "Modeling rules" below is a **default**, used only where the request doesn't
say otherwise. Whatever the user asks for in the message overrides it, including detail level,
triangle count, colors, number of materials, size, shading, style, or which parts to include or
skip. Expect casual, one-off, mixed instructions and follow them literally:

- "use red for the body and blue for the wheels" → those exact colors, even if the photo differs.
- "make it detailed" / "high poly" / "smooth" → raise the triangle budget to match (5,000+ is fine)
  and use more segments, bevels, or `SMOOTH = True` as fits. "super low poly" → go below the budgets.
- "one material" / "give the windows their own material" → do exactly that.
- "make it 2 m tall", "chunkier", "cartoony", "add a spoiler", "no mirrors" → do it.
- No photo, just words ("make a wooden barrel") → design it from the description.
- Instructions apply to that request (and its follow-up edits) only. They don't become the new
  default unless the user says "always" or "from now on". In that case, update this file.

If an instruction conflicts with the photo, follow the instruction. If it's genuinely ambiguous
(for example "make it red" on a model with five materials), pick the most likely meaning, do it,
and say what you chose in the reply. Don't stop to ask. In the reply, list which defaults you
changed because of the instructions (for example "4,800 tris since you asked for detailed").

## Recipe for a new model

1. **Name it.** Pick a short kebab-case slug (`mossy-rock`, `street-lamp`) unless one is given.
   If `models/<slug>/` exists, ask whether to replace it or choose a new slug.
2. **Study the image and the instructions.** Note anything the user asked for (it overrides the defaults below). Then, before writing code, note: overall silhouette and proportions,
   the distinct parts, the distinct flat colors (that's your material list), real-world
   size in meters, and which details are geometry versus which can be dropped.
3. **Set up Blender** if needed: `bash scripts/setup.sh` (no-op when already installed).
4. **Write `models/<slug>/build.py`** (see the API below and `models/wooden-crate/build.py`).
   If the image exists as a file in the session, copy it to `models/<slug>/reference.<ext>`.
5. **Build and check:** `bash scripts/build.sh <slug> --check`
   - It prints the triangle count and per-material triangle counts.
   - **Look at the renders** in `.check/<slug>/` (`view.png` front, `view_1` right, `view_2` back,
     `view_3` top, `view_4` 3/4, `view_5` 3/4 rear) and compare them with the reference.
     Fix proportions, colors, and missing or extra parts, then rebuild. Iterate 2–4 times
     until it reads as the same object at a glance.
6. **Publish:** commit `models/<slug>/`, `public/models/<slug>/`, and `public/models.json` with the
   message `asset: <slug>`. Push to the session's branch (or `claude/<slug>`) and open a PR
   titled `asset: <Name>` that includes the thumbnail path and stats. Vercel posts a preview
   link on the PR.
7. **Reply briefly** with the triangle count, the material list (name + hex), the size in meters,
   and the PR link. Note that the Vercel preview link appears on the PR within a minute or two.

For **edits** ("make the roof red", "fewer polys"), change `models/<slug>/build.py`, rebuild
with `--check`, and push to the same branch/PR.

## Modeling rules (defaults, overridden by anything the user says)

**By default, as low-poly as possible while still looking like the image.**
- Match the *silhouette* first; it's what reads in-game. Spend triangles only where they change
  the outline or a clearly visible shape. Don't model detail that's smaller than ~5% of the object.
- Default budgets (triangles): small prop 50–300 · medium prop/furniture 300–800 ·
  vehicle/large prop/character 800–2,000. Going over needs a reason (such as the user asking for detail); say what it was.
- Cylinders and cones: 6–8 sides (12 only for large round hero parts). Spheres: `ico(subdivisions=1)`
  or `sphere(segments=8, rings=6)`. Avoid `bevel` unless the chamfer is clearly visible in the image.
- Don't build hidden geometry: no faces fully buried inside other parts, and no parts that can't be
  seen from any angle. Prefer one box with the right proportions over several stacked boxes.
- Use `jitter()` on organic shapes (rocks, foliage, trees) so they look hand-made, not procedural.
- Flat shading (the default). Set `SMOOTH = True` only for something that's clearly smooth in the image.

**Materials, by default: separate, and as few as possible.**
- One material per *distinct color/surface* in the image, and no more. Typically 2–5 per model.
  Merge near-identical shades into one. Never use textures, UVs, or vertex colors; every color is
  its own named material so it can be swapped in Unity.
- Create each material **once** with `mat()` and reuse the variable for every part with that
  surface. The pipeline also merges identical-looking materials automatically.
- Names: short PascalCase describing the surface: `Wood`, `WoodDark`, `Leaves`, `Bark`, `Metal`,
  `Glass`, `Fabric`, `Stone`. Colors are hex values sampled from the image's lit (not shadowed) areas.
- Metal: `mat("Metal", "#8a8f96", roughness=0.4, metallic=0.7)`. Glowing parts: `emission="#ffcc66"`.

**Orientation / scale (Unity):** build in meters with Blender Z-up. The front of the object faces
**-Y** (toward the camera in `view.png`). The pipeline puts the pivot at bottom-center and exports
FBX as Y-up with scale 1, so the asset imports into Unity standing upright, rotation 0, real size.

## build.py API

```python
from lowpoly import *          # scripts/lib/lowpoly.py

NAME = "Street Lamp"           # display name (optional; defaults from slug)
CATEGORY = "prop"              # prop | nature | building | vehicle | character | item
DESCRIPTION = "One line about it."
SMOOTH = False                 # optional

def build():
    metal = mat("Metal", "#2f3338", roughness=0.5, metallic=0.6)
    glass = mat("Glass", "#ffe9a8", emission="#ffcc66")
    cylinder("Pole", radius=0.06, depth=3.0, verts=6, loc=(0, 0, 1.5), material=metal)
    box("Head", (0.35, 0.35, 0.3), loc=(0, 0, 3.1), material=glass)
```

All `loc` values are object centers, `rot` is in degrees, and sizes are full extents in meters.
- `box(name, size=(x,y,z), loc, rot, material, bevel=0)`
- `cylinder(name, radius, depth, verts=8, loc, rot, material, radius_top=None)` creates a Z-axis cylinder; `radius_top` makes a taper
- `cone(name, radius, depth, verts=8, loc, rot, material)`
- `sphere(name, radius, segments=8, rings=6, loc, rot, scale, material)`
- `ico(name, radius, subdivisions=1, loc, rot, scale, material)` (rocks, bushes, blobs)
- `wedge(name, size, loc, rot, material)` creates a ramp/roof prism, tall at -Y
- `torus(name, major, minor, major_segments=12, minor_segments=6, loc, rot, material)`
- `poly_extrude(name, [(x,y),...], height, loc, rot, material)` extrudes a 2D outline along Z
  (CCW points; base at loc.z); good for blades, signs, leaves, and flat cut-outs
- `jitter(obj, amount, seed)`, `mirror_x(obj)`, `group_rotate(objs, deg, axis, pivot)`
- Raw `bpy`/`bmesh` are available for anything else. Just leave mesh objects in the scene;
  the pipeline joins them into one mesh.

## Pipeline facts

- `scripts/build.sh` → `scripts/build_model.py` runs `build()`, then `finalize` (apply transforms,
  join, merge duplicate verts, fix normals, pivot at bottom-center, dedupe materials) → exports
  `public/models/<slug>/<slug>.fbx` (Unity) and `.glb` (web viewer), `thumb.png`, and `meta.json`
  → rebuilds `public/models.json`.
- `public/` is the static gallery site (no build step; Vercel serves it as-is). Don't hand-edit
  `models.json` or `meta.json`; they're generated.
- `.check/` and `.venv/` are git-ignored.
