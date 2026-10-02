# Paste this section into the CLAUDE.md of your Unity game repo

## Importing low-poly assets from javaleer/3d-claude

Models come from the asset gallery repo `javaleer/3d-claude`. Each one lives at
`https://raw.githubusercontent.com/javaleer/3d-claude/main/public/models/<slug>/<slug>.glb`
(also mirrored on the gallery site at `https://3d-claude.vercel.app/models/<slug>/<slug>.glb`).
An `.fbx` with the same name sits next to it if ever needed,
with metadata (materials, colors, size, triangle count) in `.../<slug>/meta.json`.

Unity imports `.glb` through the glTFast package. If `Packages/manifest.json` has no
`"com.unity.cloud.gltfast"` entry, add it (for example `"com.unity.cloud.gltfast": "6.10.1"`), and
tell the user Unity will install it the next time the project opens.

When asked to add an asset:
1. Download `<slug>.glb` and `meta.json` with `curl -fsSL`. If the request only gives a slug,
   build the URL as shown above. If one host is blocked by the network settings,
   try the other one.
2. Put the GLB at `Assets/Models/Props/<slug>/<slug>.glb`. Use `Nature/`, `Buildings/`,
   `Vehicles/`, or `Characters/` instead of `Props/` based on `category` in meta.json.
3. Don't write `.meta` files by hand; Unity generates them on import. The model is already Y-up,
   scale 1, with its pivot at bottom-center, so no import-settings changes are needed.
4. If the user asks for a prefab or for it to be placed in a scene, create a prefab at
   `Assets/Prefabs/<slug>.prefab` only when you can do so reliably as YAML. Otherwise, say
   that dragging the GLB into the scene in the Unity editor is the remaining step.
5. Commit with the message `add asset: <slug>`.

Materials are embedded per color (for example `Wood`, `Leaves`) so they can be remapped in
Unity's Model Importer → Materials tab (or Extract Materials) to the game's own materials.
